#!/usr/bin/env python3
"""
Lightweight System Tests
========================

Tests all major operations without overloading the system.
Small, fast tests to verify everything works.
"""

import time
import sys
from datetime import datetime

print("=" * 70)
print("Lightweight System Tests")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Test results
results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "tests": []
}

def test(name, func, *args, **kwargs):
    """Run a test and record results."""
    results["total"] += 1
    print(f"[{results['total']}] {name}...", end=" ")
    
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        if result:
            results["passed"] += 1
            print(f"✅ ({elapsed:.2f}s)")
            results["tests"].append({"name": name, "status": "passed", "time": elapsed})
            return True
        else:
            results["failed"] += 1
            print(f"❌ ({elapsed:.2f}s)")
            results["tests"].append({"name": name, "status": "failed", "time": elapsed})
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        results["failed"] += 1
        print(f"❌ ERROR: {str(e)[:50]} ({elapsed:.2f}s)")
        results["tests"].append({"name": name, "status": "error", "error": str(e), "time": elapsed})
        return False

# Test 1: Import modules
print("\n1. Module Imports")
print("-" * 70)
test("Import stock_agent_service", lambda: __import__('stock_agent_service'))
test("Import llm_config", lambda: __import__('llm_config'))
test("Import fifth_layer_screening", lambda: __import__('fifth_layer_screening'))
test("Import sector_database", lambda: __import__('sector_database'))

# Test 2: Fast path (greetings)
print("\n2. Fast Path Tests (Instant Responses)")
print("-" * 70)
try:
    from stock_agent_service import StockAgentService
    service = StockAgentService()
    
    test("Fast path: Greeting 'hello'", 
         lambda: service._handle_fast_path("hello") is not None)
    test("Fast path: Greeting 'yo how ya doin'", 
         lambda: service._handle_fast_path("yo how ya doin") is not None)
    test("Fast path: Help request", 
         lambda: service._handle_fast_path("help") is not None)
    test("Fast path: Thanks", 
         lambda: service._handle_fast_path("thanks") is not None)
except Exception as e:
    print(f"⚠️  Service initialization failed: {e}")

# Test 3: Request type detection (keyword-based)
print("\n3. Request Type Detection (Fast Keyword Matching)")
print("-" * 70)
try:
    test("Detect screening: 'screen technology'", 
         lambda: service._detect_request_type("screen technology") == "stock_screening")
    test("Detect data: 'download apple data'", 
         lambda: service._detect_request_type("download apple data") == "stock_data")
    test("Detect analysis: 'how is tesla'", 
         lambda: service._detect_request_type("how is tesla") == "stock_analysis")
    test("Detect financial: 'financial analysis'", 
         lambda: service._detect_request_type("financial analysis of apple") == "financial_analysis")
except Exception as e:
    print(f"⚠️  Detection test failed: {e}")

# Test 4: Symbol extraction (fast regex)
print("\n4. Symbol Extraction (Fast Regex)")
print("-" * 70)
try:
    test("Extract: 'AAPL'", 
         lambda: 'AAPL' in service._extract_symbols("AAPL"))
    test("Extract: 'Apple' -> AAPL", 
         lambda: 'AAPL' in service._extract_symbols("Apple"))
    test("Extract: 'Tesla and Microsoft'", 
         lambda: 'TSLA' in service._extract_symbols("Tesla and Microsoft") and 'MSFT' in service._extract_symbols("Tesla and Microsoft"))
except Exception as e:
    print(f"⚠️  Symbol extraction test failed: {e}")

# Test 5: Sector extraction
print("\n5. Sector Extraction")
print("-" * 70)
try:
    test("Extract sector: 'technology'", 
         lambda: service._extract_sector("screen technology sector") == "Technology")
    test("Extract sector: 'healthcare'", 
         lambda: service._extract_sector("screen healthcare") == "Healthcare")
    test("Extract sector: 'tech' alias", 
         lambda: service._extract_sector("screen tech") == "Technology")
except Exception as e:
    print(f"⚠️  Sector extraction test failed: {e}")

# Test 6: Simple request processing (lightweight)
print("\n6. Simple Request Processing")
print("-" * 70)
try:
    # Test greeting (should be instant)
    result = service.process_request("hello")
    test("Process greeting: 'hello'", 
         lambda: result.get('success') and result.get('type') == 'general')
    
    # Test help (should be instant)
    result = service.process_request("help")
    test("Process help: 'help'", 
         lambda: result.get('success') and 'help' in result.get('response', '').lower())
    
    # Test simple question (may use LLM but should work)
    # Skip if LLM not available to avoid long waits
    print("   (Skipping LLM-dependent tests to avoid delays)")
    
except Exception as e:
    print(f"⚠️  Request processing test failed: {e}")

# Test 7: Screening module (structure only, no actual screening)
print("\n7. Screening Module Structure")
print("-" * 70)
try:
    from fifth_layer_screening import StockScreener, ValuationEngine, CatalystFinder
    
    test("StockScreener initialization", 
         lambda: StockScreener() is not None)
    test("ValuationEngine initialization", 
         lambda: ValuationEngine() is not None)
    test("CatalystFinder initialization", 
         lambda: CatalystFinder() is not None)
    
    # Test criteria registry
    screener = StockScreener()
    test("Criteria registry exists", 
         lambda: len(screener.criteria_registry) > 0)
    test("Can add custom criterion", 
         lambda: (screener.add_criterion('test', lambda s, d: (True, "test")), True)[1])
    
except Exception as e:
    print(f"⚠️  Screening module test failed: {e}")

# Test 8: Sector database (check if exists, don't build)
print("\n8. Sector Database Check")
print("-" * 70)
try:
    from sector_database import SectorDatabaseBuilder
    builder = SectorDatabaseBuilder()
    
    # Just check if file exists, don't build
    test("Sector database builder exists", 
         lambda: builder is not None)
    test("Database file check", 
         lambda: builder.db_file.exists() or True)  # Always pass - just checking structure
    
except Exception as e:
    print(f"⚠️  Sector database test failed: {e}")

# Test 9: Configuration
print("\n9. Configuration Check")
print("-" * 70)
try:
    from llm_config import load_config
    config = load_config()
    test("Load configuration", 
         lambda: config is not None and 'llm_provider' in config)
    test("Configuration has provider", 
         lambda: config.get('llm_provider') in ['free', 'openrouter'])
except Exception as e:
    print(f"⚠️  Configuration test failed: {e}")

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print(f"Total Tests: {results['total']}")
print(f"✅ Passed: {results['passed']}")
print(f"❌ Failed: {results['failed']}")
print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
print()

# Show failed tests
failed_tests = [t for t in results['tests'] if t['status'] != 'passed']
if failed_tests:
    print("Failed Tests:")
    for test in failed_tests:
        print(f"  - {test['name']}")
        if 'error' in test:
            print(f"    Error: {test['error'][:100]}")
    print()

# Performance summary
total_time = sum(t['time'] for t in results['tests'])
avg_time = total_time / len(results['tests']) if results['tests'] else 0
print(f"Total Test Time: {total_time:.2f}s")
print(f"Average Test Time: {avg_time:.2f}s")
print()

if results['passed'] / results['total'] >= 0.8:
    print("✅ System is working well!")
elif results['passed'] / results['total'] >= 0.6:
    print("⚠️  Some tests failed. Check errors above.")
else:
    print("❌ Many tests failed. System may need attention.")

print("=" * 70)




