#!/bin/sh
# Entrypoint script for Cloud Run
# Cloud Run sets PORT environment variable

PORT=${PORT:-8080}
echo "Starting server on port $PORT"
exec uvicorn main:app --host 0.0.0.0 --port $PORT
