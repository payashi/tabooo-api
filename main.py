import os
import requests
from collections import defaultdict
from concurrent import futures

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import language_v1

app = Flask(__name__)
CORS(app, resources={r"/classify": {"origins": "chrome-extension://*"}})

# Set up for Cloud Natural Language API
client = language_v1.LanguageServiceClient()
type_ = language_v1.Document.Type.HTML
content_categories_version = (
    language_v1.ClassificationModelOptions.V2Model.ContentCategoriesVersion.V2
)

def classify_single_url(url: str):
    try:
        document = {
            "content": requests.get(url).text,
            "type_": type_,
        }
        response = client.classify_text(
            request={
                "document": document,
                "classification_model_options": {
                    "v2_model": {"content_categories_version": content_categories_version}
                },
            }
        )
        # category must be something like `/first(/second(/third))`
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