#!/usr/bin/env python3
"""
Update Stock Screening with Latest Data - Time Monitored
=========================================================

Updates screening data for all sectors while carefully monitoring time spent.
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path

try:
    from config import DATA_DIRECTORY
    from fifth_layer_screening import FifthLayerScreening
    from llm_config import get_llm_client
    from database import get_database
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


class TimedScreeningUpdate:
    """Update screening with time monitoring."""
    
    def __init__(self):
        """Initialize updater."""
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
        
        # Timing statistics
        self.timing_stats = {
            'start_time': None,
            'end_time': None,
            'sectors': {}
        }
    
    def update_all_sectors(self, force_refresh=False):
        """Update screening for all sectors with time monitoring."""
        print("=" * 70)
        print("STOCK SCREENING UPDATE - TIME MONITORED")
        print("=" * 70)
        print()
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
        
        # Track progress
        total_sectors = len(self.sectors)
        sectors_to_process = []
        
        for sector in self.sectors:
            if sector in weekly_results.get('sectors', {}):
                sector_data = weekly_results['sectors'][sector]
                stocks_found = sector_data.get('stocks_found', 0)
                has_error = 'error' in sector_data
                
                if not force_refresh and stocks_found > 0 and not has_error:
                    print(f"⏭️  {sector}: Already completed ({stocks_found} stocks) - SKIPPING")
                    continue
            
            sectors_to_process.append(sector)
        
        print(f"📊 Sectors to process: {len(sectors_to_process)}/{total_sectors}")
        print()
        
        # Process each sector
        for i, sector in enumerate(sectors_to_process, 1):
            print()
            print("=" * 70)
            print(f"SCREENING {i}/{len(sectors_to_process)}: {sector}")
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
                
                # Record timing
                self.timing_stats['sectors'][sector] = {
                    'time_seconds': sector_time,
                    'stocks_found': len(results)
                }
                
                # Save to database
                db = get_database()
                screening_date = datetime.now().strftime('%Y-%m-%d')
                
                for stock in results:
                    try:
                        db.insert_screening_result(
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
        print(f"Sectors processed: {len(sectors_to_process)}")
        if sectors_to_process:
            avg_time = total_time / len(sectors_to_process)
            print(f"Average time per sector: {avg_time:.1f} seconds")
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
        print("SCREENING UPDATE COMPLETE")
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
        print(f"Database updated: Yes")
        print()
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()


if __name__ == "__main__":
    import sys
    
    force = '--force' in sys.argv or '-f' in sys.argv
    
    updater = TimedScreeningUpdate()
    updater.update_all_sectors(force_refresh=force)


