#!/bin/bash

# Stop Browser-Use API Service

PORT=8765

echo "Stopping Browser-Use API on port $PORT..."

if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    lsof -ti:$PORT | xargs kill -9
    echo "✓ Service stopped"
else
    echo "✗ No service running on port $PORT"
fi