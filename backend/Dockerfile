FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
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

EXPOSE 8000

# Use environment variable for reload in development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]