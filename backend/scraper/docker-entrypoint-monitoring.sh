#!/bin/bash
# Docker entrypoint for monitoring service

# Create necessary directories
mkdir -p /app/reports/json
mkdir -p /app/reports/log
mkdir -p /app/logs

echo "Directories created:"
ls -la /app/reports/

# Check if API_BASE_URL is set
if [ -z "$API_BASE_URL" ]; then
    echo "ERROR: API_BASE_URL environment variable is not set!"
    exit 1
fi

echo "Starting monitoring service..."
echo "API Endpoint: $API_BASE_URL"
echo "Monitored Path: /app/reports/json"
echo "Log Path: /app/reports/log"

# Start the monitoring service
exec python /app/monitor_json_files.py \
    --api-endpoint "$API_BASE_URL" \
    --monitored-path /app/reports/json \
    --log-path /app/reports/log \
    "$@"