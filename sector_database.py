#!/usr/bin/env python3
"""
Sector Database Builder
========================

Builds and maintains sector database from SEC EDGAR + yfinance.
Efficient, cached, updates monthly.
"""

import requests
import yfinance as yf
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

try:
    from config import DATA_DIRECTORY
except ImportError:
    DATA_DIRECTORY = Path("data")


class SectorDatabaseBuilder:
    """Build sector database efficiently."""
    
    def __init__(self):
        """Initialize builder."""
        self.data_dir = DATA_DIRECTORY / "screening"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.data_dir / "sector_database.json"
        
        # GICS Sectors
        self.sectors = [
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
    
    def build_database(self, max_stocks_per_sector: Optional[int] = None, use_all_stocks: bool = True):
        """
        Build comprehensive sector database from ALL US stocks (SEC EDGAR).
        
        Args:
            max_stocks_per_sector: Optional limit per sector (None = no limit, include all)
            use_all_stocks: If True, process ALL SEC companies (thousands). If False, sample 1000.
        """
        print("=" * 70)
        print("Building Comprehensive Sector Database from SEC EDGAR")
        print("=" * 70)
        print()
        
        # Step 1: Get ALL SEC company list (comprehensive database)
        print("Step 1: Fetching ALL US stocks from SEC EDGAR...")
        sec_stocks = self._get_sec_companies()
        print(f"✅ Found {len(sec_stocks):,} companies in SEC database")
        print()

        if not sec_stocks:
            print("⚠️ SEC source unavailable. Falling back to the local stock database...")
            fallback_db = self._build_database_from_local_database()
            if fallback_db:
                return self._save_database(fallback_db, "local stock database fallback")
            raise RuntimeError("Could not build sector database from SEC or the local database.")
        
        # Step 2: Process all or sample (user choice)
        if not use_all_stocks and len(sec_stocks) > 1000:
            print(f"Step 2: Sampling 1000 companies for faster processing...")
            import random
            sec_stocks = random.sample(sec_stocks, 1000)
            print(f"✅ Processing {len(sec_stocks)} companies")
        else:
            print(f"Step 2: Processing ALL {len(sec_stocks):,} companies")
            print("   This will take 15-30 minutes but ensures comprehensive coverage")
        print()
        
        # Step 3: Get sector info and build database (ALL stocks, no limit)
        print("Step 3: Getting sector information for all stocks...")
        print("   This connects to yfinance for each stock (rate-limited for safety)")
        print()
        sector_db = {sector: [] for sector in self.sectors}
        sector_db['Unknown'] = []
        
        # Track start time for progress
        import time as time_module
        start_time = time_module.time()
        
        processed = 0
        skipped = 0
        errors = 0
        
        for i, stock in enumerate(sec_stocks, 1):
            ticker = stock.get('ticker', '').upper().strip()
            
            # Skip invalid tickers
            if not ticker or len(ticker) > 5 or len(ticker) < 1:
                skipped += 1
                continue
            
            try:
                # Get sector from yfinance (safe, official source)
                ticker_obj = yf.Ticker(ticker)
                info = ticker_obj.info
                sector = info.get('sector', 'Unknown')
                
                # Add to appropriate sector (no limit if max_stocks_per_sector is None)
                if sector in sector_db:
                    if max_stocks_per_sector is None or len(sector_db[sector]) < max_stocks_per_sector:
                        sector_db[sector].append(ticker)
                        processed += 1
                
                # Rate limiting (be respectful to yfinance)
                time.sleep(0.1)
                
                # Progress updates every 100 stocks
                if i % 100 == 0:
                    elapsed = time_module.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    remaining = (len(sec_stocks) - i) / rate if rate > 0 else 0
                    print(f"   Progress: {i:,}/{len(sec_stocks):,} stocks ({i*100//len(sec_stocks)}%)")
                    print(f"   Processed: {processed:,} | Skipped: {skipped:,} | Errors: {errors:,}")
                    if remaining > 0:
                        print(f"   Estimated time remaining: {remaining/60:.1f} minutes")
                    print()
                
            except Exception as e:
                errors += 1
                if errors <= 5:  # Show first few errors for debugging
                    print(f"   Warning: Error processing {ticker}: {str(e)[:50]}")
                continue
        
        print(f"✅ Processing complete!")
        print(f"   Total processed: {processed:,} stocks")
        print(f"   Skipped (invalid): {skipped:,}")
        print(f"   Errors: {errors:,}")
        print()
        
        total_stocks = sum(len(stocks) for stocks in sector_db.values())
        if total_stocks == 0:
            print("⚠️ SEC/yfinance build produced an empty sector database.")
            print("   Falling back to the local stock database to avoid clobbering the cache.")
            fallback_db = self._build_database_from_local_database()
            if fallback_db:
                return self._save_database(fallback_db, "local stock database fallback")
            raise RuntimeError("Refusing to save an empty sector database.")

        return self._save_database(sector_db, "SEC EDGAR + yfinance")
    
    def _get_sec_companies(self) -> List[Dict]:
        """Get company list from SEC EDGAR."""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            headers = {
                'User-Agent': 'Stock Agent Screening System (contact@example.com)',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                companies = []
                for key, value in data.items():
                    companies.append({
                        'ticker': value.get('ticker', ''),
                        'cik': value.get('cik_str', ''),
                        'name': value.get('title', '')
                    })
                return companies
        except Exception as e:
            print(f"Error fetching SEC data: {e}")
            return []

    def _build_database_from_local_database(self) -> Optional[Dict[str, List[str]]]:
        """Build sector data from the local SQLite database as a safe fallback."""
        try:
            from database import get_database

            db = get_database()
            sector_db = {sector: [] for sector in self.sectors}
            sector_db['Unknown'] = []

            total_stocks = 0
            for sector in self.sectors:
                stocks = db.get_stocks_by_sector(sector)
                symbols = sorted({
                    stock.get('symbol')
                    for stock in stocks
                    if stock.get('symbol')
                })
                sector_db[sector] = symbols
                total_stocks += len(symbols)

            if total_stocks == 0:
                print("⚠️ Local database fallback did not contain any sector-mapped stocks.")
                return None

            print(f"✅ Loaded {total_stocks:,} stocks from local database fallback")
            return sector_db
        except Exception as e:
            print(f"⚠️ Local database fallback failed: {e}")
            return None

    def _save_database(self, sector_db: Dict[str, List[str]], source: str) -> Dict[str, List[str]]:
        """Persist a non-empty sector database to disk."""
        total_stocks = sum(len(stocks) for stocks in sector_db.values())
        if total_stocks == 0:
            raise RuntimeError("Refusing to save an empty sector database.")

        print("Step 4: Saving database...")
        db_data = {
            'last_updated': datetime.now().isoformat(),
            'source': source,
            'sectors': sector_db,
            'total_stocks': total_stocks
        }

        with open(self.db_file, 'w') as f:
            json.dump(db_data, f, indent=2)

        print(f"✅ Database saved to {self.db_file}")
        print()

        print("=" * 70)
        print("Database Summary")
        print("=" * 70)
        for sector, stocks in sector_db.items():
            if stocks:
                print(f"{sector}: {len(stocks)} stocks")
        print(f"Total: {db_data['total_stocks']} stocks")
        print()

        return sector_db
    
    def needs_update(self) -> bool:
        """Check if database needs update (monthly)."""
        if not self.db_file.exists():
            return True
        
        with open(self.db_file, 'r') as f:
            db_data = json.load(f)
        
        last_updated = datetime.fromisoformat(db_data.get('last_updated', '2000-01-01'))
        days_old = (datetime.now() - last_updated).days
        
        return days_old > 30  # Update monthly
    
    def get_sector_stocks(self, sector: str) -> List[str]:
        """Get stocks for a sector."""
        if not self.db_file.exists() or self.needs_update():
            print("Database missing or outdated. Building...")
            self.build_database()
        
        with open(self.db_file, 'r') as f:
            db_data = json.load(f)
        
        return db_data['sectors'].get(sector, [])


if __name__ == "__main__":
    builder = SectorDatabaseBuilder()
    builder.build_database()
