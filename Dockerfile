FROM python:3.9-slim

WORKDIR /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip==24.3.1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]
