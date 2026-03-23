#!/usr/bin/env python3
"""
Stock Agent Service Layer
==========================

Backend service that handles all stock agent logic.
This can be used by both CLI and future frontend.

Usage:
    from stock_agent_service import StockAgentService
    
    service = StockAgentService()
    response = service.process_request("Apple weekly data 2020-2024")
"""

import yfinance as yf
import pandas as pd
import json
import requests
import re
from datetime import datetime
from pathlib import Path
import polars as pl
from typing import Dict, List, Optional, Tuple
import sys

# Import dependencies
try:
    from config import DATA_DIRECTORY
    from evaluation_module import StockDataEvaluator, WebScrapingValidator
    from financial_analysis_module import FourthLayerFinancialAnalysis
    from llm_config import get_llm_client
    from session_memory import SessionMemory
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


class StockAgentService:
    """
    Core service layer for stock agent functionality.
    Separated from UI/CLI for frontend integration.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the stock agent service.
        
        Args:
            llm_client: Optional LLM client instance. If None, will auto-configure.
        """
        self.data_dir = DATA_DIRECTORY
        self._create_directory_structure()
        
        # Initialize LLM client
        if llm_client:
            self.llm_client = llm_client
        else:
            self.llm_client = get_llm_client()
        
        # Initialize evaluation modules
        self.evaluator = StockDataEvaluator()
        self.web_scraping_validator = WebScrapingValidator()
        
        # Context management
        self.conversation_context = []
        self.max_context_length = 15
        
        # Session memory (comprehensive context tracking)
        self.memory = SessionMemory(llm_client=self.llm_client)
        
        # Configuration
        self.temperature = 0.1
        self.max_tokens = 1000
    
    def _create_directory_structure(self):
        """Create the organized directory structure for data storage."""
        directories = [
            "weekly/beginning", "weekly/closing",
            "monthly/beginning", "monthly/closing",
            "yearly/beginning", "yearly/closing",
            "daily/beginning", "daily/closing"
        ]
        
        for dir_path in directories:
            full_path = self.data_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
    
    def process_request(self, user_input: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        Process a user request and return structured response.
        
        Args:
            user_input: User's input text
            context: Optional conversation context
            
        Returns:
            Dict with:
                - type: Request type (stock_data, stock_analysis, financial_analysis, general)
                - response: Response text
                - data: Optional structured data
                - success: Boolean
                - status: Optional status messages during processing
        """
        # Update context
        if context:
            self.conversation_context = context[-self.max_context_length:]
        
        # FAST PATH: Handle simple greetings/commands without LLM (instant response)
        fast_response = self._handle_fast_path(user_input)
        if fast_response:
            # Track fast-path interactions in memory too
            self.memory.add_interaction(
                user_input=user_input,
                bot_response=fast_response.get('response', ''),
                request_type='fast_path',
                success=True
            )
            return fast_response
        
        # Check for contextual requests
        contextual_result = self._handle_contextual_request(user_input)
        processed_input = contextual_result['combined_request'] if contextual_result else user_input
        
        # Determine request type
        request_type = self._detect_request_type(processed_input)
        
        # Generate initial status message (FAST - no LLM call for screening)
        # For screening, use instant status. For others, generate with LLM if needed.
        if request_type == "stock_screening":
            initial_status = "🔍 Screening stocks based on your criteria. This may take a few minutes..."
        else:
            initial_status = self._generate_working_status(user_input, request_type)
        
        # Process based on type
        if request_type == "stock_screening":
            result = self._handle_stock_screening(processed_input)
        elif request_type == "financial_analysis":
            result = self._handle_financial_analysis(processed_input)
        elif request_type == "stock_data":
            result = self._handle_stock_data_request(processed_input)
        elif request_type == "stock_analysis":
            result = self._handle_stock_analysis(processed_input)
        else:
            result = self._handle_general_question(processed_input)
        
        # Add status message to result
        if initial_status:
            result['status'] = initial_status
        
        # Track interaction in session memory
        data = result.get('data')
        data_keys = []
        if isinstance(data, dict):
            data_keys = list(data.keys())
        elif isinstance(data, list) and data:
            data_keys = [f"list_{len(data)}_items"]
        
        self.memory.add_interaction(
            user_input=user_input,
            bot_response=result.get('response', ''),
            request_type=request_type,
            success=result.get('success', False),
            metadata={'data_keys': data_keys}
        )
        
        return result
    
    def _generate_working_status(self, user_input: str, request_type: str) -> str:
        """
        Generate instant status message - NO LLM CALL (hardcoded for speed).
        """
        # Hardcoded status messages - instant response, no LLM needed
        STATUS_MESSAGES = {
            "stock_screening": "🔍 Screening stocks based on your criteria. This may take a few minutes...",
            "stock_data": "📥 Downloading stock data. Please wait...",
            "stock_analysis": "📊 Analyzing stock performance. Gathering data...",
            "financial_analysis": "💼 Performing financial analysis. This may take a moment...",
            "general": "🤔 Processing your request..."
        }
        
        return STATUS_MESSAGES.get(request_type, "⏳ Working on it...")
    
    def _handle_fast_path(self, user_input: str) -> Optional[Dict]:
        """
        Fast path for simple queries that don't need LLM.
        Returns instant response without LLM call.
        Only matches EXACT phrases or words at word boundaries.
        """
        user_lower = user_input.lower().strip()
        words = set(user_lower.split())  # Split into words for exact matching
        
        # Greetings - must be exact word match or exact phrase
        # Single word greetings (must match entire input or be a standalone word)
        single_word_greetings = {'hello', 'hi', 'hey', 'yo', 'howdy', 'greetings', 'sup', 'hiya'}
        
        # Multi-word greetings (exact phrase match)
        phrase_greetings = ['good morning', 'good afternoon', 'good evening',
                           'how ya doin', 'how are you', 'whats up', "what's up"]
        
        # Check if input IS a greeting (short input) or STARTS with greeting
        if user_lower in single_word_greetings or words & single_word_greetings:
            # Only trigger if it's clearly a greeting (short message or greeting word is prominent)
            if len(user_lower) < 20 or user_lower.split()[0] in single_word_greetings:
                return {
                    "type": "general",
                    "response": "👋 Hey! I'm your Stock Agent! I can help you with:\n\n• **Stock Data**: \"Apple weekly data 2020-2024\"\n• **Stock Analysis**: \"How is Tesla performing?\"\n• **Financial Analysis**: \"Stock analysis of NVIDIA\"\n• **Stock Screening**: \"Screen technology sector\"\n• **General Questions**: \"What is 2+2?\"\n\nWhat would you like to know?",
                    "success": True
                }
        
        # Check phrase greetings
        if any(greeting in user_lower for greeting in phrase_greetings):
            return {
                "type": "general", 
                "response": "👋 Hey! I'm your Stock Agent! I can help you with:\n\n• **Stock Data**: \"Apple weekly data 2020-2024\"\n• **Stock Analysis**: \"How is Tesla performing?\"\n• **Financial Analysis**: \"Stock analysis of NVIDIA\"\n• **Stock Screening**: \"Screen technology sector\"\n• **General Questions**: \"What is 2+2?\"\n\nWhat would you like to know?",
                "success": True
            }
        
        # Help requests - exact phrase match only
        help_phrases = ['help', 'what can you do', 'what do you do', 'capabilities', 'features']
        if user_lower in help_phrases or any(phrase == user_lower for phrase in help_phrases):
            return {
                "type": "general",
                "response": "📊 **I'm your Stock Agent!** Here's how I can help:\n\n**Stock Data Download:**\n• \"Apple weekly data 2020-2024\"\n• \"Microsoft and Google daily 2023\"\n\n**Stock Analysis:**\n• \"How is Tesla performing?\"\n• \"Compare Apple and Microsoft\"\n\n**Financial Analysis:**\n• \"Stock analysis of NVIDIA\"\n• \"Should I buy Tesla?\"\n\n**Stock Screening (NEW!):**\n• \"Screen technology sector\"\n• \"Find undervalued healthcare stocks\"\n\n**General Questions:**\n• \"What is 2+2?\"\n• Any questions!\n\nJust ask me anything! 🚀",
                "success": True
            }
        
        # Also check if 'help' is a standalone word in short messages
        if 'help' in words and len(user_lower) < 30:
            return {
                "type": "general",
                "response": "📊 **I'm your Stock Agent!** Here's how I can help:\n\n**Stock Data Download:**\n• \"Apple weekly data 2020-2024\"\n• \"Microsoft and Google daily 2023\"\n\n**Stock Analysis:**\n• \"How is Tesla performing?\"\n• \"Compare Apple and Microsoft\"\n\n**Financial Analysis:**\n• \"Stock analysis of NVIDIA\"\n• \"Should I buy Tesla?\"\n\n**Stock Screening (NEW!):**\n• \"Screen technology sector\"\n• \"Find undervalued healthcare stocks\"\n\n**General Questions:**\n• \"What is 2+2?\"\n• Any questions!\n\nJust ask me anything! 🚀",
                "success": True
            }
        
        # Thank you - word must be present
        thanks_words = {'thank', 'thanks', 'thx'}
        if words & thanks_words:
            return {
                "type": "general",
                "response": "You're welcome! Happy to help! 😊",
                "success": True
            }
        
        # Exit commands - exact word match
        exit_words = {'bye', 'goodbye', 'quit', 'exit'}
        exit_phrases = ['see ya', 'see you later']
        if words & exit_words or any(phrase in user_lower for phrase in exit_phrases):
            return {
                "type": "general",
                "response": "👋 Goodbye! Thanks for using Stock Agent!",
                "success": True
            }
        
        return None  # Not a fast path query, continue with normal processing
    
    def _detect_request_type(self, user_input: str) -> str:
        """
        Detect the type of request using FAST keyword matching first.
        Uses fuzzy matching for typos. LLM only for truly ambiguous cases.
        """
        from difflib import get_close_matches
        
        user_lower = user_input.lower().strip()
        words = user_lower.split()
        
        # EXPANDED keyword sets with common misspellings
        SCREENING_KEYWORDS = {
            'screen', 'screening', 'scren', 'screeen', 'screning',  # misspellings
            'find good stocks', 'find undervalued', 'undervalued stocks', 
            'sector', 'sectors', 'criteria', 'filter stocks', 'find stocks', 
            'good stocks', 'investment opportunities', 'cheap stocks',
            'value stocks', 'undervalue', 'bargain', 'bargains'
        }
        
        DATA_KEYWORDS = {
            'download', 'donwload', 'downlod',  # misspellings
            'historical', 'historicl', 'historial',
            'weekly', 'monthly', 'daily', 'yearly',
            'get data', 'fetch data', 'stock data', 'price data',
            '2020', '2021', '2022', '2023', '2024', '2025'
        }
        
        FINANCIAL_KEYWORDS = {
            'financial analysis', 'financial statement', 'balance sheet',
            'income statement', 'cash flow', 'financials', 'fundamental analysis',
            'analyze financial', 'financial metrics', 'valuation', 'intrinsic value',
            'dcf', 'discounted cash flow', 'eps', 'revenue growth', 'profit margin',
            'balance sheet', 'balancesheet', 'income statment'  # misspellings
        }
        
        ANALYSIS_KEYWORDS = {
            'how is', 'how are', 'tell me about', 'analyze', 'analyse',  # UK spelling
            'performance', 'performing', 'price', 'stock price', 'current price',
            'trading', 'market cap', 'pe ratio', 'p/e', 'compare', 'vs', 'versus',
            'what about', 'whats happening', "what's happening"
        }
        
        COMPANY_NAMES = {
            'apple', 'tesla', 'microsoft', 'google', 'alphabet', 'amazon', 
            'nvidia', 'meta', 'facebook', 'netflix', 'amd', 'intel', 'ibm',
            'disney', 'boeing', 'walmart', 'costco', 'nike', 'coca-cola', 'pepsi'
        }
        
        # FAST PATH 1: Exact keyword match (no fuzzy needed)
        # Priority order: Screening > Analysis > Financial > Data (analysis should override data)
        if any(keyword in user_lower for keyword in SCREENING_KEYWORDS):
            return "stock_screening"
        
        # Check ANALYSIS_KEYWORDS FIRST (before data) - "analyze" should take precedence
        if any(keyword in user_lower for keyword in ANALYSIS_KEYWORDS):
            if re.search(r'\b[A-Z]{1,5}\b', user_input) or any(name in user_lower for name in COMPANY_NAMES):
                return "stock_analysis"
        
        if any(keyword in user_lower for keyword in FINANCIAL_KEYWORDS):
            return "financial_analysis"
        
        # DATA_KEYWORDS check - only if NOT an analysis request
        # Make it more specific: require explicit download keywords OR years, not just time periods
        if any(keyword in user_lower for keyword in DATA_KEYWORDS):
            # Only return stock_data if it's clearly a download request
            # Check for explicit download verbs OR specific year ranges
            has_download_verb = any(verb in user_lower for verb in ['download', 'donwload', 'downlod', 'get data', 'fetch data'])
            has_specific_years = any(year in user_lower for year in ['2020', '2021', '2022', '2023', '2024', '2025'])
            
            # If it has download verb OR specific years, it's a data request
            # But if it also has "analyze", prioritize analysis (already handled above)
            if has_download_verb or has_specific_years:
                return "stock_data"
        
        # FAST PATH 2: Fuzzy matching for typos (only if exact match failed)
        # Same priority order: Screening > Analysis > Financial > Data
        single_word_screening = {'screen', 'screening', 'sector', 'sectors', 'undervalued', 'criteria'}
        single_word_data = {'download', 'historical'}  # Removed time periods - they're ambiguous
        single_word_financial = {'financial', 'financials', 'valuation', 'balance', 'dcf'}
        single_word_analysis = {'analyze', 'analyse', 'performance', 'price', 'compare'}
        
        for word in words:
            if len(word) >= 4:  # Only fuzzy match words with 4+ chars
                if get_close_matches(word, single_word_screening, n=1, cutoff=0.8):
                    return "stock_screening"
                # Check analysis BEFORE data (same priority as exact match)
                if get_close_matches(word, single_word_analysis, n=1, cutoff=0.8):
                    if re.search(r'\b[A-Z]{1,5}\b', user_input) or any(name in user_lower for name in COMPANY_NAMES):
                        return "stock_analysis"
                if get_close_matches(word, single_word_financial, n=1, cutoff=0.8):
                    return "financial_analysis"
                # Data keywords - only explicit download terms
                if get_close_matches(word, single_word_data, n=1, cutoff=0.8):
                    return "stock_data"
        
        # LLM FALLBACK: Only for truly ambiguous cases (should be rare <5%)
        intent_prompt = f"""Classify this request into ONE category:

"{user_input}"

Categories:
- GENERAL_QUESTION: Non-stock questions
- STOCK_ANALYSIS: Current stock performance
- STOCK_DATA_DOWNLOAD: Historical data download
- FINANCIAL_ANALYSIS: Financial statement analysis  
- STOCK_SCREENING: Finding undervalued stocks by criteria

Reply with ONLY the category name."""

        intent = self._call_llm(intent_prompt)
        
        if intent:
            intent_upper = intent.upper().strip()
            if "STOCK_SCREENING" in intent_upper:
                return "stock_screening"
            elif "FINANCIAL_ANALYSIS" in intent_upper:
                return "financial_analysis"
            elif "STOCK_DATA_DOWNLOAD" in intent_upper:
                return "stock_data"
            elif "STOCK_ANALYSIS" in intent_upper:
                return "stock_analysis"
        
        return "general"
    
    def _call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Call the LLM."""
        try:
            return self.llm_client.call(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        except Exception as e:
            print(f"ERROR: LLM call failed: {e}")
            return None
    
    def _handle_contextual_request(self, user_input: str) -> Optional[Dict]:
        """Handle contextual requests."""
        if not self.conversation_context:
            return None
        
        # Simple context handling - can be enhanced
        last_entry = self.conversation_context[-1]
        if last_entry.get('request_type') == 'clarification':
            return {
                'combined_request': f"{last_entry['user_input']} {user_input}",
                'original_previous': last_entry['user_input'],
                'original_current': user_input,
                'context_used': True
            }
        return None
    
    def _handle_financial_analysis(self, user_input: str) -> Dict:
        """Handle financial analysis requests."""
        try:
            symbols = self._extract_symbols(user_input)
            if not symbols:
                return {
                    "type": "financial_analysis",
                    "response": "ERROR: Could not identify any stock symbols.",
                    "success": False
                }
            
            symbol = symbols[0]
            analyzer = FourthLayerFinancialAnalysis()
            analysis_result = analyzer.analyze_stock_financials(symbol)
            
            return {
                "type": "financial_analysis",
                "response": analysis_result,
                "symbol": symbol,
                "success": True
            }
        except Exception as e:
            return {
                "type": "financial_analysis",
                "response": f"ERROR: {str(e)}",
                "success": False
            }
    
    def _handle_stock_data_request(self, user_input: str) -> Dict:
        """Handle stock data download requests."""
        parsed_request = self._parse_request(user_input)
        
        if not parsed_request:
            return {
                "type": "stock_data",
                "response": "ERROR: Failed to parse request.",
                "success": False
            }
        
        if parsed_request.get('clarification_needed'):
            return {
                "type": "stock_data",
                "response": parsed_request.get('clarification_message', 'Clarification needed'),
                "success": False,
                "clarification_needed": True
            }
        
        # Extract information from parsed request
        symbols = parsed_request.get('symbols', [])
        time_frame = parsed_request.get('time_frame', {})
        data_type = parsed_request.get('data_type', 'both')
        data_frequencies = parsed_request.get('data_frequencies', ['daily'])
        is_multiple_files = parsed_request.get('is_multiple_files', False)
        
        if not symbols:
            return {
                "type": "stock_data",
                "response": "ERROR: Could not identify any stock symbols.",
                "success": False
            }
        
        # Process the download
        success_count = 0
        total_files = 0
        downloaded_files = []
        
        if is_multiple_files:
            # Handle multiple files (e.g., "2023 and 2024")
            years = []
            if time_frame.get('start_date') and time_frame.get('end_date'):
                start_date = time_frame['start_date']
                end_date = time_frame['end_date']
                if isinstance(start_date, list):
                    years = [date.split('-')[0] if isinstance(date, str) else str(date).split('-')[0] for date in start_date]
                else:
                    start_year = start_date.split('-')[0]
                    end_year = end_date.split('-')[0] if isinstance(end_date, str) else str(end_date).split('-')[0]
                    if start_year == end_year:
                        years = [start_year]
                    else:
                        years = [start_year, end_year]
            
            if not years:
                # Extract years from user input
                year_pattern = r'\b(20\d{2})\b'
                years = re.findall(year_pattern, user_input)
            
            for symbol in symbols:
                for data_frequency in data_frequencies:
                    for year in years:
                        year_time_frame = {
                            'start_date': f"{year}-01-01",
                            'end_date': f"{year}-12-31",
                            'data_frequencies': [data_frequency]
                        }
                        total_files += 1
                        files = self._download_and_save(symbol, year_time_frame, data_frequency, data_type)
                        if files:
                            success_count += 1
                            downloaded_files.extend(files)
        else:
            # Handle single file
            for symbol in symbols:
                for data_frequency in data_frequencies:
                    total_files += 1
                    files = self._download_and_save(symbol, time_frame, data_frequency, data_type)
                    if files:
                        success_count += 1
                        downloaded_files.extend(files)
        
        if success_count > 0:
            response_msg = f"✅ Successfully downloaded {success_count}/{total_files} file(s)!\n\n"
            response_msg += f"**Downloaded files:**\n"
            for file_path in downloaded_files:
                response_msg += f"• {file_path}\n"
            
            # Track downloads in session memory
            period_str = f"{time_frame.get('start_date', '')} to {time_frame.get('end_date', '')}"
            for symbol in symbols:
                self.memory.track_stock(symbol=symbol)
                for freq in data_frequencies:
                    self.memory.track_download(
                        symbol=symbol,
                        period=period_str,
                        interval=freq,
                        filepath=str(downloaded_files[0]) if downloaded_files else None
                    )
            
            return {
                "type": "stock_data",
                "response": response_msg,
                "data": {
                    "symbols": symbols,
                    "files_downloaded": downloaded_files,
                    "success_count": success_count,
                    "total_files": total_files
                },
                "success": True
            }
        else:
            return {
                "type": "stock_data",
                "response": "ERROR: Failed to download any data. Please check the symbols and date range.",
                "success": False
            }
    
    def _map_frequency_to_interval(self, data_frequency: str) -> str:
        """Map data frequency to Yahoo Finance interval."""
        mapping = {
            'daily': '1d',
            'weekly': '1wk',
            'monthly': '1mo',
            'yearly': '1y',
            'minute': '1m',
            'hourly': '1h'
        }
        return mapping.get(data_frequency.lower(), '1d')
    
    def _map_frequency_to_period(self, data_frequency: str) -> str:
        """Map data frequency to Yahoo Finance period."""
        mapping = {
            'daily': '1mo',
            'weekly': '1y',
            'monthly': '2y',
            'yearly': 'max',
            'minute': '1d',
            'hourly': '1d'
        }
        return mapping.get(data_frequency.lower(), '1mo')
    
    def _fetch_historical_data(self, symbol: str, time_frame: Dict, data_frequency: str) -> Optional[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            interval = self._map_frequency_to_interval(data_frequency)
            
            if time_frame.get('start_date') and time_frame.get('end_date'):
                start_date = time_frame['start_date']
                end_date = time_frame['end_date']
                
                # For minute/hourly data, extend end date to next day
                if data_frequency in ['minute', 'hourly']:
                    from datetime import datetime, timedelta
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                    end_date = end_dt.strftime('%Y-%m-%d')
                
                hist = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                period = self._map_frequency_to_period(data_frequency)
                hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                return None
            
            return hist
            
        except Exception as e:
            print(f"ERROR: Error fetching data for {symbol}: {e}")
            return None
    
    def _download_and_save(self, symbol: str, time_frame: Dict, data_frequency: str, data_type: str) -> List[str]:
        """Download and save stock data. Returns list of saved file paths."""
        saved_files = []
        
        # Fetch data
        data = self._fetch_historical_data(symbol, time_frame, data_frequency)
        if data is None:
            return saved_files
        
        # Save based on data_type
        if data_type == "opening":
            file_path = self._save_data(symbol, data, "opening", time_frame, data_frequency)
            if file_path:
                saved_files.append(str(file_path))
        elif data_type == "closing":
            file_path = self._save_data(symbol, data, "closing", time_frame, data_frequency)
            if file_path:
                saved_files.append(str(file_path))
        else:  # both
            file_path1 = self._save_data(symbol, data, "opening", time_frame, data_frequency)
            file_path2 = self._save_data(symbol, data, "closing", time_frame, data_frequency)
            if file_path1:
                saved_files.append(str(file_path1))
            if file_path2:
                saved_files.append(str(file_path2))
        
        return saved_files
    
    def _save_data(self, symbol: str, data: pd.DataFrame, data_type: str, time_frame: Dict, data_frequency: str) -> Optional[Path]:
        """Save data to database and optionally CSV (Phase 2/3: database-first with optional CSV). Returns file path if CSV written."""
        if data is None or data.empty:
            return None
        
        # Select essential columns
        essential_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        available_columns = [col for col in essential_columns if col in data.columns]
        
        if not available_columns:
            return None
        
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
        
        # Reset index to get Date column
        save_data.reset_index(inplace=True)
        if 'Date' not in save_data.columns and 'Datetime' in save_data.columns:
            save_data.rename(columns={'Datetime': 'Date'}, inplace=True)
        
        # ========== PHASE 2: WRITE TO DATABASE (PRIMARY) ==========
        try:
            from database import get_database
            db = get_database()
            
            # Insert prices into database
            db.insert_prices(symbol, save_data.copy(), data_frequency, data_type)
            
            # Also upsert stock if not exists (basic info)
            if not db.get_stock(symbol):
                db.upsert_stock(symbol=symbol)
        except Exception as e:
            # Database write should not fail silently in Phase 2
            print(f"WARNING: Database write failed: {e}")
        
        # ========== PHASE 3: OPTIONAL CSV WRITE ==========
        from config import ENABLE_CSV_WRITES
        if not ENABLE_CSV_WRITES:
            # Phase 3: CSV writes disabled
            return None
        
        # Phase 2: CSV writes still enabled (backup)
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
        
        # Save data (overwrite if exists - no user prompt in API mode)
        try:
            save_data.to_csv(file_path, index=False)
            return file_path
        except Exception as e:
            print(f"ERROR: Failed to save data to {file_path}: {e}")
            return None
    
    def _handle_stock_analysis(self, user_input: str) -> Dict:
        """Handle stock analysis requests."""
        symbols = self._extract_symbols(user_input)
        
        # Handle general market questions without specific symbols
        if not symbols:
            # Check if this is a general market question
            general_market_keywords = ['stock market', 'market', 'markets', 'dow', 's&p', 'nasdaq', 'overall market']
            if any(keyword in user_input.lower() for keyword in general_market_keywords):
                return self._handle_general_market_question(user_input)
            
            return {
                "type": "stock_analysis",
                "response": "I can help you analyze specific stocks. Please mention a stock symbol or company name (e.g., 'How is Apple performing?' or 'Tell me about TSLA').",
                "success": False
            }
        
        # Check if user wants to analyze downloaded data
        analysis_keywords = ['analyze', 'analysis', 'analyze the data', 'analyze data', 'look at the data', 'review the data']
        wants_data_analysis = any(keyword in user_input.lower() for keyword in analysis_keywords)
        
        # Try to load downloaded data first if analysis requested
        if wants_data_analysis:
            data_analysis = self._analyze_downloaded_data(symbols, user_input)
            if data_analysis:
                return data_analysis
        
        # Get current stock data (HARDCODED data fetching)
        stock_info = []
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                    
                    # Gather more hardcoded metrics
                    # Get dividend yield (can be None if company doesn't pay dividends)
                    dividend_yield = info.get('dividendYield') or info.get('trailingAnnualDividendYield')
                    if dividend_yield:
                        dividend_yield = float(dividend_yield) * 100  # Convert to percentage
                    
                    # Get payout ratio for dividend sustainability
                    payout_ratio = info.get('payoutRatio')
                    if payout_ratio:
                        payout_ratio = float(payout_ratio) * 100  # Convert to percentage
                    
                    stock_info.append({
                        'symbol': symbol,
                        'name': info.get('longName', symbol),
                        'current_price': float(current_price),
                        'change_percent': float(change_pct),
                        'pe_ratio': info.get('trailingPE', 'N/A'),
                        'market_cap': info.get('marketCap', 0),
                        'volume': info.get('volume', 0),
                        '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                        '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
                        'sector': info.get('sector', 'Unknown'),
                        'dividend_yield': dividend_yield if dividend_yield else None,  # None if no dividend
                        'payout_ratio': payout_ratio if payout_ratio else None,  # Payout ratio for sustainability
                    })
            except:
                pass
        
        if not stock_info:
            return {
                "type": "stock_analysis",
                "response": "Could not fetch data for the requested stocks.",
                "success": False
            }
        
        # Build STRUCTURED prompt with HARDCODED data for LLM
        structured_data = []
        for s in stock_info:
            mc_str = f"${s['market_cap']/1e9:.2f}B" if isinstance(s['market_cap'], (int, float)) and s['market_cap'] > 0 else "N/A"
            # Build dividend string with payout ratio for sustainability context
            if s.get('dividend_yield') and s.get('payout_ratio'):
                div_str = f"{s['dividend_yield']:.2f}% (Payout Ratio: {s['payout_ratio']:.0f}%)"
            elif s.get('dividend_yield'):
                div_str = f"{s['dividend_yield']:.2f}%"
            else:
                div_str = "No dividend"
            structured_data.append(f"""
**{s['symbol']}** ({s['name']}):
- Current Price: ${s['current_price']:.2f} ({s['change_percent']:+.2f}% today)
- P/E Ratio: {s['pe_ratio']}
- Market Cap: {mc_str}
- Dividend Yield: {div_str}
- 52-Week Range: ${s.get('52_week_low', 'N/A')} - ${s.get('52_week_high', 'N/A')}
- Sector: {s['sector']}""")
        
        # Get context first
        context_prompt = self.memory.get_context_prompt()
        
        # Build analysis prompt with context awareness
        if context_prompt:
            analysis_prompt = f"""Analyze these stocks using the EXACT metrics provided below:

{chr(10).join(structured_data)}

User asked: "{user_input}"

IMPORTANT: Check the SESSION CONTEXT in the system message. If the user's question refers to:
- "last week", "this week", "recently" - they may be asking about historical performance
- "it", "that stock", "the stock" - they're referring to a stock from previous conversation
- Time periods mentioned earlier - use the context to understand what period they mean

Provide a 2-3 paragraph analysis that:
1. References the SPECIFIC numbers above (price, P/E, market cap, etc.)
2. If the user asks about a specific time period (like "last week"), acknowledge if you need historical data or explain what you can provide
3. Compares to typical market valuations
4. Notes the 52-week position (near high/low?)
5. Gives a brief outlook

Be conversational and helpful. Use the exact data provided. If context shows previous discussion about this stock, reference it naturally."""
        else:
            analysis_prompt = f"""Analyze these stocks using the EXACT metrics provided below:

{chr(10).join(structured_data)}

User asked: "{user_input}"

Provide a 2-3 paragraph analysis that:
1. References the SPECIFIC numbers above (price, P/E, market cap, etc.)
2. Compares to typical market valuations
3. Notes the 52-week position (near high/low?)
4. Gives a brief outlook

Be conversational and helpful. Use the exact data provided."""

        # Inject session context into the LLM call
        system_prompt_with_context = f"{context_prompt}\n\nYou are a helpful stock analysis assistant. Use the SESSION CONTEXT above to understand what was previously discussed." if context_prompt else None
        analysis = self._call_llm(analysis_prompt, system_prompt=system_prompt_with_context)
        
        # Track stocks in session memory
        for s in stock_info:
            self.memory.track_stock(
                symbol=s['symbol'],
                name=s.get('name'),
                price=s.get('current_price'),
                sector=s.get('sector'),
                data={'pe_ratio': s.get('pe_ratio'), 'market_cap': s.get('market_cap')}
            )
            # Track the analysis
            self.memory.track_analysis(
                symbol=s['symbol'],
                analysis_type='stock_analysis',
                summary=f"Analyzed at ${s.get('current_price', 0):.2f}, P/E {s.get('pe_ratio', 'N/A')}"
            )
        
        return {
            "type": "stock_analysis",
            "response": analysis or "Analysis completed.",
            "data": stock_info,
            "success": True
        }
    
    def _handle_general_market_question(self, user_input: str) -> Dict:
        """Handle general market questions without specific symbols."""
        try:
            # Get major indices
            import yfinance as yf
            
            indices = {
                'SPY': 'S&P 500',
                'QQQ': 'NASDAQ',
                'DIA': 'Dow Jones'
            }
            
            market_data = []
            for symbol, name in indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    if not hist.empty and len(hist) >= 2:
                        current = hist['Close'].iloc[-1]
                        previous = hist['Close'].iloc[-2]
                        change = ((current - previous) / previous) * 100
                        market_data.append(f"{name}: ${current:.2f} ({change:+.2f}%)")
                except:
                    pass
            
            market_summary = "\n".join(market_data) if market_data else "Market data unavailable"
            
            prompt = f"""User asked: "{user_input}"

Current market data:
{market_summary}

Provide a helpful response about the stock market today."""
            
            # Inject session context
            context_prompt = self.memory.get_context_prompt()
            system_prompt_with_context = f"{context_prompt}\n\nYou are a helpful stock market assistant." if context_prompt else None
            response = self._call_llm(prompt, system_prompt=system_prompt_with_context)
            
            return {
                "type": "stock_analysis",
                "response": response or f"Here's today's market overview:\n{market_summary}",
                "success": True,
                "data": {"market_indices": market_data}
            }
        except Exception as e:
            return {
                "type": "stock_analysis",
                "response": f"I encountered an error getting market data: {str(e)}",
                "success": False
            }
    
    def _handle_stock_screening(self, user_input: str) -> Dict:
        """Handle fifth layer stock screening requests."""
        try:
            from fifth_layer_screening import FifthLayerScreening
            from llm_config import load_config, OpenRouterClientDirect
            
            # Extract sector from user input
            sector = self._extract_sector(user_input)
            if not sector:
                return {
                    "type": "stock_screening",
                    "response": "Please specify a sector to screen. Available sectors: Technology, Healthcare, Financials, Consumer Discretionary, Communication Services, Industrials, Consumer Staples, Energy, Utilities, Real Estate, Materials",
                    "success": False
                }
            
            # For screening tasks, prefer OpenRouter API (faster, better quality)
            # Fallback to local LLM if OpenRouter not available
            screening_llm_client = self._get_screening_llm_client()
            
            # Log which LLM is being used
            if hasattr(screening_llm_client, 'api_key'):
                print("🚀 Using OpenRouter API for screening (faster, better quality)")
            else:
                print("ℹ️ Using local LLM for screening")
            
            # Initialize screening system with appropriate LLM client
            screening = FifthLayerScreening(llm_client=screening_llm_client)
            
            # Run screening
            results = screening.screen_sector(sector)
            
            # Format results
            formatted_results = screening.format_results(results)
            
            # Handle case where no stocks found
            if len(results) == 0:
                return {
                    "type": "stock_screening",
                    "response": f"📊 **Screening Complete for {sector} Sector**\n\n"
                               f"**Result:** No undervalued stocks found that meet all criteria.\n\n"
                               f"**Why?** The screening criteria (all 6 must pass):\n"
                               f"1. Market cap < $5B (relaxed from $2B)\n"
                               f"2. P/B ratio < 1.5 (relaxed from 1.0)\n"
                               f"3. P/E ratio < 20 (relaxed from 15)\n"
                               f"4. Shares outstanding < 2B (relaxed from 1B)\n"
                               f"5. Debt < 65% (relaxed from 50%)\n"
                               f"6. Profit stability (no >20% decline in 5 years) (relaxed from 10%)\n\n"
                               f"**💡 Suggestions:**\n"
                               f"• Try a different sector (Technology, Financials, etc.)\n"
                               f"• This is normal - strict criteria ensure quality\n"
                               f"• Larger sectors have better chances of finding matches",
                    "data": [],
                    "success": True  # Still successful - screening completed, just no matches
                }
            
            return {
                "type": "stock_screening",
                "response": formatted_results,
                "data": results,
                "success": True
            }
            
        except ImportError:
            return {
                "type": "stock_screening",
                "response": "ERROR: Fifth layer screening module not found.",
                "success": False
            }
        except Exception as e:
            return {
                "type": "stock_screening",
                "response": f"ERROR: Screening failed: {str(e)}",
                "success": False
            }
    
    def _get_screening_llm_client(self):
        """
        Get LLM client for screening tasks.
        Prefers OpenRouter API (faster, better quality) but falls back to local LLM.
        """
        try:
            from llm_config import load_config, OpenRouterClientDirect
            
            config = load_config()
            
            # Try OpenRouter first (preferred for screening)
            if config.get("openrouter_api_key"):
                try:
                    # Try to import OpenRouter client
                    try:
                        from llm_client_openrouter import OpenRouterClient
                        return OpenRouterClient(
                            api_key=config["openrouter_api_key"],
                            model=config.get("openrouter_model", "anthropic/claude-3.5-sonnet")
                        )
                    except ImportError:
                        # Fallback to direct API client
                        return OpenRouterClientDirect(
                            api_key=config["openrouter_api_key"],
                            model=config.get("openrouter_model", "anthropic/claude-3.5-sonnet")
                        )
                except Exception as e:
                    print(f"⚠️ OpenRouter not available for screening, using local LLM: {e}")
                    # Fall back to local LLM
                    pass
            
            # Fallback to local LLM (current default)
            print("ℹ️ Using local LLM for screening (OpenRouter not configured)")
            return self.llm_client
            
        except Exception as e:
            print(f"⚠️ Error getting screening LLM client, using default: {e}")
            return self.llm_client
    
    def _extract_sector(self, user_input: str) -> Optional[str]:
        """Extract sector from user input using expanded aliases + fuzzy matching."""
        from difflib import get_close_matches
        
        # All 11 GICS sectors
        SECTORS = [
            "Technology", "Healthcare", "Financials", "Consumer Discretionary",
            "Communication Services", "Industrials", "Consumer Staples",
            "Energy", "Utilities", "Real Estate", "Materials"
        ]
        
        # EXPANDED sector aliases (5+ per sector)
        SECTOR_ALIASES = {
            # Technology
            'tech': 'Technology', 'technology': 'Technology', 'software': 'Technology',
            'hardware': 'Technology', 'semiconductor': 'Technology', 'semiconductors': 'Technology',
            'it': 'Technology', 'information technology': 'Technology', 'computer': 'Technology',
            'computers': 'Technology', 'chips': 'Technology', 'ai': 'Technology',
            # Healthcare
            'health': 'Healthcare', 'healthcare': 'Healthcare', 'medical': 'Healthcare',
            'pharma': 'Healthcare', 'pharmaceutical': 'Healthcare', 'biotech': 'Healthcare',
            'biotechnology': 'Healthcare', 'drug': 'Healthcare', 'drugs': 'Healthcare',
            'hospital': 'Healthcare', 'hospitals': 'Healthcare', 'medicine': 'Healthcare',
            # Financials
            'finance': 'Financials', 'financials': 'Financials', 'financial': 'Financials',
            'banking': 'Financials', 'banks': 'Financials', 'bank': 'Financials',
            'insurance': 'Financials', 'investment': 'Financials', 'fintech': 'Financials',
            'credit': 'Financials', 'mortgage': 'Financials', 'asset management': 'Financials',
            # Consumer Discretionary
            'consumer': 'Consumer Discretionary', 'consumer discretionary': 'Consumer Discretionary',
            'retail': 'Consumer Discretionary', 'retailers': 'Consumer Discretionary',
            'auto': 'Consumer Discretionary', 'automotive': 'Consumer Discretionary',
            'cars': 'Consumer Discretionary', 'restaurants': 'Consumer Discretionary',
            'leisure': 'Consumer Discretionary', 'travel': 'Consumer Discretionary',
            'hotels': 'Consumer Discretionary', 'apparel': 'Consumer Discretionary',
            # Communication Services
            'communications': 'Communication Services', 'communication': 'Communication Services',
            'communication services': 'Communication Services', 'media': 'Communication Services',
            'telecom': 'Communication Services', 'telecommunications': 'Communication Services',
            'social media': 'Communication Services', 'streaming': 'Communication Services',
            'entertainment': 'Communication Services', 'gaming': 'Communication Services',
            # Industrials
            'industrial': 'Industrials', 'industrials': 'Industrials', 'manufacturing': 'Industrials',
            'aerospace': 'Industrials', 'defense': 'Industrials', 'machinery': 'Industrials',
            'construction': 'Industrials', 'transportation': 'Industrials', 'logistics': 'Industrials',
            'shipping': 'Industrials', 'airlines': 'Industrials', 'railroad': 'Industrials',
            # Consumer Staples
            'staples': 'Consumer Staples', 'consumer staples': 'Consumer Staples',
            'food': 'Consumer Staples', 'beverage': 'Consumer Staples', 'beverages': 'Consumer Staples',
            'grocery': 'Consumer Staples', 'household': 'Consumer Staples', 'tobacco': 'Consumer Staples',
            'personal care': 'Consumer Staples', 'cleaning': 'Consumer Staples',
            # Energy
            'energy': 'Energy', 'oil': 'Energy', 'gas': 'Energy', 'oil and gas': 'Energy',
            'petroleum': 'Energy', 'fuel': 'Energy', 'drilling': 'Energy',
            'pipeline': 'Energy', 'refining': 'Energy', 'solar': 'Energy', 'renewable': 'Energy',
            # Utilities
            'utilities': 'Utilities', 'utility': 'Utilities', 'electric': 'Utilities',
            'electricity': 'Utilities', 'water': 'Utilities', 'power': 'Utilities',
            'natural gas': 'Utilities', 'regulated': 'Utilities',
            # Real Estate
            'real estate': 'Real Estate', 'realestate': 'Real Estate', 'reit': 'Real Estate',
            'reits': 'Real Estate', 'property': 'Real Estate', 'properties': 'Real Estate',
            'commercial real estate': 'Real Estate', 'residential': 'Real Estate',
            # Materials
            'materials': 'Materials', 'material': 'Materials', 'mining': 'Materials',
            'metals': 'Materials', 'steel': 'Materials', 'chemicals': 'Materials',
            'chemical': 'Materials', 'gold': 'Materials', 'copper': 'Materials',
            'aluminum': 'Materials', 'paper': 'Materials', 'packaging': 'Materials',
        }
        
        user_lower = user_input.lower()
        
        # STEP 1: Exact sector name match
        for sector in SECTORS:
            if sector.lower() in user_lower:
                return sector
        
        # STEP 2: Exact alias match
        for alias, sector in SECTOR_ALIASES.items():
            if alias in user_lower:
                return sector
        
        # STEP 3: Fuzzy matching for typos
        words = user_lower.split()
        alias_keys = list(SECTOR_ALIASES.keys())
        for word in words:
            if len(word) >= 4:
                matches = get_close_matches(word, alias_keys, n=1, cutoff=0.8)
                if matches:
                    return SECTOR_ALIASES[matches[0]]
        
        return None
    
    def _handle_general_question(self, user_input: str) -> Dict:
        """Handle general questions - always use LLM for proper responses."""
        user_lower = user_input.lower().strip()
        
        # Only skip truly empty inputs
        if len(user_input.strip()) == 0:
            return {
                "type": "general",
                "response": "I didn't catch that. How can I help you today? 😊",
                "success": True
            }
        
        # Get context first
        context_prompt = self.memory.get_context_prompt()
        
        # Format prompt to encourage better structured responses
        # Explicitly instruct LLM to use context if available
        if context_prompt:
            formatted_prompt = f"""User asked: "{user_input}"

IMPORTANT: Use the SESSION CONTEXT provided in the system message to understand what was previously discussed. 
- If the user's question refers to something mentioned earlier (like "last week", "that stock", "it", etc.), 
  check the RECENT CONVERSATION section to understand what they're referring to.
- Reference specific stocks, analyses, or data from the STOCKS DISCUSSED section when relevant.
- If the question is unclear, use the context to infer what the user might mean.

Provide a clear, helpful response. If the question is unclear or seems random:
- Politely acknowledge it
- Offer helpful suggestions about what you can help with
- Be friendly and conversational

If it's a valid question, answer it clearly. If the response is long or contains multiple points:
- Use **bold** for section headers
- Use bullet points for lists
- Break into clear sections
- Make it easy to scan and read

Keep the response informative and helpful."""
        else:
            formatted_prompt = f"""User asked: "{user_input}"

Provide a clear, helpful response. If the question is unclear or seems random:
- Politely acknowledge it
- Offer helpful suggestions about what you can help with
- Be friendly and conversational

If it's a valid question, answer it clearly. If the response is long or contains multiple points:
- Use **bold** for section headers
- Use bullet points for lists
- Break into clear sections
- Make it easy to scan and read

Keep the response informative and helpful."""
        
        try:
            # Inject session context for general questions
            system_prompt_with_context = f"{context_prompt}\n\nYou are a helpful assistant. Use the SESSION CONTEXT above to understand what was previously discussed in this conversation." if context_prompt else None
            response = self._call_llm(formatted_prompt, system_prompt=system_prompt_with_context)
            if response and len(response.strip()) > 0:
                return {
                    "type": "general",
                    "response": response,
                    "success": True
                }
        except Exception as e:
            print(f"Error in general question handler: {e}")
        
        # Fallback response if LLM fails
        return {
            "type": "general",
            "response": f"I'm not quite sure what you mean by \"{user_input}\", but I'm here to help! 😊\n\nI can help you with:\n• **Stock Analysis**: \"How is Tesla performing?\"\n• **Data Download**: \"Apple weekly data 2020-2024\"\n• **Stock Screening**: \"Screen technology sector\"\n• **General Questions**: Ask me anything!\n\nWhat would you like to know?",
            "success": True
        }
    
    def _extract_symbols(self, user_input: str) -> List[str]:
        """
        Extract stock symbols from user input.
        Uses FAST regex + expanded company dictionary + fuzzy matching.
        LLM only as last resort.
        """
        from difflib import get_close_matches
        
        # EXPANDED company to symbol mapping (50+ companies)
        COMPANY_TO_SYMBOL = {
            # Tech Giants
            'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'alphabet': 'GOOGL',
            'tesla': 'TSLA', 'amazon': 'AMZN', 'meta': 'META', 'facebook': 'META',
            'nvidia': 'NVDA', 'netflix': 'NFLX', 'intel': 'INTC', 'amd': 'AMD',
            'oracle': 'ORCL', 'adobe': 'ADBE', 'salesforce': 'CRM', 'ibm': 'IBM',
            'qualcomm': 'QCOM', 'cisco': 'CSCO', 'broadcom': 'AVGO', 'paypal': 'PYPL',
            'uber': 'UBER', 'airbnb': 'ABNB', 'spotify': 'SPOT', 'shopify': 'SHOP',
            'snowflake': 'SNOW', 'palantir': 'PLTR', 'zoom': 'ZM', 'docusign': 'DOCU',
            'crowdstrike': 'CRWD', 'datadog': 'DDOG', 'twilio': 'TWLO', 'square': 'SQ',
            'block': 'SQ', 'servicenow': 'NOW', 'workday': 'WDAY', 'splunk': 'SPLK',
            # Consumer
            'nike': 'NKE', 'disney': 'DIS', 'coca cola': 'KO', 'coke': 'KO', 'pepsi': 'PEP',
            'walmart': 'WMT', 'target': 'TGT', 'costco': 'COST', 'home depot': 'HD',
            'lowes': 'LOW', 'starbucks': 'SBUX', 'mcdonalds': 'MCD', 'chipotle': 'CMG',
            'dominos': 'DPZ', 'yum brands': 'YUM', 'procter gamble': 'PG', 'p&g': 'PG',
            'johnson johnson': 'JNJ', 'jnj': 'JNJ', 'colgate': 'CL',
            # Finance
            'jpmorgan': 'JPM', 'jp morgan': 'JPM', 'chase': 'JPM', 'bank of america': 'BAC',
            'wells fargo': 'WFC', 'goldman sachs': 'GS', 'morgan stanley': 'MS',
            'visa': 'V', 'mastercard': 'MA', 'american express': 'AXP', 'amex': 'AXP',
            'blackrock': 'BLK', 'berkshire': 'BRK-B', 'berkshire hathaway': 'BRK-B',
            'charles schwab': 'SCHW', 'schwab': 'SCHW', 'fidelity': 'FNF',
            # Healthcare
            'pfizer': 'PFE', 'moderna': 'MRNA', 'unitedhealth': 'UNH', 'united health': 'UNH',
            'abbvie': 'ABBV', 'merck': 'MRK', 'eli lilly': 'LLY', 'lilly': 'LLY',
            'bristol myers': 'BMY', 'amgen': 'AMGN', 'gilead': 'GILD', 'regeneron': 'REGN',
            'cvs': 'CVS', 'walgreens': 'WBA', 'anthem': 'ELV', 'cigna': 'CI',
            # Energy
            'exxon': 'XOM', 'exxonmobil': 'XOM', 'chevron': 'CVX', 'conocophillips': 'COP',
            'schlumberger': 'SLB', 'halliburton': 'HAL', 'marathon': 'MPC', 'valero': 'VLO',
            # Industrial/Other
            'boeing': 'BA', 'lockheed': 'LMT', 'lockheed martin': 'LMT', 'raytheon': 'RTX',
            'general electric': 'GE', 'ge': 'GE', '3m': 'MMM', 'caterpillar': 'CAT',
            'honeywell': 'HON', 'deere': 'DE', 'john deere': 'DE', 'ups': 'UPS', 'fedex': 'FDX',
            # EV/Auto
            'rivian': 'RIVN', 'lucid': 'LCID', 'ford': 'F', 'gm': 'GM', 'general motors': 'GM',
            # Magnificent 7 aliases
            'mag 7': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
            'magnificent 7': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
            'magnificent seven': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
            'faang': ['META', 'AAPL', 'AMZN', 'NFLX', 'GOOGL'],
        }
        
        # Common words to exclude from symbol detection
        COMMON_WORDS = {
            'I', 'A', 'AN', 'THE', 'IS', 'IT', 'IN', 'ON', 'AT', 'TO', 'OF', 'FOR', 
            'AND', 'OR', 'BUT', 'BY', 'AS', 'IF', 'MY', 'ME', 'WE', 'US', 'AM', 'PM',
            'AI', 'API', 'URL', 'HTTP', 'HTTPS', 'PDF', 'CSV', 'JSON', 'XML', 'HTML',
            'CSS', 'JS', 'TS', 'PY', 'GO', 'IO', 'TV', 'FY', 'Q1', 'Q2', 'Q3', 'Q4',
            'YTD', 'EPS', 'PE', 'PB', 'ROE', 'ROI', 'DCF', 'SEC', 'IPO', 'ETF', 'CEO',
            'CFO', 'COO', 'CTO', 'VP', 'SVP', 'EVP', 'LTD', 'INC', 'LLC', 'PLC', 'NV',
            'SA', 'AG', 'AB', 'UK', 'EU', 'US', 'USA', 'NYSE', 'NASDAQ', 'DOW', 'SP'
        }
        
        valid_symbols = []
        user_lower = user_input.lower()
        
        # STEP 1: Regex for explicit tickers (FAST)
        symbol_pattern = r'\b([A-Z]{1,5})\b'
        regex_symbols = re.findall(symbol_pattern, user_input)
        
        for sym in regex_symbols:
            if sym not in COMMON_WORDS and len(sym) >= 2:
                valid_symbols.append(sym)
        
        # STEP 2: Exact company name match (FAST)
        for company, symbol in COMPANY_TO_SYMBOL.items():
            if company in user_lower:
                if isinstance(symbol, list):
                    valid_symbols.extend(symbol)
                elif symbol not in valid_symbols:
                    valid_symbols.append(symbol)
        
        # STEP 3: Fuzzy company name match (only if no exact match)
        if not valid_symbols:
            company_names = [c for c in COMPANY_TO_SYMBOL.keys() if not isinstance(COMPANY_TO_SYMBOL[c], list)]
            words = user_lower.split()
            for word in words:
                if len(word) >= 4:
                    matches = get_close_matches(word, company_names, n=1, cutoff=0.85)
                    if matches:
                        matched_company = matches[0]
                        symbol = COMPANY_TO_SYMBOL[matched_company]
                        if isinstance(symbol, str) and symbol not in valid_symbols:
                            valid_symbols.append(symbol)
        
        # If found via hardcoded paths, return (fast path complete)
        if valid_symbols:
            return list(set(valid_symbols))
        
        # STEP 4: LLM fallback (rare - <5% of requests)
        prompt = f"""Extract stock symbols from: "{user_input}"
Return ONLY a JSON array like: ["AAPL", "MSFT"] or [] if none found."""
        
        response = self._call_llm(prompt)
        if response:
            try:
                response = response.strip()
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                
                symbols = json.loads(response)
                return symbols if isinstance(symbols, list) else []
            except:
                pass
        
        return []
    
    def _parse_request(self, user_input: str) -> Optional[Dict]:
        """Parse stock data request."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_year = datetime.now().year
        
        system_prompt = f"""Parse this stock data request and return JSON:
{{
    "symbols": ["AAPL"],
    "time_frame": {{"start_date": "2020-01-01", "end_date": "2024-12-31"}},
    "data_frequencies": ["weekly"],
    "data_type": "both",
    "clarification_needed": false
}}"""
        
        prompt = f"""Parse: "{user_input}"
Today is {current_date}. Return only JSON."""
        
        response = self._call_llm(prompt, system_prompt)
        if response:
            try:
                response = response.strip()
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                
                return json.loads(response)
            except:
                pass
        
        return None
    
    def _find_data_files(self, symbol: str, frequency: str = None) -> List[Path]:
        """Find all data files for a given symbol (Phase 2: check database first, fallback to CSV)."""
        from config import USE_DATABASE_READS
        
        # Phase 2: If database reads enabled, return empty list (data loaded from DB)
        if USE_DATABASE_READS:
            return []  # Signal to use database instead
        
        # Fallback: Original CSV file search (Phase 1 compatibility)
        symbol = symbol.upper()
        found_files = []
        
        # Check all frequencies if not specified
        frequencies = [frequency] if frequency else ['daily', 'weekly', 'monthly', 'yearly']
        
        for freq in frequencies:
            # Check both closing and opening data
            for data_type in ['closing', 'opening']:
                data_path = self.data_dir / freq / data_type / symbol
                if data_path.exists():
                    csv_files = list(data_path.glob("*.csv"))
                    found_files.extend(csv_files)
        
        return found_files
    
    def _load_data_files(self, files: List[Path], symbol: str = None, frequency: str = None, data_type: str = None) -> pd.DataFrame:
        """Load data from database (Phase 2) or CSV files (fallback)."""
        from config import USE_DATABASE_READS
        
        # Phase 2: Load from database if enabled
        if USE_DATABASE_READS:
            try:
                from database import get_database
                db = get_database()
                
                if symbol:
                    # Load from database
                    df = db.get_prices(symbol, frequency=frequency, data_type=data_type)
                    if not df.empty:
                        return df
                
                # If no symbol provided or database empty, fall back to CSV
                if not files:
                    return pd.DataFrame()
            except Exception as e:
                # If database fails, fall back to CSV
                print(f"WARNING: Database read failed, falling back to CSV: {e}")
        
        # Fallback: Original CSV loading (Phase 1 compatibility)
        if not files:
            return pd.DataFrame()
        
        all_data = []
        
        for file_path in files:
            try:
                df = pd.read_csv(file_path)
                # Standardize column names
                df.columns = df.columns.str.strip()
                all_data.append(df)
            except Exception as e:
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        # Combine all dataframes
        combined = pd.concat(all_data, ignore_index=True)
        
        # Remove duplicates and sort by date
        if 'Date' in combined.columns:
            combined['Date'] = pd.to_datetime(combined['Date'], errors='coerce')
            combined = combined.drop_duplicates(subset=['Date'], keep='last')
            combined = combined.sort_values('Date')
        
        return combined
    
    def _calculate_statistics(self, df: pd.DataFrame, symbol: str) -> Dict:
        """Calculate statistics from the data."""
        stats = {}
        
        # Find price column (could be Closing_Price, Close, etc.)
        price_col = None
        for col in ['Closing_Price', 'Close', 'Close_Price', 'Price']:
            if col in df.columns:
                price_col = col
                break
        
        if price_col:
            prices = pd.to_numeric(df[price_col], errors='coerce').dropna()
            
            if len(prices) > 0:
                stats = {
                    'min_price': float(prices.min()),
                    'max_price': float(prices.max()),
                    'avg_price': float(prices.mean()),
                    'current_price': float(prices.iloc[-1]),
                    'first_price': float(prices.iloc[0]),
                    'price_change': float(prices.iloc[-1] - prices.iloc[0]),
                    'price_change_pct': float((prices.iloc[-1] / prices.iloc[0] - 1) * 100),
                    'volatility': float(prices.std()),
                    'data_points': len(prices)
                }
                
                # Date range
                if 'Date' in df.columns:
                    dates = pd.to_datetime(df['Date'], errors='coerce').dropna()
                    if len(dates) > 0:
                        stats['date_range'] = {
                            'start': dates.min().strftime('%Y-%m-%d'),
                            'end': dates.max().strftime('%Y-%m-%d')
                        }
        
        # Volume analysis if available
        volume_col = None
        for col in ['Volume_Traded', 'Volume', 'Vol']:
            if col in df.columns:
                volume_col = col
                break
        
        if volume_col:
            volumes = pd.to_numeric(df[volume_col], errors='coerce').dropna()
            if len(volumes) > 0:
                stats['avg_volume'] = float(volumes.mean())
                stats['max_volume'] = float(volumes.max())
        
        return stats
    
    def _generate_data_analysis(self, df: pd.DataFrame, stats: Dict, symbol: str, user_input: str) -> str:
        """Generate analysis text using LLM based on actual data."""
        stats_summary = f"""
**{symbol} Stock Analysis**

📊 **Data Overview:**
- Data Points: {stats.get('data_points', 0):,}
- Date Range: {stats.get('date_range', {}).get('start', 'N/A')} to {stats.get('date_range', {}).get('end', 'N/A')}

💰 **Price Statistics:**
- Price Range: ${stats.get('min_price', 0):.2f} - ${stats.get('max_price', 0):.2f}
- Average Price: ${stats.get('avg_price', 0):.2f}
- Starting Price: ${stats.get('first_price', 0):.2f}
- Current Price: ${stats.get('current_price', 0):.2f}
- Price Change: ${stats.get('price_change', 0):+.2f} ({stats.get('price_change_pct', 0):+.2f}%)
- Volatility (Std Dev): ${stats.get('volatility', 0):.2f}
"""
        
        if stats.get('avg_volume'):
            stats_summary += f"\n📈 **Volume Statistics:**\n"
            stats_summary += f"- Average Volume: {stats.get('avg_volume', 0):,.0f}\n"
            stats_summary += f"- Maximum Volume: {stats.get('max_volume', 0):,.0f}\n"
        
        prompt = f"""Analyze this stock data for {symbol}:

{stats_summary}

User asked: "{user_input}"

Provide a well-formatted, comprehensive analysis with clear sections:

**Key Findings:**
[Summarize main insights in 2-3 bullet points]

**Price Performance:**
[Analyze price trends, changes, and what they indicate]

**Volatility Analysis:**
[Assess volatility levels and what they mean for risk]

**Notable Patterns:**
[Identify any trends, cycles, or anomalies in the data]

**Insights & Recommendations:**
[Provide actionable insights based on the data]

Format your response with clear section headers using **bold** and bullet points for easy reading. Be specific and reference actual numbers from the data."""
        
        # Inject session context for data analysis
        context_prompt = self.memory.get_context_prompt()
        system_prompt_with_context = f"{context_prompt}\n\nYou are a helpful stock data analyst." if context_prompt else None
        analysis = self._call_llm(prompt, system_prompt=system_prompt_with_context)
        
        # Format the final output nicely
        formatted_output = f"{stats_summary}\n\n---\n\n{analysis}" if analysis else f"{stats_summary}"
        return formatted_output
    
    def _combine_analysis(self, all_analysis: List[Dict], user_input: str) -> str:
        """Combine analysis from multiple symbols."""
        if len(all_analysis) == 1:
            return all_analysis[0]['analysis']
        
        # Multiple symbols - create combined analysis
        summary = "## 📊 Comparative Stock Analysis\n\n"
        summary += f"Analyzing {len(all_analysis)} stock(s): {', '.join([a['symbol'] for a in all_analysis])}\n\n"
        
        summary += "### 📈 Quick Overview:\n\n"
        for analysis in all_analysis:
            stats = analysis['statistics']
            summary += f"**{analysis['symbol']}**:\n"
            summary += f"- 📁 {analysis['files_found']} data file(s) | 📊 {analysis['data_points']:,} data points\n"
            summary += f"- 💰 Price: ${stats.get('min_price', 0):.2f} - ${stats.get('max_price', 0):.2f}\n"
            summary += f"- 📍 Current: ${stats.get('current_price', 0):.2f} ({stats.get('price_change_pct', 0):+.2f}%)\n"
            summary += f"- 📉 Volatility: ${stats.get('volatility', 0):.2f}\n\n"
        
        # Use LLM to create comparative analysis
        prompt = f"""User asked: "{user_input}"

Here are the analysis results for multiple stocks:
{summary}

Provide a well-formatted comparative analysis with:

**Comparative Overview:**
[Compare the stocks side-by-side]

**Performance Comparison:**
[Which performed better/worse and why]

**Risk Assessment:**
[Compare volatility and risk levels]

**Key Differences:**
[Highlight notable differences between the stocks]

**Overall Insights:**
[Provide actionable insights comparing these stocks]

Format with clear section headers using **bold** and bullet points. Be specific with numbers."""
        
        combined = self._call_llm(prompt)
        return f"{summary}\n---\n\n{combined}" if combined else summary
    
    def _analyze_downloaded_data(self, symbols: List[str], user_input: str) -> Optional[Dict]:
        """Analyze downloaded data from database (Phase 2) or CSV files (fallback)."""
        all_analysis = []
        
        for symbol in symbols:
            # Find data files (may return empty if using database)
            data_files = self._find_data_files(symbol)
            
            # Load the data (from database if USE_DATABASE_READS, else CSV)
            df = self._load_data_files(data_files, symbol=symbol)
            
            if df.empty:
                continue
            
            # Perform statistical analysis
            stats = self._calculate_statistics(df, symbol)
            
            # Generate insights using LLM
            analysis_text = self._generate_data_analysis(df, stats, symbol, user_input)
            
            all_analysis.append({
                'symbol': symbol,
                'files_found': len(data_files),
                'data_points': len(df),
                'statistics': stats,
                'analysis': analysis_text
            })
        
        if not all_analysis:
            return None
        
        # Combine analysis for all symbols
        combined_response = self._combine_analysis(all_analysis, user_input)
        
        return {
            "type": "stock_analysis",
            "response": combined_response,
            "data": {
                "symbols_analyzed": [a['symbol'] for a in all_analysis],
                "analysis_details": all_analysis
            },
            "success": True
        }
    
    def get_context(self) -> List[Dict]:
        """Get current conversation context."""
        return self.conversation_context.copy()
    
    def add_to_context(self, user_input: str, bot_response: str, request_type: str):
        """Add entry to conversation context."""
        entry = {
            'user_input': user_input,
            'bot_response': bot_response,
            'request_type': request_type,
            'timestamp': datetime.now().isoformat()
        }
        self.conversation_context.append(entry)
        if len(self.conversation_context) > self.max_context_length:
            self.conversation_context.pop(0)
    
    # ==================== Session Memory Methods ====================
    
    def get_memory(self) -> 'SessionMemory':
        """Get the session memory instance."""
        return self.memory
    
    def get_memory_context(self) -> str:
        """Get formatted memory context for LLM prompts."""
        return self.memory.get_context_prompt()
    
    def get_memory_stats(self) -> Dict:
        """Get session memory statistics."""
        return self.memory.get_stats()
    
    def get_remembered_stocks(self) -> List[str]:
        """Get list of stocks mentioned in this session."""
        return self.memory.get_mentioned_stocks()
    
    def clear_memory(self):
        """Clear session memory (call on session end)."""
        self.memory.clear()
        self.conversation_context = []

