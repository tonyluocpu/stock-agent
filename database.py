#!/usr/bin/env python3
"""
Database Module for Stock Agent
================================

SQLite database for storing stocks, prices, screening results, and cache.
Phase 1: Dual-write (database + CSV/JSON files).
"""

import sqlite3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


class StockDatabase:
    """SQLite database for stock data."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file. Defaults to data/stock_agent.db
        """
        from config import DATA_DIRECTORY
        
        if db_path is None:
            self.db_path = DATA_DIRECTORY / "stock_agent.db"
        else:
            self.db_path = Path(db_path)
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables
        self._create_tables()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create all database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Stocks table (basic info)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    name TEXT,
                    sector TEXT,
                    industry TEXT,
                    market_cap BIGINT,
                    pe_ratio REAL,
                    price_to_book REAL,
                    current_price REAL,
                    dividend_yield REAL,
                    shares_outstanding BIGINT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for stocks
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(sector)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stocks_market_cap ON stocks(market_cap)
            """)
            
            # Prices table (historical data)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    frequency TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    close_price REAL,
                    volume BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(symbol) REFERENCES stocks(symbol) ON DELETE CASCADE,
                    UNIQUE(symbol, date, frequency, data_type)
                )
            """)
            
            # Create indexes for prices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prices_symbol_date 
                ON prices(symbol, date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prices_date_frequency 
                ON prices(date, frequency)
            """)
            
            # Screening results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screening_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    screening_date DATE NOT NULL,
                    composite_score REAL,
                    undervaluation_pct REAL,
                    catalyst_score INTEGER,
                    intrinsic_value REAL,
                    current_price REAL,
                    market_cap BIGINT,
                    pe_ratio REAL,
                    pb_ratio REAL,
                    passed_layers TEXT,
                    missing_layers TEXT,
                    missing_criteria TEXT,
                    catalysts TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(symbol) REFERENCES stocks(symbol) ON DELETE SET NULL
                )
            """)
            
            # Create indexes for screening_results
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_screening_symbol_date 
                ON screening_results(symbol, screening_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_screening_sector_date 
                ON screening_results(sector, screening_date)
            """)
            
            # Cache table (API responses)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for cache
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at)
            """)
            
            conn.commit()
    
    # ==================== STOCKS TABLE METHODS ====================
    
    def upsert_stock(self, symbol: str, name: Optional[str] = None,
                    sector: Optional[str] = None, industry: Optional[str] = None,
                    market_cap: Optional[int] = None, pe_ratio: Optional[float] = None,
                    price_to_book: Optional[float] = None, current_price: Optional[float] = None,
                    dividend_yield: Optional[float] = None, shares_outstanding: Optional[int] = None) -> bool:
        """
        Insert or update stock info.
        
        Args:
            symbol: Stock symbol
            name: Company name
            sector: GICS sector
            industry: Industry
            market_cap: Market capitalization
            pe_ratio: P/E ratio
            price_to_book: Price-to-book ratio
            current_price: Current stock price
            dividend_yield: Dividend yield (as percentage)
            shares_outstanding: Shares outstanding
            
        Returns:
            True if successful
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if stock exists
            cursor.execute("SELECT symbol FROM stocks WHERE symbol = ?", (symbol,))
            exists = cursor.fetchone() is not None
            
            if exists:
                # Update existing stock
                updates = []
                values = []
                
                if name is not None:
                    updates.append("name = ?")
                    values.append(name)
                if sector is not None:
                    updates.append("sector = ?")
                    values.append(sector)
                if industry is not None:
                    updates.append("industry = ?")
                    values.append(industry)
                if market_cap is not None:
                    updates.append("market_cap = ?")
                    values.append(market_cap)
                if pe_ratio is not None:
                    updates.append("pe_ratio = ?")
                    values.append(pe_ratio)
                if price_to_book is not None:
                    updates.append("price_to_book = ?")
                    values.append(price_to_book)
                if current_price is not None:
                    updates.append("current_price = ?")
                    values.append(current_price)
                if dividend_yield is not None:
                    updates.append("dividend_yield = ?")
                    values.append(dividend_yield)
                if shares_outstanding is not None:
                    updates.append("shares_outstanding = ?")
                    values.append(shares_outstanding)
                
                if updates:
                    updates.append("last_updated = CURRENT_TIMESTAMP")
                    values.append(symbol)  # Add symbol for WHERE clause
                    cursor.execute(
                        f"UPDATE stocks SET {', '.join(updates)} WHERE symbol = ?",
                        values
                    )
            else:
                # Insert new stock
                cursor.execute("""
                    INSERT INTO stocks (
                        symbol, name, sector, industry, market_cap, pe_ratio,
                        price_to_book, current_price, dividend_yield, shares_outstanding
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, name, sector, industry, market_cap, pe_ratio,
                      price_to_book, current_price, dividend_yield, shares_outstanding))
            
            return True
    
    def get_stock(self, symbol: str) -> Optional[Dict]:
        """Get stock info by symbol."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM stocks WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_stocks_by_sector(self, sector: str) -> List[Dict]:
        """Get all stocks in a sector."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM stocks WHERE sector = ? ORDER BY symbol", (sector,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== PRICES TABLE METHODS ====================
    
    def insert_prices(self, symbol: str, df: pd.DataFrame, frequency: str, data_type: str) -> int:
        """
        Insert price data from DataFrame.
        
        Args:
            symbol: Stock symbol
            df: DataFrame with columns: Date, Opening_Price, High_Price, Low_Price, Closing_Price, Volume_Traded
            frequency: 'daily', 'weekly', 'monthly', 'yearly'
            data_type: 'opening' or 'closing'
            
        Returns:
            Number of rows inserted/updated
        """
        if df is None or df.empty:
            return 0
        
        # Ensure Date column exists and is datetime
        if 'Date' not in df.columns:
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
            else:
                return 0
        
        # Convert Date to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['Date']):
            df['Date'] = pd.to_datetime(df['Date'])
        
        rows_inserted = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO prices (
                            symbol, date, frequency, data_type,
                            open_price, high_price, low_price, close_price, volume
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        symbol,
                        row['Date'].strftime('%Y-%m-%d'),
                        frequency,
                        data_type,
                        row.get('Opening_Price'),
                        row.get('High_Price'),
                        row.get('Low_Price'),
                        row.get('Closing_Price'),
                        int(row.get('Volume_Traded', 0)) if pd.notna(row.get('Volume_Traded')) else None
                    ))
                    rows_inserted += 1
                except Exception as e:
                    # Skip invalid rows but continue
                    continue
        
        return rows_inserted
    
    def get_prices(self, symbol: str, start_date: Optional[str] = None,
                   end_date: Optional[str] = None, frequency: Optional[str] = None,
                   data_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get price data for a symbol.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            frequency: 'daily', 'weekly', 'monthly', 'yearly'
            data_type: 'opening' or 'closing'
            
        Returns:
            DataFrame with price data
        """
        with self._get_connection() as conn:
            query = "SELECT date, frequency, data_type, open_price, high_price, low_price, close_price, volume FROM prices WHERE symbol = ?"
            params = [symbol]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            if frequency:
                query += " AND frequency = ?"
                params.append(frequency)
            if data_type:
                query += " AND data_type = ?"
                params.append(data_type)
            
            query += " ORDER BY date"
            
            df = pd.read_sql_query(query, conn, params=params)
            
            if not df.empty:
                df['Date'] = pd.to_datetime(df['date'])
                df = df.rename(columns={
                    'open_price': 'Opening_Price',
                    'high_price': 'High_Price',
                    'low_price': 'Low_Price',
                    'close_price': 'Closing_Price',
                    'volume': 'Volume_Traded'
                })
                df = df[['Date', 'Opening_Price', 'High_Price', 'Low_Price', 'Closing_Price', 'Volume_Traded']]
            
            return df
    
    # ==================== SCREENING RESULTS TABLE METHODS ====================
    
    def insert_screening_result(self, symbol: str, sector: str, screening_date: str,
                               composite_score: Optional[float] = None,
                               undervaluation_pct: Optional[float] = None,
                               catalyst_score: Optional[int] = None,
                               intrinsic_value: Optional[float] = None,
                               current_price: Optional[float] = None,
                               market_cap: Optional[int] = None,
                               pe_ratio: Optional[float] = None,
                               pb_ratio: Optional[float] = None,
                               passed_layers: Optional[List[str]] = None,
                               missing_layers: Optional[List[str]] = None,
                               missing_criteria: Optional[List[str]] = None,
                               catalysts: Optional[Dict] = None) -> int:
        """
        Insert screening result.
        
        Returns:
            ID of inserted row
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            passed_layers_str = json.dumps(passed_layers) if passed_layers else None
            missing_layers_str = json.dumps(missing_layers) if missing_layers else None
            missing_criteria_str = json.dumps(missing_criteria) if missing_criteria else None
            catalysts_str = json.dumps(catalysts) if catalysts else None
            
            cursor.execute("""
                INSERT INTO screening_results (
                    symbol, sector, screening_date, composite_score, undervaluation_pct,
                    catalyst_score, intrinsic_value, current_price, market_cap, pe_ratio, pb_ratio,
                    passed_layers, missing_layers, missing_criteria, catalysts
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol, sector, screening_date, composite_score, undervaluation_pct,
                catalyst_score, intrinsic_value, current_price, market_cap, pe_ratio, pb_ratio,
                passed_layers_str, missing_layers_str, missing_criteria_str, catalysts_str
            ))
            
            return cursor.lastrowid
    
    def get_screening_results(self, symbol: Optional[str] = None, sector: Optional[str] = None,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> List[Dict]:
        """Get screening results with optional filters."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM screening_results WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if sector:
                query += " AND sector = ?"
                params.append(sector)
            if start_date:
                query += " AND screening_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND screening_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY screening_date DESC, composite_score DESC"
            
            cursor.execute(query, params)
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                if result.get('passed_layers'):
                    result['passed_layers'] = json.loads(result['passed_layers'])
                if result.get('missing_layers'):
                    result['missing_layers'] = json.loads(result['missing_layers'])
                if result.get('missing_criteria'):
                    result['missing_criteria'] = json.loads(result['missing_criteria'])
                if result.get('catalysts'):
                    result['catalysts'] = json.loads(result['catalysts'])
                results.append(result)
            
            return results
    
    # ==================== CACHE TABLE METHODS ====================
    
    def set_cache(self, key: str, data: Any, expires_in_hours: int = 24) -> bool:
        """
        Set cache entry.
        
        Args:
            key: Cache key
            data: Data to cache (will be JSON serialized)
            expires_in_hours: Hours until expiry
        """
        import datetime as dt
        expires_at = datetime.now() + dt.timedelta(hours=expires_in_hours)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO cache (key, data, expires_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(data), expires_at.isoformat()))
            return True
    
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cache entry if not expired."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data, expires_at FROM cache WHERE key = ?
            """, (key,))
            row = cursor.fetchone()
            
            if row:
                expires_at = datetime.fromisoformat(row['expires_at'])
                if datetime.now() < expires_at:
                    return json.loads(row['data'])
                else:
                    # Delete expired entry
                    cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
            return None
    
    def clear_expired_cache(self):
        """Remove expired cache entries."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache WHERE expires_at < CURRENT_TIMESTAMP")
    
    # ==================== UTILITY METHODS ====================
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count stocks
            cursor.execute("SELECT COUNT(*) FROM stocks")
            stats['total_stocks'] = cursor.fetchone()[0]
            
            # Count prices
            cursor.execute("SELECT COUNT(*) FROM prices")
            stats['total_price_records'] = cursor.fetchone()[0]
            
            # Count screening results
            cursor.execute("SELECT COUNT(*) FROM screening_results")
            stats['total_screening_results'] = cursor.fetchone()[0]
            
            # Count cache entries
            cursor.execute("SELECT COUNT(*) FROM cache")
            stats['total_cache_entries'] = cursor.fetchone()[0]
            
            # Database size
            stats['database_size_mb'] = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            
            return stats


# Global database instance
_db_instance = None

def get_database() -> StockDatabase:
    """Get or create global database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = StockDatabase()
    return _db_instance

