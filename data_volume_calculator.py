#!/usr/bin/env python3
"""
Calculate Total Data Volume Needed for Fifth Layer Screening
============================================================
"""

import requests
import json
import yfinance as yf
from pathlib import Path

def calculate_data_requirements():
    """Calculate all data requirements."""
    
    print("=" * 70)
    print("Data Volume Calculation for Fifth Layer Screening")
    print("=" * 70)
    print()
    
    # 1. SEC EDGAR Company List
    print("1. SEC EDGAR Company List")
    print("-" * 70)
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {'User-Agent': 'Stock Agent (test@example.com)'}
        response = requests.get(url, headers=headers, timeout=10)
        
        sec_size_kb = len(response.content) / 1024
        data = response.json()
        num_companies = len(data)
        
        print(f"   File size: {sec_size_kb:.1f} KB")
        print(f"   Companies: {num_companies:,}")
        print(f"   ✅ Already downloaded in feasibility test")
    except Exception as e:
        print(f"   Error: {e}")
        sec_size_kb = 0
        num_companies = 0
    
    print()
    
    # 2. Sector Database (with sector info)
    print("2. Sector Database (SEC + yfinance sector info)")
    print("-" * 70)
    # For each company, we need to get sector from yfinance
    # Estimated: ~100 bytes per company (ticker + sector)
    sector_db_size_kb = (num_companies * 100) / 1024
    print(f"   Estimated size: {sector_db_size_kb:.1f} KB")
    print(f"   (Ticker + Sector info per company)")
    print()
    
    # 3. Financial Data for Screening (per stock)
    print("3. Financial Data for Screening")
    print("-" * 70)
    print("   For each stock, we need:")
    print("   - Basic info (market cap, P/E, P/B, etc.): ~2 KB")
    print("   - Financial statements (if screening): ~10-50 KB per stock")
    print()
    
    # Calculate for different scenarios
    scenarios = {
        "Per Sector Screening (50-300 stocks)": {
            "stocks": 200,  # Average
            "basic_info": 2,  # KB per stock
            "full_financials": 30  # KB per stock (if needed)
        },
        "Full Database (10,499 stocks)": {
            "stocks": num_companies,
            "basic_info": 2,
            "full_financials": 30
        }
    }
    
    for scenario_name, scenario in scenarios.items():
        print(f"   {scenario_name}:")
        stocks = scenario["stocks"]
        basic_mb = (stocks * scenario["basic_info"]) / 1024
        full_mb = (stocks * scenario["full_financials"]) / 1024
        
        print(f"     Basic info only: {basic_mb:.1f} MB")
        print(f"     Full financials: {full_mb:.1f} MB")
        print()
    
    # 4. Model Data (already downloaded)
    print("4. LLM Model (Already Downloaded)")
    print("-" * 70)
    model_size_gb = 7.1
    print(f"   Model size: {model_size_gb} GB")
    print(f"   ✅ Already downloaded")
    print()
    
    # 5. Cache Files
    print("5. Cache Files")
    print("-" * 70)
    cache_estimates = {
        "Sector database JSON": f"{sector_db_size_kb:.1f} KB",
        "Screening results (per run)": "~100-500 KB",
        "Financial data cache (optional)": "~10-50 MB per sector"
    }
    
    for item, size in cache_estimates.items():
        print(f"   {item}: {size}")
    print()
    
    # Total Summary
    print("=" * 70)
    print("TOTAL DATA VOLUME SUMMARY")
    print("=" * 70)
    print()
    
    # Minimum (just SEC list + sector info)
    min_total_kb = sec_size_kb + sector_db_size_kb
    print(f"MINIMUM (Essential Data):")
    print(f"   SEC company list: {sec_size_kb:.1f} KB")
    print(f"   Sector database: {sector_db_size_kb:.1f} KB")
    print(f"   Total: {min_total_kb:.1f} KB ({min_total_kb/1024:.2f} MB)")
    print()
    
    # Typical (one sector screening)
    typical_mb = min_total_kb/1024 + (200 * 2)/1024  # Basic info for 200 stocks
    print(f"TYPICAL (One Sector Screening):")
    print(f"   Essential data: {min_total_kb/1024:.2f} MB")
    print(f"   Basic info (200 stocks): {(200 * 2)/1024:.2f} MB")
    print(f"   Total: {typical_mb:.2f} MB")
    print()
    
    # Maximum (full database with financials)
    max_total_mb = min_total_kb/1024 + (num_companies * 30)/1024
    print(f"MAXIMUM (Full Database with Financials):")
    print(f"   Essential data: {min_total_kb/1024:.2f} MB")
    print(f"   Full financials ({num_companies:,} stocks): {(num_companies * 30)/1024:.1f} MB")
    print(f"   Total: {max_total_mb:.1f} MB ({max_total_mb/1024:.2f} GB)")
    print()
    
    # With Model
    print(f"WITH LLM MODEL:")
    print(f"   Model: {model_size_gb} GB (already downloaded)")
    print(f"   Data: {typical_mb:.2f} MB (typical usage)")
    print(f"   Total: {model_size_gb + typical_mb/1024:.2f} GB")
    print()
    
    # Network Transfer Estimates
    print("=" * 70)
    print("NETWORK TRANSFER ESTIMATES")
    print("=" * 70)
    print()
    print("Initial Setup (One-time):")
    print(f"   SEC company list: {sec_size_kb:.1f} KB (~1 request)")
    print(f"   Sector info (10,499 companies): ~{num_companies * 0.1:.0f} requests")
    print(f"   Estimated time: 15-30 minutes (with rate limiting)")
    print()
    print("Per Sector Screening:")
    print(f"   Basic info (200 stocks): ~200 requests")
    print(f"   Estimated time: 2-5 minutes (with rate limiting)")
    print()
    
    # Storage Requirements
    print("=" * 70)
    print("STORAGE REQUIREMENTS")
    print("=" * 70)
    print()
    print(f"Minimum (cached data only): {min_total_kb/1024:.2f} MB")
    print(f"Typical (one sector cached): {typical_mb:.2f} MB")
    print(f"Full database cache: {max_total_mb:.1f} MB ({max_total_mb/1024:.2f} GB)")
    print(f"LLM Model: {model_size_gb} GB")
    print(f"Total (model + full cache): {model_size_gb + max_total_mb/1024:.2f} GB")
    print()
    
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print()
    print("✅ RECOMMENDED APPROACH:")
    print("   1. Download SEC list once: ~{:.1f} KB".format(sec_size_kb))
    print("   2. Build sector database: ~{:.1f} KB".format(sector_db_size_kb))
    print("   3. Cache locally, update monthly")
    print("   4. Fetch financial data on-demand during screening")
    print("   5. Don't cache all financials - fetch as needed")
    print()
    print("   Total storage needed: ~{:.2f} MB + {:.1f} GB (model)".format(
        min_total_kb/1024 + 10, model_size_gb))
    print("   Network usage per screening: ~2-5 MB")
    print()


if __name__ == "__main__":
    calculate_data_requirements()




