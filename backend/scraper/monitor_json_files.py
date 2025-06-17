#!/usr/bin/env python3
"""
JSON File Monitoring and Processing Service

This service monitors a folder for new JSON files and processes them through
a Redis queue and API endpoint.

Usage:
    python monitor_json_files.py --api-endpoint http://api.example.com/endpoint
    
    Or with custom paths:
    python monitor_json_files.py \
        --api-endpoint http://api.example.com/endpoint \
        --monitored-path /custom/path/to/json \
        --log-path /custom/path/to/logs
"""

import sys
import os
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()

# Add the src directory to Python path
sys.path.insert(0, str(SCRIPT_DIR))

# Set working directory to script directory for consistent path resolution
os.chdir(SCRIPT_DIR)

from src.infrastructure.monitoring.monitoring_service import main

if __name__ == "__main__":
    main()