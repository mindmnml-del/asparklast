#!/bin/bash
set -e

echo "AISpark Studio - Container Starting..."

# Run Alembic migrations
echo "Running database migrations..."
python -m alembic upgrade head
echo "Database migrations applied."

# Start the application
echo "Starting uvicorn on port 8001..."
exec uvicorn main:app --host 0.0.0.0 --port 8001 --workers ${UVICORN_WORKERS:-1}
