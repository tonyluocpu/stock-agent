#!/usr/bin/env python3
"""
Migration Script: Import Existing Data to Database
===================================================

Phase 1: Import existing CSV files, JSON cache files, and screening results
into SQLite database. Original files are NOT deleted - dual storage.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
from typing import Dict, List

try:
    from config import DATA_DIRECTORY
    from database import StockDatabase
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


class DatabaseMigrator:
    """Migrate existing data to database."""
    
    def __init__(self):
        """Initialize migrator."""
        self.data_dir = DATA_DIRECTORY
        self.db = StockDatabase()
        
        # Statistics
        self.stats = {
            'stocks_imported': 0,
            'prices_imported': 0,
            'cache_imported': 0,
            'screening_results_imported': 0,
            'errors': 0
        }
    
    def migrate_all(self):
        """Migrate all existing data."""
        print("=" * 70)
        print("DATABASE MIGRATION - Phase 1")
        print("=" * 70)
        print()
        print("This will import existing data into SQLite database.")
        print("Original files will NOT be deleted (dual storage).")
        print()
        
        try:
            # Step 1: Import CSV price files
            print("Step 1: Importing historical price data (CSV files)...")
            self.migrate_csv_prices()
            print()
            
            # Step 2: Import JSON cache files
            print("Step 2: Importing cache files (stock info)...")
            self.migrate_cache_files()
            print()
            
            # Step 3: Import screening results
            print("Step 3: Importing screening results...")
            self.migrate_screening_results()
            print()
            
            # Step 4: Import sector database
            print("Step 4: Importing sector database...")
            self.migrate_sector_database()
            print()
            
            # Final statistics
            print("=" * 70)
            print("MIGRATION COMPLETE")
            print("=" * 70)
            print()
            print(f"✅ Stocks imported: {self.stats['stocks_imported']}")
            print(f"✅ Price records imported: {self.stats['prices_imported']}")
            print(f"✅ Cache entries imported: {self.stats['cache_imported']}")
            print(f"✅ Screening results imported: {self.stats['screening_results_imported']}")
            if self.stats['errors'] > 0:
                print(f"⚠️  Errors: {self.stats['errors']}")
            print()
            
            # Database stats
            db_stats = self.db.get_stats()
            print("Database Statistics:")
            print(f"  Total stocks: {db_stats['total_stocks']}")
            print(f"  Total price records: {db_stats['total_price_records']}")
            print(f"  Total screening results: {db_stats['total_screening_results']}")
            print(f"  Database size: {db_stats['database_size_mb']:.2f} MB")
            print()
            print(f"Database location: {self.db.db_path}")
            print()
            
        except Exception as e:
            print(f"❌ ERROR during migration: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
    
    def migrate_csv_prices(self):
        """Import CSV price files into database."""
        frequencies = ['daily', 'weekly', 'monthly', 'yearly']
        data_types = ['opening', 'closing']
        
        total_files = 0
        for frequency in frequencies:
            for data_type in data_types:
                csv_dir = self.data_dir / frequency / data_type
                if not csv_dir.exists():
                    continue
                
                # Find all CSV files
                csv_files = list(csv_dir.glob("**/*.csv"))
                total_files += len(csv_files)
                
                for csv_file in csv_files:
                    try:
                        # Extract symbol from path
                        # Path format: data/frequency/data_type/SYMBOL/filename.csv
                        symbol = csv_file.parent.name
                        
                        # Read CSV
                        df = pd.read_csv(csv_file)
                        
                        if df.empty:
                            continue
                        
                        # Ensure Date column is datetime
                        if 'Date' in df.columns:
                            df['Date'] = pd.to_datetime(df['Date'], utc=True)
                        else:
                            continue
                        
                        # Insert into database
                        rows_inserted = self.db.insert_prices(symbol, df, frequency, data_type)
                        
                        if rows_inserted > 0:
                            self.stats['prices_imported'] += rows_inserted
                            # Also upsert stock if not exists
                            if not self.db.get_stock(symbol):
                                self.db.upsert_stock(symbol=symbol)
                                self.stats['stocks_imported'] += 1
                    
                    except Exception as e:
                        self.stats['errors'] += 1
                        continue
        
        print(f"  Processed {total_files} CSV files")
        print(f"  Imported {self.stats['prices_imported']} price records")
    
    def migrate_cache_files(self):
        """Import JSON cache files into database."""
        # Try both locations
        cache_dirs = [
            self.data_dir / "screening" / "cache",
            self.data_dir / "screening"
        ]
        
        cache_files = []
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                cache_files.extend(list(cache_dir.glob("*_data.json")))
        
        if not cache_files:
            print("  No cache files found")
            return
        
        print(f"  Found {len(cache_files)} cache files")
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Extract symbol from filename (e.g., "AAPL_data.json" -> "AAPL")
                symbol = cache_file.stem.replace('_data', '')
                
                # Get data and timestamp
                data = cache_data.get('data', {})
                timestamp = cache_data.get('timestamp')
                
                if not data or not timestamp:
                    continue
                
                # Upsert stock info (only count if new)
                stock_existed = self.db.get_stock(symbol) is not None
                self.db.upsert_stock(
                    symbol=symbol,
                    name=data.get('name'),
                    sector=data.get('sector'),
                    industry=data.get('industry'),
                    market_cap=data.get('market_cap'),
                    pe_ratio=data.get('pe_ratio'),
                    price_to_book=data.get('price_to_book'),
                    current_price=data.get('current_price'),
                    dividend_yield=data.get('dividend_yield'),
                    shares_outstanding=data.get('shares_outstanding')
                )
                if not stock_existed:
                    self.stats['stocks_imported'] += 1
                
                # Store in cache table (key: symbol_data)
                cache_key = f"{symbol}_data"
                self.db.set_cache(cache_key, data, expires_in_hours=24)
                self.stats['cache_imported'] += 1
            
            except Exception as e:
                self.stats['errors'] += 1
                continue
    
    def migrate_screening_results(self):
        """Import screening results JSON into database."""
        screening_dir = self.data_dir / "screening"
        if not screening_dir.exists():
            print("  No screening directory found")
            return
        
        # Look for weekly_screening_results.json
        results_file = screening_dir / "weekly_screening_results.json"
        if not results_file.exists():
            print("  No weekly screening results file found")
            return
        
        try:
            with open(results_file, 'r') as f:
                results_data = json.load(f)
            
            sectors = results_data.get('sectors', {})
            
            for sector, sector_data in sectors.items():
                if 'stocks' not in sector_data:
                    continue
                
                screening_date = sector_data.get('screened_at', datetime.now().isoformat())
                # Parse ISO format date
                try:
                    screening_date_obj = datetime.fromisoformat(screening_date.replace('Z', '+00:00'))
                    screening_date_str = screening_date_obj.strftime('%Y-%m-%d')
                except:
                    screening_date_str = datetime.now().strftime('%Y-%m-%d')
                
                stocks = sector_data.get('stocks', [])
                
                for stock in stocks:
                    try:
                        symbol = stock.get('symbol')
                        if not symbol:
                            continue
                        
                        # Insert screening result
                        self.db.insert_screening_result(
                            symbol=symbol,
                            sector=sector,
                            screening_date=screening_date_str,
                            composite_score=stock.get('composite_score'),
                            undervaluation_pct=stock.get('undervaluation_pct'),
                            catalyst_score=stock.get('catalyst_score'),
                            intrinsic_value=stock.get('intrinsic_value'),
                            current_price=stock.get('current_price'),
                            market_cap=stock.get('market_cap'),
                            pe_ratio=stock.get('pe_ratio'),
                            pb_ratio=stock.get('pb_ratio'),
                            passed_layers=stock.get('passed_layers'),
                            missing_layers=stock.get('missing_layers'),
                            missing_criteria=stock.get('missing_criteria'),
                            catalysts=stock.get('catalysts')
                        )
                        self.stats['screening_results_imported'] += 1
                        
                        # Also upsert stock if not exists
                        if not self.db.get_stock(symbol):
                            self.db.upsert_stock(
                                symbol=symbol,
                                sector=sector,
                                market_cap=stock.get('market_cap'),
                                pe_ratio=stock.get('pe_ratio'),
                                price_to_book=stock.get('pb_ratio'),
                                current_price=stock.get('current_price')
                            )
                            self.stats['stocks_imported'] += 1
                    
                    except Exception as e:
                        self.stats['errors'] += 1
                        continue
        
        except Exception as e:
            print(f"  ❌ Error importing screening results: {e}")
            self.stats['errors'] += 1
    
    def migrate_sector_database(self):
        """Import sector database (stocks grouped by sector)."""
        sector_db_file = self.data_dir / "stock_lists" / "sector_database.json"
        if not sector_db_file.exists():
            print("  No sector database file found")
            return
        
        try:
            with open(sector_db_file, 'r') as f:
                sector_db = json.load(f)
            
            sectors = sector_db.get('sectors', {})
            stocks_imported = 0
            
            for sector, symbols in sectors.items():
                if not isinstance(symbols, list):
                    continue
                
                for symbol in symbols:
                    if not isinstance(symbol, str):
                        continue
                    
                    # Upsert stock with sector
                    if not self.db.get_stock(symbol):
                        self.db.upsert_stock(symbol=symbol, sector=sector)
                        stocks_imported += 1
            
            print(f"  Imported {stocks_imported} stocks from sector database")
            self.stats['stocks_imported'] += stocks_imported
        
        except Exception as e:
            print(f"  ❌ Error importing sector database: {e}")
            self.stats['errors'] += 1


if __name__ == "__main__":
    migrator = DatabaseMigrator()
    migrator.migrate_all()

