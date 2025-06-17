#!/usr/bin/env python3
"""
Startup script for JSON monitoring service with directory setup.
"""

import os
import sys
import subprocess
from pathlib import Path


def setup_directories():
    """Create necessary directories for the monitoring service."""
    script_dir = Path(__file__).parent.resolve()

    # Define directories
    directories = [
        script_dir / "reports" / "json",
        script_dir / "reports" / "log",
        script_dir / "logs",
    ]

    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created/verified directory: {directory}")

    return script_dir


def main():
    """Main entry point."""
    print("JSON Monitoring Service Startup")
    print("=" * 50)

    # Setup directories
    script_dir = setup_directories()

    # Get API endpoint from command line or environment
    api_endpoint = None
    for i, arg in enumerate(sys.argv):
        if arg == "--api-endpoint" and i + 1 < len(sys.argv):
            api_endpoint = sys.argv[i + 1]
            break

    if not api_endpoint:
        api_endpoint = os.environ.get("API_BASE_URL")

    if not api_endpoint:
        print("\nERROR: API endpoint not specified!")
        print(
            "Usage: python start_monitoring.py --api-endpoint http://api.example.com/endpoint"
        )
        print("Or set API_BASE_URL environment variable")
        sys.exit(1)

    # Build command
    cmd = [
        sys.executable,
        str(script_dir / "monitor_json_files.py"),
        "--api-endpoint",
        api_endpoint,
        "--monitored-path",
        str(script_dir / "reports" / "json"),
        "--log-path",
        str(script_dir / "reports" / "log"),
    ]

    # Add any additional arguments
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg not in ["--api-endpoint", api_endpoint] and not (
            i > 1 and sys.argv[i - 1] == "--api-endpoint"
        ):
            cmd.append(arg)

    print(f"\nStarting monitoring service...")
    print(f"API Endpoint: {api_endpoint}")
    print(f"Monitored Path: {script_dir / 'reports' / 'json'}")
    print(f"Log Path: {script_dir / 'reports' / 'log'}")
    print(f"\nCommand: {' '.join(cmd)}")
    print("=" * 50)

    # Run the monitoring service
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nService stopped by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
