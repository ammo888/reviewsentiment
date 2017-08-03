import sys
import json
import csv
from functools import reduce, partial
from collections import defaultdict
import six
from google.cloud.gapic.language.v1beta2 import enums
from google.cloud.gapic.language.v1beta2 import language_service_client
from google.cloud.proto.language.v1beta2 import language_service_pb2
from google.cloud import translate

class EntitySentimentAnalysis():
    def __init__(self):
        self.language_client = language_service_client.LanguageServiceClient()
        self.translate_client = translate.Client()
        self.encoding = enums.EncodingType.UTF16 if sys.maxunicode == 65535 else enums.EncodingType.UTF32
        with open(sys.argv[1]) as config:
            config_json = json.load(config)
            self.data = config_json['data']
            self.topics = config_json['topics']
            self.sentiment_classes = config_json['classes']

    def analyze_reviews(self):
        with open(self.data, 'r') as csvfile:
            review_reader = csv.DictReader(csvfile)
            with open('sentiment.csv', 'w') as outfile:
                writer_fieldnames = review_reader.fieldnames + ['parent_topic', 'topic', 'sentiment']
                review_writer = csv.DictWriter(outfile, fieldnames=writer_fieldnames)
                review_writer.writeheader()
                count = 0
                for i, row in enumerate(review_reader):
                    if i > 100:
                        break

                    print(i, row['author'], row['text'][:20]+'...')

                    translated_text = row['text']
                    if row['detected_lang'] != 'en':
                        translated_text = self.translate_client.translate(row['text'])['translatedText']

                    sentiments = self.entity_sentiment(translated_text)
                    if sentiments:
                        for parent_topic in sentiments:
                            for topic in sentiments[parent_topic]:
                                row['parent_topic'] = parent_topic
                                row['topic'] = topic
                                row['sentiment'] = sentiments[parent_topic][topic]
                                review_writer.writerow(row)

    def entity_sentiment(self, text):
        if isinstance(text, six.binary_type):
            text = text.decode('utf-8')

        document = language_service_pb2.Document()
        document.content = text.encode('utf-8')
        document.type = enums.Document.Type.PLAIN_TEXT
        
        result = self.language_client.analyze_entity_sentiment(
            document, self.encoding)

        sentiments = defaultdict(partial(defaultdict, float))
        for entity in result.entities:
            if entity.sentiment.score != 0 and entity.sentiment.magnitude != 0:
                for parent_topic in self.topics:
                    for topic in self.topics[parent_topic]:
                        if topic in entity.name.lower():
                            sentiments[parent_topic][topic] += entity.sentiment.score
        def classify(self, val):
            for sent_class in self.sentiment_classes:
                class_range = self.sentiment_classes[sent_class]
                if class_range['min'] <= val and val < class_range['max']:
                    return sent_class
            return None
        sentiments = {pt:{t:classify(self, sentiments[pt][t]) for t in sentiments[pt]} for pt in sentiments}
        return sentiments

if __name__ == '__main__':
    assert len(sys.argv) == 2, "Usage: python newanalysis.py <configname.json>"
    analyzer = EntitySentimentAnalysis()
    analyzer.analyze_reviews()
