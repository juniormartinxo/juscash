#!/usr/bin/env python3
"""
Test script for the JSON monitoring service.

This script creates test JSON files to verify the monitoring service is working correctly.
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
import argparse


def create_test_json_file(directory: Path, index: int) -> Path:
    """Create a test JSON file with sample data."""
    test_data = {
        "process_number": f"1234567-{index:02d}.2024.8.26.0000",
        "publication_date": datetime.now().strftime("%Y-%m-%d"),
        "availability_date": datetime.now().strftime("%Y-%m-%d"),
        "authors": [f"Test Author {index}"],
        "defendant": "Test Defendant Inc.",
        "content": f"This is test content for file {index}",
        "test_metadata": {
            "created_at": datetime.now().isoformat(),
            "test_index": index,
            "test_run": True,
        },
    }

    filename = f"test_publication_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{index}.json"
    file_path = directory / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    return file_path


def main():
    parser = argparse.ArgumentParser(description="Test the JSON monitoring service")
    parser.add_argument(
        "--directory",
        default="./reports/json",
        help="Directory to create test files in"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of test files to create"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Interval between file creation (seconds)"
    )
    
    args = parser.parse_args()
    
    directory = Path(args.directory)
    directory.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating {args.count} test JSON files in {directory}")
    print(f"Interval: {args.interval} seconds")
    print("Press Ctrl+C to stop\n")
    
    try:
        for i in range(1, args.count + 1):
            file_path = create_test_json_file(directory, i)
            print(f"[{i}/{args.count}] Created: {file_path.name}")
            
            if i < args.count:
                time.sleep(args.interval)
                
        print(f"\nSuccessfully created {args.count} test files")
        print("Check the monitoring service logs to verify processing")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error creating test files: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
