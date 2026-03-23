#!/usr/bin/env python3
"""
Test All Sectors Screening
===========================
Tests screening for all available sectors to find which ones have matches.
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fifth_layer_screening import FifthLayerScreening
from llm_config import load_config, OpenRouterClientDirect

def test_all_sectors():
    """Test screening for all sectors."""
    print("="*70)
    print("🧪 Testing ALL Sectors with Relaxed Criteria")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # All GICS sectors
    all_sectors = [
        "Technology",
        "Healthcare", 
        "Financials",
        "Consumer Discretionary",
        "Communication Services",
        "Industrials",
        "Consumer Staples",
        "Energy",
        "Utilities",
        "Real Estate",
        "Materials"
    ]
    
    # Get LLM client (OpenRouter for speed)
    config = load_config()
    if config.get("openrouter_api_key"):
        llm_client = OpenRouterClientDirect(
            api_key=config["openrouter_api_key"],
            model=config.get("openrouter_model", "anthropic/claude-3.5-sonnet")
        )
        print("✅ Using OpenRouter API (Claude 3.5 Sonnet)")
    else:
        from llm_config import get_llm_client
        llm_client = get_llm_client()
        print("✅ Using local LLM")
    
    print()
    
    # Initialize screening system
    screening = FifthLayerScreening(llm_client=llm_client)
    
    # Check which sectors have stocks
    print("Checking sector database...")
    from fifth_layer_screening import StockScreener
    screener = StockScreener()
    
    sectors_with_stocks = {}
    for sector in all_sectors:
        stocks = screener.get_sector_stocks(sector)
        sectors_with_stocks[sector] = len(stocks)
        if stocks:
            print(f"  {sector}: {len(stocks)} stocks")
    
    print()
    print("="*70)
    print("Starting Screening Tests")
    print("="*70)
    print()
    
    results = []
    total_start_time = time.time()
    
    for sector in all_sectors:
        stock_count = sectors_with_stocks.get(sector, 0)
        if stock_count == 0:
            print(f"⏭️  Skipping {sector} (no stocks in database)")
            results.append({
                "sector": sector,
                "success": True,
                "stocks_found": 0,
                "time_seconds": 0,
                "skipped": True,
                "reason": "No stocks in database"
            })
            continue
        
        print(f"\n{'='*70}")
        print(f"🔍 Testing: {sector} ({stock_count} stocks)")
        print(f"{'='*70}")
        start_time = time.time()
        
        try:
            # Run screening
            sector_results = screening.screen_sector(sector)
            elapsed_time = time.time() - start_time
            
            stocks_found = len(sector_results)
            
            print(f"\n✅ {sector}: {stocks_found} stocks found in {elapsed_time:.1f}s")
            
            if stocks_found > 0:
                print(f"\n🎯 MATCHES FOUND in {sector}!")
                for i, stock in enumerate(sector_results[:5], 1):  # Show top 5
                    symbol = stock.get('symbol', 'N/A')
                    underval = stock.get('undervaluation_pct', 0)
                    print(f"  {i}. {symbol}: {underval:.1f}% undervalued")
            
            results.append({
                "sector": sector,
                "success": True,
                "stocks_found": stocks_found,
                "time_seconds": elapsed_time,
                "results": sector_results,
                "skipped": False
            })
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"\n❌ {sector}: Error - {str(e)}")
            results.append({
                "sector": sector,
                "success": False,
                "stocks_found": 0,
                "time_seconds": elapsed_time,
                "error": str(e),
                "skipped": False
            })
    
    total_time = time.time() - total_start_time
    
    # Print summary
    print("\n" + "="*70)
    print("📊 COMPLETE TEST SUMMARY")
    print("="*70)
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print()
    
    # Summary by result
    sectors_with_matches = [r for r in results if r.get("stocks_found", 0) > 0]
    sectors_no_matches = [r for r in results if r.get("stocks_found", 0) == 0 and not r.get("skipped")]
    sectors_skipped = [r for r in results if r.get("skipped")]
    
    if sectors_with_matches:
        print("🎯 SECTORS WITH MATCHES:")
        print("-"*70)
        for result in sectors_with_matches:
            print(f"  ✅ {result['sector']}: {result['stocks_found']} stocks found ({result['time_seconds']:.1f}s)")
        print()
    
    if sectors_no_matches:
        print("📊 SECTORS TESTED (No Matches):")
        print("-"*70)
        for result in sectors_no_matches:
            print(f"  ⚪ {result['sector']}: 0 stocks ({result['time_seconds']:.1f}s)")
        print()
    
    if sectors_skipped:
        print("⏭️  SECTORS SKIPPED (No Stocks in Database):")
        print("-"*70)
        for result in sectors_skipped:
            print(f"  ⏭️  {result['sector']}: {result.get('reason', 'No stocks')}")
        print()
    
    # Overall stats
    total_stocks_found = sum(r.get("stocks_found", 0) for r in results)
    sectors_tested = len([r for r in results if not r.get("skipped")])
    
    print("="*70)
    print("📈 OVERALL STATISTICS")
    print("="*70)
    print(f"Total sectors tested: {sectors_tested}")
    print(f"Sectors with matches: {len(sectors_with_matches)}")
    print(f"Total stocks found: {total_stocks_found}")
    print(f"Average time per sector: {total_time/sectors_tested:.1f}s" if sectors_tested > 0 else "N/A")
    print()
    
    if sectors_with_matches:
        print("="*70)
        print("✅ SUCCESS! Found stocks in the following sectors:")
        print("="*70)
        for result in sectors_with_matches:
            print(f"\n{result['sector']} - {result['stocks_found']} stocks:")
            for stock in result.get('results', [])[:3]:
                symbol = stock.get('symbol', 'N/A')
                underval = stock.get('undervaluation_pct', 0)
                price = stock.get('current_price', 0)
                intrinsic = stock.get('intrinsic_value', 0)
                print(f"  • {symbol}: ${price:.2f} → ${intrinsic:.2f} ({underval:.1f}% undervalued)")
    else:
        print("="*70)
        print("ℹ️  No stocks found in any sector")
        print("="*70)
        print("This means:")
        print("  • The relaxed criteria are still filtering out stocks")
        print("  • Try even more lenient criteria if needed")
        print("  • Or the database needs more stocks")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    return results

if __name__ == "__main__":
    results = test_all_sectors()




