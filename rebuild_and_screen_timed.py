#!/usr/bin/env python3
"""
Rebuild Sector Database and Screen - Time Monitored
===================================================

Rebuilds sector database from SEC EDGAR, then runs smart screening update.
All with careful time monitoring.
"""

import sys
import time
from datetime import datetime

try:
    from config import DATA_DIRECTORY
    from sector_database import SectorDatabaseBuilder
    from smart_screening_update import SmartScreeningUpdate
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


def rebuild_and_screen():
    """Rebuild sector database and run smart screening with time monitoring."""
    print("=" * 70)
    print("REBUILD SECTOR DATABASE & SMART SCREENING UPDATE")
    print("=" * 70)
    print()
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    overall_start = time.time()
    
    # Step 1: Rebuild sector database
    print("=" * 70)
    print("STEP 1: REBUILDING SECTOR DATABASE")
    print("=" * 70)
    print()
    print("This will process ALL US stocks from SEC EDGAR")
    print("Estimated time: 15-30 minutes")
    print()
    
    db_start = time.time()
    try:
        builder = SectorDatabaseBuilder()
        builder.build_database(max_stocks_per_sector=None, use_all_stocks=True)
        db_time = time.time() - db_start
        print()
        print(f"✅ Sector database rebuilt in {db_time:.1f} seconds ({db_time/60:.1f} minutes)")
    except Exception as e:
        print(f"❌ ERROR building database: {e}")
        import traceback
        traceback.print_exc()
        return
    print()
    
    # Step 2: Smart screening update
    print("=" * 70)
    print("STEP 2: SMART SCREENING UPDATE")
    print("=" * 70)
    print()
    
    screening_start = time.time()
    try:
        updater = SmartScreeningUpdate()
        updater.update_sectors_smart(force_refresh=False)  # Smart update (only old sectors)
        screening_time = time.time() - screening_start
        print()
        print(f"✅ Smart screening completed in {screening_time:.1f} seconds ({screening_time/60:.1f} minutes)")
    except Exception as e:
        print(f"❌ ERROR during screening: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # Final summary
    total_time = time.time() - overall_start
    
    print("=" * 70)
    print("COMPLETE TIMING SUMMARY")
    print("=" * 70)
    print()
    print(f"Step 1 - Database rebuild: {db_time:.1f}s ({db_time/60:.1f} min)")
    print(f"Step 2 - Smart screening: {screening_time:.1f}s ({screening_time/60:.1f} min)")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print()
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


if __name__ == "__main__":
    rebuild_and_screen()


