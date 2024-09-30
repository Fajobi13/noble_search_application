import time
import requests
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError, NotFoundError
from flask_caching import Cache

# Initialize Flask app
app = Flask(__name__)

# Cache configuration with Redis (or other caching backends)
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300})

# Initialize Elasticsearch client
es = Elasticsearch(hosts=["http://elasticsearch:9200"], timeout=60)


# Load Nobel Prize data into Elasticsearch with retry mechanism
def load_data():
    url = "https://api.nobelprize.org/v1/prize.json"

    # Fetch data from Nobel API
    try:
        print("Fetching data from Nobel API...")
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        data = response.json()
        print(f"Fetched {len(data['prizes'])} prizes from the Nobel API.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Nobel API: {e}")
        return

    # Retry connecting to Elasticsearch up to 5 times
    for i in range(5):
        try:
            es.info()  # Try to connect to Elasticsearch
            print("Connected to Elasticsearch.")
            break
        except ConnectionError as e:
            print(f"Elasticsearch not ready, retrying... ({i + 1}/5): {e}")
            time.sleep(5)
    else:
        print("Failed to connect to Elasticsearch after 5 attempts.")
        return

    # Check if the index already exists
    try:
        if not es.indices.exists(index="nobel_prizes"):
            print("Index 'nobel_prizes' not found. Creating and loading data.")

            actions = []
            for prize in data["prizes"]:
                # Prepare actions for bulk insertion into Elasticsearch
                action = {
                    "_index": "nobel_prizes",
                    "_source": {
                        "year": prize['year'],
                        "category": prize['category'],
                        "laureates": prize.get('laureates', [])
                    }
                }
                actions.append(action)

            # Bulk insert actions into Elasticsearch
            if actions:
                helpers.bulk(es, actions)
                print(f"Loaded {len(actions)} records into the 'nobel_prizes' index.")
            else:
                print("No data to load.")
        else:
            print("Index 'nobel_prizes' already exists. Skipping data load.")
    except Exception as e:
        print(f"Error while loading data into Elasticsearch: {e}")


# Root route
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Nobel Prize Search API!"})


# Search by name with fuzzy matching
@cache.cached(timeout=60, query_string=True)
@app.route('/search/name', methods=['GET'])
def search_by_name():
    try:
        query = request.args.get('q', '')  # Get 'q' parameter from URL query string
        page = int(request.args.get('page', 1))  # Get 'page' parameter
        size = int(request.args.get('size', 10))  # Get 'size' parameter
        start = (page - 1) * size  # Pagination logic

        # Construct Elasticsearch search request
        res = es.search(index="nobel_prizes", body={
            "from": start,  # Pagination offset
            "size": size,  # Number of results per page
            "query": {
                "nested": {
                    "path": "laureates",  # Assuming 'laureates' is a nested field
                    "query": {
                        "match": {
                            "laureates.firstname": {
                                "query": query,  # Pass the search term
                                "fuzziness": "AUTO"  # Enable fuzzy search for partial matches
                            }
                        }
                    }
                }
            }
        })

        # Return the search results as JSON
        return jsonify(res['hits']['hits'])
    except NotFoundError:
        return jsonify({"error": "Index 'nobel_prizes' not found"}), 404
    except Exception as e:
        print(f"Error during search by name: {e}")
        return jsonify({"error": str(e)}), 500


# Search by category
@app.route('/search/category', methods=['GET'])
def search_by_category():
    try:
        category = request.args.get('q', '')
        res = es.search(index="nobel_prizes", body={
            "query": {
                "match": {
                    "category": category
                }
            }
        })
        return jsonify(res['hits']['hits'])
    except NotFoundError:
        return jsonify({"error": "Index 'nobel_prizes' not found"}), 404
    except Exception as e:
        print(f"Error during search by category: {e}")
        return jsonify({"error": str(e)}), 500


# Search by year or year range
@app.route('/search/year', methods=['GET'])
def search_by_year():
    try:
        start_year = request.args.get('start', None)
        end_year = request.args.get('end', None)

        if start_year and end_year:
            body = {
                "query": {
                    "range": {
                        "year": {
                            "gte": start_year,
                            "lte": end_year
                        }
                    }
                }
            }
        else:
            year = request.args.get('q', '')
            body = {
                "query": {
                    "match": {
                        "year": year
                    }
                }
            }

        res = es.search(index="nobel_prizes", body=body)
        return jsonify(res['hits']['hits'])
    except NotFoundError:
        return jsonify({"error": "Index 'nobel_prizes' not found"}), 404
    except Exception as e:
        print(f"Error during search by year: {e}")
        return jsonify({"error": str(e)}), 500


# Full-text search in motivation
@app.route('/search/motivation', methods=['GET'])
def search_by_motivation():
    try:
        query = request.args.get('q', '')
        res = es.search(index="nobel_prizes", body={
            "query": {
                "match": {
                    "laureates.motivation": {
                        "query": query
                    }
                }
            }
        })
        return jsonify(res['hits']['hits'])
    except NotFoundError:
        return jsonify({"error": "Index 'nobel_prizes' not found"}), 404
    except Exception as e:
        print(f"Error during search by motivation: {e}")
        return jsonify({"error": str(e)}), 500


# Advanced search by multiple fields (name, category, year) with sorting
@app.route('/search', methods=['GET'])
def advanced_search():
    try:
        name = request.args.get('name', '')
        category = request.args.get('category', '')
        year = request.args.get('year', '')
        sort = request.args.get('sort', 'year:asc')

        sort_field, sort_order = sort.split(':')

        query_body = {
            "bool": {
                "must": []
            }
        }

        if name:
            query_body['bool']['must'].append({
                "nested": {
                    "path": "laureates",
                    "query": {
                        "match": {
                            "laureates.firstname": {
                                "query": name,
                                "fuzziness": "AUTO"
                            }
                        }
                    }
                }
            })

        if category:
            query_body['bool']['must'].append({
                "match": {
                    "category": category
                }
            })

        if year:
            query_body['bool']['must'].append({
                "match": {
                    "year": year
                }
            })

        res = es.search(index="nobel_prizes", body={
            "query": query_body,
            "sort": [
                {sort_field: {"order": sort_order}}
            ]
        })
        return jsonify(res['hits']['hits'])
    except NotFoundError:
        return jsonify({"error": "Index 'nobel_prizes' not found"}), 404
    except Exception as e:
        print(f"Error during advanced search: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    load_data()  # Load data into Elasticsearch when the app starts
    app.run(host="0.0.0.0", port=4000, debug=True)
