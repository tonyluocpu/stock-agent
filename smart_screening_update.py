#!/usr/bin/env python3
"""
Smart Stock Screening Update - Database Approach
================================================

Intelligently updates only sectors that need refreshing, using database (Phase 2/3).
"""

import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    from config import DATA_DIRECTORY
    from fifth_layer_screening import FifthLayerScreening
    from llm_config import get_llm_client
    from database import get_database
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


class SmartScreeningUpdate:
    """Smart screening update using database approach."""
    
    def __init__(self):
        """Initialize updater."""
        self.data_dir = DATA_DIRECTORY / "screening"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results_file = self.data_dir / "weekly_screening_results.json"
        self.db = get_database()
        
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
        
        # Refresh threshold: update if older than 3 days
        self.refresh_threshold_days = 3
        
        # Timing statistics
        self.timing_stats = {
            'start_time': None,
            'end_time': None,
            'sectors': {},
            'skipped': [],
            'updated': []
        }
    
    def _needs_refresh(self, sector: str, existing_data: dict) -> bool:
        """Check if sector needs refresh based on age and data quality."""
        if 'error' in existing_data:
            return True  # Always refresh if there was an error
        
        screened_at = existing_data.get('screened_at', '')
        if not screened_at:
            return True  # No data, needs refresh
        
        try:
            screened_date = datetime.fromisoformat(screened_at.replace('Z', '+00:00'))
            days_old = (datetime.now() - screened_date).days
            return days_old >= self.refresh_threshold_days
        except:
            return True  # Can't parse date, refresh to be safe
    
    def _get_sector_stocks_from_db(self, sector: str) -> list:
        """Get stocks for sector from database (Phase 2 approach)."""
        stocks = self.db.get_stocks_by_sector(sector)
        return [s['symbol'] for s in stocks if s.get('symbol')]
    
    def update_sectors_smart(self, force_refresh=False):
        """Update only sectors that need refreshing."""
        print("=" * 70)
        print("SMART STOCK SCREENING UPDATE - DATABASE APPROACH")
        print("=" * 70)
        print()
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Refresh threshold: {self.refresh_threshold_days} days")
        print()
        
        self.timing_stats['start_time'] = time.time()
        overall_start = time.time()
        
        # Initialize screening system
        print("Initializing screening system...")
        init_start = time.time()
        llm_client = get_llm_client()
        screening = FifthLayerScreening(llm_client=llm_client)
        init_time = time.time() - init_start
        print(f"✅ Initialized in {init_time:.2f} seconds")
        print()
        
        # Load existing results
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                weekly_results = json.load(f)
        else:
            weekly_results = {
                'week_start': datetime.now().isoformat(),
                'sectors': {}
            }
        
        # Determine which sectors need updating
        sectors_to_update = []
        sectors_to_skip = []
        
        for sector in self.sectors:
            existing_data = weekly_results.get('sectors', {}).get(sector, {})
            
            if force_refresh:
                sectors_to_update.append(sector)
            elif self._needs_refresh(sector, existing_data):
                sectors_to_update.append(sector)
            else:
                sectors_to_skip.append(sector)
                stocks_found = existing_data.get('stocks_found', 0)
                screened_at = existing_data.get('screened_at', '')
                print(f"⏭️  {sector}: Recent data ({stocks_found} stocks, {screened_at[:10]}) - SKIPPING")
        
        self.timing_stats['skipped'] = sectors_to_skip
        self.timing_stats['updated'] = sectors_to_update
        
        print()
        print(f"📊 Smart update plan:")
        print(f"   • Sectors to update: {len(sectors_to_update)}")
        print(f"   • Sectors to skip: {len(sectors_to_skip)}")
        print()
        
        if not sectors_to_update:
            print("✅ All sectors are up to date! No refresh needed.")
            print()
            return
        
        # Process sectors that need updating
        for i, sector in enumerate(sectors_to_update, 1):
            print()
            print("=" * 70)
            print(f"SCREENING {i}/{len(sectors_to_update)}: {sector}")
            print("=" * 70)
            print()
            
            sector_start = time.time()
            
            try:
                # Screen the sector
                results = screening.screen_sector(sector)
                
                sector_time = time.time() - sector_start
                
                # Save results
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
                
                # Save after each sector
                with open(self.results_file, 'w') as f:
                    json.dump(weekly_results, f, indent=2)
                
                # Save to database (Phase 2/3 approach)
                screening_date = datetime.now().strftime('%Y-%m-%d')
                
                for stock in results:
                    try:
                        self.db.insert_screening_result(
                            symbol=stock.get('symbol'),
                            sector=sector,
                            screening_date=screening_date,
                            composite_score=stock.get('composite_score'),
                            undervaluation_pct=stock.get('undervaluation_pct'),
                            catalyst_score=stock.get('catalyst_score'),
                            intrinsic_value=stock.get('intrinsic_value'),
                            current_price=stock.get('current_price'),
                            market_cap=stock.get('data', {}).get('market_cap'),
                            pe_ratio=stock.get('data', {}).get('pe_ratio'),
                            pb_ratio=stock.get('data', {}).get('price_to_book'),
                            passed_layers=stock.get('passed_layers'),
                            missing_layers=stock.get('missing_layers'),
                            missing_criteria=stock.get('missing_criteria'),
                            catalysts=stock.get('catalysts')
                        )
                    except Exception as e:
                        print(f"  ⚠️  Warning: Failed to save {stock.get('symbol')} to database: {e}")
                
                # Record timing
                self.timing_stats['sectors'][sector] = {
                    'time_seconds': sector_time,
                    'stocks_found': len(results)
                }
                
                print()
                print(f"✅ {sector}: {len(results)} stocks found in {sector_time:.1f} seconds")
                
                # Show summary
                if results:
                    print(f"   Top stocks:")
                    for j, stock in enumerate(results[:3], 1):
                        symbol = stock.get('symbol')
                        score = stock.get('composite_score', 0)
                        print(f"   {j}. {symbol} - Score: {score:.1f}")
                
            except Exception as e:
                sector_time = time.time() - sector_start
                print(f"❌ ERROR screening {sector}: {e}")
                import traceback
                traceback.print_exc()
                
                # Save error state
                weekly_results['sectors'][sector] = {
                    'screened_at': datetime.now().isoformat(),
                    'error': str(e),
                    'time_taken_seconds': sector_time,
                    'stocks_found': 0,
                    'stocks': []
                }
                with open(self.results_file, 'w') as f:
                    json.dump(weekly_results, f, indent=2)
                
                self.timing_stats['sectors'][sector] = {
                    'time_seconds': sector_time,
                    'error': str(e),
                    'stocks_found': 0
                }
        
        # Final timing
        self.timing_stats['end_time'] = time.time()
        total_time = self.timing_stats['end_time'] - self.timing_stats['start_time']
        
        # Print timing summary
        print()
        print("=" * 70)
        print("TIMING SUMMARY")
        print("=" * 70)
        print()
        print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"Sectors updated: {len(sectors_to_update)}")
        print(f"Sectors skipped: {len(sectors_to_skip)}")
        if sectors_to_update:
            avg_time = total_time / len(sectors_to_update)
            print(f"Average time per updated sector: {avg_time:.1f} seconds")
            print()
            print("Time per sector:")
            for sector, stats in self.timing_stats['sectors'].items():
                time_taken = stats.get('time_seconds', 0)
                stocks = stats.get('stocks_found', 0)
                status = f"{stocks} stocks" if stocks > 0 else "ERROR"
                print(f"  {sector:30} {time_taken:6.1f}s ({status})")
        print()
        
        # Final summary
        print("=" * 70)
        print("SMART SCREENING UPDATE COMPLETE")
        print("=" * 70)
        print()
        
        total_stocks = 0
        sectors_with_stocks = 0
        
        for sector, data in weekly_results['sectors'].items():
            count = data.get('stocks_found', 0)
            total_stocks += count
            if count > 0:
                sectors_with_stocks += 1
        
        print(f"Total stocks found: {total_stocks}")
        print(f"Sectors with stocks: {sectors_with_stocks}/{len(self.sectors)}")
        print(f"Results saved to: {self.results_file}")
        print(f"Database updated: Yes (Phase 2/3 approach)")
        print()
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()


if __name__ == "__main__":
    import sys
    
    force = '--force' in sys.argv or '-f' in sys.argv
    
    updater = SmartScreeningUpdate()
    updater.update_sectors_smart(force_refresh=force)


