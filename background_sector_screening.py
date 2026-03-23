#!/usr/bin/env python3
"""
Background Sector Screening
============================

Builds comprehensive database and screens ALL sectors.
Saves 5 stocks per sector for this week.
Runs in background - don't stop until complete.
"""

import json
import time
from datetime import datetime
from pathlib import Path
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Helper for flushing output (use with -u flag: python3 -u script.py)
def print_flush(*args, **kwargs):
    print(*args, **kwargs, flush=True)

try:
    from config import DATA_DIRECTORY
    from sector_database import SectorDatabaseBuilder
    from fifth_layer_screening import FifthLayerScreening
    from llm_config import get_llm_client
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


class BackgroundSectorScreener:
    """Background screening for all sectors."""
    
    def __init__(self):
        """Initialize background screener."""
        self.data_dir = DATA_DIRECTORY / "screening"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.data_dir / "weekly_screening_results.json"
        
        # All 11 GICS sectors
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
    
    def build_comprehensive_database(self):
        """Build comprehensive database from SEC EDGAR (ALL stocks)."""
        print("=" * 70)
        print("STEP 1: Building Comprehensive Database from SEC EDGAR")
        print("=" * 70)
        print()
        print("This will process ALL US stocks (10,000+ companies)")
        print("Estimated time: 15-30 minutes")
        print()
        
        builder = SectorDatabaseBuilder()
        builder.build_database(max_stocks_per_sector=None, use_all_stocks=True)
        
        print()
        print("✅ Comprehensive database built!")
        print()
    
    def screen_all_sectors(self):
        """Screen all sectors and save 5 stocks per sector."""
        print("=" * 70)
        print("STEP 2: Screening ALL Sectors")
        print("=" * 70)
        print()
        
        # Initialize screening system
        llm_client = get_llm_client()
        screening = FifthLayerScreening(llm_client=llm_client)
        
        # Load existing results or create new
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                weekly_results = json.load(f)
        else:
            weekly_results = {
                'week_start': datetime.now().isoformat(),
                'sectors': {}
            }
        
        # Screen each sector (skip already completed ones)
        for sector in self.sectors:
            # Check if sector already completed successfully
            if sector in weekly_results.get('sectors', {}):
                sector_data = weekly_results['sectors'][sector]
                stocks_found = sector_data.get('stocks_found', 0)
                has_error = 'error' in sector_data
                
                # Skip if completed successfully (has stocks and no error)
                if stocks_found > 0 and not has_error:
                    print()
                    print(f"⏭️  SKIPPING {sector} - Already completed ({stocks_found} stocks found)")
                    continue
                
                # Re-screen if it had an error (bug is now fixed)
                if has_error:
                    print()
                    print(f"🔄 RE-SCREENING {sector} - Previous error fixed")
            
            print()
            print("=" * 70)
            print(f"SCREENING: {sector}")
            print("=" * 70)
            print()
            
            sector_start_time = time.time()
            
            try:
                # Screen the sector (will return up to 5 stocks)
                results = screening.screen_sector(sector)
                
                sector_time = time.time() - sector_start_time
                
                # Save results for this sector
                weekly_results['sectors'][sector] = {
                    'screened_at': datetime.now().isoformat(),
                    'time_taken_seconds': sector_time,
                    'stocks_found': len(results),
                    'stocks': []
                }
                
                # Save stock data
                for stock in results:
                    stock_data = {
                        'symbol': stock.get('symbol'),
                        'composite_score': stock.get('composite_score', 0),
                        'undervaluation_pct': stock.get('undervaluation_pct', 0),
                        'catalyst_score': stock.get('catalyst_score', 1),
                        'intrinsic_value': stock.get('intrinsic_value', 0),
                        'current_price': stock.get('current_price', 0),
                        'passed_layers': stock.get('passed_layers', []),
                        'missing_layers': stock.get('missing_layers', []),
                        'missing_criteria': stock.get('missing_criteria', []),
                        'market_cap': stock.get('data', {}).get('market_cap', 0),
                        'pe_ratio': stock.get('data', {}).get('pe_ratio', 0),
                        'pb_ratio': stock.get('data', {}).get('price_to_book', 0),
                        'sector': stock.get('data', {}).get('sector', sector),
                        'catalysts': stock.get('catalysts', {})
                    }
                    weekly_results['sectors'][sector]['stocks'].append(stock_data)
                
                # Save after each sector (in case of interruption)
                with open(self.results_file, 'w') as f:
                    json.dump(weekly_results, f, indent=2)
                
                print()
                print(f"✅ {sector}: {len(results)} stocks found and saved ({sector_time:.1f}s)")
                
                # Show summary
                if results:
                    print(f"   Top stocks:")
                    for i, stock in enumerate(results[:3], 1):
                        symbol = stock.get('symbol')
                        score = stock.get('composite_score', 0)
                        layers = stock.get('passed_layers', [])
                        status = "✅ All layers" if 'catalyst' in layers else "⚠️ Partial"
                        print(f"   {i}. {symbol} - Score: {score:.1f} - {status}")
                
            except Exception as e:
                print(f"❌ ERROR screening {sector}: {e}")
                import traceback
                traceback.print_exc()
                # Save error state
                weekly_results['sectors'][sector] = {
                    'screened_at': datetime.now().isoformat(),
                    'error': str(e),
                    'stocks_found': 0,
                    'stocks': []
                }
                with open(self.results_file, 'w') as f:
                    json.dump(weekly_results, f, indent=2)
                continue
        
        # Final summary
        print()
        print("=" * 70)
        print("SCREENING COMPLETE - SUMMARY")
        print("=" * 70)
        print()
        
        total_stocks = 0
        sectors_with_stocks = 0
        
        for sector, data in weekly_results['sectors'].items():
            count = data.get('stocks_found', 0)
            total_stocks += count
            if count > 0:
                sectors_with_stocks += 1
                print(f"✅ {sector}: {count} stocks")
            else:
                print(f"⚪ {sector}: 0 stocks")
        
        print()
        print(f"Total stocks found: {total_stocks}")
        print(f"Sectors with stocks: {sectors_with_stocks}/{len(self.sectors)}")
        print()
        print(f"Results saved to: {self.results_file}")
        print()
    
    def run(self, skip_database_build=False, resume=True):
        """
        Run complete background screening process.
        
        Args:
            skip_database_build: If True, skip database building step
            resume: If True, skip already-completed sectors
        """
        start_time = time.time()
        
        print("=" * 70)
        print("BACKGROUND SECTOR SCREENING")
        print("=" * 70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        if resume:
            print("🔄 RESUME MODE: Will skip completed sectors and re-screen failed ones")
            print()
        
        print("This will:")
        if not skip_database_build:
            print("1. Build comprehensive database from SEC EDGAR (ALL US stocks)")
            print("2. Screen all 11 sectors")
        else:
            print("1. Screen remaining sectors (database already built)")
        print("3. Save 5 stocks per sector for this week")
        print()
        print("Estimated total time: 30-60 minutes")
        print("Running in background - results will be saved automatically")
        print()
        
        try:
            # Step 1: Build database (skip if requested)
            if not skip_database_build:
                self.build_comprehensive_database()
            else:
                print("⏭️  Skipping database build (already exists)")
                print()
            
            # Step 2: Screen all sectors (will skip completed if resume=True)
            self.screen_all_sectors()
            
            total_time = time.time() - start_time
            
            print("=" * 70)
            print("✅ BACKGROUND SCREENING COMPLETE!")
            print("=" * 70)
            print(f"Total time: {total_time/60:.1f} minutes")
            print(f"Results saved to: {self.results_file}")
            print()
            
        except KeyboardInterrupt:
            print()
            print("⚠️ Interrupted by user")
            print("Partial results saved - you can resume later")
        except Exception as e:
            print()
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            print("Partial results may have been saved")


if __name__ == "__main__":
    import sys
    
    screener = BackgroundSectorScreener()
    
    # Check command line arguments
    skip_db = '--skip-db' in sys.argv or '--resume' in sys.argv
    resume = '--resume' in sys.argv or True  # Default to resume mode
    
    screener.run(skip_database_build=skip_db, resume=resume)

