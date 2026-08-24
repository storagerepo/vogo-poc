FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies if necessary
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download required LiveKit plugin model files into the container image
# (Fails gracefully if the download-files script isn't available for the specific plugins used)
RUN python -m livekit.agents download-files || true

# Copy the rest of the application code
COPY . .

# Command to run the application
CMD ["python", "-m", "app.main", "start"]
