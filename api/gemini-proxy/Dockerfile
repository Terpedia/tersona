FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy terpenes module
COPY terpenes.py .
COPY stt_helpers.py .

# Copy application code
COPY main_fastapi.py main.py

# Expose port
EXPOSE 8080

# Run the application (Cloud Run sets PORT env var)
# Use shell form to expand PORT variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
