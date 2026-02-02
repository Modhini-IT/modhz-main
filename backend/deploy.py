#!/usr/bin/env python3
"""
Quick deployment script for face recognition system
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd, cwd=None):
    """Run a shell command"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Command failed: {cmd}")
            logger.error(f"Error: {result.stderr}")
            return False
        logger.info(f"✅ {cmd}")
        return True
    except Exception as e:
        logger.error(f"Error running command {cmd}: {e}")
        return False

def main():
    """Deploy the face recognition system"""
    logger.info("🚀 Starting deployment...")
    
    # Check if we're in the backend directory
    if not Path("app").exists():
        logger.error("Please run this script from the backend directory")
        sys.exit(1)
    
    # Install dependencies
    logger.info("📦 Installing dependencies...")
    if not run_command("pip install -r requirements.txt"):
        logger.error("Failed to install dependencies")
        sys.exit(1)
    
    # Train the model
    logger.info("🧠 Training face recognition model...")
    if not run_command("python train_model.py"):
        logger.error("Failed to train model")
        sys.exit(1)
    
    # Start the server
    logger.info("🌐 Starting server...")
    logger.info("Server will be available at: http://localhost:8000")
    logger.info("API documentation at: http://localhost:8000/docs")
    
    # Run the server
    os.system("python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    main()