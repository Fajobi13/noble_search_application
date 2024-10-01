import requests
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from bson.regex import Regex
from bson import ObjectId

# Initialize Flask app
app = Flask(__name__)

# Initialize MongoDB client (connect to the MongoDB container or localhost)
client = MongoClient("mongodb://mongodb:27017")  # Use 'localhost' if MongoDB is running locally
db = client['nobel_db']  # Database name
collection = db['prizes']  # Collection name

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

# Utility function to convert ObjectId to string
def convert_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    if isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    return obj

# Root route
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Nobel Prize Search API!"})

# Search by name with partial/fuzzy matching
@app.route('/search/name', methods=['GET'])
def search_by_name():
    query = request.args.get('q', '')
    print(f"Received search query for name: {query}")
    regex_query = Regex(f".*{query}.*", "i")  # Case-insensitive regex match

    try:
        laureates = collection.aggregate([
            {"$unwind": "$laureates"},
            {"$match": {"laureates.firstname": regex_query}},
            {"$project": {"laureates": 1, "year": 1, "category": 1}}  # Keep _id if needed
        ])
        result = list(laureates)
        result = convert_objectid(result)  # Convert ObjectId to string
        print(f"Query result for name: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error during MongoDB query for name: {e}")
        return jsonify({"error": str(e)}), 500

# Search by category
@app.route('/search/category', methods=['GET'])
def search_by_category():
    category = request.args.get('q', '')
    print(f"Received search query for category: {category}")

    try:
        prizes = collection.find({"category": category}, {"_id": 0, "laureates": 1, "year": 1, "category": 1})
        result = list(prizes)
        print(f"Query result for category: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error during MongoDB query for category: {e}")
        return jsonify({"error": str(e)}), 500

# Search by motivation (description)
@app.route('/search/motivation', methods=['GET'])
def search_by_motivation():
    query = request.args.get('q', '')
    regex_query = Regex(f".*{query}.*", "i")  # Case-insensitive regex match
    print(f"Received search query for motivation: {query}")

    try:
        # Test MongoDB connection
        client.admin.command('ping')
        print("MongoDB connection successful.")

        laureates = collection.aggregate([
            {"$unwind": "$laureates"},
            {"$match": {"laureates.motivation": regex_query}},
            {"$project": {"laureates": 1, "year": 1, "category": 1}}  # Include _id
        ])

        result = list(laureates)
        result = convert_objectid(result)  # Convert ObjectId to string
        print(f"Query result for motivation: {result}")
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
        app.run(host="0.0.0.0", port=4000, debug=True)  # Enable debug mode for detailed error messages
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
