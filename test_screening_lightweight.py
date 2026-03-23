#!/usr/bin/env python3
"""
Lightweight Screening Tests
===========================

Tests screening operations with small datasets to avoid overloading.
"""

import time
import sys
from datetime import datetime

print("=" * 70)
print("Lightweight Screening Tests")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test results
results = {"total": 0, "passed": 0, "failed": 0}

def test(name, func, *args, **kwargs):
    """Run a test."""
    results["total"] += 1
    print(f"[{results['total']}] {name}...", end=" ")
    
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        if result:
            results["passed"] += 1
            print(f"✅ ({elapsed:.2f}s)")
            return True
        else:
            results["failed"] += 1
            print(f"❌ ({elapsed:.2f}s)")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        results["failed"] += 1
        print(f"❌ ERROR: {str(e)[:50]} ({elapsed:.2f}s)")
        return False

# Test 1: Screening module structure
print("1. Screening Module Structure")
print("-" * 70)
try:
    from fifth_layer_screening import StockScreener, ValuationEngine
    
    screener = StockScreener()
    test("StockScreener initialized", lambda: screener is not None)
    test("Has criteria registry", lambda: len(screener.criteria_registry) >= 6)
    test("Has all 6 basic criteria", lambda: all(c in screener.criteria_registry for c in 
         ['market_cap', 'price_to_book', 'pe_ratio', 'shares_outstanding', 'debt_structure', 'profit_stability']))
    
except Exception as e:
    print(f"⚠️  Error: {e}")

# Test 2: Criteria checking (with mock data)
print("\n2. Criteria Checking (Mock Data)")
print("-" * 70)
try:
    from fifth_layer_screening import StockScreener
    screener = StockScreener()
    
    # Mock stock data that should pass all criteria
    mock_data_pass = {
        'market_cap': 1_500_000_000,  # < $2B ✅
        'price_to_book': 0.8,  # < 1.0 ✅
        'pe_ratio': 12,  # < 15 ✅
        'shares_outstanding': 500_000_000,  # < 1B ✅
        'total_debt': 400_000_000,
        'total_assets': 1_000_000_000,  # Debt ratio = 40% < 50% ✅
        'net_income_history': [100, 105, 110, 108, 112]  # Stable ✅
    }
    
    # Mock stock data that should fail
    mock_data_fail = {
        'market_cap': 5_000_000_000,  # > $2B ❌
        'price_to_book': 1.5,  # > 1.0 ❌
        'pe_ratio': 20,  # > 15 ❌
        'shares_outstanding': 2_000_000_000,  # > 1B ❌
    }
    
    # Test individual criteria
    passed, reason = screener._check_market_cap("TEST", mock_data_pass)
    test("Market cap check (pass)", lambda: passed == True)
    
    passed, reason = screener._check_market_cap("TEST", mock_data_fail)
    test("Market cap check (fail)", lambda: passed == False)
    
    passed, reason = screener._check_price_to_book("TEST", mock_data_pass)
    test("P/B ratio check (pass)", lambda: passed == True)
    
    passed, reason = screener._check_pe_ratio("TEST", mock_data_pass)
    test("P/E ratio check (pass)", lambda: passed == True)
    
    passed, reason = screener._check_debt_structure("TEST", mock_data_pass)
    test("Debt structure check (pass)", lambda: passed == True)
    
except Exception as e:
    print(f"⚠️  Error: {e}")

# Test 3: Valuation engine (structure only)
print("\n3. Valuation Engine Structure")
print("-" * 70)
try:
    from fifth_layer_screening import ValuationEngine
    valuator = ValuationEngine()
    
    test("ValuationEngine initialized", lambda: valuator is not None)
    test("Has DCF method", lambda: hasattr(valuator, '_calculate_dcf'))
    test("Has relative valuation method", lambda: hasattr(valuator, '_calculate_relative_valuation'))
    test("Has main calculation method", lambda: hasattr(valuator, 'calculate_intrinsic_value'))
    
except Exception as e:
    print(f"⚠️  Error: {e}")

# Test 4: Sector database (check structure, don't build)
print("\n4. Sector Database Structure")
print("-" * 70)
try:
    from sector_database import SectorDatabaseBuilder
    builder = SectorDatabaseBuilder()
    
    test("SectorDatabaseBuilder initialized", lambda: builder is not None)
    test("Has build method", lambda: hasattr(builder, 'build_database'))
    test("Has get_sector_stocks method", lambda: hasattr(builder, 'get_sector_stocks'))
    test("Has needs_update method", lambda: hasattr(builder, 'needs_update'))
    test("Has 11 sectors defined", lambda: len(builder.sectors) == 11)
    
except Exception as e:
    print(f"⚠️  Error: {e}")

# Test 5: Data fetching (single stock, lightweight)
print("\n5. Data Fetching (Single Stock Test)")
print("-" * 70)
try:
    from fifth_layer_screening import StockScreener
    screener = StockScreener()
    
    # Test fetching data for one well-known stock (should be fast with cache)
    print("   Fetching data for AAPL (test)...", end=" ")
    start = time.time()
    data = screener._get_stock_data("AAPL")
    elapsed = time.time() - start
    
    if data:
        test("Fetch AAPL data", lambda: data.get('symbol') == 'AAPL')
        test("Has market cap", lambda: data.get('market_cap') is not None)
        test("Has P/E ratio", lambda: data.get('pe_ratio') is not None)
        print(f"   ✅ Data fetched in {elapsed:.2f}s")
    else:
        print("   ⚠️  No data (may need internet connection)")
        
except Exception as e:
    print(f"⚠️  Error: {e}")

# Test 6: Service integration
print("\n6. Service Integration")
print("-" * 70)
try:
    from stock_agent_service import StockAgentService
    service = StockAgentService()
    
    # Test that screening handler exists
    test("Has screening handler", lambda: hasattr(service, '_handle_stock_screening'))
    test("Has sector extractor", lambda: hasattr(service, '_extract_sector'))
    
    # Test sector extraction
    sector = service._extract_sector("screen technology sector")
    test("Extract sector from request", lambda: sector == "Technology")
    
except Exception as e:
    print(f"⚠️  Error: {e}")

# Summary
print("\n" + "=" * 70)
print("Screening Test Summary")
print("=" * 70)
print(f"Total Tests: {results['total']}")
print(f"✅ Passed: {results['passed']}")
print(f"❌ Failed: {results['failed']}")
if results['total'] > 0:
    print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
print()

if results['passed'] / results['total'] >= 0.8 if results['total'] > 0 else False:
    print("✅ Screening system is working!")
else:
    print("⚠️  Some screening tests failed.")

print("=" * 70)
print()
print("Note: Full screening tests with real stocks would take longer.")
print("These tests verify the structure and basic functionality.")




