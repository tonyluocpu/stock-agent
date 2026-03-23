#!/usr/bin/env python3
"""Quick script to check background screening progress."""

import json
from pathlib import Path
from datetime import datetime

try:
    from config import DATA_DIRECTORY
except ImportError:
    DATA_DIRECTORY = Path("data")

results_file = DATA_DIRECTORY / "screening" / "weekly_screening_results.json"

print("=" * 70)
print("BACKGROUND SCREENING PROGRESS")
print("=" * 70)
print()

if results_file.exists():
    with open(results_file, 'r') as f:
        data = json.load(f)
    
    week_start = data.get('week_start', 'Unknown')
    sectors = data.get('sectors', {})
    
    print(f"Week started: {week_start}")
    print()
    print("Sector Progress:")
    print("-" * 70)
    
    sectors_list = [
        "Technology", "Healthcare", "Financials", "Consumer Discretionary",
        "Communication Services", "Industrials", "Consumer Staples",
        "Energy", "Utilities", "Real Estate", "Materials"
    ]
    
    completed = 0
    total_stocks = 0
    
    for sector in sectors_list:
        if sector in sectors:
            sector_data = sectors[sector]
            stocks_found = sector_data.get('stocks_found', 0)
            screened_at = sector_data.get('screened_at', 'Not screened')
            
            if stocks_found > 0:
                print(f"✅ {sector:25} {stocks_found:2} stocks - {screened_at}")
                completed += 1
                total_stocks += stocks_found
            elif 'error' in sector_data:
                print(f"❌ {sector:25} ERROR - {sector_data.get('error', 'Unknown')[:40]}")
            else:
                print(f"⚪ {sector:25} 0 stocks - {screened_at}")
        else:
            print(f"⏳ {sector:25} Not started yet")
    
    print()
    print("-" * 70)
    print(f"Completed: {completed}/11 sectors")
    print(f"Total stocks found: {total_stocks}")
    print()
    
    if completed == 11:
        print("✅ ALL SECTORS COMPLETE!")
    else:
        print(f"⏳ Still processing... ({11-completed} sectors remaining)")
else:
    print("⏳ Screening not started yet or database building...")
    print("   Check log: tail -f /tmp/background_screening.log")

print()




