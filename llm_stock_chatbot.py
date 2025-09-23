#!/usr/bin/env python3
"""
LLM-Powered Stock Chatbot - Uses LLM for Natural Language Processing
================================================================

This chatbot uses an LLM to properly understand natural language requests
and processes stock data accordingly.

Author: Stock Agent
Created: 2025-01-22
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

class LLMStockChatbot:
    """
    LLM-Powered Stock Chatbot that uses an LLM for natural language understanding.
    """
    
    def __init__(self):
        """Initialize the LLM Stock Chatbot."""
        self.name = "LLM Stock Data Chatbot"
        self.data_dir = Path("data")
        self._create_directory_structure()
        
        # LLM Configuration
        self.api_key = "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"
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet"
        
        # Magnificent 7 stocks
        self.magnificent_7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA']
        
        # Company name mappings
        self.company_mappings = {
            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'amazon': 'AMZN',
            'tesla': 'TSLA', 'meta': 'META', 'nvidia': 'NVDA', 'netflix': 'NFLX',
            'amd': 'AMD', 'intel': 'INTC', 'ibm': 'IBM', 'oracle': 'ORCL'
        }
        
        print(f"🤖 {self.name} initialized!")
        print("🧠 I use an LLM to understand your natural language requests!")
        print("📊 I can handle complex requests like 'Apple and Microsoft weekly 2019-2021'!")
        print("🔄 I'll stay active until you say goodbye!")
    
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
        
        print(f"📁 Data directories ready in {self.data_dir}")
    
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
            print(f"❌ LLM Error: {e}")
            return None
    
    def _parse_request_with_llm(self, user_input):
        """Use LLM to parse the user request into structured data."""
        
        system_prompt = """You are a stock data parsing assistant. Parse the user's natural language request and return a JSON response with the following structure:

{
    "symbols": ["AAPL", "MSFT"],
    "time_frame": {
        "start_date": "2019-01-01",
        "end_date": "2021-12-31",
        "data_frequencies": ["weekly"]
    },
    "data_type": "both",
    "is_multiple_files": false,
    "clarification_needed": false,
    "clarification_message": ""
}

Rules:
1. Extract stock symbols (handle company names like "Apple" -> "AAPL", "Microsoft" -> "MSFT")
2. Handle "magnificent 7" as all 7 stocks: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
3. Parse date ranges like "2019-2021", "last year", "10 years"
4. Detect data frequencies: daily, weekly, monthly, yearly
5. Determine data type: opening, closing, or both
6. If user says "and" between different symbols/timeframes, set is_multiple_files to true
7. If unclear, set clarification_needed to true with clarification_message
8. Always return valid JSON only, no other text"""

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
            print(f"❌ Failed to parse LLM response as JSON: {e}")
            print(f"LLM Response: {llm_response}")
            return None
    
    def _is_stock_data_request(self, user_input):
        """Detect if the user input is a stock data request."""
        user_input_lower = user_input.lower()
        
        # Keywords that indicate stock data requests
        stock_keywords = [
            'data', 'historical', 'price', 'quote', 'chart', 'stock', 'stocks',
            'weekly', 'monthly', 'yearly', 'daily', 'opening', 'closing',
            'from', 'to', 'between', 'range', 'period', 'year', 'years',
            'magnificent', 'secondly', 'last year', 'this year', 'yesterday'
        ]
        
        # Check for stock symbols, company names, or magnificent 7
        has_symbols = bool(re.search(r'\b([A-Z]{1,5})\b', user_input.upper()))
        has_companies = any(company in user_input_lower for company in self.company_mappings.keys())
        has_magnificent = 'magnificent' in user_input_lower
        
        has_keywords = any(keyword in user_input_lower for keyword in stock_keywords)
        
        return (has_symbols or has_companies or has_magnificent) and has_keywords
    
    def _fetch_historical_data(self, symbol, time_frame, data_frequency):
        """Fetch historical data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            
            if time_frame.get('start_date') and time_frame.get('end_date'):
                hist = ticker.history(start=time_frame['start_date'], end=time_frame['end_date'])
            else:
                # Use default period based on frequency
                period_map = {'daily': '1mo', 'weekly': '1y', 'monthly': '2y', 'yearly': 'max'}
                period = period_map.get(data_frequency, '1mo')
                hist = ticker.history(period=period)
            
            if hist.empty:
                print(f"❌ No data found for {symbol}")
                return None
            
            return hist
            
        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
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
            print(f"⚠️  File already exists: {file_path}")
            while True:
                response = input("Replace it? (y/n): ").lower().strip()
                if response in ['y', 'yes']:
                    break
                elif response in ['n', 'no']:
                    print("❌ Skipping this file.")
                    return False
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
        
        # Save data
        save_data = save_data.reset_index()
        save_data['Date'] = save_data['Date'].dt.strftime('%Y-%m-%d')
        save_data.to_csv(file_path, index=False)
        
        print(f"✅ Data saved to: {file_path}")
        print(f"📊 Records: {len(save_data)}")
        return True
    
    def _process_stock_request_with_llm(self, user_input):
        """Process stock request using LLM for natural language understanding."""
        print(f"\n🔍 Processing with LLM: '{user_input}'")
        print("=" * 60)
        
        # Use LLM to parse the request
        parsed_request = self._parse_request_with_llm(user_input)
        
        if not parsed_request:
            print("❌ Failed to parse request with LLM.")
            return False
        
        # Check if clarification is needed
        if parsed_request.get('clarification_needed'):
            print(f"🤔 {parsed_request.get('clarification_message', 'I need clarification.')}")
            return False
        
        # Extract information from parsed request
        symbols = parsed_request.get('symbols', [])
        time_frame = parsed_request.get('time_frame', {})
        data_type = parsed_request.get('data_type', 'both')
        is_multiple_files = parsed_request.get('is_multiple_files', False)
        
        if not symbols:
            print("❌ Could not identify any stock symbols.")
            return False
        
        # Show what the LLM understood
        print(f"🧠 LLM understood:")
        print(f"   • Symbols: {', '.join(symbols)}")
        if time_frame.get('start_date') and time_frame.get('end_date'):
            print(f"   • Date Range: {time_frame['start_date']} to {time_frame['end_date']}")
        if time_frame.get('data_frequencies'):
            print(f"   • Frequencies: {', '.join(time_frame['data_frequencies'])}")
        print(f"   • Data Type: {data_type}")
        if is_multiple_files:
            print(f"   • Multiple Files: Yes")
        
        # Ask for confirmation
        while True:
            response = input("\nProceed with this request? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                break
            elif response in ['n', 'no']:
                print("❌ Request cancelled.")
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
        
        # Process each symbol and frequency
        success_count = 0
        total_files = 0
        
        for symbol in symbols:
            frequencies = time_frame.get('data_frequencies', ['daily'])
            
            for data_frequency in frequencies:
                print(f"\n📡 Fetching {data_frequency} data for {symbol}...")
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
            print(f"\n🎉 Successfully processed {success_count}/{total_files} file(s)!")
        
        return success_count > 0
    
    def _generate_chat_response(self, user_input):
        """Generate a chatbot response for general chat."""
        user_input_lower = user_input.lower()
        
        # Greeting responses
        if any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "👋 Hello! I'm your LLM-Powered Stock Data Chatbot! I use advanced AI to understand your requests like 'Apple and Microsoft weekly 2019-2021'!"
        
        # Help responses
        if any(word in user_input_lower for word in ['help', 'what can you do', 'how', 'examples']):
            return """🤖 I'm an LLM-Powered Stock Data Chatbot! Here's what I can do:

🧠 **AI-Powered Understanding:**
• "Apple and Microsoft weekly 2019-2021"
• "magnificent 7 last year daily data"
• "TSLA from 2020 to 2023 monthly"
• Complex natural language requests

💡 **Features:**
• Uses LLM for natural language processing
• Handles company names and symbols
• Multiple symbols and timeframes
• Essential data storage (price, volume, etc.)
• Actually processes your requests!

Just ask me for any stock data in natural language!"""
        
        # Thank you responses
        if any(word in user_input_lower for word in ['thank', 'thanks', 'appreciate']):
            return "😊 You're welcome! I'm here to help with all your stock data needs using AI!"
        
        # General responses
        if '?' in user_input:
            return "🤔 That's an interesting question! I'm specialized in stock data processing using AI. Try asking me for data like 'Apple and Microsoft weekly 2019-2021'!"
        
        # Default response
        return "💬 I'm listening! I use AI to understand your requests. Try something like 'Apple and Microsoft weekly 2019-2021'!"
    
    def chat(self):
        """Main chatbot loop."""
        print(f"\n🤖 {self.name} - Chat Mode")
        print("=" * 50)
        print("💬 Hi! I'm your LLM-Powered Stock Data Chatbot!")
        print("🧠 I use advanced AI to understand your natural language requests!")
        print("🔄 I'll stay active until you say goodbye!")
        print("\n💡 **Examples of what I can do:**")
        print("   • \"Apple and Microsoft weekly 2019-2021\"")
        print("   • \"magnificent 7 last year daily data\"")
        print("   • \"TSLA from 2020 to 2023 monthly\"")
        print("   • \"Hello!\" (for general chat)")
        print("\nType 'quit', 'exit', or 'goodbye' to end our conversation.")
        print()
        
        while True:
            try:
                user_input = input("🤖 LLM Stock Bot> ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye', 'stop', 'end']:
                    print("👋 Goodbye! Thanks for using the LLM Stock Data Chatbot!")
                    break
                
                # Check if it's a stock data request
                if self._is_stock_data_request(user_input):
                    self._process_stock_request_with_llm(user_input)
                else:
                    # Generate a general chat response
                    response = self._generate_chat_response(user_input)
                    print(f"\n{response}")
                
                print()  # Add blank line for readability
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye! Thanks for using the LLM Stock Data Chatbot!")
                break
            except EOFError:
                print("\n👋 Input closed. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

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
            print("❌ That doesn't appear to be a stock data request.")
            print("💡 Try something like: 'Apple and Microsoft weekly 2019-2021'")
    elif args.chat:
        chatbot.chat()
    else:
        # Default to chatbot mode
        chatbot.chat()

if __name__ == "__main__":
    main()
