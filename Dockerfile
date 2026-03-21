# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy your requirements first (helps with caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project (including those large files!)
COPY . .

# Render exposes port 10000 by default
EXPOSE 10000

# Command to run the FastAPI server
CMD ["uvicorn", "Backend.app:app", "--host", "0.0.0.0", "--port", "10000"]