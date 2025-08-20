#!/bin/bash
# Script to set up Python virtual environment, install requirements, activate env, and run count-tokens.py

set -e

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# If user asked for help, show local usage and exit
for arg in "$@"; do
    case "$arg" in
        -h|--help)
            echo "Usage: $0 [path/to/chat.txt] [model]"
            echo "If no path is provided, defaults to chats/token-chat.txt"
            exit 0
            ;;
    esac
done

# If no arguments supplied, default to the bundled chat file
if [ "$#" -eq 0 ]; then
    set -- "chats/token-chat.txt"
fi

# Forward all provided args to the Python script
python count-tokens.py "$@"
