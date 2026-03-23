#!/usr/bin/env python3
"""
Natural Language Database Testing
==================================

Test Phase 1 database implementation with REAL natural language queries,
including typos, mistakes, and conversational language.
"""

import sys
import time
from pathlib import Path

try:
    from stock_agent_service import StockAgentService
    from database import get_database
    from config import DATA_DIRECTORY
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


def test_natural_language_queries():
    """Test with natural language queries including mistakes."""
    
    print("=" * 70)
    print("NATURAL LANGUAGE DATABASE TEST - Phase 1")
    print("=" * 70)
    print()
    print("Testing with REAL user queries (typos, mistakes, conversational)")
    print()
    
    service = StockAgentService()
    db = get_database()
    
    # Track what we're testing
    test_results = {
        'total_queries': 0,
        'successful': 0,
        'database_verified': 0,
        'csv_verified': 0,
        'errors': []
    }
    
    # ========== TEST CASES ==========
    test_cases = [
        # Basic queries with typos
        {
            'query': "can you get me apple stock data?",
            'description': 'Basic request with typo (apple vs AAPL)',
            'should_download': True,
            'expected_symbol': 'AAPL'
        },
        {
            'query': "show me tesla price please",
            'description': 'Simple request (tesla vs TSLA)',
            'should_download': False,  # Just checking price, not downloading
            'expected_symbol': 'TSLA'
        },
        {
            'query': "i want microsoft data from last year",
            'description': 'Natural language with time reference',
            'should_download': True,
            'expected_symbol': 'MSFT'
        },
        {
            'query': "give me nvda weekly data 2023",
            'description': 'Short natural language (nvda vs NVDA)',
            'should_download': True,
            'expected_symbol': 'NVDA'
        },
        {
            'query': "how is google performing?",
            'description': 'Conversational question (google vs GOOGL)',
            'should_download': False,
            'expected_symbol': 'GOOGL'
        },
        {
            'query': "can u download meta stock info?",
            'description': 'Very casual with abbreviation (can u, meta)',
            'should_download': True,
            'expected_symbol': 'META'
        },
        {
            'query': "what about amazon? whats their price?",
            'description': 'Very conversational with typos',
            'should_download': False,
            'expected_symbol': 'AMZN'
        },
        {
            'query': "i need apple and microsoft daily data from 2024",
            'description': 'Multiple stocks with natural language',
            'should_download': True,
            'expected_symbols': ['AAPL', 'MSFT']
        },
        {
            'query': "download tesla weekly closing prices 2023 and 2024",
            'description': 'Specific request with multiple years',
            'should_download': True,
            'expected_symbol': 'TSLA'
        },
        {
            'query': "tell me about the magnificent 7",
            'description': 'Group reference (magnificent 7)',
            'should_download': False,
            'expected_multiple': True
        },
    ]
    
    print(f"Running {len(test_cases)} natural language test cases...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print("-" * 70)
        print(f"Test {i}/{len(test_cases)}: {test_case['description']}")
        print(f"Query: \"{test_case['query']}\"")
        print()
        
        test_results['total_queries'] += 1
        
        try:
            # Process the natural language query
            response = service.process_request(test_case['query'])
            
            print(f"Response type: {response.get('type', 'unknown')}")
            print(f"Success: {response.get('success', False)}")
            
            if response.get('success'):
                test_results['successful'] += 1
                print("✅ Query processed successfully")
            else:
                print(f"⚠️  Query failed: {response.get('response', 'Unknown error')}")
                test_results['errors'].append({
                    'query': test_case['query'],
                    'error': response.get('response', 'Unknown error')
                })
            
            # If this should download data, check database
            if test_case.get('should_download'):
                expected_symbols = test_case.get('expected_symbols', [test_case.get('expected_symbol')])
                expected_symbols = [s for s in expected_symbols if s]  # Filter None
                
                if expected_symbols:
                    print()
                    print("Checking database for downloaded data...")
                    for symbol in expected_symbols:
                        # Check if stock exists in database
                        stock = db.get_stock(symbol)
                        if stock:
                            print(f"  ✅ {symbol} found in database")
                            test_results['database_verified'] += 1
                        else:
                            print(f"  ⚠️  {symbol} not found in database (may need to download)")
                        
                        # Check if prices exist in database
                        prices = db.get_prices(symbol, frequency='daily', data_type='closing')
                        if not prices.empty:
                            print(f"  ✅ {symbol} prices found in database ({len(prices)} records)")
                            test_results['database_verified'] += 1
                        else:
                            # Try other frequencies
                            for freq in ['weekly', 'monthly', 'yearly']:
                                prices = db.get_prices(symbol, frequency=freq, data_type='closing')
                                if not prices.empty:
                                    print(f"  ✅ {symbol} {freq} prices found ({len(prices)} records)")
                                    test_results['database_verified'] += 1
                                    break
            
            # Check CSV files (dual-write verification)
            if test_case.get('should_download'):
                expected_symbols = test_case.get('expected_symbols', [test_case.get('expected_symbol')])
                expected_symbols = [s for s in expected_symbols if s]
                
                for symbol in expected_symbols:
                    # Check if CSV files exist (dual-write)
                    csv_dir = DATA_DIRECTORY / "daily" / "closing" / symbol
                    if csv_dir.exists():
                        csv_files = list(csv_dir.glob("*.csv"))
                        if csv_files:
                            print(f"  ✅ {symbol} CSV files found ({len(csv_files)} files)")
                            test_results['csv_verified'] += 1
            
            print()
            time.sleep(0.5)  # Small delay between tests
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            test_results['errors'].append({
                'query': test_case['query'],
                'error': str(e)
            })
            print()
    
    # ========== SUMMARY ==========
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    print(f"Total queries: {test_results['total_queries']}")
    print(f"Successful: {test_results['successful']} ({test_results['successful']*100/test_results['total_queries']:.1f}%)")
    print(f"Database verifications: {test_results['database_verified']}")
    print(f"CSV verifications: {test_results['csv_verified']}")
    print()
    
    if test_results['errors']:
        print("Errors encountered:")
        for error in test_results['errors']:
            print(f"  • \"{error['query']}\": {error['error']}")
        print()
    
    # Database statistics
    print("Database Statistics:")
    stats = db.get_stats()
    print(f"  Total stocks: {stats['total_stocks']}")
    print(f"  Total price records: {stats['total_price_records']:,}")
    print(f"  Database size: {stats['database_size_mb']:.2f} MB")
    print()
    
    # Verify Phase 1 (dual-write)
    print("Phase 1 Verification:")
    if test_results['database_verified'] > 0 and test_results['csv_verified'] > 0:
        print("  ✅ Dual-write working (data in both database AND CSV)")
    elif test_results['database_verified'] > 0:
        print("  ⚠️  Database write working, but CSV verification limited")
    else:
        print("  ❌ No database writes verified")
    print()
    
    print("=" * 70)
    print("NATURAL LANGUAGE TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_natural_language_queries()


