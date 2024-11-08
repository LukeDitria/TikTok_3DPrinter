#!/bin/bash

# Directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate virtual environment
source venv/bin/activate

# Function to check if process is running
is_running() {
    if [ -f "process.pid" ]; then
        if ps -p $(cat process.pid) > /dev/null; then
            return 0
        fi
    fi
    return 1
}

case "$1" in
    start)
        if is_running; then
            echo "Process is already running."
        else
            echo "Starting TikTok Printer Controller..."
            # Run the process in background and save PID
            nohup python3 tiktok_printer_run.py > logs/output.log 2>&1 & echo $! > process.pid
            echo "Started!"
        fi
        ;;
    stop)
        if is_running; then
            echo "Stopping process..."
            kill $(cat process.pid)
            rm process.pid
            echo "Stopped!"
        else
            echo "Process is not running."
        fi
        ;;
    status)
        if is_running; then
            echo "Process is running (PID: $(cat process.pid))"
        else
            echo "Process is not running"
        fi
        ;;
    logs)
        tail -f logs/printer_stream.log
        ;;
    *)
        echo "Usage: $0 {start|stop|status|logs}"
        exit 1
        ;;
esac