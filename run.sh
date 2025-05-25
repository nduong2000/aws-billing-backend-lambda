#!/bin/bash

echo "=== Starting Python Backend ==="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8+ to continue."
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    #python3 -m venv venv
    python3.12 -m venv venv_py312
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv_py312/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run server
echo "Starting server..."
echo "Server will run on port 5002 or the port specified in .env"
python3 main.py

# Deactivate virtual environment when done
deactivate 