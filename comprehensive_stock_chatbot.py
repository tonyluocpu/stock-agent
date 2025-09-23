#!/usr/bin/env python3
"""
LLM-Powered Stock Chatbot - Uses LLM for Natural Language Processing
================================================================

This chatbot uses an LLM to properly understand natural language requests
and processes stock data accordingly.
"""

import yfinance as yf
import pandas as pd
import os
import re
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import sys

# Import configuration
try:
    from config import *
    from api_config import API_KEY, API_URL, MODEL
except ImportError:
        print("ERROR: Configuration files not found. Please ensure config.py and api_config.py exist.")
        sys.exit(1)

class LLMStockChatbot:
    """
    LLM-Powered Stock Chatbot that uses an LLM for natural language understanding.
    """
    
    def __init__(self):
        """Initialize the LLM Stock Chatbot."""
        self.name = "LLM Stock Data Chatbot"
        self.data_dir = DATA_DIRECTORY
        self._create_directory_structure()
        
        # LLM Configuration from config files
        self.api_key = API_KEY
        self.api_url = API_URL
        self.model = MODEL
        
        # Configuration loaded - all symbol extraction and mapping now handled by LLM
        
        print(f"{self.name} initialized!")
        print("I use an LLM to understand your natural language requests!")
        print("I can handle stock data AND answer general questions!")
        print("I'll stay active until you say goodbye!")
    
    def _create_directory_structure(self):
        """Create the organized directory structure for data storage."""
        directories = [
            "weekly/beginning",
            "weekly/closing", 
            "monthly/beginning",
            "monthly/closing",
            "yearly/beginning",
            "yearly/closing",
            "daily/beginning",
            "daily/closing"
        ]
        
        for dir_path in directories:
            full_path = self.data_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        print(f" Data directories ready in {self.data_dir}")
    
    def _call_llm(self, prompt, system_prompt=None):
        """Call the LLM to process natural language."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"ERROR: LLM Error: {e}")
            return None
    
    def _parse_request_with_llm(self, user_input):
        """Use LLM to parse the user request into structured data."""
        
        # Get current date dynamically
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_year = datetime.now().year
        
        system_prompt = f"""You are a stock data parsing assistant. Parse the user's natural language request and return a JSON response with the following structure:

IMPORTANT: Today's date is {current_date} (Year: {current_year})

{{
    "symbols": ["AAPL", "MSFT"],
    "time_frame": {{
        "start_date": "2019-01-01",
        "end_date": "2021-12-31",
        "data_frequencies": ["weekly"]
    }},
    "data_type": "both",
    "is_multiple_files": false,
    "clarification_needed": false,
    "clarification_message": ""
}}

CRITICAL RULES FOR "AND" vs "TO":

**"AND" = SEPARATE FILES (Multiple Files):**
- "2019 and 2021" = 2 separate files (one for 2019, one for 2021)
- "Apple and Microsoft" = 2 separate files (one for each symbol)
- "daily and weekly" = 2 separate files (one for each frequency)
- "Apple and Microsoft 2019 and 2021" = 4 separate files (2×2 combinations)

**"TO" = SINGLE FILE (Date Range):**
- "2019 to 2021" = 1 file with date range from 2019-01-01 to 2021-12-31
- "Apple weekly 2019 to 2021" = 1 file

**SPECIFIC EXAMPLES:**
- "Apple and Microsoft weekly 2019 and 2021" = 4 files:
  * AAPL_WEEKLY_2019.csv
  * AAPL_WEEKLY_2021.csv  
  * MSFT_WEEKLY_2019.csv
  * MSFT_WEEKLY_2021.csv

- "Apple weekly 2019 to 2021" = 1 file:
  * AAPL_WEEKLY_2019_2021.csv

- "Apple daily and weekly 2020" = 2 files:
  * AAPL_DAILY_2020.csv
  * AAPL_WEEKLY_2020.csv

Other Rules:
1. Extract stock symbols (handle company names like "Apple" -> "AAPL", "Microsoft" -> "MSFT")
2. Handle "magnificent 7" as all 7 stocks: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
3. Parse date ranges like "2019-2021", "last year", "10 years", "up to today", "through today"
4. For "today", "up to today", "through today" use {current_date} as end_date
5. For "last year" use {current_year-1}-01-01 to {current_year-1}-12-31
6. For "this year" use {current_year}-01-01 to {current_date}
7. Detect data frequencies: daily, weekly, monthly, yearly, minute, hourly (note: minute/hourly data only available for last 30 days)
8. Determine data type: opening, closing, or both
9. If unclear, set clarification_needed to true with clarification_message
10. Always return valid JSON only, no other text

IMPORTANT: When you see "2019 and 2021", set is_multiple_files to true and create separate time frames for each year. Do NOT combine them into a date range."""

        prompt = f"""Parse this stock data request: "{user_input}"

Return only the JSON response:"""

        llm_response = self._call_llm(prompt, system_prompt)
        
        if not llm_response:
            return None
        
        try:
            # Clean the response to extract JSON
            llm_response = llm_response.strip()
            if llm_response.startswith('```json'):
                llm_response = llm_response[7:]
            if llm_response.endswith('```'):
                llm_response = llm_response[:-3]
            if llm_response.startswith('```'):
                llm_response = llm_response[3:]
            
            parsed_request = json.loads(llm_response)
            return parsed_request
            
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse LLM response as JSON: {e}")
            print(f"LLM Response: {llm_response}")
            return None
    
    def _is_stock_data_request(self, user_input):
        """Use LLM to intelligently detect if the user input is a stock data download request."""
        intent_prompt = f"""Analyze this user input and determine their intent:

User Input: "{user_input}"

Determine which category this falls into:
1. GENERAL_QUESTION - Non-stock related questions (weather, date, general knowledge, personal questions)
2. STOCK_ANALYSIS - User wants to know about current stock performance, analysis, or insights
3. STOCK_DATA_DOWNLOAD - User wants to download historical stock data files

Examples:
- "what date is it today" → GENERAL_QUESTION
- "do you like cheese" → GENERAL_QUESTION  
- "what does apple stock look like" → STOCK_ANALYSIS
- "how is tesla performing" → STOCK_ANALYSIS
- "apple weekly data 2019-2021" → STOCK_DATA_DOWNLOAD
- "download microsoft daily data" → STOCK_DATA_DOWNLOAD

Respond with ONLY one of: GENERAL_QUESTION, STOCK_ANALYSIS, or STOCK_DATA_DOWNLOAD"""

        intent = self._call_llm(intent_prompt)
        
        if intent and "STOCK_DATA_DOWNLOAD" in intent.upper():
            return True
        else:
            return False
    
    def _is_stock_analysis_request(self, user_input):
        """Use LLM to intelligently detect if the user input is a stock analysis request."""
        intent_prompt = f"""Analyze this user input and determine their intent:

User Input: "{user_input}"

Determine which category this falls into:
1. GENERAL_QUESTION - Non-stock related questions (weather, date, general knowledge, personal questions)
2. STOCK_ANALYSIS - User wants to know about current stock performance, analysis, or insights
3. STOCK_DATA_DOWNLOAD - User wants to download historical stock data files

Examples:
- "what date is it today" → GENERAL_QUESTION
- "do you like cheese" → GENERAL_QUESTION  
- "what does apple stock look like" → STOCK_ANALYSIS
- "how is tesla performing" → STOCK_ANALYSIS
- "apple weekly data 2019-2021" → STOCK_DATA_DOWNLOAD
- "download microsoft daily data" → STOCK_DATA_DOWNLOAD

Respond with ONLY one of: GENERAL_QUESTION, STOCK_ANALYSIS, or STOCK_DATA_DOWNLOAD"""

        intent = self._call_llm(intent_prompt)
        
        if intent and "STOCK_ANALYSIS" in intent.upper():
            return True
        else:
            return False
    
    def _extract_symbols_with_llm(self, user_input):
        """Use LLM to extract stock symbols from natural language."""
        prompt = f"""Extract stock symbols from this user input:

User Input: "{user_input}"

Instructions:
1. Identify all stock symbols mentioned (e.g., AAPL, TSLA, MSFT)
2. Convert company names to symbols (e.g., "Apple" -> "AAPL", "Tesla" -> "TSLA")
3. Handle "magnificent 7" as: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
4. Ignore common words like "stock", "data", "price", "today", etc.
5. Handle misspellings (e.g., "macrosft" -> "MSFT", "tfsla" -> "TSLA")

Return ONLY a JSON array of symbols, like: ["AAPL", "MSFT"]"""

        response = self._call_llm(prompt)
        
        if response:
            try:
                # Clean the response to extract JSON
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.endswith('```'):
                    response = response[:-3]
                if response.startswith('```'):
                    response = response[3:]
                
                symbols = json.loads(response)
                return symbols if isinstance(symbols, list) else []
            except json.JSONDecodeError:
                return []
        
        return []
    
    def _map_frequency_to_interval(self, data_frequency):
        """Map data frequency to Yahoo Finance interval using LLM understanding."""
        prompt = f"""Map this data frequency to Yahoo Finance interval:

Data Frequency: "{data_frequency}"

Map to Yahoo Finance interval:
- daily -> 1d
- weekly -> 1wk  
- monthly -> 1mo
- yearly -> 1y
- minute -> 1m
- hourly -> 1h

Return ONLY the interval code (e.g., "1d", "1wk", etc.):"""

        response = self._call_llm(prompt)
        
        if response and response.strip() in ['1d', '1wk', '1mo', '1y', '1m', '1h']:
            return response.strip()
        else:
            # Fallback to default
            return '1d'
    
    def _map_frequency_to_period(self, data_frequency):
        """Map data frequency to Yahoo Finance period using LLM understanding."""
        prompt = f"""Map this data frequency to Yahoo Finance period:

Data Frequency: "{data_frequency}"

Map to Yahoo Finance period:
- daily -> 1mo
- weekly -> 1y
- monthly -> 2y
- yearly -> max
- minute -> 1d
- hourly -> 1d

Return ONLY the period code (e.g., "1mo", "1y", etc.):"""

        response = self._call_llm(prompt)
        
        if response and response.strip() in ['1mo', '1y', '2y', 'max', '1d']:
            return response.strip()
        else:
            # Fallback to default
            return '1mo'
    
    def _fetch_historical_data(self, symbol, time_frame, data_frequency):
        """Fetch historical data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Map data frequency to Yahoo Finance interval using LLM understanding
            interval = self._map_frequency_to_interval(data_frequency)
            
            if time_frame.get('start_date') and time_frame.get('end_date'):
                # For minute data, add 1 day to end_date to ensure we get the full day
                start_date = time_frame['start_date']
                end_date = time_frame['end_date']
                
                # For minute/hourly data, extend end date to next day to get full trading day
                if data_frequency in ['minute', 'hourly']:
                    from datetime import datetime, timedelta
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    end_date = end_dt.strftime('%Y-%m-%d')
                
                hist = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                # Use LLM-based period mapping
                period = self._map_frequency_to_period(data_frequency)
                hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                # Check if it's a minute data limitation
                if data_frequency in ['minute', 'hourly']:
                    print(f"ERROR: No {data_frequency} data found for {symbol}")
                    print(f"Note: Note: {data_frequency} data is only available for the last 30 days")
                else:
                    print(f"ERROR: No data found for {symbol}")
                return None
            
            return hist
            
        except Exception as e:
            print(f"ERROR: Error fetching data for {symbol}: {e}")
            # Check for specific Yahoo Finance error messages
            if "not available" in str(e) and "30 days" in str(e):
                print(f"Note: Note: {data_frequency} data is only available for the last 30 days")
            return None
    
    def _save_data(self, symbol, data, data_type, time_frame, data_frequency):
        """Save data with essential information."""
        if data is None:
            return False
        
        # Select essential data columns (up to 5 items)
        essential_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        available_columns = [col for col in essential_columns if col in data.columns]
        
        if len(available_columns) > 5:
            available_columns = available_columns[:5]
        
        save_data = data[available_columns].copy()
        
        # Rename columns
        column_names = {
            'Open': 'Opening_Price',
            'High': 'High_Price', 
            'Low': 'Low_Price',
            'Close': 'Closing_Price',
            'Volume': 'Volume_Traded'
        }
        save_data.columns = [column_names.get(col, col) for col in save_data.columns]
        
        # Create directory
        symbol_dir = self.data_dir / data_frequency / data_type / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        if time_frame.get('start_date') and time_frame.get('end_date'):
            start_year = time_frame['start_date'].split('-')[0]
            end_year = time_frame['end_date'].split('-')[0]
            if start_year == end_year:
                filename = f"{symbol}_{data_frequency.upper()}_{start_year}.csv"
            else:
                filename = f"{symbol}_{data_frequency.upper()}_{start_year}_{end_year}.csv"
        else:
            filename = f"{symbol}_{data_frequency.upper()}.csv"
        
        file_path = symbol_dir / filename
        
        # Check for existing file
        if file_path.exists():
            print(f"WARNING:  File already exists: {file_path}")
            while True:
                response = input("Replace it? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    break
                elif response in ['n', 'no']:
                    print("ERROR: Skipping this file.")
                    return False
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
        
        # Save data
        save_data = save_data.reset_index()
        save_data['Date'] = save_data['Date'].dt.strftime('%Y-%m-%d')
        save_data.to_csv(file_path, index=False)
        
        print(f"SUCCESS: Data saved to: {file_path}")
        print(f" Records: {len(save_data)}")
        return True
    
    def _process_stock_request_with_llm(self, user_input):
        """Process stock request using LLM for natural language understanding."""
        print(f"\nProcessing with LLM: '{user_input}'")
        print("=" * 60)
        
        # Use LLM to parse the request
        parsed_request = self._parse_request_with_llm(user_input)
        
        if not parsed_request:
            print("ERROR: Failed to parse request with LLM.")
            return False
        
        # Check if clarification is needed
        if parsed_request.get('clarification_needed'):
            print(f" {parsed_request.get('clarification_message', 'I need clarification.')}")
            return False
        
        # Extract information from parsed request
        symbols = parsed_request.get('symbols', [])
        time_frame = parsed_request.get('time_frame', {})
        data_type = parsed_request.get('data_type', 'both')
        is_multiple_files = parsed_request.get('is_multiple_files', False)
        
        if not symbols:
            print("ERROR: Could not identify any stock symbols.")
            return False
        
        # Show what the LLM understood
        print(f" LLM understood:")
        print(f"   - Symbols: {', '.join(symbols)}")
        if time_frame.get('start_date') and time_frame.get('end_date'):
            print(f"   - Date Range: {time_frame['start_date']} to {time_frame['end_date']}")
        if time_frame.get('data_frequencies'):
            print(f"   - Frequencies: {', '.join(time_frame['data_frequencies'])}")
        print(f"   - Data Type: {data_type}")
        if is_multiple_files:
            print(f"   - Multiple Files: Yes")
        
        # Ask for confirmation
        while True:
            response = input("\nProceed with this request? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                break
            elif response in ['n', 'no']:
                print("ERROR: Request cancelled.")
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        
        # Process based on whether it's multiple files or single file
        success_count = 0
        total_files = 0
        
        if is_multiple_files:
            # Handle multiple files - need to create separate requests
            print(f"\n Processing as multiple files...")
            
            # If we have multiple years, create separate time frames for each
            years = []
            if time_frame.get('start_date') and time_frame.get('end_date'):
                # Handle both string and list formats
                start_date = time_frame['start_date']
                end_date = time_frame['end_date']
                
                if isinstance(start_date, list):
                    # If LLM returned lists, extract years from each
                    years = [date.split('-')[0] if isinstance(date, str) else str(date).split('-')[0] for date in start_date]
                else:
                    # Handle single string format
                    start_year = start_date.split('-')[0]
                    end_year = end_date.split('-')[0] if isinstance(end_date, str) else str(end_date).split('-')[0]
                    if start_year == end_year:
                        years = [start_year]
                    else:
                        years = [start_year, end_year]
            
            # Extract years from the original request if not in time_frame
            if not years:
                year_pattern = r'\b(20\d{2})\b'
                years = re.findall(year_pattern, user_input)
            
            # Create combinations for multiple files
            frequencies = time_frame.get('data_frequencies', ['daily'])
            
            for symbol in symbols:
                for data_frequency in frequencies:
                    for year in years:
                        # Create specific time frame for this year
                        year_time_frame = {
                            'start_date': f"{year}-01-01",
                            'end_date': f"{year}-12-31",
                            'data_frequencies': [data_frequency]
                        }
                        
                        print(f"\n Fetching {data_frequency} data for {symbol} ({year})...")
                        total_files += 1
                        
                        # Fetch data
                        data = self._fetch_historical_data(symbol, year_time_frame, data_frequency)
                        if data is None:
                            continue
                        
                        # Save data
                        if data_type == "opening":
                            success = self._save_data(symbol, data, "opening", year_time_frame, data_frequency)
                        elif data_type == "closing":
                            success = self._save_data(symbol, data, "closing", year_time_frame, data_frequency)
                        else:  # both
                            success1 = self._save_data(symbol, data, "opening", year_time_frame, data_frequency)
                            success2 = self._save_data(symbol, data, "closing", year_time_frame, data_frequency)
                            success = success1 and success2
                        
                        if success:
                            success_count += 1
        else:
            # Handle single file
            for symbol in symbols:
                frequencies = time_frame.get('data_frequencies', ['daily'])
                
                for data_frequency in frequencies:
                    print(f"\n Fetching {data_frequency} data for {symbol}...")
                    total_files += 1
                    
                    # Fetch data
                    data = self._fetch_historical_data(symbol, time_frame, data_frequency)
                    if data is None:
                        continue
                    
                    # Save data
                    if data_type == "opening":
                        success = self._save_data(symbol, data, "opening", time_frame, data_frequency)
                    elif data_type == "closing":
                        success = self._save_data(symbol, data, "closing", time_frame, data_frequency)
                    else:  # both
                        success1 = self._save_data(symbol, data, "opening", time_frame, data_frequency)
                        success2 = self._save_data(symbol, data, "closing", time_frame, data_frequency)
                        success = success1 and success2
                    
                    if success:
                        success_count += 1
        
        if success_count > 0:
            print(f"\n Successfully processed {success_count}/{total_files} file(s)!")
        
        return success_count > 0
    
    def _handle_stock_analysis_request(self, user_input):
        """Handle stock analysis requests using LLM."""
        print(f"\nProcessing stock analysis: '{user_input}'")
        print("=" * 60)
        
        # Get current date for LLM context
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Extract symbols from the request using LLM
        symbols = self._extract_symbols_with_llm(user_input)
        if not symbols:
            return "ERROR: Could not identify any stock symbols in your analysis request."
        
        # Get current stock data
        stock_info = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                
                # Suppress Yahoo Finance error messages
                import warnings
                import sys
                import io
                
                # Temporarily redirect stderr to suppress Yahoo Finance errors
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        
                        info = ticker.info
                        
                        # Get current price data
                        hist = ticker.history(period="1d")
                        if not hist.empty:
                            current_price = hist['Close'].iloc[-1]
                            prev_close = info.get('previousClose', current_price)
                            change = current_price - prev_close
                            change_percent = (change / prev_close) * 100 if prev_close else 0
                            
                            stock_data = {
                                'symbol': symbol,
                                'name': info.get('longName', symbol),
                                'current_price': current_price,
                                'previous_close': prev_close,
                                'change': change,
                                'change_percent': change_percent,
                                'volume': info.get('volume', 0),
                                'market_cap': info.get('marketCap', 0),
                                'pe_ratio': info.get('trailingPE', 0),
                                'sector': info.get('sector', 'Unknown')
                            }
                            stock_info.append(stock_data)
                        else:
                            stock_info.append({'symbol': symbol, 'error': 'No recent data available'})
                finally:
                    # Restore stderr
                    sys.stderr = old_stderr
                    
            except Exception as e:
                # Only show meaningful errors, suppress common Yahoo Finance errors
                if "delisted" not in str(e).lower() and "not found" not in str(e).lower():
                    stock_info.append({'symbol': symbol, 'error': str(e)})
                else:
                    stock_info.append({'symbol': symbol, 'error': 'Symbol not found or delisted'})
        
        # Use LLM to analyze the stock data
        analysis_prompt = f"""Analyze this stock information and provide insights:

IMPORTANT: Today's date is {current_date}

User Question: "{user_input}"

Stock Data:
{stock_info}

Please provide:
1. Current stock performance analysis
2. Key metrics and what they mean
3. Brief market context
4. Any notable trends or insights

Note: If the user mentions a specific date like "09-23-2025" and today is {current_date}, this is today's data, not future data.

Keep it concise but informative (2-3 paragraphs max)."""

        llm_analysis = self._call_llm(analysis_prompt)
        
        if llm_analysis:
            # Format the response nicely
            response = f" **Stock Analysis for {', '.join(symbols)}**\n\n"
            
            # Add current data summary
            for stock in stock_info:
                if 'error' not in stock:
                    response += f"**{stock['symbol']} ({stock['name']})**: "
                    response += f"${stock['current_price']:.2f} "
                    if stock['change'] >= 0:
                        response += f" +${stock['change']:.2f} (+{stock['change_percent']:.2f}%)\n"
                    else:
                        response += f"-${abs(stock['change']):.2f} ({stock['change_percent']:.2f}%)\n"
                else:
                    response += f"**{stock['symbol']}**: ERROR: {stock['error']}\n"
            
            response += f"\n **AI Analysis:**\n{llm_analysis.strip()}"
            return response
        else:
            return "ERROR: Sorry, I couldn't analyze the stock data right now. Please try again."
    
    def _generate_chat_response(self, user_input):
        """Generate a chatbot response for general chat using LLM."""
        user_input_lower = user_input.lower()
        
        # Greeting responses
        if any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return " Hello! I'm your LLM-Powered Stock Data Chatbot! I can help with stock data AND answer general questions using AI!"
        
        # Help responses
        if any(word in user_input_lower for word in ['help', 'what can you do', 'how', 'examples']):
            return """ I'm an LLM-Powered Chatbot! Here's what I can do:

 **Stock Data Processing:**
- "Apple and Microsoft weekly 2019-2021"
- "magnificent 7 last year daily data"
- "TSLA from 2020 to 2023 monthly"

 **General Questions (NEW!):**
- "What is the weather like today?"
- "What is the 13th amendment?"
- Any general knowledge questions

Note: **Features:**
- Uses LLM for both stock data AND general questions
- Handles company names and symbols
- Multiple symbols and timeframes
- Essential data storage (price, volume, etc.)
- Actually processes your requests!

Just ask me anything - stock data or general questions!"""
        
        # Thank you responses
        if any(word in user_input_lower for word in ['thank', 'thanks', 'appreciate']):
            return "You're welcome! I'm here to help with stock data AND general questions using AI!"
        
        # For general questions, use LLM to answer
        return self._answer_general_question(user_input)
    
    def _answer_general_question(self, user_input):
        """Use LLM to answer general questions."""
        print(f"\n Processing general question with LLM...")
        
        user_input_lower = user_input.lower()
        
        # Handle date/time questions specifically
        if any(indicator in user_input_lower for indicator in ['what date', 'what time', 'what day', 'when is', 'what is today', 'current date', 'current time']):
            from datetime import datetime
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M %p")
            
            return f" **General Question Answer:**\nToday is {date_str}\nThe current time is {time_str}"
        
        system_prompt = """You are a helpful AI assistant. Answer the user's question clearly and concisely. 
        Keep responses informative but not too long. If it's a factual question, provide accurate information.
        If it's a personal question, respond appropriately."""
        
        prompt = f"""Answer this question: "{user_input}"

Provide a clear, helpful response:"""

        llm_response = self._call_llm(prompt, system_prompt)
        
        if llm_response:
            return f" **General Question Answer:**\n{llm_response.strip()}"
        else:
            return "ERROR: Sorry, I couldn't process that question right now. Please try again or ask me about stock data!"
    
    def chat(self):
        """Main chatbot loop."""
        print(f"\n {self.name} - Chat Mode")
        print("=" * 50)
        print(" Hi! I'm your LLM-Powered Chatbot!")
        print(" I can handle stock data AND answer general questions!")
        print(" I'll stay active until you say goodbye!")
        print("\nNote: **Examples of what I can do:**")
        print(" **Stock Data Download:**")
        print("   - \"Apple and Microsoft weekly 2019-2021\"")
        print("   - \"magnificent 7 last year daily data\"")
        print("   - \"TSLA from 2020 to 2023 monthly\"")
        print(" **Stock Analysis (NEW!):**")
        print("   - \"What does Apple stock look like today?\"")
        print("   - \"How is Tesla performing?\"")
        print("   - \"Compare Apple and Microsoft\"")
        print(" **General Questions:**")
        print("   - \"What is the weather like today?\"")
        print("   - \"What is the 13th amendment?\"")
        print("   - \"Hello!\" (for general chat)")
        print("\nType 'quit', 'exit', or 'goodbye' to end our conversation.")
        print()
        
        while True:
            try:
                user_input = input(" LLM Stock Bot> ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye', 'stop', 'end']:
                    print(" Goodbye! Thanks for using the LLM Stock Data Chatbot!")
                    break
                
                # Check if it's a stock data request
                if self._is_stock_data_request(user_input):
                    self._process_stock_request_with_llm(user_input)
                elif self._is_stock_analysis_request(user_input):
                    # Handle stock analysis request
                    response = self._handle_stock_analysis_request(user_input)
                    print(f"\n{response}")
                else:
                    # Generate a general chat response
                    response = self._generate_chat_response(user_input)
                    print(f"\n{response}")
                
                print()  # Add blank line for readability
                
            except KeyboardInterrupt:
                print("\n Goodbye! Thanks for using the LLM Stock Data Chatbot!")
                break
            except EOFError:
                print("\n Input closed. Goodbye!")
                break
            except Exception as e:
                print(f"ERROR: Error: {e}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='LLM-Powered Stock Data Chatbot')
    parser.add_argument('--request', '-r', help='Process a single request')
    parser.add_argument('--chat', '-c', action='store_true', help='Start chatbot mode')
    
    args = parser.parse_args()
    
    chatbot = LLMStockChatbot()
    
    if args.request:
        if chatbot._is_stock_data_request(args.request):
            chatbot._process_stock_request_with_llm(args.request)
        else:
            print("ERROR: That doesn't appear to be a stock data request.")
            print("Note: Try something like: 'Apple and Microsoft weekly 2019-2021'")
    elif args.chat:
        chatbot.chat()
    else:
        # Default to chatbot mode
        chatbot.chat()

if __name__ == "__main__":
    main()
