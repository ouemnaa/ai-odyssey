#!/bin/bash
# Blockchain Forensics Backend Quick Start Script for Unix/Linux/Mac

echo ""
echo "============================================"
echo "Blockchain Forensics Backend - Quick Start"
echo "============================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "[1/5] Checking Python installation..."
python3 --version
echo "OK"

echo ""
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi
echo "OK"

echo ""
echo "[3/5] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo "OK"

echo ""
echo "[4/5] Installing dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "OK"

echo ""
echo "[5/5] Starting Backend API Server..."
echo ""
echo "============================================"
echo "Backend API is starting..."
echo "============================================"
echo ""
echo "API Documentation:   http://localhost:8000/docs"
echo "Health Check:        http://localhost:8000/api/v1/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
