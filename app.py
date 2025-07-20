#!/usr/bin/env python3
"""
Simple startup script for Render deployment
This ensures the FastAPI app starts correctly in production
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Change to modeling directory
os.chdir(os.path.join(os.path.dirname(__file__), 'modeling'))

# Import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from api import app
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
