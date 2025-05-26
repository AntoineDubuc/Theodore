#!/usr/bin/env python3
"""
Theodore CLI - Easy access to Theodore company intelligence features
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main_pipeline import main

if __name__ == "__main__":
    main()