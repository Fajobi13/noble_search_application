import os
import requests
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.regex import Regex
from bson import ObjectId
from rapidfuzz import process
import redis
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint

# Initialize Flask app
app = Flask(__name__)

# Get Redis and MongoDB host and port from environment variables
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))

mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = int(os.getenv('MONGO_PORT', 27017))

# Initialize Redis client for caching
cache = redis.Redis(host=redis_host, port=redis_port, db=0)

# Initialize MongoDB client (connect to MongoDB via service name or localhost)
client = MongoClient(f"mongodb://{mongo_host}:{mongo_port}")
db = client['nobel_db']  # Database name
collection = db['prizes']  # Collection name

# Limiter to rate limit the API requests
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# Swagger UI setup
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'  # Path to your swagger.json file
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Nobel Prize API"})
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


# Utility function to convert ObjectId to string
def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    if isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    return obj


# Load Nobel Prize data into MongoDB
def load_data():
    try:
        url = "https://api.nobelprize.org/v1/prize.json"
        response = requests.get(url)
        data = response.json()

        # Insert data into MongoDB only if the collection is empty
        if collection.count_documents({}) == 0:
            collection.insert_many(data["prizes"])
            print(f"Loaded {len(data['prizes'])} prizes into MongoDB.")
        else:
            print("Data already loaded into MongoDB. Skipping data load.")
    except Exception as e:
        print(f"Error loading data: {e}")


# Root route
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Nobel Prize Search API!"})


# Caching function
def cache_result(key, value, expiration=300):
    cache.setex(key, expiration, jsonify(value).data)


def get_cached_result(key):
    cached_result = cache.get(key)
    if cached_result:
        return jsonify(eval(cached_result))
    return None


# Search by name with partial/fuzzy matching
@app.route('/search/name', methods=['GET'])
@limiter.limit("10 per minute")  # Rate limiting
def search_by_name():
    query = request.args.get('q', '')
    cache_key = f"name:{query}"

    # Check if the result is already cached
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return cached_result

    try:
        laureates = collection.aggregate([{"$unwind": "$laureates"}])
        laureate_list = list(laureates)
        name_list = [l['laureates']['firstname'] for l in laureate_list]

        # Fuzzy match with RapidFuzz
        matches = process.extract(query, name_list, limit=5)

        # Filter based on fuzzy matching
        matched_laureates = [l for l in laureate_list if l['laureates']['firstname'] in [match[0] for match in matches]]
        result = convert_objectid(matched_laureates)

        # Cache the result
        cache_result(cache_key, result)

        return jsonify(result)
    except Exception as e:
        print(f"Error during MongoDB query for name: {e}")
        return jsonify({"error": str(e)}), 500


# Search by category with pagination and sorting
@app.route('/search/category', methods=['GET'])
@limiter.limit("10 per minute")
def search_by_category():
    category = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    sort_by = request.args.get('sort_by', 'year')

    cache_key = f"category:{category}:{page}:{page_size}:{sort_by}"

    # Check if the result is already cached
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return cached_result

    try:
        prizes = collection.find({"category": category}, {"_id": 0, "laureates": 1, "year": 1, "category": 1}) \
            .sort(sort_by).skip((page - 1) * page_size).limit(page_size)
        result = convert_objectid(list(prizes))

        # Cache the result
        cache_result(cache_key, result)

        return jsonify(result)
    except Exception as e:
        print(f"Error during MongoDB query for category: {e}")
        return jsonify({"error": str(e)}), 500


# Search by motivation (description)
@app.route('/search/motivation', methods=['GET'])
@limiter.limit("10 per minute")
def search_by_motivation():
    query = request.args.get('q', '')
    regex_query = Regex(f".*{query}.*", "i")  # Case-insensitive regex match
    cache_key = f"motivation:{query}"

    # Check if the result is already cached
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return cached_result

    try:
        laureates = collection.aggregate([
            {"$unwind": "$laureates"},
            {"$match": {"laureates.motivation": regex_query}},
            {"$project": {"laureates": 1, "year": 1, "category": 1}}
        ])

        result = convert_objectid(list(laureates))

        # Cache the result
        cache_result(cache_key, result)

        return jsonify(result)
    except Exception as e:
        print(f"Error during MongoDB query for motivation: {e}")
        return jsonify({"error": str(e)}), 500


# Initialize the database and start the Flask app
if __name__ == "__main__":
    try:
        client.admin.command('ping')  # Check MongoDB connection
        print("Connected to MongoDB")
        load_data()  # Load Nobel Prize data into MongoDB on startup
        app.run(host="0.0.0.0", port=4000, debug=True)
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
