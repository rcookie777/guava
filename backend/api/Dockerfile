# Use an official Python runtime as a parent image
FROM python:3.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project directory to the container
COPY . /app/

# Expose port 8080 for the Flask app
EXPOSE 8080

# Run the Flask app located in api/main.py
CMD ["python", "main.py"]
