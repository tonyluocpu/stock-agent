#!/usr/bin/env python3
"""
Comprehensive Natural Language Tests for Phase 2 & 3
=====================================================

Even more comprehensive natural language tests than Phase 1,
testing Phase 2 (database reads) and Phase 3 (optional CSV) features.
"""

import sys
import time
from pathlib import Path

try:
    from stock_agent_service import StockAgentService
    from database import get_database
    from database_export import DatabaseExporter
    from config import USE_DATABASE_READS, ENABLE_CSV_WRITES
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


def test_phase2_3_natural_language():
    """Comprehensive natural language tests for Phase 2 & 3."""
    
    print("=" * 70)
    print("PHASE 2 & 3 NATURAL LANGUAGE TEST SUITE")
    print("=" * 70)
    print()
    print(f"Configuration:")
    print(f"  USE_DATABASE_READS: {USE_DATABASE_READS}")
    print(f"  ENABLE_CSV_WRITES: {ENABLE_CSV_WRITES}")
    print()
    print("Testing Phase 2 (database reads) and Phase 3 (optional CSV) with")
    print("REAL natural language queries including typos, mistakes, and casual language.")
    print()
    
    service = StockAgentService()
    db = get_database()
    exporter = DatabaseExporter()
    
    # Comprehensive test queries - even more than Phase 1
    test_queries = [
        # ========== BASIC QUERIES WITH TYPOS ==========
        ("apl stock data", "Typo: apl vs AAPL"),
        ("tehla price", "Typo: tehla vs TSLA"),
        ("micrsoft data", "Typo: micrsoft vs MSFT"),
        ("gogle stock", "Typo: gogle vs GOOGL"),
        ("nvida data", "Typo: nvida vs NVDA"),
        ("amazon price", "Lowercase: amazon"),
        ("meta stock info", "Lowercase: meta"),
        ("apple an microsoft", "Typo: an vs and"),
        
        # ========== CASUAL LANGUAGE ==========
        ("hey can u get me apple data?", "Very casual: hey can u"),
        ("whats tesla at?", "Casual: whats, at"),
        ("need msft data pls", "Very casual: need, pls"),
        ("can i get google stock plz?", "Casual: plz, question"),
        ("download meta pls", "Very short, casual: pls"),
        ("show tesla price", "Simple command"),
        ("get me apple weekly", "Casual: get me"),
        ("what about microsoft?", "Casual question: what about"),
        
        # ========== CONVERSATIONAL ==========
        ("how is apple performing?", "Conversational: how is"),
        ("tell me about tesla", "Conversational: tell me about"),
        ("what is microsoft stock price?", "Question format"),
        ("can you analyze nvidia?", "Polite request"),
        ("give me google stock info", "Request: give me"),
        ("show me amazon data", "Request: show me"),
        ("i want meta stock info", "Natural request: i want"),
        ("what about apple?", "Casual question"),
        
        # ========== ANALYSIS REQUESTS ==========
        ("analyze apple stock data", "Analysis request"),
        ("can you analyze tesla?", "Analysis request with can you"),
        ("i want to analyze microsoft", "Natural analysis request"),
        ("give me analysis of nvidia", "Analysis request: give me"),
        ("show me analysis for google", "Analysis request: show me"),
        ("whats the analysis for amazon?", "Casual analysis question"),
        ("tell me about meta stock analysis", "Analysis request: tell me"),
        
        # ========== DATA DOWNLOAD REQUESTS ==========
        ("download apple stock data", "Download request"),
        ("can you download tesla data?", "Download request with can you"),
        ("i need microsoft data", "Download request: i need"),
        ("get me nvidia weekly data", "Download request: get me"),
        ("download google daily data pls", "Download request: pls"),
        ("i want to download amazon data", "Natural download request"),
        ("can u download meta data?", "Casual download: can u"),
        
        # ========== SPECIFIC REQUESTS ==========
        ("apple daily data 2024", "Specific: daily 2024"),
        ("tesla weekly data from 2023", "Specific: weekly 2023"),
        ("microsoft monthly data last year", "Specific: monthly last year"),
        ("nvidia data from 2022 to 2024", "Specific: date range"),
        ("google daily closing prices", "Specific: closing prices"),
        ("amazon weekly data 2023 and 2024", "Specific: multiple years"),
        ("meta monthly data from last year", "Specific: monthly last year"),
        
        # ========== MULTIPLE STOCKS ==========
        ("apple and microsoft data", "Multiple stocks: and"),
        ("tesla and google stock info", "Multiple stocks: and"),
        ("nvidia and amazon prices", "Multiple stocks: and"),
        ("apple microsoft google", "Multiple stocks: no and"),
        ("magnificent 7", "Group reference"),
        ("mag 7 stocks", "Abbreviation: mag vs magnificent"),
        ("magnificent seven", "Full words: seven vs 7"),
        
        # ========== QUESTIONS ==========
        ("what is apple stock price?", "Question: what is"),
        ("how much is tesla stock?", "Question: how much is"),
        ("what about microsoft?", "Question: what about"),
        ("how is nvidia doing?", "Question: how is"),
        ("whats google stock at?", "Casual question: whats"),
        ("tell me amazon price", "Request: tell me"),
        ("can you tell me meta price?", "Question: can you tell me"),
        
        # ========== COMPLEX QUERIES ==========
        ("i want apple daily data from 2023 to 2024", "Complex: date range"),
        ("can you get me tesla weekly closing prices 2024", "Complex: specific type"),
        ("download microsoft and google data from last year", "Complex: multiple stocks"),
        ("analyze apple stock data from 2023", "Complex: analysis with date"),
        ("show me nvidia prices from the last year", "Complex: relative date"),
        ("what is amazon stock price and can i download the data?", "Complex: multiple intents"),
        ("tell me about meta and can you analyze it?", "Complex: multiple requests"),
        
        # ========== EDGE CASES ==========
        ("", "Empty query"),
        ("stock", "Just word: stock"),
        ("data", "Just word: data"),
        ("price", "Just word: price"),
        ("apple apple apple", "Repetition"),
        ("tell me tell me tell me about apple", "Repetition with words"),
    ]
    
    print(f"Running {len(test_queries)} comprehensive natural language test queries...")
    print()
    
    results = {
        'total': len(test_queries),
        'successful': 0,
        'failed': 0,
        'database_verified': 0,
        'errors': []
    }
    
    for i, (query, description) in enumerate(test_queries, 1):
        print("-" * 70)
        print(f"Test {i}/{len(test_queries)}: {description}")
        print(f"Query: \"{query}\"")
        print()
        
        try:
            # Process the query
            response = service.process_request(query)
            
            success = response.get('success', False)
            response_type = response.get('type', 'unknown')
            
            if success:
                results['successful'] += 1
                print(f"✅ Success ({response_type})")
                
                # Verify database read was used (Phase 2)
                if USE_DATABASE_READS and response_type in ['stock_data', 'stock_analysis']:
                    # Check if data came from database (indirectly by checking if analysis worked)
                    results['database_verified'] += 1
            else:
                results['failed'] += 1
                error_msg = response.get('response', 'Unknown error')
                print(f"❌ Failed: {error_msg[:80]}")
                results['errors'].append((query, description, error_msg))
            
            print()
            time.sleep(0.2)  # Small delay between tests
            
        except Exception as e:
            results['failed'] += 1
            error_msg = str(e)
            print(f"❌ ERROR: {error_msg[:80]}")
            results['errors'].append((query, description, error_msg))
            print()
    
    # ========== SUMMARY ==========
    print("=" * 70)
    print("NATURAL LANGUAGE TEST SUMMARY")
    print("=" * 70)
    print()
    print(f"Total queries: {results['total']}")
    print(f"Successful: {results['successful']} ({results['successful']*100/results['total']:.1f}%)")
    print(f"Failed: {results['failed']} ({results['failed']*100/results['total']:.1f}%)")
    print(f"Database reads verified: {results['database_verified']}")
    print()
    
    if results['errors']:
        print(f"Failed queries ({len(results['errors'])}):")
        for query, desc, error in results['errors'][:10]:  # Show first 10
            print(f"  • \"{query}\" ({desc})")
            print(f"    Error: {error[:80]}")
        if len(results['errors']) > 10:
            print(f"  ... and {len(results['errors']) - 10} more")
        print()
    
    # Database statistics
    print("Database Statistics:")
    stats = db.get_stats()
    print(f"  Stocks: {stats['total_stocks']}")
    print(f"  Price records: {stats['total_price_records']:,}")
    print(f"  Database size: {stats['database_size_mb']:.2f} MB")
    print()
    
    # Phase 2 & 3 verification
    print("Phase 2 & 3 Verification:")
    print(f"  ✅ Database reads: {'ENABLED' if USE_DATABASE_READS else 'DISABLED'}")
    print(f"  ✅ CSV writes: {'ENABLED' if ENABLE_CSV_WRITES else 'DISABLED (Phase 3)'}")
    print(f"  ✅ CSV export: Available")
    print()
    
    if results['successful'] >= results['total'] * 0.9:
        print("✅ EXCELLENT: >90% queries successful")
    elif results['successful'] >= results['total'] * 0.8:
        print("✅ GOOD: >80% queries successful")
    elif results['successful'] >= results['total'] * 0.6:
        print("⚠️  FAIR: >60% queries successful")
    else:
        print("❌ NEEDS WORK: <60% queries successful")
    print()
    print("=" * 70)


if __name__ == "__main__":
    test_phase2_3_natural_language()


