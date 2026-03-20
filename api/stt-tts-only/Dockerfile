FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy terpenes module
COPY terpenes.py .

# Copy application code
COPY main.py .

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8080

# Run the application (Cloud Run sets PORT env var)
ENTRYPOINT ["./entrypoint.sh"]
