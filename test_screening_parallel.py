#!/usr/bin/env python3
"""
Parallel Stock Screening Test
=============================
Tests screening for 2 sectors in parallel to verify everything works.
"""

import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fifth_layer_screening import FifthLayerScreening
from llm_config import load_config, OpenRouterClientDirect

def test_sector_screening(sector_name, use_openrouter=True):
    """
    Test screening for a single sector.
    
    Args:
        sector_name: Name of the sector to screen
        use_openrouter: Whether to use OpenRouter API (faster)
    
    Returns:
        Dict with results and timing info
    """
    start_time = time.time()
    print(f"\n{'='*70}")
    print(f"🚀 Starting screening for: {sector_name}")
    print(f"{'='*70}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Using OpenRouter: {use_openrouter}")
    print()
    
    try:
        # Get LLM client
        if use_openrouter:
            config = load_config()
            if config.get("openrouter_api_key"):
                llm_client = OpenRouterClientDirect(
                    api_key=config["openrouter_api_key"],
                    model=config.get("openrouter_model", "anthropic/claude-3.5-sonnet")
                )
                print(f"✅ Using OpenRouter API (Claude 3.5 Sonnet)")
            else:
                print("⚠️ OpenRouter API key not found, using local LLM")
                from llm_config import get_llm_client
                llm_client = get_llm_client()
        else:
            from llm_config import get_llm_client
            llm_client = get_llm_client()
            print(f"✅ Using local LLM")
        
        # Initialize screening system
        screening = FifthLayerScreening(llm_client=llm_client)
        
        # Run screening
        print(f"📊 Running screening for {sector_name}...")
        results = screening.screen_sector(sector_name)
        
        elapsed_time = time.time() - start_time
        
        # Format results
        formatted_results = screening.format_results(results)
        
        print(f"\n{'='*70}")
        print(f"✅ Screening completed for: {sector_name}")
        print(f"{'='*70}")
        print(f"Time taken: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"Stocks found: {len(results)}")
        print()
        
        return {
            "sector": sector_name,
            "success": True,
            "results": results,
            "formatted_results": formatted_results,
            "time_seconds": elapsed_time,
            "stocks_found": len(results),
            "error": None
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"❌ Screening failed for: {sector_name}")
        print(f"{'='*70}")
        print(f"Error: {str(e)}")
        print(f"Time taken: {elapsed_time:.1f} seconds")
        print()
        
        import traceback
        traceback.print_exc()
        
        return {
            "sector": sector_name,
            "success": False,
            "results": [],
            "formatted_results": None,
            "time_seconds": elapsed_time,
            "stocks_found": 0,
            "error": str(e)
        }

def main():
    """Run parallel screening tests for 2 sectors."""
    print("="*70)
    print("🧪 Parallel Stock Screening Test")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 2 sectors: Utilities (smallest) and Materials (small-medium)
    test_sectors = ["Utilities", "Materials"]
    
    print(f"📋 Testing sectors: {', '.join(test_sectors)}")
    print(f"🔄 Running in parallel...")
    print()
    
    # Run in parallel
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both tasks
        future_to_sector = {
            executor.submit(test_sector_screening, sector, use_openrouter=True): sector 
            for sector in test_sectors
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_sector):
            sector = future_to_sector[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Exception for {sector}: {e}")
                results.append({
                    "sector": sector,
                    "success": False,
                    "error": str(e)
                })
    
    total_time = time.time() - start_time
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print()
    
    for result in results:
        status = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
        sector = result.get("sector", "Unknown")
        stocks = result.get("stocks_found", 0)
        time_taken = result.get("time_seconds", 0)
        error = result.get("error")
        
        print(f"{status} - {sector}")
        print(f"  Stocks found: {stocks}")
        print(f"  Time: {time_taken:.1f}s ({time_taken/60:.1f} min)")
        if error:
            print(f"  Error: {error}")
        print()
    
    # Check if all succeeded
    all_success = all(r.get("success", False) for r in results)
    
    if all_success:
        print("="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        print(f"Both sectors screened successfully in {total_time/60:.1f} minutes")
        print()
        
        # Show sample results
        for result in results:
            if result.get("stocks_found", 0) > 0:
                print(f"\n{result['sector']} - Top 3 stocks:")
                stocks = result.get("results", [])[:3]
                for i, stock in enumerate(stocks, 1):
                    symbol = stock.get('symbol', 'N/A')
                    underval = stock.get('undervaluation_pct', 0)
                    print(f"  {i}. {symbol}: {underval:.1f}% undervalued")
    else:
        print("="*70)
        print("❌ SOME TESTS FAILED")
        print("="*70)
        failed = [r for r in results if not r.get("success")]
        for result in failed:
            print(f"  - {result.get('sector')}: {result.get('error')}")
        sys.exit(1)
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

if __name__ == "__main__":
    main()




