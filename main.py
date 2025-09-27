#!/usr/bin/env python3
"""
CodeForge AI - Main entry point
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.cli import cli

if __name__ == "__main__":
    cli()
