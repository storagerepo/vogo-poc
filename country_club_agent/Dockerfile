# Use official Python 3.11 lightweight base image
FROM python:3.11-slim

# Set environment variables to optimize Python performance in container
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies required for build/audio packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download required LiveKit plugin model files into the container image
# (Fails gracefully if the download-files script isn't available for the specific plugins used)
RUN python -m livekit.agents download-files || true

# Copy application code files
COPY app/ ./app/
COPY mock_data/ ./mock_data/

# Run the LiveKit voice agent worker in production start mode
CMD ["python", "-m", "app.main", "start"]
