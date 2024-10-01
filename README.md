Here’s a detailed and well-structured `README.md` file for your project that includes all the features, setup instructions, and usage examples.

---

## Nobel Prize Search API

### Overview

The **Nobel Prize Search API** allows users to search through Nobel laureates by name, category, or motivation. It leverages modern features such as fuzzy search, Redis caching for performance, and pagination to handle large datasets. The API also implements rate limiting to prevent abuse and provides comprehensive Swagger API documentation for ease of use.

This project is fully containerized using Docker, making deployment and environment setup seamless.

---

## Key Features

- **Fuzzy Search by Name**: Allows flexible searches for laureates even with partial or misspelled names.
- **Caching with Redis**: Improves response times by caching frequent queries.
- **API Rate Limiting**: Controls the rate of requests to prevent abuse.
- **Pagination and Sorting**: Handles large datasets with pagination and allows sorting by specific fields.
- **Search by Motivation**: Enables searching by the motivation behind a laureate’s award.
- **Swagger Documentation**: Interactive API documentation available through Swagger UI.
- **Dockerized Setup**: The entire application is containerized for easy deployment.
- **Environment Variable Configuration**: Supports dynamic configuration of Redis and MongoDB services.

---

## Table of Contents

- [Technologies Used](#technologies-used)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Testing the API](#testing-the-api)
- [Features](#features)
- [Metrics and Monitoring](#metrics-and-monitoring)
- [Contributions](#contributions)
- [License](#license)

---

## Technologies Used

- **Python 3.8+**
- **Flask**: Web framework for building the API.
- **MongoDB**: NoSQL database for storing Nobel Prize data.
- **Redis**: In-memory key-value store used for caching.
- **Swagger UI**: For API documentation.
- **Docker**: Containerization of services (Flask, MongoDB, Redis).
- **Prometheus (Optional)**: For monitoring and metrics.

---

## Prerequisites

- **Docker** and **Docker Compose** should be installed on your machine.
- **Python 3.8+** (only needed if you are running the app without Docker).
- **Redis and MongoDB** should be set up (if not using Docker).

---

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fajobi13/nobel-prize-search-api.git
   cd nobel-prize-search-api
   ```

2. **Create a `requirements.txt` file** or ensure it has the following content:
   ```txt
   Flask>=2.1
   pymongo>=4.2
   redis>=4.5.1
   flask-limiter>=2.0
   flask-swagger-ui>=0.0.9
   rapidfuzz>=2.8.0
   requests>=2.28.0
   ```

3. **Run the application using Docker**:

   Build and run the Docker containers:
   ```bash
   docker-compose up --build
   ```

---

## Running the Application

### Running with Docker

Simply run the following command to bring up the application:

```bash
docker-compose up --build
```

This will:
- Set up MongoDB and Redis services.
- Build and run the Flask application.

### Running Locally

If you'd like to run the application locally (without Docker), follow these steps:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run MongoDB and Redis** (if not using Docker):

   Run MongoDB and Redis locally or in Docker:

   MongoDB:
   ```bash
   docker run -d -p 27017:27017 mongo
   ```

   Redis:
   ```bash
   docker run -d -p 6379:6379 redis
   ```

3. **Start the Flask app**:
   ```bash
   python main.py
   ```

The app will be available at `http://localhost:4000`.

---

## API Endpoints

### Root Endpoint
- **URL**: `/`
- **Method**: `GET`
- **Description**: Returns a welcome message.
```bash
curl http://localhost:4000/
```

### Search by Name (Fuzzy Matching)
- **URL**: `/search/name`
- **Method**: `GET`
- **Parameters**: 
  - `q` (Query for the laureate's name, case-insensitive).
- **Description**: Search for laureates by name using fuzzy matching.
```bash
curl "http://localhost:4000/search/name?q=Albert"
```

### Search by Category with Pagination and Sorting
- **URL**: `/search/category`
- **Method**: `GET`
- **Parameters**: 
  - `q` (Query for the category, e.g., physics).
  - `page` (Optional, pagination page number).
  - `page_size` (Optional, number of results per page).
  - `sort_by` (Optional, field to sort by, default is `year`).
- **Description**: Search for laureates by their award category.
```bash
curl "http://localhost:4000/search/category?q=physics&page=1&page_size=5&sort_by=year"
```

### Search by Motivation (Description)
- **URL**: `/search/motivation`
- **Method**: `GET`
- **Parameters**: 
  - `q` (Query for the motivation description).
- **Description**: Search for laureates based on their award motivation.
```bash
curl "http://localhost:4000/search/motivation?q=theoretical"
```

### Swagger Documentation
- **URL**: `/swagger`
- **Method**: `GET`
- **Description**: View the API documentation via Swagger UI.
```bash
http://localhost:4000/swagger
```

---

## Testing the API

You can test the API using `curl` commands or a tool like **Postman**.

For example, to search for a laureate by name:
```bash
curl "http://localhost:4000/search/name?q=Albert"
```

---

## Features

### Fuzzy Search (Powered by RapidFuzz)
Allows users to search for laureates by name, even with partial or misspelled names.

### Redis Caching
Caches frequent queries to improve response times and reduce database load.

### API Rate Limiting
Limits API requests to prevent abuse (default: 10 requests per minute per endpoint).

### Pagination and Sorting
Handles large result sets with pagination and sorting by fields like year.

### Swagger API Documentation
Easily accessible interactive API documentation at `/swagger`.

### Dockerized Setup
Fully containerized using Docker for easy deployment, including MongoDB, Redis, and Flask.

---

## Metrics and Monitoring (Optional)

You can integrate **Prometheus** and **Grafana** for monitoring and visualization. Prometheus metrics are available at `/metrics`.

```bash
curl http://localhost:4000/metrics
```

---

## Contributions

Contributions are welcome! If you'd like to contribute to this project, please open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

---

This `README.md` covers all the features, setup instructions, and usage examples in detail, making it easy for others to get started with your project. Let me know if you'd like to add or modify anything!