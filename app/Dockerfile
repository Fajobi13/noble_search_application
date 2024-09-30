# Use the official Python image from Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Expose port 4000 for Flask app
EXPOSE 4000

# Run the Flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=4000"]
