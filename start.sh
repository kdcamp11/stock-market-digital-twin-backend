#!/bin/bash

# Install dependencies
pip install -r modeling/requirements.txt

# Start the FastAPI application
cd modeling
uvicorn api:app --host 0.0.0.0 --port $PORT
