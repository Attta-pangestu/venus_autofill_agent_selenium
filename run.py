#!/usr/bin/env python3
"""
Selenium AutoFill - Run Script
Simple launcher for the automation application
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import and run main application
from main import main
import asyncio

if __name__ == "__main__":
    print("🤖 Starting Selenium AutoFill Application...")
    asyncio.run(main()) 