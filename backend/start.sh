#!/bin/bash

# Default settings
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-1}
APP_MODULE=${APP_MODULE:-"app.main:app"}

echo "🚀 Starting HNMS in $APP_ENV mode..."

if [ "$APP_ENV" = "development" ]; then
    echo "🛠️  Development mode: Hot reload enabled."
    # --reload implies single worker
    exec uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --reload --reload-exclude "data/*" --reload-exclude "mqtt_debug.log"
else
    echo "🏭 Production mode: Running with $WORKERS worker(s)."
    exec uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --workers "$WORKERS"
fi
