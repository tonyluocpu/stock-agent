#!/usr/bin/env python3
"""
Test Database Functionality
============================

Quick test to verify database queries work correctly.
"""

import sys
from pathlib import Path

try:
    from database import StockDatabase
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


def test_database():
    """Test database queries."""
    print("=" * 70)
    print("DATABASE TEST")
    print("=" * 70)
    print()
    
    db = StockDatabase()
    
    # Test 1: Get database stats
    print("Test 1: Database Statistics")
    print("-" * 70)
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Test 2: Get a stock
    print("Test 2: Get Stock Info")
    print("-" * 70)
    stock = db.get_stock("AAPL")
    if stock:
        print(f"  Symbol: {stock.get('symbol')}")
        print(f"  Sector: {stock.get('sector')}")
        print(f"  Market Cap: {stock.get('market_cap')}")
        print(f"  P/E Ratio: {stock.get('pe_ratio')}")
    else:
        print("  No stock found (database may be empty)")
    print()
    
    # Test 3: Get prices
    print("Test 3: Get Price Data")
    print("-" * 70)
    prices_df = db.get_prices("AAPL", frequency="daily", data_type="closing")
    if not prices_df.empty:
        print(f"  Found {len(prices_df)} price records")
        print(f"  Date range: {prices_df['Date'].min()} to {prices_df['Date'].max()}")
        print(f"  Sample rows:")
        print(prices_df.head(3).to_string())
    else:
        print("  No price data found")
    print()
    
    # Test 4: Get screening results
    print("Test 4: Get Screening Results")
    print("-" * 70)
    results = db.get_screening_results()
    if results:
        print(f"  Found {len(results)} screening results")
        for result in results[:3]:
            print(f"  {result.get('symbol')}: Score {result.get('composite_score')}, Sector {result.get('sector')}")
    else:
        print("  No screening results found")
    print()
    
    # Test 5: Get stocks by sector
    print("Test 5: Get Stocks by Sector")
    print("-" * 70)
    tech_stocks = db.get_stocks_by_sector("Technology")
    if tech_stocks:
        print(f"  Found {len(tech_stocks)} Technology stocks")
        for stock in tech_stocks[:5]:
            print(f"    {stock.get('symbol')}: {stock.get('name', 'N/A')}")
    else:
        print("  No Technology stocks found")
    print()
    
    print("=" * 70)
    print("DATABASE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_database()

