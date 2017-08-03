"""Review analysis"""
import sys
import csv
import json
from functools import partial
from collections import defaultdict, Counter
from google.cloud.gapic.language.v1beta2 import enums
from google.cloud.gapic.language.v1beta2 import language_service_client
from google.cloud.proto.language.v1beta2 import language_service_pb2
from google.cloud import translate

class EntitySentimentAnalysis():
    """Class for analyzing reviews"""
    def __init__(self):
        # Client to Natural Language API (v1beta2)
        self.language_client = language_service_client.LanguageServiceClient()
        # Client to Translate API
        self.translate_client = translate.Client()
        # Encoding to pass to API
        self.encoding = enums.EncodingType.UTF32
        # Open config file
        with open(sys.argv[1]) as config:
            config_json = json.load(config)
            # Data, topic, and classification information
            self.data = config_json['data']
            self.topics = config_json['topics']
            self.sentiment_classes = config_json['classes']

    def analyze_reviews(self):
        """Analyzes reviews using NL API and Translate API"""
        with open(self.data, 'r') as csvfile:
            # CSV reader
            review_reader = csv.DictReader(csvfile)
            with open('sentiment.csv', 'w') as outfile:
                # Headers for output CSV file
                writer_fieldnames = review_reader.fieldnames + \
                                    ['translated_text', 'parent_topic', 'topic', 'sentiment']
                # CSV writer to output
                review_writer = csv.DictWriter(outfile, fieldnames=writer_fieldnames)
                # Write header
                review_writer.writeheader()
                # Go through each review
                for i, row in enumerate(review_reader):
                    # Go through all reviews
                    if int(sys.argv[2]) == 0:
                        pass
                    # Go up to specified review
                    elif i >= int(sys.argv[2]):
                        break
                    # Print review number and part of the review text
                    print(i, row['author'], row['text'][:30]+'...')

                    # Translate non-english reviews to english
                    # and add to output row
                    translated_text = row['text']
                    if row['detected_lang'] != 'en':
                        translation = self.translate_client.translate(row['text'])
                        translated_text = translation['translatedText']
                    row['translated_text'] = translated_text

                    # Entity sentiment analysis
                    sentiments = self.entity_sentiment(translated_text)
                    # If any relevant entities identified
                    if sentiments:
                        for parent_topic in sentiments:
                            for topic in sentiments[parent_topic]:
                                # Write row with topic and sentiment information
                                row['parent_topic'] = parent_topic
                                row['topic'] = topic
                                row['sentiment'] = sentiments[parent_topic][topic]
                                review_writer.writerow(row)
                    # Default information to 'unknown'
                    else:
                        row['parent_topic'] = 'unknown'
                        row['topic'] = 'unknown'
                        row['sentiment'] = 'unknown'
                        review_writer.writerow(row)

    def entity_sentiment(self, text: str):
        """Identifies relevant entities and records sentiment"""

        # Create document, set content, and type
        document = language_service_pb2.Document()
        document.content = text
        document.type = enums.Document.Type.PLAIN_TEXT

        # Result from API call
        result = self.language_client.analyze_entity_sentiment(
            document, self.encoding)
        # Nested dictionary to hold parent topic, topic, and sentiment
        sentiments = defaultdict(partial(defaultdict, float))
        # Counter for appearances of each topic for normalization
        topic_counter = Counter()
        # Go through each entity
        for entity in result.entities:
            # If sentiment is present
            if entity.sentiment.score != 0 and entity.sentiment.magnitude != 0:
                # Go through each parent topic
                for parent_topic in self.topics:
                    # Go through each subtopic
                    for topic in self.topics[parent_topic]:
                        # If topic present in entity
                        if topic in entity.name.lower():
                            # Add to dictionary
                            sentiments[parent_topic][topic] += entity.sentiment.score
                            # Add to counter
                            topic_counter[topic] += 1

        def classify(self, val):
            """Classifies entity sentiment by score"""
            for sent_class in self.sentiment_classes:
                class_range = self.sentiment_classes[sent_class]
                if class_range['min'] <= val and val < class_range['max']:
                    return sent_class
            return None

        # Normalize sentiment scores and classify
        sentiments = {pt:{t:classify(self, sentiments[pt][t] / topic_counter[t])
                          for t in sentiments[pt]} for pt in sentiments}
        return sentiments

def main():
    """Review analysis logic"""
    assert len(sys.argv) == 3, "Usage: python newanalysis.py <configname.json> <# of reviews>"
    assert sys.argv[2].isdigit(), "<# of reviews> has to be an integer"
    analyzer = EntitySentimentAnalysis()
    analyzer.analyze_reviews()

if __name__ == '__main__':
    main()
