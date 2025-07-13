#!/usr/bin/env python3
"""
A1 Taxi Hosur Dev - Main Entry Point
"""

import os
import sys
from dotenv import load_dotenv

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)