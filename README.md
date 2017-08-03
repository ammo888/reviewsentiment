# Review Sentiment Analysis

## Before Getting Started

  This project assumes that you have already collected review information that contain basic information such as the author, the review text, and preferrably the detected language of the review.

  Additionally, you need a Google Cloud account with access the the Natural Language and Translate API. You will need service account credentials downloaded.

## Getting Started

  Clone repository
  ```fish
  $ git clone https://github.com/ammo888/reviewsentiment
  ```

  Create virtual environment, install dependencies
  ```fish
  $ cd reviewsentiment
  $ python3 -m venv env
  $ source env/bin/activate
  (env) pip install -r requirements.txt # might need sudo
  ```

  Setup environment variable for API access
  ```fish
  (env) export GOOGLE_AUTHENTICATION_CREDENTIALS=<path-to-credentials.json>
  ```

  Running the program
  ```fish
  (env) python analysis.py <config.json> <# of reviews>
  ```
  `sentiment.csv` should be created with the same information as the original csv file, but with extra three headers: `parent_topic`, `topic`, `sentiment`.

  For each topic that is identified to match the configuration file, the program creates a copy of the row and adds the topic and sentiment information.

  The second argument is the number of reviews to parse - useful if you don't want to analyze all the reviews. If the argument is 0, then the program will analyze the entire file.

## Configuration file

  The configuration files, `config.json`, and `configlong.json`, are just examples for you to use. Here's the general structure of the file:
  ```json
    {
        "data" : "<path-to-reviews>.csv",
        "topics" : {
            "parent_topic1" : [
                "topic1",
                "topic2",
                ...
            ],
            "parent_topic2" : [
                ...
            ]
        ...
        },
        "classes" : {
            "negative" : {
                "min" : <float>,
                "max" : <float>
            },
            "positive" : {
                "min" : <float>,
                "max" : <float>
            },
            ...
        }
    }
  ```

### Data

  `"data"` value is the relative path to the reviews CSV file. The required fieldnames are:

  * `"detected_lang"` - this is used to determine whether the Translation API is needed to be called to translate to English.

  * `"text"` - the body of the review

### Topics

  `"topics"` contains the parent topics and the subtopics that the program looks for in a review. Examples of parent topics:

  * `"housekeeping"`
  * `"service"`
  * `"facilities"`

  Each parent topic has a list of subtopics associated with it, such as:

  * `"bed"`
  * `"wifi"`
  * `"breakfast"`

  The program searches in entities that the Google API has identified for occurences of the provided subtopics, and takes note of the sentiment score.

### Classes

  `"classes"` contains the sentiment classifications based on the value.

  The Natural Language API provides sentiment scores from `-1.0` to `1.0`, with the higher the score being more positive.

  You can specify the name of the classification and the `min` and `max` for the range of sentiment scores that will be classified as such.
