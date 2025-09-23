#!/usr/bin/env python3
"""
Configuration file for the Stock Agent Chatbot
==============================================

This file contains essential configuration settings for the chatbot.
All symbol extraction, frequency mapping, and filtering is now handled
intelligently by the LLM, eliminating the need for hardcoded mappings.
"""

import os
from pathlib import Path

# API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"

# Data Configuration
DATA_DIRECTORY = Path("data")

# File naming configuration
FILE_NAMING_FORMATS = {
    'single_year': '{symbol}_{frequency}_{year}.csv',
    'year_range': '{symbol}_{frequency}_{start_year}_{end_year}.csv',
    'multiple_files': '{symbol}_{frequency}_{year}.csv'
}

# Validation
def validate_config():
    """Validate that required configuration is present."""
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not found. Please set it as an environment variable "
            "or add it to this config file."
        )
    return True
