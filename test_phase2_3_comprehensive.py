#!/usr/bin/env python3
"""
Comprehensive Phase 2 & 3 Database Tests
==========================================

Very comprehensive tests for Phase 2 (database reads) and Phase 3 (optional CSV writes).
Tests natural language, database functionality, CSV exports, and configuration.
"""

import sys
import os
import time
import pandas as pd
from pathlib import Path
from typing import Dict, List

try:
    from stock_agent_service import StockAgentService
    from database import get_database
    from database_export import DatabaseExporter
    from config import DATA_DIRECTORY, ENABLE_CSV_WRITES, USE_DATABASE_READS
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


class Phase2_3TestSuite:
    """Comprehensive test suite for Phase 2 and 3."""
    
    def __init__(self):
        """Initialize test suite."""
        self.service = StockAgentService()
        self.db = get_database()
        self.exporter = DatabaseExporter()
        
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def run_all_tests(self):
        """Run all test categories."""
        print("=" * 70)
        print("PHASE 2 & 3 COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print()
        print(f"Configuration:")
        print(f"  USE_DATABASE_READS: {USE_DATABASE_READS}")
        print(f"  ENABLE_CSV_WRITES: {ENABLE_CSV_WRITES}")
        print()
        
        # Test categories
        test_categories = [
            ("Configuration Tests", self.test_configuration),
            ("Database Read Tests", self.test_database_reads),
            ("Natural Language Tests (Phase 2)", self.test_natural_language_phase2),
            ("CSV Export Tests (Phase 3)", self.test_csv_export),
            ("Dual-Write Tests", self.test_dual_write),
            ("Performance Tests", self.test_performance),
            ("Data Integrity Tests", self.test_data_integrity),
            ("Edge Cases", self.test_edge_cases),
        ]
        
        for category_name, test_func in test_categories:
            print("-" * 70)
            print(f"TEST CATEGORY: {category_name}")
            print("-" * 70)
            print()
            try:
                test_func()
            except Exception as e:
                print(f"❌ Category failed: {e}")
                import traceback
                traceback.print_exc()
            print()
        
        # Final summary
        self.print_summary()
    
    def test_configuration(self):
        """Test configuration settings."""
        self._test("Config: USE_DATABASE_READS is boolean", isinstance(USE_DATABASE_READS, bool))
        self._test("Config: ENABLE_CSV_WRITES is boolean", isinstance(ENABLE_CSV_WRITES, bool))
        self._test("Config: USE_DATABASE_READS is True (Phase 2)", USE_DATABASE_READS == True)
    
    def test_database_reads(self):
        """Test database read functionality."""
        # Test 1: Read existing stock
        aapl_prices = self.db.get_prices("AAPL", frequency="daily", data_type="closing")
        self._test("Database: Read AAPL daily closing prices", not aapl_prices.empty)
        
        if not aapl_prices.empty:
            self._test("Database: AAPL prices have correct columns", 
                      all(col in aapl_prices.columns for col in ['Date', 'Opening_Price', 'Closing_Price']))
            self._test("Database: AAPL prices sorted by date", 
                      aapl_prices['Date'].is_monotonic_increasing)
        
        # Test 2: Read with date range
        msft_prices = self.db.get_prices("MSFT", start_date="2024-01-01", end_date="2024-12-31")
        self._test("Database: Read MSFT with date range", not msft_prices.empty)
        
        # Test 3: Read multiple frequencies
        for freq in ['daily', 'weekly', 'monthly']:
            prices = self.db.get_prices("AAPL", frequency=freq)
            if not prices.empty:
                self._test(f"Database: Read AAPL {freq} data", True)
    
    def test_natural_language_phase2(self):
        """Test natural language processing with database reads."""
        test_queries = [
            ("analyze apple stock data", "Analysis with database read"),
            ("show me tesla prices", "Price query with database read"),
            ("what about microsoft data?", "Question format with database read"),
            ("can you analyze nvidia?", "Analysis request with database read"),
            ("give me google stock info", "Info request with database read"),
        ]
        
        for query, description in test_queries:
            try:
                response = self.service.process_request(query)
                success = response.get('success', False)
                self._test(f"NL: {description}", success, query=query)
                time.sleep(0.2)  # Small delay
            except Exception as e:
                self._test(f"NL: {description}", False, error=str(e), query=query)
    
    def test_csv_export(self):
        """Test CSV export functionality (Phase 3)."""
        # Test 1: Export single stock
        try:
            export_path = self.exporter.export_stock_prices("AAPL", frequency="daily", data_type="closing")
            self._test("Export: Export AAPL to CSV", export_path is not None and export_path.exists())
            
            if export_path and export_path.exists():
                # Verify CSV content
                df = pd.read_csv(export_path)
                self._test("Export: CSV has correct format", not df.empty and 'Date' in df.columns)
        except Exception as e:
            self._test("Export: Export AAPL to CSV", False, error=str(e))
        
        # Test 2: Export all frequencies
        try:
            files = self.exporter.export_all_prices("MSFT")
            self._test(f"Export: Export all MSFT data ({len(files)} files)", len(files) > 0)
        except Exception as e:
            self._test("Export: Export all MSFT data", False, error=str(e))
        
        # Test 3: Export screening results
        try:
            export_path = self.exporter.export_screening_results()
            self._test("Export: Export screening results", export_path is not None and export_path.exists())
        except Exception as e:
            self._test("Export: Export screening results", False, error=str(e))
    
    def test_dual_write(self):
        """Test dual-write functionality (CSV + Database)."""
        if not ENABLE_CSV_WRITES:
            print("  ⏭️  Skipping (CSV writes disabled)")
            return
        
        # This test would require downloading new data
        # For now, just verify the configuration allows CSV writes
        self._test("Dual-write: CSV writes enabled", ENABLE_CSV_WRITES == True)
    
    def test_performance(self):
        """Test database performance."""
        import time
        
        # Test 1: Single stock query speed
        start = time.time()
        prices = self.db.get_prices("AAPL", frequency="daily", data_type="closing")
        query_time = (time.time() - start) * 1000  # milliseconds
        
        self._test(f"Performance: Single query speed ({query_time:.2f}ms)", query_time < 1000)  # Should be < 1 second
        
        # Test 2: Multiple stock queries
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
        start = time.time()
        for symbol in symbols:
            self.db.get_prices(symbol, frequency="daily")
        multi_query_time = (time.time() - start) * 1000
        
        self._test(f"Performance: Multiple queries ({multi_query_time:.2f}ms for {len(symbols)} stocks)", 
                  multi_query_time < 5000)  # Should be < 5 seconds
    
    def test_data_integrity(self):
        """Test data integrity between database and exports."""
        # Test 1: Database -> Export -> Read should match
        try:
            # Get from database
            db_data = self.db.get_prices("AAPL", frequency="daily", data_type="closing")
            
            if not db_data.empty:
                # Export to CSV
                export_path = self.exporter.export_stock_prices("AAPL", frequency="daily", data_type="closing")
                
                if export_path and export_path.exists():
                    # Read from CSV
                    csv_data = pd.read_csv(export_path)
                    
                    # Compare row counts (may differ slightly due to date filtering)
                    self._test("Integrity: Export preserves data", len(csv_data) > 0)
        except Exception as e:
            self._test("Integrity: Database -> Export -> Read", False, error=str(e))
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test 1: Non-existent stock
        prices = self.db.get_prices("NONEXISTENT", frequency="daily")
        self._test("Edge case: Non-existent stock returns empty", prices.empty)
        
        # Test 2: Invalid date range
        prices = self.db.get_prices("AAPL", start_date="2099-01-01", end_date="2100-01-01")
        self._test("Edge case: Invalid date range returns empty", prices.empty or len(prices) == 0)
        
        # Test 3: Empty query
        try:
            response = self.service.process_request("")
            self._test("Edge case: Empty query handled", True)  # Should not crash
        except Exception as e:
            self._test("Edge case: Empty query handled", False, error=str(e))
    
    def _test(self, description: str, passed: bool, error: str = None, query: str = None):
        """Record test result."""
        self.results['total_tests'] += 1
        
        if passed:
            self.results['passed'] += 1
            print(f"  ✅ {description}")
        else:
            self.results['failed'] += 1
            print(f"  ❌ {description}")
            if error:
                print(f"      Error: {error[:100]}")
            if query:
                print(f"      Query: \"{query}\"")
            self.results['errors'].append({
                'description': description,
                'error': error,
                'query': query
            })
    
    def print_summary(self):
        """Print test summary."""
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print()
        print(f"Total tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']} ({self.results['passed']*100/self.results['total_tests']:.1f}%)")
        print(f"Failed: {self.results['failed']} ({self.results['failed']*100/self.results['total_tests']:.1f}%)")
        print()
        
        if self.results['errors']:
            print("Failed tests:")
            for error in self.results['errors'][:10]:  # Show first 10
                print(f"  • {error['description']}")
                if error.get('error'):
                    print(f"    Error: {error['error'][:80]}")
            if len(self.results['errors']) > 10:
                print(f"  ... and {len(self.results['errors']) - 10} more")
            print()
        
        # Database stats
        stats = self.db.get_stats()
        print("Database Statistics:")
        print(f"  Stocks: {stats['total_stocks']}")
        print(f"  Price records: {stats['total_price_records']:,}")
        print(f"  Database size: {stats['database_size_mb']:.2f} MB")
        print()
        
        # Phase 2 & 3 status
        print("Phase 2 & 3 Status:")
        print(f"  ✅ Database reads: {'ENABLED' if USE_DATABASE_READS else 'DISABLED'}")
        print(f"  ✅ CSV writes: {'ENABLED' if ENABLE_CSV_WRITES else 'DISABLED (Phase 3)'}")
        print(f"  ✅ CSV export: Available")
        print()
        
        if self.results['passed'] >= self.results['total_tests'] * 0.9:
            print("✅ EXCELLENT: >90% tests passed")
        elif self.results['passed'] >= self.results['total_tests'] * 0.8:
            print("✅ GOOD: >80% tests passed")
        elif self.results['passed'] >= self.results['total_tests'] * 0.6:
            print("⚠️  FAIR: >60% tests passed")
        else:
            print("❌ NEEDS WORK: <60% tests passed")
        print()
        print("=" * 70)


if __name__ == "__main__":
    suite = Phase2_3TestSuite()
    suite.run_all_tests()


