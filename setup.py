#!/usr/bin/env python3
"""
Setup script for Stock Agent Chatbot
===================================
"""

from pathlib import Path
import os

def setup_project():
    """Set up the project environment."""
    print("Setting up Stock Agent Chatbot...")
    
    # Check if api_config.py exists
    if not Path("api_config.py").exists():
        print("WARNING: api_config.py not found!")
        print("Please copy api_config_template.py to api_config.py and add your API key.")
        print("Get your API key from: https://openrouter.ai/")
        return False
    
    # Create data directories
    data_dirs = [
        "data/daily/opening", "data/daily/closing",
        "data/weekly/opening", "data/weekly/closing", 
        "data/monthly/opening", "data/monthly/closing",
        "data/yearly/opening", "data/yearly/closing"
    ]
    
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("Data directories created!")
    print("Setup complete! Run: python comprehensive_stock_chatbot.py --chat")
    return True

if __name__ == "__main__":
    setup_project()
