# Nobel Prize Search API

## Overview

The **Nobel Prize Search API** is a web service that allows users to search through the Nobel Prize dataset. It provides various endpoints for searching Nobel laureates by name, category, and motivation. The application leverages MongoDB for data storage, Redis for caching, and Flask to create the API.

### Key Features:
- **Fuzzy Search by Name**: Search for laureates using fuzzy matching to handle partial or misspelled queries.
- **Search by Category**: Filter laureates based on their prize category (e.g., physics, chemistry).
- **Search by Motivation**: Find laureates based on their award motivation.
- **API Rate Limiting**: Prevent abuse and ensure scalable usage.
- **Caching**: Uses Redis to cache frequently accessed data for performance optimization.
- **Swagger Documentation**: Auto-generated API documentation for ease of use.

## Technologies Used

- **Python**: Backend development using Flask.
- **Flask**: Microframework to create the API.
- **MongoDB**: NoSQL database to store the Nobel Prize data.
- **Redis**: In-memory key-value store used for caching.
- **Docker**: Containerization for easy deployment.
- **Prometheus & Grafana**: (Optional) For metrics and monitoring.

## Prerequisites

- **Python 3.8+**
- **Docker**
- **Docker Compose**
- **Redis** (Optional if running in Docker)
- **MongoDB** (Optional if running in Docker)

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/fajobi13/nobel-prize-search-api.git
cd nobel-prize-search-api
