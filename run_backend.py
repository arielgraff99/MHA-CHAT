#!/usr/bin/env python3
"""
TimelineNarrator Backend Server
Main entry point for running the FastAPI application
"""

import uvicorn
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app
from backend.config import config

if __name__ == "__main__":
    print("Starting TimelineNarrator Backend Server...")
    print(f"API will be available at: http://{config.API_HOST}:{config.API_PORT}")
    print(f"API Documentation: http://{config.API_HOST}:{config.API_PORT}/docs")
    print(f"Debug mode: {config.DEBUG}")
    
    uvicorn.run(
        "backend.app:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        log_level=config.LOG_LEVEL.lower()
    )