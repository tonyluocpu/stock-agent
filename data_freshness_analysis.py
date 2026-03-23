#!/usr/bin/env python3
"""
Data Freshness Analysis for Stock Screening
===========================================

Analyzes how fresh the data is and update requirements.
"""

import yfinance as yf
import requests
from datetime import datetime, timedelta
import json

def analyze_data_freshness():
    """Analyze freshness of different data sources."""
    
    print("=" * 70)
    print("Data Freshness Analysis for Stock Screening")
    print("=" * 70)
    print()
    
    # Test with a real stock
    test_symbol = "AAPL"
    ticker = yf.Ticker(test_symbol)
    
    print("1. YAHOO FINANCE DATA FRESHNESS")
    print("-" * 70)
    
    try:
        # Get current stock info
        info = ticker.info
        
        # Check last update times
        print(f"Testing with: {test_symbol}")
        print()
        
        # Price data (most critical)
        hist = ticker.history(period="1d")
        if not hist.empty:
            last_price_date = hist.index[-1].date()
            today = datetime.now().date()
            days_old = (today - last_price_date).days
            
            print("Price Data:")
            print(f"   Last price date: {last_price_date}")
            print(f"   Today: {today}")
            print(f"   Age: {days_old} day(s)")
            print(f"   ✅ {'FRESH' if days_old <= 1 else 'STALE'}")
            print()
        
        # Financial metrics
        print("Financial Metrics (from yfinance.info):")
        metrics = {
            'marketCap': info.get('marketCap', 'N/A'),
            'trailingPE': info.get('trailingPE', 'N/A'),
            'priceToBook': info.get('priceToBook', 'N/A'),
            'sharesOutstanding': info.get('sharesOutstanding', 'N/A'),
            'totalDebt': info.get('totalDebt', 'N/A'),
            'totalCash': info.get('totalCash', 'N/A'),
        }
        
        for key, value in metrics.items():
            if value != 'N/A':
                print(f"   {key}: {value}")
        
        # Check when financials were last updated
        print()
        print("Financial Statements Update Frequency:")
        print("   Income Statement: Updated quarterly (every 3 months)")
        print("   Balance Sheet: Updated quarterly (every 3 months)")
        print("   Cash Flow: Updated quarterly (every 3 months)")
        print("   ⚠️  Financial statements are NOT daily - quarterly only")
        print()
        
        # Real-time vs delayed data
        print("Data Update Frequency:")
        print("   Stock Prices: ✅ Real-time (updated during market hours)")
        print("   Market Cap: ✅ Real-time (calculated from price × shares)")
        print("   P/E Ratio: ✅ Real-time (calculated from price ÷ earnings)")
        print("   P/B Ratio: ⚠️  Semi-real-time (book value updated quarterly)")
        print("   Financial Statements: ❌ Quarterly only (3 months old)")
        print()
        
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("2. SEC EDGAR DATA FRESHNESS")
    print("-" * 70)
    print("   Company List: ✅ Updated daily")
    print("   Filing Data: ✅ Updated as companies file")
    print("   ⚠️  But we only use this for company list, not financials")
    print()
    
    print("3. DATA FRESHNESS BY METRIC")
    print("-" * 70)
    
    freshness_table = {
        "Stock Price": {
            "Update": "Real-time (during market hours)",
            "Age": "0-1 days",
            "Source": "yfinance",
            "Freshness": "✅ EXCELLENT"
        },
        "Market Cap": {
            "Update": "Real-time (price × shares)",
            "Age": "0-1 days",
            "Source": "yfinance",
            "Freshness": "✅ EXCELLENT"
        },
        "P/E Ratio": {
            "Update": "Real-time (price ÷ trailing EPS)",
            "Age": "0-1 days",
            "Source": "yfinance",
            "Freshness": "✅ EXCELLENT"
        },
        "P/B Ratio": {
            "Update": "Semi-real-time (book value quarterly)",
            "Age": "0-90 days",
            "Source": "yfinance",
            "Freshness": "⚠️  GOOD (book value lags)"
        },
        "Shares Outstanding": {
            "Update": "Updated quarterly",
            "Age": "0-90 days",
            "Source": "yfinance",
            "Freshness": "⚠️  GOOD"
        },
        "Debt Structure": {
            "Update": "Updated quarterly",
            "Age": "0-90 days",
            "Source": "yfinance financials",
            "Freshness": "⚠️  GOOD"
        },
        "Profit History": {
            "Update": "Updated quarterly",
            "Age": "0-90 days",
            "Source": "yfinance financials",
            "Freshness": "⚠️  GOOD"
        },
        "Intrinsic Value (DCF)": {
            "Update": "Depends on financials (quarterly)",
            "Age": "0-90 days",
            "Source": "Calculated from financials",
            "Freshness": "⚠️  GOOD"
        }
    }
    
    for metric, info in freshness_table.items():
        print(f"{metric}:")
        print(f"   Update: {info['Update']}")
        print(f"   Age: {info['Age']}")
        print(f"   Freshness: {info['Freshness']}")
        print()
    
    print("4. UPDATE REQUIREMENTS FOR YOUR CRITERIA")
    print("-" * 70)
    
    criteria_freshness = {
        "1. Market cap < 2B": {
            "Data": "Market Cap",
            "Update": "Daily (real-time)",
            "Freshness": "✅ EXCELLENT - Update daily"
        },
        "2. P/B < 1": {
            "Data": "P/B Ratio",
            "Update": "Daily (book value quarterly)",
            "Freshness": "✅ GOOD - Update daily, book value quarterly"
        },
        "3. P/E < 15": {
            "Data": "P/E Ratio",
            "Update": "Daily (real-time)",
            "Freshness": "✅ EXCELLENT - Update daily"
        },
        "4. Shares float < 1B": {
            "Data": "Shares Outstanding",
            "Update": "Quarterly",
            "Freshness": "⚠️  ACCEPTABLE - Update weekly/monthly"
        },
        "5. Debt < 50%": {
            "Data": "Debt Structure",
            "Update": "Quarterly",
            "Freshness": "⚠️  ACCEPTABLE - Update monthly"
        },
        "6. Profit decline < 10%": {
            "Data": "Profit History (5 years)",
            "Update": "Quarterly",
            "Freshness": "⚠️  ACCEPTABLE - Update quarterly"
        },
        "7. Intrinsic Value": {
            "Data": "DCF + Relative Valuation",
            "Update": "Depends on financials",
            "Freshness": "⚠️  ACCEPTABLE - Update monthly"
        }
    }
    
    for criterion, info in criteria_freshness.items():
        print(f"{criterion}:")
        print(f"   Data: {info['Data']}")
        print(f"   Update Frequency: {info['Update']}")
        print(f"   Recommendation: {info['Freshness']}")
        print()
    
    print("5. RECOMMENDED UPDATE STRATEGY")
    print("=" * 70)
    print()
    print("For 'few days' freshness requirement:")
    print()
    print("DAILY Updates (Critical):")
    print("   ✅ Stock prices")
    print("   ✅ Market cap")
    print("   ✅ P/E ratio")
    print("   ✅ Current stock price (for intrinsic value comparison)")
    print()
    print("WEEKLY Updates (Important):")
    print("   ✅ P/B ratio (recalculate with latest price)")
    print("   ✅ Shares outstanding (check for changes)")
    print()
    print("MONTHLY Updates (Acceptable):")
    print("   ⚠️  Debt structure")
    print("   ⚠️  Financial statements (if new filings)")
    print()
    print("QUARTERLY Updates (Required):")
    print("   ⚠️  Full financial statements")
    print("   ⚠️  Profit history")
    print()
    print("=" * 70)
    print("IMPLEMENTATION STRATEGY")
    print("=" * 70)
    print()
    print("To achieve 'few days' freshness:")
    print()
    print("1. Real-time Data Fetching:")
    print("   - Fetch stock prices DAILY before screening")
    print("   - Fetch market cap, P/E DAILY")
    print("   - Use yfinance (free, real-time)")
    print()
    print("2. Cached Data with Timestamps:")
    print("   - Cache financial statements with dates")
    print("   - Re-fetch if older than 30 days")
    print("   - Check for new filings")
    print()
    print("3. Update Schedule:")
    print("   - Daily: Prices, market cap, P/E (before each screening)")
    print("   - Weekly: P/B, shares outstanding")
    print("   - Monthly: Full financial refresh")
    print()
    print("4. Data Freshness Check:")
    print("   - Store last update timestamp for each stock")
    print("   - Auto-refresh stale data")
    print("   - Warn if data > 7 days old")
    print()
    
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    print()
    print("✅ YES, we can achieve 'few days' freshness!")
    print()
    print("Strategy:")
    print("   - Fetch real-time data (prices, market cap, P/E) DAILY")
    print("   - Use cached financials (updated monthly)")
    print("   - Re-fetch stale data automatically")
    print()
    print("Network Usage:")
    print("   - Daily screening: ~200 requests (2-5 MB)")
    print("   - Monthly refresh: ~10,499 requests (310 MB)")
    print()
    print("Storage:")
    print("   - Cache with timestamps: ~10-50 MB")
    print("   - Update as needed")
    print()


if __name__ == "__main__":
    analyze_data_freshness()




