#!/usr/bin/env python3
"""
Database Export Utility - Phase 3
==================================

Export data from database to CSV files when needed.
"""

import sys
import pandas as pd
from pathlib import Path
from typing import Optional, List
from datetime import datetime

try:
    from config import DATA_DIRECTORY
    from database import get_database
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


class DatabaseExporter:
    """Export database data to CSV files."""
    
    def __init__(self):
        """Initialize exporter."""
        self.data_dir = DATA_DIRECTORY
        self.db = get_database()
    
    def export_stock_prices(self, symbol: str, frequency: Optional[str] = None,
                           data_type: Optional[str] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Export stock prices from database to CSV file.
        
        Args:
            symbol: Stock symbol
            frequency: 'daily', 'weekly', 'monthly', 'yearly' (optional)
            data_type: 'opening' or 'closing' (optional)
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)
            output_dir: Output directory (defaults to standard data directory structure)
            
        Returns:
            Path to exported CSV file, or None if export failed
        """
        # Get data from database
        df = self.db.get_prices(symbol, start_date=start_date, end_date=end_date,
                               frequency=frequency, data_type=data_type)
        
        if df.empty:
            return None
        
        # Determine output directory
        if output_dir is None:
            # Use standard directory structure
            freq = frequency or 'daily'
            dtype = data_type or 'closing'
            output_dir = self.data_dir / freq / dtype / symbol
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        if start_date and end_date:
            start_year = start_date.split('-')[0]
            end_year = end_date.split('-')[0]
            if start_year == end_year:
                filename = f"{symbol}_{freq.upper()}_{start_year}.csv"
            else:
                filename = f"{symbol}_{freq.upper()}_{start_year}_{end_year}.csv"
        else:
            # Use date range from data
            if not df.empty and 'Date' in df.columns:
                min_date = df['Date'].min().strftime('%Y')
                max_date = df['Date'].max().strftime('%Y')
                if min_date == max_date:
                    filename = f"{symbol}_{freq.upper()}_{min_date}.csv"
                else:
                    filename = f"{symbol}_{freq.upper()}_{min_date}_{max_date}.csv"
            else:
                filename = f"{symbol}_{freq.upper()}.csv"
        
        file_path = output_dir / filename
        
        # Save to CSV
        try:
            df.to_csv(file_path, index=False)
            return file_path
        except Exception as e:
            print(f"ERROR: Failed to export to {file_path}: {e}")
            return None
    
    def export_all_prices(self, symbol: str, output_dir: Optional[Path] = None) -> List[Path]:
        """
        Export all price data for a symbol to CSV files (all frequencies and types).
        
        Returns:
            List of exported file paths
        """
        exported_files = []
        frequencies = ['daily', 'weekly', 'monthly', 'yearly']
        data_types = ['opening', 'closing']
        
        for freq in frequencies:
            for dtype in data_types:
                file_path = self.export_stock_prices(symbol, frequency=freq, data_type=dtype,
                                                    output_dir=output_dir)
                if file_path:
                    exported_files.append(file_path)
        
        return exported_files
    
    def export_screening_results(self, symbol: Optional[str] = None,
                                sector: Optional[str] = None,
                                start_date: Optional[str] = None,
                                end_date: Optional[str] = None,
                                output_file: Optional[Path] = None) -> Optional[Path]:
        """
        Export screening results to JSON file.
        
        Args:
            symbol: Filter by symbol (optional)
            sector: Filter by sector (optional)
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)
            output_file: Output file path (optional)
            
        Returns:
            Path to exported JSON file, or None if export failed
        """
        import json
        
        # Get results from database
        results = self.db.get_screening_results(symbol=symbol, sector=sector,
                                               start_date=start_date, end_date=end_date)
        
        if not results:
            return None
        
        # Determine output file
        if output_file is None:
            output_dir = self.data_dir / "screening" / "exports"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screening_results_{timestamp}.json"
            if symbol:
                filename = f"screening_results_{symbol}_{timestamp}.json"
            elif sector:
                filename = f"screening_results_{sector}_{timestamp}.json"
            
            output_file = output_dir / filename
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Export to JSON
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            return output_file
        except Exception as e:
            print(f"ERROR: Failed to export to {output_file}: {e}")
            return None


def export_stock_to_csv(symbol: str, frequency: Optional[str] = None,
                        data_type: Optional[str] = None) -> Optional[Path]:
    """Convenience function to export stock data to CSV."""
    exporter = DatabaseExporter()
    return exporter.export_stock_prices(symbol, frequency=frequency, data_type=data_type)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python database_export.py <symbol> [frequency] [data_type]")
        print("Example: python database_export.py AAPL daily closing")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    frequency = sys.argv[2] if len(sys.argv) > 2 else None
    data_type = sys.argv[3] if len(sys.argv) > 3 else None
    
    exporter = DatabaseExporter()
    
    if frequency and data_type:
        # Export specific frequency/type
        file_path = exporter.export_stock_prices(symbol, frequency=frequency, data_type=data_type)
        if file_path:
            print(f"✅ Exported to: {file_path}")
        else:
            print(f"❌ No data found for {symbol} ({frequency}, {data_type})")
    else:
        # Export all
        files = exporter.export_all_prices(symbol)
        if files:
            print(f"✅ Exported {len(files)} files for {symbol}:")
            for f in files:
                print(f"   {f}")
        else:
            print(f"❌ No data found for {symbol}")


