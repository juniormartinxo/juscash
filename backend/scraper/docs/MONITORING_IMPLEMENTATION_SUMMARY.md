# JSON File Monitoring and Processing Service - Implementation Summary

## Overview
A complete Python-based service has been implemented to monitor a folder for new JSON files and process them using Redis queue and an API endpoint.

## Components Implemented

### 1. File Monitor (`src/infrastructure/monitoring/file_monitor.py`)
- Uses `watchdog` library to monitor the specified directory
- Detects new JSON files in real-time
- Adds file metadata to Redis queue when new files are detected
- Handles Redis connection with retry logic
- Includes periodic health checks for Redis connection

### 2. API Worker (`src/infrastructure/monitoring/api_worker.py`)
- Consumes items from Redis queue
- Processes one item every 0.5 seconds
- Sends JSON data to specified API endpoint
- Implements exponential backoff retry mechanism (max 5 attempts)
- Logs failures to designated log directory in JSON format
- Handles various error scenarios (network issues, API errors, file errors)

### 3. Monitoring Orchestrator (`src/infrastructure/monitoring/monitoring_service.py`)
- Manages both File Monitor and API Worker as separate processes
- Automatically restarts failed processes
- Handles graceful shutdown on signals
- Provides centralized logging and configuration

### 4. Configuration Updates
- Updated `src/infrastructure/config/settings.py` to include Redis URL property
- Supports both REDIS_URL environment variable and individual Redis settings

## File Structure
```
backend/scraper/
├── src/infrastructure/monitoring/
│   ├── __init__.py
│   ├── file_monitor.py      # File monitoring service
│   ├── api_worker.py        # API worker service
│   └── monitoring_service.py # Main orchestrator
├── monitor_json_files.py     # Entry point script
├── test_monitoring_service.py # Test script
├── requirements-monitoring.txt # Dependencies
├── MONITORING_SERVICE_README.md # Documentation
├── docker-compose.monitoring.yml # Docker setup
└── Dockerfile.monitoring     # Docker image
```

## Key Features

### Error Handling
- Retry mechanism with exponential backoff (2^n seconds, max 60s)
- Failed items moved to separate Redis queue after max retries
- Comprehensive error logging with timestamps and details

### Fault Tolerance
- Automatic reconnection to Redis on connection loss
- Process monitoring and automatic restart
- Graceful handling of file system and network errors

### Logging
- Structured JSON logs for failures
- Configurable log levels
- Daily log files with failure details

### Performance
- Asynchronous file monitoring
- Configurable processing interval
- Redis connection pooling
- HTTP session reuse

## Usage

### Basic Command
```bash
python monitor_json_files.py --api-endpoint http://api.example.com/endpoint
```

### With Custom Paths
```bash
python monitor_json_files.py \
    --api-endpoint http://api.example.com/endpoint \
    --monitored-path ./reports/json \
    --log-path backend/scraper/reports/log
```

### Using Docker Compose
```bash
# Set API endpoint in environment
export API_BASE_URL=http://your-api.com/endpoint

# Start services
docker-compose -f docker-compose.monitoring.yml up -d
```

## Testing
A test script is provided to generate sample JSON files:
```bash
python test_monitoring_service.py --count 10 --interval 1
```

## Redis Queues Used
- `json_files_queue`: Main queue for new files
- `json_files_processing`: Temporary queue during processing
- `json_files_failed`: Queue for permanently failed items

## Log Format
Failed processing attempts are logged as JSON:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "file_name": "example.json",
  "file_path": "/path/to/example.json",
  "error_message": "API returned status 500",
  "retry_count": 5,
  "first_detected": "2024-01-15T10:25:30.123456",
  "processing_duration": 315.0
}
```

## Environment Variables
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`: Alternative Redis config
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Dependencies
- watchdog: File system monitoring
- redis: Redis client
- requests: HTTP requests
- urllib3: HTTP client utilities

The implementation follows PEP 8 style guidelines and includes comprehensive error handling, logging, and documentation.