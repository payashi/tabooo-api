import os
import requests
from collections import defaultdict
from concurrent import futures

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import language_v1
from lxml import html

app = Flask(__name__)
CORS(app, resources={r"/classify": {"origins": "chrome-extension://eidcnjleeocfiinfohngojmekjeaknej"}})

# Set up for Cloud Natural Language API
TYPE = language_v1.Document.Type.PLAIN_TEXT
CONTENT_CATEGORY_VERSION = (
    language_v1.ClassificationModelOptions.V2Model.ContentCategoriesVersion.V2
)
client = language_v1.LanguageServiceClient()

# Find text in the following xpath tags
XPATH_TAGS = './/title|.//h1|.//h2|.//h3|.//h4|.//h5|.//h6|.//p'

def extract_text_from_url(url: str):
    try:
        html_text = requests.get(url).text
        root = html.fromstring(html_text)
        text_list = map(lambda tag: tag.text_content(), root.xpath(XPATH_TAGS))
        return ' '.join(text_list)
    except:
        # Accept only http(s) scheme
        raise Exception("Invalid scheme or content")

def classify_single_url(url: str):
    try:
        # Clip letters to keep bills down
        text = extract_text_from_url(url)[:990]
        document = {
            "content": text,
            "type_": TYPE,
        }
        response = client.classify_text(
            request={
                "document": document,
                "classification_model_options": {
                    "v2_model": {"content_categories_version": CONTENT_CATEGORY_VERSION}
                },
            }
        )
        # `category` must be something like `/first(/second(/third))`
        category = response.categories[0].name
        category = category.split('/')[1]
    except:
        category = 'Unclassified'

    return (f"{category}", f"{url}")


@app.post('/classify')
def classify():
    ret = defaultdict(list)

    try:
        with futures.ThreadPoolExecutor() as executor:
            future_list = [executor.submit(classify_single_url, url) for url in request.json['urls']]
            for future in futures.as_completed(fs=future_list):
                category, url = future.result()
                ret[category].append(url)
        return jsonify(ret)

    except:
        return 'threading failed', 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))