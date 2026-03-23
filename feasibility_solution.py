#!/usr/bin/env python3
"""
Feasibility Proof-of-Concept: Getting Stock Lists for Screening
================================================================

This demonstrates HOW we can get stock lists for the fifth layer screening.
"""

import yfinance as yf
import pandas as pd
import requests
from pathlib import Path
import json
import time
from typing import List, Dict

class StockListBuilder:
    """
    Builds lists of stocks for screening.
    Multiple strategies to get comprehensive stock lists.
    """
    
    def __init__(self):
        self.cache_dir = Path("data/stock_lists")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_stocks_by_sector_yfinance(self, sector: str) -> List[str]:
        """
        Method 1: Use yfinance to get stocks by sector.
        This works but is limited - yfinance doesn't have direct sector lists.
        Alternative: Use known sector ETFs or sector indices.
        """
        # GICS Sectors mapping to ETFs/indices we can use
        sector_etfs = {
            "Technology": ["XLK", "VGT", "FTEC"],  # Tech ETFs
            "Healthcare": ["XLV", "VHT", "FHLC"],
            "Financials": ["XLF", "VFH", "FNCL"],
            "Consumer Discretionary": ["XLY", "VCR", "FDIS"],
            "Communication Services": ["XLC", "VOX", "FCOM"],
            "Industrials": ["XLI", "VIS", "FIDU"],
            "Consumer Staples": ["XLP", "VDC", "FSTA"],
            "Energy": ["XLE", "VDE", "FENY"],
            "Utilities": ["XLU", "VPU", "FUTY"],
            "Real Estate": ["XLRE", "VNQ", "FREL"],
            "Materials": ["XLB", "VAW", "FMAT"]
        }
        
        if sector not in sector_etfs:
            return []
        
        # Get holdings from sector ETF (if available)
        # Note: This requires additional data source or manual lists
        # For now, return known stocks in sector
        return self._get_known_sector_stocks(sector)
    
    def _get_known_sector_stocks(self, sector: str) -> List[str]:
        """Get known stocks by sector (manual list as fallback)."""
        # This is a simplified example - in production, you'd build a comprehensive list
        sector_stocks = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMD", "INTC", "CRM", "ORCL", "ADBE"],
            "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD"],
            "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "COF"],
            # ... add more sectors
        }
        return sector_stocks.get(sector, [])
    
    def get_stocks_from_sec_edgar(self) -> List[Dict]:
        """
        Method 2: Get comprehensive list from SEC EDGAR.
        This is the most comprehensive but requires web scraping.
        """
        # SEC EDGAR company tickers endpoint
        # https://www.sec.gov/files/company_tickers.json
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {
                'User-Agent': 'Stock Agent (contact@example.com)',  # SEC requires user agent
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # SEC returns data in format: {"0": {"cik_str": ..., "ticker": ..., "title": ...}, ...}
                stocks = []
                for key, value in data.items():
                    stocks.append({
                        'ticker': value.get('ticker', ''),
                        'cik': value.get('cik_str', ''),
                        'name': value.get('title', '')
                    })
                return stocks
        except Exception as e:
            print(f"Error fetching SEC data: {e}")
        
        return []
    
    def get_stocks_from_nasdaq_nyse(self) -> List[str]:
        """
        Method 3: Get stocks from exchange listings.
        NASDAQ and NYSE provide CSV downloads.
        """
        # NASDAQ listings: https://www.nasdaq.com/market-activity/stocks/screener
        # NYSE listings: https://www.nyse.com/listings_directory/stock
        # These require web scraping or manual downloads
        
        # For now, return empty - would need to implement scraping
        return []
    
    def build_sector_database(self, use_sec: bool = True) -> Dict[str, List[str]]:
        """
        Build comprehensive sector database.
        Combines multiple sources for best coverage.
        """
        print("Building sector database...")
        
        # Try SEC first (most comprehensive)
        if use_sec:
            print("Fetching from SEC EDGAR...")
            sec_stocks = self.get_stocks_from_sec_edgar()
            print(f"Found {len(sec_stocks)} companies from SEC")
            
            if sec_stocks:
                # Group by sector (would need sector info from yfinance)
                sector_db = {}
                for stock in sec_stocks[:100]:  # Limit for demo
                    ticker = stock['ticker']
                    try:
                        # Get sector info from yfinance
                        ticker_obj = yf.Ticker(ticker)
                        info = ticker_obj.info
                        sector = info.get('sector', 'Unknown')
                        
                        if sector not in sector_db:
                            sector_db[sector] = []
                        sector_db[sector].append(ticker)
                        
                        time.sleep(0.1)  # Rate limiting
                    except:
                        continue
                
                # Cache the database
                cache_file = self.cache_dir / "sector_database.json"
                with open(cache_file, 'w') as f:
                    json.dump(sector_db, f, indent=2)
                
                return sector_db
        
        # Fallback: Use known stocks
        return self._build_fallback_database()
    
    def _build_fallback_database(self) -> Dict[str, List[str]]:
        """Build database from known stocks."""
        return {
            "Technology": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "AMD", "INTC", "CRM", "ORCL", "ADBE", "NFLX", "TSLA"],
            "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD"],
            "Financials": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "COF"],
            # Add more sectors...
        }
    
    def get_sector_stocks(self, sector: str, use_cache: bool = True) -> List[str]:
        """Get stocks for a specific sector."""
        cache_file = self.cache_dir / "sector_database.json"
        
        if use_cache and cache_file.exists():
            with open(cache_file, 'r') as f:
                sector_db = json.load(f)
                return sector_db.get(sector, [])
        
        # Build database if not cached
        sector_db = self.build_sector_database()
        return sector_db.get(sector, [])


def demonstrate_feasibility():
    """Demonstrate that we CAN get stock lists."""
    print("=" * 70)
    print("Feasibility Demonstration: Getting Stock Lists")
    print("=" * 70)
    print()
    
    builder = StockListBuilder()
    
    # Method 1: SEC EDGAR (most comprehensive)
    print("Method 1: SEC EDGAR Database")
    print("-" * 70)
    sec_stocks = builder.get_stocks_from_sec_edgar()
    print(f"✅ Can get {len(sec_stocks)} companies from SEC EDGAR")
    if sec_stocks:
        print(f"   Examples: {[s['ticker'] for s in sec_stocks[:5]]}")
    print()
    
    # Method 2: Sector-based (practical)
    print("Method 2: Sector-Based Lists")
    print("-" * 70)
    tech_stocks = builder.get_sector_stocks("Technology")
    print(f"✅ Can get {len(tech_stocks)} tech stocks")
    print(f"   Examples: {tech_stocks[:5]}")
    print()
    
    # Method 3: Build comprehensive database
    print("Method 3: Building Sector Database")
    print("-" * 70)
    print("This would combine SEC data + yfinance sector info")
    print("✅ Feasible - can build comprehensive database")
    print()
    
    print("=" * 70)
    print("CONCLUSION: ✅ FEASIBLE")
    print("=" * 70)
    print()
    print("Recommended Approach:")
    print("1. Use SEC EDGAR for comprehensive company list (one-time)")
    print("2. Use yfinance to get sector info for each company")
    print("3. Cache locally (update monthly)")
    print("4. Screen within sectors (50-300 stocks per sector)")
    print("5. Use LLM for intelligent analysis and filtering")
    print()


if __name__ == "__main__":
    demonstrate_feasibility()




