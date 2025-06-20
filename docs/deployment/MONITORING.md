# JSON File Monitoring and Processing Service

This service monitors a specified folder for new JSON files and processes them using a Redis queue and an API endpoint.

## Features

- **File Monitoring**: Continuously monitors a folder for new JSON files using watchdog
- **Redis Queue**: Queues detected files in Redis for reliable processing
- **API Integration**: Sends JSON data to a specified API endpoint
- **Retry Mechanism**: Implements exponential backoff with up to 5 retry attempts
- **Error Logging**: Logs failed processing attempts to a designated folder
- **Fault Tolerance**: Handles file system errors, network issues, and API downtime gracefully

## Architecture

The service consists of three main components:

1. **File Monitor** (`file_monitor.py`): Watches the specified directory for new JSON files
2. **API Worker** (`api_worker.py`): Processes files from the Redis queue
3. **Monitoring Orchestrator** (`monitoring_service.py`): Manages both services

## Installation

1. Install dependencies:
```bash
pip install -r requirements-monitoring.txt
```

2. Configure Redis connection in `.env` file:
```env
REDIS_URL=redis://localhost:6379/0
# Or use individual settings:
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_password  # Optional
```

## Usage

### Basic Usage

```bash
python monitor_json_files.py --api-endpoint http://api.example.com/endpoint
```

### Advanced Usage

```bash
python monitor_json_files.py \
    --api-endpoint http://api.example.com/endpoint \
    --monitored-path ./reports/json \
    --log-path backend/scraper/reports/log \
    --redis-url redis://localhost:6379/0 \
    --log-level INFO
```

### Command Line Arguments

- `--api-endpoint` (required): API endpoint URL for sending JSON data
- `--monitored-path`: Path to monitor for new JSON files (default: `./reports/json`)
- `--log-path`: Path for storing error logs (default: `backend/scraper/reports/log`)
- `--redis-url`: Redis connection URL (overrides environment variable)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Processing Flow

1. **File Detection**: When a new JSON file is added to the monitored folder
2. **Queue Creation**: File information is added to Redis queue with metadata
3. **Worker Processing**: Worker picks up items from queue every 0.5 seconds
4. **API Request**: JSON content is sent to the API endpoint
5. **Retry Logic**: Failed requests are retried with exponential backoff
6. **Error Logging**: After 5 failed attempts, error is logged to file

## Error Handling

### Retry Mechanism
- Maximum retries: 5 attempts
- Exponential backoff: 2^n seconds (max 60 seconds)
- Failed items are moved to a separate Redis queue

### Error Logs
Error logs are saved in JSON format with the following structure:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "file_name": "example.json",
  "file_path": "/path/to/example.json",
  "error_message": "API returned status 500: Internal Server Error",
  "retry_count": 5,
  "first_detected": "2024-01-15T10:25:30.123456",
  "processing_duration": 315.0
}
```

## Redis Queues

The service uses three Redis queues:
- `json_files_queue`: Main queue for new files
- `json_files_processing`: Temporary queue for items being processed
- `json_files_failed`: Queue for items that failed after max retries

## Monitoring

The orchestrator monitors both services and automatically restarts them if they fail.

### Service Health
- Redis connection is checked every minute
- Failed processes are automatically restarted
- Graceful shutdown on SIGINT/SIGTERM signals

## Running as a Service

### Using systemd (Linux)

Create `/etc/systemd/system/json-monitor.service`:
```ini
[Unit]
Description=JSON File Monitoring Service
After=network.target redis.service

[Service]
Type=simple
User=scraper
WorkingDirectory=/path/to/backend/scraper
Environment="PYTHONPATH=/path/to/backend/scraper"
ExecStart=/usr/bin/python3 /path/to/backend/scraper/monitor_json_files.py --api-endpoint http://api.example.com/endpoint
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable json-monitor
sudo systemctl start json-monitor
```

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements-monitoring.txt .
RUN pip install -r requirements-monitoring.txt

COPY . .

CMD ["python", "monitor_json_files.py", "--api-endpoint", "${API_BASE_URL}"]
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check Redis is running: `redis-cli ping`
   - Verify connection URL in environment variables
   - Check firewall/network settings

2. **Files Not Being Detected**
   - Verify monitored path exists and has correct permissions
   - Check file extension is `.json`
   - Ensure watchdog is properly installed

3. **API Requests Failing**
   - Verify API endpoint is accessible
   - Check network connectivity
   - Review error logs in log directory

### Debug Mode

Run with debug logging:
```bash
python monitor_json_files.py --api-endpoint http://api.example.com/endpoint --log-level DEBUG
```

## Performance Considerations

- Processing interval: 0.5 seconds per item
- Redis connection pooling for efficiency
- Exponential backoff prevents API overload
- File system events are processed asynchronously

## Security Notes

- Ensure Redis is properly secured (password, firewall)
- Use HTTPS for API endpoints in production
- Validate JSON content before processing
- Set appropriate file permissions on log directory