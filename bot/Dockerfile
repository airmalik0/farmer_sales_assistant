FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Copy application code
COPY --chown=app:app . .

CMD ["python", "main.py"]