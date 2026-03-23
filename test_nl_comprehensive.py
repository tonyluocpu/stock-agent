#!/usr/bin/env python3
"""
Comprehensive Natural Language Test with Many Mistakes
========================================================

Test Phase 1 database with REAL messy natural language queries.
"""

import sys
import time

try:
    from stock_agent_service import StockAgentService
    from database import get_database
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


def test_messy_natural_language():
    """Test with really messy natural language queries."""
    
    print("=" * 70)
    print("MESSY NATURAL LANGUAGE TEST - Phase 1 Database")
    print("=" * 70)
    print()
    print("Testing with REAL user typos, mistakes, and casual language")
    print()
    
    service = StockAgentService()
    db = get_database()
    
    # Really messy natural language queries
    messy_queries = [
        # Typos and mistakes
        ("apl stock data pls", "Typo: apl vs AAPL, casual: pls"),
        ("tehla price?", "Typo: tehla vs TSLA, casual question"),
        ("micrsoft weekly data", "Typo: micrsoft vs MSFT"),
        ("gogle stock info plz", "Typo: gogle vs GOOGL, casual: plz"),
        ("nvidia data from last yr", "Casual: nvidia vs NVDA, yr vs year"),
        ("amazon price whats it?", "Casual question, no punctuation"),
        ("apple and googl data 2024", "Multiple stocks, typo: googl"),
        ("tesla weekly closing prices pls", "Casual: pls"),
        ("microsoft daily data from 2023 to 2024", "Full date range"),
        ("how is nvda doing?", "Conversational question"),
        
        # Very casual language
        ("hey can u get me apple data?", "Very casual: hey can u"),
        ("whats tesla at?", "Casual: whats, at"),
        ("need msft data", "Very short, casual"),
        ("can i get google stock?", "Question format, casual"),
        ("download meta pls", "Very short, casual"),
        ("tell me about nvidia", "Conversational"),
        ("i want amazon stock data", "Natural request"),
        ("show tesla price", "Simple command"),
        ("get me apple weekly", "Casual: get me"),
        ("what about microsoft?", "Casual question"),
        
        # Mistakes and abbreviations
        ("appl stock", "Abbreviation: appl vs AAPL"),
        ("tsla price", "Lowercase: tsla"),
        ("MSFT daily", "Symbol without context"),
        ("GOOGL data", "Symbol without context"),
        ("NVDA weekly 2023", "Symbol with context"),
        ("META closing prices", "Symbol with type"),
        ("AMZN stock info", "Symbol with context"),
        ("AAPL and TSLA", "Multiple symbols"),
        ("magnificent seven", "Full words: seven vs 7"),
        ("mag 7 stocks", "Abbreviation: mag vs magnificent"),
        
        # Real user-like queries
        ("can you download apple stock data?", "Polite request"),
        ("i need tesla prices", "Natural request"),
        ("what is microsoft stock price?", "Question format"),
        ("download google data please", "Polite: please"),
        ("show me nvidia info", "Request: show me"),
        ("tell me tesla price", "Conversational: tell me"),
        ("get apple and microsoft data", "Multiple stocks"),
        ("how much is amazon stock?", "Question format"),
        ("what about meta stock?", "Casual question"),
        ("i want to download tesla data", "Natural request"),
    ]
    
    print(f"Running {len(messy_queries)} messy natural language queries...")
    print()
    
    successful = 0
    failed = 0
    errors = []
    
    for i, (query, description) in enumerate(messy_queries, 1):
        print("-" * 70)
        print(f"Test {i}/{len(messy_queries)}: {description}")
        print(f"Query: \"{query}\"")
        print()
        
        try:
            # Process the messy query
            response = service.process_request(query)
            
            success = response.get('success', False)
            response_type = response.get('type', 'unknown')
            
            if success:
                successful += 1
                print(f"✅ Success ({response_type})")
            else:
                failed += 1
                error_msg = response.get('response', 'Unknown error')
                print(f"❌ Failed: {error_msg[:100]}")
                errors.append((query, error_msg))
            
            print()
            time.sleep(0.3)  # Small delay
            
        except Exception as e:
            failed += 1
            error_msg = str(e)
            print(f"❌ ERROR: {error_msg[:100]}")
            errors.append((query, error_msg))
            print()
    
    # ========== SUMMARY ==========
    print("=" * 70)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)
    print()
    print(f"Total queries: {len(messy_queries)}")
    print(f"Successful: {successful} ({successful*100/len(messy_queries):.1f}%)")
    print(f"Failed: {failed} ({failed*100/len(messy_queries):.1f}%)")
    print()
    
    if errors:
        print(f"Failed queries ({len(errors)}):")
        for query, error in errors[:10]:  # Show first 10
            print(f"  • \"{query}\"")
            print(f"    Error: {error[:80]}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        print()
    
    # Database statistics
    print("Database Statistics:")
    stats = db.get_stats()
    print(f"  Total stocks: {stats['total_stocks']}")
    print(f"  Total price records: {stats['total_price_records']:,}")
    print(f"  Database size: {stats['database_size_mb']:.2f} MB")
    print()
    
    print("=" * 70)
    print("COMPREHENSIVE TEST COMPLETE")
    print("=" * 70)
    print()
    
    if successful >= len(messy_queries) * 0.8:
        print("✅ PASSED: Most queries successful (>80%)")
    elif successful >= len(messy_queries) * 0.6:
        print("⚠️  PARTIAL: Many queries successful (60-80%)")
    else:
        print("❌ FAILED: Too many queries failed (<60%)")


if __name__ == "__main__":
    test_messy_natural_language()


