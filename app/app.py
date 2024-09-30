import time
import requests
from elasticsearch import Elasticsearch, helpers
from flask import Flask, request, jsonify
from elasticsearch.exceptions import ConnectionError

# Initialize Flask app
app = Flask(__name__)

# Initialize Elasticsearch client
es = Elasticsearch(hosts=["http://elasticsearch:9200"])

# Load Nobel Prize data into Elasticsearch with a retry mechanism
def load_data():
    url = "https://api.nobelprize.org/v1/prize.json"
    response = requests.get(url)
    data = response.json()

    # Retry connecting to Elasticsearch up to 5 times
    for i in range(5):
        try:
            es.info()  # Try to connect to Elasticsearch
            break
        except ConnectionError:
            print(f"Elasticsearch not ready, retrying... ({i+1}/5)")
            time.sleep(5)
    else:
        print("Failed to connect to Elasticsearch")
        return

    # Check if the index already exists
    if not es.indices.exists(index="nobel_prizes"):
        print("Index not found. Creating and loading data.")
        actions = [
            {
                "_index": "nobel_prizes",
                "_source": {
                    "year": prize['year'],
                    "category": prize['category'],
                    "laureates": prize.get('laureates', [])
                }
            }
            for prize in data["prizes"]
        ]
        helpers.bulk(es, actions)
        print("Data successfully loaded into the 'nobel_prizes' index.")
    else:
        print("Index already exists. Skipping data load.")

# Root route
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Nobel Prize Search API!"})

# Search by name with fuzzy matching
@app.route('/search/name', methods=['GET'])
def search_by_name():
    query = request.args.get('q', '')
    res = es.search(index="nobel_prizes", body={
        "query": {
            "nested": {
                "path": "laureates",
                "query": {
                    "match": {
                        "laureates.firstname": {
                            "query": query,
                            "fuzziness": "AUTO"
                        }
                    }
                }
            }
        }
    })
    return jsonify(res['hits']['hits'])

# Search by category
@app.route('/search/category', methods=['GET'])
def search_by_category():
    category = request.args.get('q', '')
    res = es.search(index="nobel_prizes", body={
        "query": {
            "match": {
                "category": category
            }
        }
    })
    return jsonify(res['hits']['hits'])

if __name__ == "__main__":
    load_data()  # Load data into Elasticsearch when the app starts
    app.run(host="0.0.0.0", port=4000)
