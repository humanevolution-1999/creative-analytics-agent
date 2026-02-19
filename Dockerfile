# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port
EXPOSE 8080

# Run the server
# Run the server
# Host 0.0.0.0 is crucial for Docker, Port must match $PORT on Render
CMD sh -c "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}"
