#!/usr/bin/env python3
"""
Configuration file for the Stock Agent Chatbot
==============================================

This file contains all configuration settings, API keys, and mappings
to keep sensitive information separate from the main code.
"""

import os
from pathlib import Path

# API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"

# Data Configuration
DATA_DIRECTORY = Path("data")

# Stock Configuration
MAGNIFICENT_7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']

# Company name mappings (can be expanded)
COMPANY_MAPPINGS = {
    'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'amazon': 'AMZN',
    'tesla': 'TSLA', 'meta': 'META', 'nvidia': 'NVDA', 'netflix': 'NFLX',
    'amd': 'AMD', 'intel': 'INTC', 'ibm': 'IBM', 'oracle': 'ORCL',
    'cisco': 'CSCO', 'adobe': 'ADBE', 'salesforce': 'CRM', 'paypal': 'PYPL',
    'uber': 'UBER', 'airbnb': 'ABNB', 'spotify': 'SPOT', 'twitter': 'TWTR',
    'snapchat': 'SNAP', 'pinterest': 'PINS', 'zoom': 'ZM', 'slack': 'WORK'
}

# Common words to filter out when extracting stock symbols
COMMON_WORDS_FILTER = {
    'AND', 'TO', 'FROM', 'THE', 'IN', 'ON', 'AT', 'FOR', 'OF', 'WITH', 
    'LAST', 'YEAR', 'YEARS', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY',
    'ONLY', 'JUST', 'ALL', 'DATA', 'FILES', 'FILE', 'TWO', 'MULTIPLE',
    'WHAT', 'HOW', 'DOES', 'LOOK', 'LIKE', 'TODAY', 'NOW', 'PRICE', 
    'PERFORMANCE', 'STOCK', 'STOCKS', 'PAST', 'IS', 'ARE', 'WAS', 'WERE', 
    'BE', 'BEEN', 'BEING', 'HAVE', 'HAS', 'HAD', 'HAVING', 'WILL', 'WOULD', 
    'COULD', 'SHOULD', 'CAN', 'MAY', 'MIGHT', 'MUST', 'SHALL', 'MINUTES', 
    'HOURS', 'DAYS', 'WEEKS', 'MONTHS', 'AGO', 'TIME', 'TIMES', 'GET', 
    'GOT', 'GETTING', 'BUY', 'SELL', 'TRADE', 'TRADING', 'MARKET', 'MARKETS'
}

# Yahoo Finance Configuration
YAHOO_FREQUENCY_MAP = {
    'daily': '1d',
    'weekly': '1wk', 
    'monthly': '1mo',
    'yearly': '1y',
    'minute': '1m',
    'hourly': '1h'
}

YAHOO_PERIOD_MAP = {
    'daily': '1mo',
    'weekly': '1y',
    'monthly': '2y',
    'yearly': 'max',
    'minute': '1d',
    'hourly': '1d'
}

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
