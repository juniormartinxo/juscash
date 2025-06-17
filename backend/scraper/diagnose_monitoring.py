#!/usr/bin/env python3
"""
Diagnostic script to check monitoring service setup.
"""

import os
import sys
from pathlib import Path
import redis
import json


def check_directories():
    """Check if required directories exist."""
    print("Checking directories...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Script location: {Path(__file__).resolve()}")

    script_dir = Path(__file__).parent.resolve()
    directories = {
        "JSON Reports": script_dir / "reports" / "json",
        "Error Logs": script_dir / "reports" / "log",
        "Application Logs": script_dir / "logs",
    }

    for name, path in directories.items():
        if path.exists():
            print(f"✓ {name}: {path} (exists)")
            # List files in directory
            files = list(path.iterdir())
            if files:
                print(f"  Files: {len(files)}")
                for f in files[:5]:  # Show first 5 files
                    print(f"    - {f.name}")
                if len(files) > 5:
                    print(f"    ... and {len(files) - 5} more")
        else:
            print(f"✗ {name}: {path} (missing)")
            # Try to create it
            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"  → Created directory")
            except Exception as e:
                print(f"  → Failed to create: {e}")


def check_redis():
    """Check Redis connection."""
    print("\nChecking Redis connection...")

    # Try to get Redis URL from environment
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        # Try to construct from individual settings
        host = os.environ.get("REDIS_HOST", "localhost")
        port = os.environ.get("REDIS_PORT", "6379")
        password = os.environ.get("REDIS_PASSWORD", "")
        db = os.environ.get("REDIS_DB", "0")

        if password:
            redis_url = f"redis://:{password}@{host}:{port}/{db}"
        else:
            redis_url = f"redis://{host}:{port}/{db}"

    print(f"Redis URL: {redis_url}")

    try:
        client = redis.from_url(redis_url, decode_responses=True, socket_timeout=5)
        client.ping()
        print("✓ Redis connection successful")

        # Check queues
        queues = ["json_files_queue", "json_files_processing", "json_files_failed"]
        for queue in queues:
            length = client.llen(queue)
            print(f"  Queue '{queue}': {length} items")

    except Exception as e:
        print(f"✗ Redis connection failed: {e}")


def check_environment():
    """Check environment variables."""
    print("\nChecking environment variables...")

    important_vars = [
        "API_BASE_URL",
        "REDIS_URL",
        "REDIS_HOST",
        "REDIS_PORT",
        "REDIS_PASSWORD",
        "PYTHONPATH",
    ]

    for var in important_vars:
        value = os.environ.get(var)
        if value:
            if "PASSWORD" in var:
                print(f"✓ {var}: ****** (set)")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"✗ {var}: not set")


def create_test_file():
    """Create a test JSON file."""
    print("\nCreating test JSON file...")

    script_dir = Path(__file__).parent.resolve()
    json_dir = script_dir / "reports" / "json"
    json_dir.mkdir(parents=True, exist_ok=True)

    test_data = {
        "test": True,
        "timestamp": str(Path(__file__).stat().st_mtime),
        "message": "This is a diagnostic test file",
    }

    test_file = json_dir / "diagnostic_test.json"
    with open(test_file, "w") as f:
        json.dump(test_data, f, indent=2)

    print(f"✓ Created test file: {test_file}")
    print(f"  Size: {test_file.stat().st_size} bytes")


def main():
    """Run all diagnostics."""
    print("=" * 60)
    print("Monitoring Service Diagnostics")
    print("=" * 60)

    check_directories()
    check_environment()
    check_redis()
    create_test_file()

    print("\n" + "=" * 60)
    print("Diagnostics complete!")

    # Provide startup command
    script_dir = Path(__file__).parent.resolve()
    print("\nTo start the monitoring service, run:")
    print(f"python {script_dir}/start_monitoring.py --api-endpoint YOUR_API_ENDPOINT")

    api_endpoint = os.environ.get("API_BASE_URL")
    if api_endpoint:
        print(f"\nOr with current environment:")
        print(
            f"python {script_dir}/monitor_json_files.py --api-endpoint {api_endpoint}"
        )


if __name__ == "__main__":
    main()
