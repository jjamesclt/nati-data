FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies (including vi)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    vim-tiny \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Default command
CMD ["python", "main.py"]
