#!/usr/bin/env python3
"""
Fifth Layer: Stock Screening & Valuation System
================================================

Finds undervalued stocks based on investment criteria.
Modular design for easy addition of new criteria.
"""

import yfinance as yf
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys

# Import dependencies
try:
    from config import DATA_DIRECTORY
    from llm_config import get_llm_client
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}")
    sys.exit(1)


class StockScreener:
    """
    Modular stock screener with extensible criteria system.
    """
    
    def __init__(self, llm_client=None):
        """Initialize the screener."""
        self.data_dir = DATA_DIRECTORY / "screening"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM client for catalyst search
        self.llm_client = llm_client
        if not self.llm_client:
            try:
                self.llm_client = get_llm_client()
            except:
                self.llm_client = None
        
        # Criteria registry (easily extensible)
        self.criteria_registry = {
            'market_cap': self._check_market_cap,
            'price_to_book': self._check_price_to_book,
            'pe_ratio': self._check_pe_ratio,
            'shares_outstanding': self._check_shares_outstanding,
            'debt_structure': self._check_debt_structure,
            'profit_stability': self._check_profit_stability,
        }
        
        # Cache for financial data (with timestamps)
        self.data_cache = {}
        self.cache_expiry_days = {
            'price': 1,  # Daily
            'basic_info': 1,  # Daily
            'financials': 30,  # Monthly
        }
    
    def add_criterion(self, name: str, check_function):
        """
        Add a new screening criterion (for future extensibility).
        
        Args:
            name: Criterion name
            check_function: Function that takes (symbol, data) and returns (passed: bool, reason: str)
        """
        self.criteria_registry[name] = check_function
    
    def screen_stocks(self, symbols: List[str], max_matches: Optional[int] = None) -> List[Dict]:
        """
        Screen ALL stocks against basic criteria (fast checks only).
        No early stopping - screens entire list to find all matches.
        
        Args:
            symbols: List of stock symbols to screen
            max_matches: Optional limit (None = screen all stocks)
            
        Returns:
            List of ALL stocks that passed all basic criteria
        """
        matches = []
        
        print(f"Screening ALL {len(symbols)} stocks using basic metrics criteria...")
        if max_matches:
            print(f"Note: Will stop after finding {max_matches} matches")
        else:
            print("Note: Screening entire list - no early stopping")
        print()
        
        for i, symbol in enumerate(symbols, 1):
            if max_matches and len(matches) >= max_matches:
                print(f"\nStopped early at {max_matches} matches")
                break
            
            print(f"[{i}/{len(symbols)}] Checking {symbol}...", end=" ")
            
            try:
                # Get stock data (with caching) - FAST operation
                stock_data = self._get_stock_data(symbol)
                
                if not stock_data:
                    print("❌ No data")
                    continue
                
                # Check all basic criteria - FAST operation (no LLM)
                passed, results = self._check_all_criteria(symbol, stock_data)
                
                if passed:
                    matches.append({
                        'symbol': symbol,
                        'data': stock_data,
                        'criteria_results': results
                    })
                    print(f"✅ PASSED")
                else:
                    failed_criteria = [k for k, v in results.items() if not v.get('passed')]
                    print(f"❌ Failed: {', '.join(failed_criteria[:2])}")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error: {str(e)[:30]}")
                continue
        
        print()
        print(f"✅ Basic screening complete: {len(matches)}/{len(symbols)} stocks passed all criteria")
        return matches
    
    def _get_stock_data(self, symbol: str, force_refresh: bool = False) -> Optional[Dict]:
        """Get stock data with database-first approach (Phase 2) and caching fallback."""
        # Phase 2: Check database first
        try:
            from database import get_database
            from config import USE_DATABASE_READS
            
            if USE_DATABASE_READS:
                db = get_database()
                stock = db.get_stock(symbol)
                
                if stock:
                    # Check database cache table
                    cache_key = f"{symbol}_data"
                    cached_data = db.get_cache(cache_key)
                    
                    if cached_data and not force_refresh:
                        # Use cached data from database
                        return cached_data
                    
                    # Build data dict from database stock info
                    data = {
                        'symbol': stock.get('symbol'),
                        'market_cap': stock.get('market_cap'),
                        'pe_ratio': stock.get('pe_ratio'),
                        'price_to_book': stock.get('price_to_book'),
                        'shares_outstanding': stock.get('shares_outstanding'),
                        'current_price': stock.get('current_price'),
                        'sector': stock.get('sector'),
                        'industry': stock.get('industry'),
                        'dividend_yield': stock.get('dividend_yield'),
                    }
                    
                    # If we have basic data from database, use it and fetch financials if needed
                    if data.get('current_price'):
                        # Store in database cache
                        db.set_cache(cache_key, data, expires_in_hours=24)
                        # Still fetch financials from yfinance (not in database yet)
                        return self._enrich_with_financials(symbol, data)
        except Exception as e:
            # Fall back to original method if database fails
            pass
        
        # Fallback: Original cache file approach
        cache_file = self.cache_dir / f"{symbol}_data.json"
        
        # Check cache first
        if not force_refresh and cache_file.exists():
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                cache_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
                
                # Check if cache is still fresh
                age_days = (datetime.now() - cache_time).days
                
                if age_days < self.cache_expiry_days.get('basic_info', 1):
                    return cached.get('data')
        
        # Fetch fresh data from yfinance
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get basic metrics (fast)
            # Get dividend yield (convert to percentage if available)
            dividend_yield = info.get('dividendYield') or info.get('trailingAnnualDividendYield')
            if dividend_yield:
                dividend_yield = float(dividend_yield) * 100  # Convert to percentage
            
            data = {
                'symbol': symbol,
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'price_to_book': info.get('priceToBook'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'dividend_yield': dividend_yield,  # None if no dividend, percentage if available
            }
            
            # Get financials (slower, cache longer)
            try:
                balance_sheet = ticker.balance_sheet
                income_stmt = ticker.income_stmt
                
                if not balance_sheet.empty:
                    latest_bs = balance_sheet.iloc[:, 0]
                    data['total_assets'] = latest_bs.get('Total Assets', 0)
                    data['total_debt'] = latest_bs.get('Total Debt', latest_bs.get('Long Term Debt', 0))
                    data['total_equity'] = latest_bs.get('Stockholders Equity', 0)
                
                if not income_stmt.empty:
                    # Get 5 years of net income
                    net_income_history = []
                    for col in income_stmt.columns[:5]:  # Last 5 years
                        ni = income_stmt[col].get('Net Income', 0)
                        if pd.notna(ni):
                            net_income_history.append(float(ni))
                    data['net_income_history'] = net_income_history
                    
            except:
                # Financials not available, use basic data
                pass
            
            # Cache the data (both database and file - Phase 2/3 approach)
            try:
                from database import get_database
                from config import USE_DATABASE_READS
                
                if USE_DATABASE_READS:
                    db = get_database()
                    # Store in database cache
                    cache_key = f"{symbol}_data"
                    db.set_cache(cache_key, data, expires_in_hours=24)
                    
                    # Also upsert stock info to database
                    db.upsert_stock(
                        symbol=symbol,
                        name=info.get('longName'),
                        sector=info.get('sector'),
                        industry=info.get('industry'),
                        market_cap=info.get('marketCap'),
                        pe_ratio=info.get('trailingPE'),
                        price_to_book=info.get('priceToBook'),
                        current_price=info.get('currentPrice') or info.get('regularMarketPrice'),
                        dividend_yield=dividend_yield,
                        shares_outstanding=info.get('sharesOutstanding')
                    )
            except:
                pass  # Continue with file cache if database fails
            
            # Also cache to file (backup)
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            return data
            
        except Exception as e:
            return None
    
    def _enrich_with_financials(self, symbol: str, base_data: Dict) -> Dict:
        """Enrich base data with financials from yfinance (Phase 2: database has basic info, fetch financials)."""
        try:
            ticker = yf.Ticker(symbol)
            balance_sheet = ticker.balance_sheet
            income_stmt = ticker.income_stmt
            
            if not balance_sheet.empty:
                latest_bs = balance_sheet.iloc[:, 0]
                base_data['total_assets'] = latest_bs.get('Total Assets', 0)
                base_data['total_debt'] = latest_bs.get('Total Debt', latest_bs.get('Long Term Debt', 0))
                base_data['total_equity'] = latest_bs.get('Stockholders Equity', 0)
            
            if not income_stmt.empty:
                # Get 5 years of net income
                net_income_history = []
                for col in income_stmt.columns[:5]:  # Last 5 years
                    ni = income_stmt[col].get('Net Income', 0)
                    if pd.notna(ni):
                        net_income_history.append(float(ni))
                base_data['net_income_history'] = net_income_history
        except:
            pass  # Financials not available
        
        return base_data
    
    def _check_all_criteria(self, symbol: str, data: Dict) -> Tuple[bool, Dict]:
        """Check all criteria and return results."""
        results = {}
        all_passed = True
        
        for criterion_name, check_func in self.criteria_registry.items():
            try:
                passed, reason = check_func(symbol, data)
                results[criterion_name] = {
                    'passed': passed,
                    'reason': reason
                }
                if not passed:
                    all_passed = False
            except Exception as e:
                results[criterion_name] = {
                    'passed': False,
                    'reason': f"Error: {str(e)[:50]}"
                }
                all_passed = False
        
        return all_passed, results
    
    # Criteria check functions (MODERATE thresholds for better match rates)
    def _check_market_cap(self, symbol: str, data: Dict) -> Tuple[bool, str]:
        """Criterion 1: Market cap < $10 billion (MODERATE - relaxed from $5B)."""
        market_cap = data.get('market_cap')
        if market_cap is None:
            return False, "Market cap not available"
        
        passed = market_cap < 10_000_000_000  # $10B (MODERATE threshold)
        reason = f"Market cap: ${market_cap/1e9:.2f}B {'< $10B' if passed else '>= $10B'}"
        return passed, reason
    
    def _check_price_to_book(self, symbol: str, data: Dict) -> Tuple[bool, str]:
        """Criterion 2: P/B ratio < 2.0 (MODERATE - relaxed from 1.5)."""
        pb = data.get('price_to_book')
        if pb is None or pb <= 0:
            return False, "P/B ratio not available"
        
        passed = pb < 2.0  # MODERATE threshold
        reason = f"P/B: {pb:.2f} {'< 2.0' if passed else '>= 2.0'}"
        return passed, reason
    
    def _check_pe_ratio(self, symbol: str, data: Dict) -> Tuple[bool, str]:
        """Criterion 3: P/E ratio < 25 (MODERATE - relaxed from 20)."""
        pe = data.get('pe_ratio')
        if pe is None or pe <= 0:
            return False, "P/E ratio not available"
        
        passed = pe < 25  # MODERATE threshold
        reason = f"P/E: {pe:.2f} {'< 25' if passed else '>= 25'}"
        return passed, reason
    
    def _check_shares_outstanding(self, symbol: str, data: Dict) -> Tuple[bool, str]:
        """Criterion 4: Shares outstanding < 3 billion (MODERATE - relaxed from 2B)."""
        shares = data.get('shares_outstanding')
        if shares is None:
            return False, "Shares outstanding not available"
        
        passed = shares < 3_000_000_000  # 3B shares (MODERATE threshold)
        reason = f"Shares: {shares/1e9:.2f}B {'< 3B' if passed else '>= 3B'}"
        return passed, reason
    
    def _check_debt_structure(self, symbol: str, data: Dict) -> Tuple[bool, str]:
        """Criterion 5: Debt < 70% of assets (MODERATE - relaxed from 65%)."""
        total_debt = data.get('total_debt', 0)
        total_assets = data.get('total_assets', 0)
        
        if total_assets == 0:
            # Try equity-based calculation
            total_equity = data.get('total_equity', 0)
            if total_equity == 0:
                return False, "Debt data not available"
            debt_ratio = total_debt / (total_debt + total_equity) if (total_debt + total_equity) > 0 else 1.0
        else:
            debt_ratio = total_debt / total_assets
        
        passed = debt_ratio < 0.70  # MODERATE threshold (70%)
        reason = f"Debt ratio: {debt_ratio*100:.1f}% {'< 70%' if passed else '>= 70%'}"
        return passed, reason
    
    def _check_profit_stability(self, symbol: str, data: Dict) -> Tuple[bool, str]:
        """Criterion 6: Profit decline < 25% in any year (MODERATE - relaxed from 20%)."""
        net_income_history = data.get('net_income_history', [])
        
        if len(net_income_history) < 2:
            return False, "Insufficient profit history"
        
        # Check year-over-year changes
        for i in range(1, len(net_income_history)):
            prev = net_income_history[i-1]
            curr = net_income_history[i]
            
            if prev == 0:
                continue
            
            decline = (prev - curr) / abs(prev)
            if decline > 0.25:  # MODERATE threshold (25%)
                return False, f"Profit declined {decline*100:.1f}% year {i}"
        
        return True, "Profit stable (no >25% declines)"
    
    def get_sector_stocks(self, sector: str) -> List[str]:
        """
        Get stocks for a sector from comprehensive SEC EDGAR database.
        Always connects to database (cached locally, rebuilt weekly).
        """
        sector_db_file = self.data_dir / "sector_database.json"
        
        needs_rebuild = True
        if sector_db_file.exists():
            try:
                with open(sector_db_file, 'r') as f:
                    sector_db = json.load(f)
                needs_rebuild = sector_db.get('total_stocks', 0) <= 0
            except Exception:
                needs_rebuild = True

        if needs_rebuild:
            print(f"Sector database not found. Building comprehensive database from SEC EDGAR...")
            print("   This will process ALL US stocks (thousands) - first time only, then cached")
            from sector_database import SectorDatabaseBuilder
            builder = SectorDatabaseBuilder()
            builder.build_database(max_stocks_per_sector=None, use_all_stocks=True)
        
        with open(sector_db_file, 'r') as f:
            sector_db = json.load(f)
        
        # Database structure: {"sectors": {"Technology": [...], ...}, "total_stocks": 556}
        sectors = sector_db.get('sectors', {})
        stocks = sectors.get(sector, [])
        
        total_in_db = sector_db.get('total_stocks', 0)
        print(f"📊 Database contains {total_in_db:,} total stocks across all sectors")
        print(f"📊 {sector} sector: {len(stocks):,} stocks available for screening")
        
        return stocks


class ValuationEngine:
    """Calculate intrinsic value using DCF and Relative Valuation."""
    
    def __init__(self):
        """Initialize valuation engine."""
        pass
    
    def calculate_intrinsic_value(self, symbol: str, stock_data: Dict) -> Optional[float]:
        """
        Calculate intrinsic value using DCF + Relative Valuation average.
        
        Args:
            symbol: Stock symbol
            stock_data: Stock data dictionary
            
        Returns:
            Intrinsic value per share or None
        """
        dcf_value = self._calculate_dcf(symbol, stock_data)
        relative_value = self._calculate_relative_valuation(symbol, stock_data)
        
        if dcf_value is None and relative_value is None:
            return None
        
        if dcf_value is None:
            return relative_value
        
        if relative_value is None:
            return dcf_value
        
        # Average of both methods
        return (dcf_value + relative_value) / 2
    
    def _calculate_dcf(self, symbol: str, data: Dict) -> Optional[float]:
        """Calculate DCF intrinsic value."""
        try:
            ticker = yf.Ticker(symbol)
            cash_flow = ticker.cashflow
            
            if cash_flow.empty:
                return None
            
            # Get operating cash flow history
            ocf_history = []
            for col in cash_flow.columns[:5]:  # Last 5 years
                ocf = cash_flow[col].get('Total Cash From Operating Activities', 0)
                if pd.notna(ocf) and ocf > 0:
                    ocf_history.append(float(ocf))
            
            if len(ocf_history) < 3:
                return None
            
            # Simple DCF: Average OCF * growth factor / discount rate
            avg_ocf = sum(ocf_history) / len(ocf_history)
            growth_rate = 0.05  # Conservative 5% growth
            discount_rate = 0.10  # 10% WACC
            
            # Terminal value approach (simplified)
            terminal_value = avg_ocf * (1 + growth_rate) / (discount_rate - growth_rate)
            
            # Get shares outstanding
            shares = data.get('shares_outstanding', 1)
            if shares == 0:
                return None
            
            intrinsic_value = terminal_value / shares
            
            return intrinsic_value
            
        except Exception as e:
            return None
    
    def _calculate_relative_valuation(self, symbol: str, data: Dict) -> Optional[float]:
        """Calculate relative valuation based on industry peers."""
        try:
            sector = data.get('sector')
            if not sector:
                return None
            
            # Get sector average P/E
            # Simplified: Use current P/E and assume fair value at sector average
            current_pe = data.get('pe_ratio')
            current_price = data.get('current_price')
            
            if not current_pe or not current_price:
                return None
            
            # Assume sector average P/E is 20 (can be improved with actual sector data)
            sector_avg_pe = 20
            
            # Relative value = (Current Price / Current P/E) * Sector Avg P/E
            earnings_per_share = current_price / current_pe
            relative_value = earnings_per_share * sector_avg_pe
            
            return relative_value
            
        except Exception as e:
            return None


class CatalystFinder:
    """Find and SCORE catalysts for undervalued stocks."""
    
    def __init__(self, llm_client=None):
        """Initialize catalyst finder."""
        self.llm_client = llm_client
    
    def find_and_score_catalysts(self, symbol: str, stock_data: Dict) -> Dict:
        """
        Search for catalysts and return a QUALITY SCORE (1-10).
        
        Args:
            symbol: Stock symbol
            stock_data: Hardcoded stock data to provide context
            
        Returns:
            Dict with catalyst information and score (1-10)
        """
        result = {
            'catalysts_found': [],
            'catalyst_score': 1,  # Default: no catalysts
            'summary': 'No significant catalysts found.'
        }
        
        if not self.llm_client:
            return result
        
        # Build prompt with HARDCODED stock data context
        sector = stock_data.get('sector', 'Unknown')
        market_cap = stock_data.get('market_cap', 0)
        mc_str = f"${market_cap/1e9:.2f}B" if market_cap else "N/A"
        
        prompt = f"""Analyze recent catalysts for {symbol}:

STOCK CONTEXT:
- Sector: {sector}
- Market Cap: {mc_str}

Search for these catalyst types:
1. New partnerships or agreements
2. New management or restructuring  
3. Acquisition target or merger activity
4. Industry-wide catalysts (government policies, Fed decisions, global trends)

For each catalyst found, explain briefly.

Then provide an overall CATALYST STRENGTH SCORE from 1-10:
- 1-3: No significant catalysts found
- 4-6: Minor catalysts (small partnerships, industry tailwinds)
- 7-8: Strong catalysts (major partnership, management change)
- 9-10: Exceptional catalysts (M&A target, major policy benefit)

Respond in JSON format ONLY:
{{"catalysts_found": ["catalyst 1", "catalyst 2"], "catalyst_score": 7, "summary": "Brief explanation"}}"""
        
        try:
            response = self.llm_client.call(prompt, max_tokens=500)
            if response:
                # Try to parse JSON response
                import json
                response = response.strip()
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                
                try:
                    parsed = json.loads(response)
                    result['catalysts_found'] = parsed.get('catalysts_found', [])
                    result['catalyst_score'] = max(1, min(10, int(parsed.get('catalyst_score', 1))))
                    result['summary'] = parsed.get('summary', response)
                except json.JSONDecodeError:
                    # Fallback: use raw response as summary, estimate score
                    result['summary'] = response
                    # Simple heuristic: if response mentions specific catalysts, score higher
                    response_lower = response.lower()
                    if 'acquisition' in response_lower or 'merger' in response_lower:
                        result['catalyst_score'] = 8
                    elif 'partnership' in response_lower or 'deal' in response_lower:
                        result['catalyst_score'] = 6
                    elif 'no significant' in response_lower or 'no major' in response_lower:
                        result['catalyst_score'] = 2
                    else:
                        result['catalyst_score'] = 4
        except Exception as e:
            pass
        
        return result
    
    def find_catalysts(self, symbol: str) -> Dict:
        """Legacy method - calls find_and_score_catalysts with empty data."""
        return self.find_and_score_catalysts(symbol, {})


class FifthLayerScreening:
    """Main interface for fifth layer screening with COMPOSITE RANKING and WEEKLY REFRESH."""
    
    # Constants for ranking
    UNDERVALUATION_WEIGHT = 0.70  # 70% weight for undervaluation
    CATALYST_WEIGHT = 0.30        # 30% weight for catalyst quality
    DIVIDEND_PENALTY_WEIGHT = 0.10  # 10% penalty for dividend yield (high dividends = lower score)
    TOP_N_RESULTS = 5             # Return exactly 5 stocks per sector
    REFRESH_INTERVAL_DAYS = 7     # Weekly refresh
    
    def __init__(self, llm_client=None):
        """Initialize fifth layer screening system."""
        self.screener = StockScreener(llm_client)
        self.valuator = ValuationEngine()
        self.catalyst_finder = CatalystFinder(llm_client)
        self.data_dir = DATA_DIRECTORY / "screening"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _sector_database_is_usable(self) -> bool:
        """Return True when the sector database exists and contains real data."""
        sector_db_file = self.data_dir / "sector_database.json"
        if not sector_db_file.exists():
            return False

        try:
            with open(sector_db_file, 'r') as f:
                sector_db = json.load(f)
            return sector_db.get('total_stocks', 0) > 0
        except Exception:
            return False
    
    def _check_refresh_needed(self) -> bool:
        """Check if data refresh is needed (weekly)."""
        timestamp_file = self.data_dir / "last_refresh.json"
        
        if not timestamp_file.exists():
            return True
        
        try:
            with open(timestamp_file, 'r') as f:
                data = json.load(f)
            
            last_refresh = datetime.fromisoformat(data.get('last_refresh', '2000-01-01'))
            days_since = (datetime.now() - last_refresh).days
            
            return days_since >= self.REFRESH_INTERVAL_DAYS
        except Exception:
            return True
    
    def _update_refresh_timestamp(self):
        """Update the last refresh timestamp."""
        timestamp_file = self.data_dir / "last_refresh.json"
        try:
            with open(timestamp_file, 'w') as f:
                json.dump({
                    'last_refresh': datetime.now().isoformat(),
                    'refresh_interval_days': self.REFRESH_INTERVAL_DAYS
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not update refresh timestamp: {e}")
    
    def _refresh_all_data(self):
        """Refresh sector database and clear screening cache."""
        print("🔄 Data refresh triggered (weekly refresh)")
        print("-" * 70)

        refresh_succeeded = False
        
        # 1. Rebuild sector database from SEC EDGAR (ALL stocks, comprehensive)
        print("📊 Rebuilding sector database from SEC EDGAR...")
        print("   Processing ALL US stocks (thousands) - this may take 15-30 minutes")
        try:
            from sector_database import SectorDatabaseBuilder
            builder = SectorDatabaseBuilder()
            sector_db = builder.build_database(max_stocks_per_sector=None, use_all_stocks=True)
            total_stocks = sum(len(stocks) for stocks in sector_db.values())
            refresh_succeeded = total_stocks > 0
            if refresh_succeeded:
                print(f"   ✅ Sector database rebuilt with {total_stocks:,} stocks")
            else:
                print("   ⚠️ Sector database rebuild returned no stocks")
        except ImportError:
            print("   ⚠️ Sector database builder not available")
        except Exception as e:
            print(f"   ⚠️ Sector database rebuild failed: {e}")

        if not refresh_succeeded:
            print("⚠️ Refresh aborted before cache clear or timestamp update.")
            print("   Existing sector data will be kept as-is.")
            print()
            return False
        
        # 2. Clear screening cache (force fresh yfinance data)
        print("🗑️ Clearing screening cache...")
        cache_dir = self.data_dir / "cache"
        if cache_dir.exists():
            deleted_count = 0
            for cache_file in cache_dir.glob("*_data.json"):
                try:
                    cache_file.unlink()
                    deleted_count += 1
                except:
                    pass
            print(f"   ✅ Deleted {deleted_count} cached files")
        else:
            print("   ✅ No cache to clear")
        
        # Update timestamp
        self._update_refresh_timestamp()
        print("✅ Data refresh complete!")
        print(f"   Next refresh: {self.REFRESH_INTERVAL_DAYS} days from now")
        print()
        return True
    
    def _calculate_composite_score(self, undervaluation_pct: float, catalyst_score: int, dividend_yield: float = 0) -> float:
        """
        Calculate composite ranking score.
        
        Formula: 70% undervaluation + 30% catalyst - 10% dividend penalty
        
        Rationale: High dividends can make stocks appear undervalued when they're not.
        Dividend payments reduce stock price and book value, creating false undervaluation signals.
        We penalize high dividend yields to correct for this effect.
        
        Normalization:
        - Undervaluation: cap at 100% for scoring (actual % still shown)
        - Catalyst: 1-10 scale, multiply by 10 for 10-100 range
        - Dividend penalty: cap at 10% yield, scale to 0-100 range, then SUBTRACT
        """
        # Normalize undervaluation (cap at 100 for scoring purposes)
        underval_score = min(undervaluation_pct, 100.0)
        
        # Normalize catalyst (1-10 becomes 10-100)
        catalyst_normalized = catalyst_score * 10
        
        # Normalize dividend penalty (cap at 10% yield, scale to 0-100)
        # 0% = 0 penalty, 2% = 20 penalty, 5% = 50 penalty, 10%+ = 100 penalty (max)
        dividend_penalty = min(dividend_yield or 0, 10.0) * 10
        
        # Weighted composite: ADD undervaluation and catalyst, SUBTRACT dividend penalty
        composite = (underval_score * self.UNDERVALUATION_WEIGHT) + \
                    (catalyst_normalized * self.CATALYST_WEIGHT) - \
                    (dividend_penalty * self.DIVIDEND_PENALTY_WEIGHT)
        
        # Ensure score doesn't go negative (floor at 0)
        return max(composite, 0)
    
    def screen_sector(self, sector: str) -> List[Dict]:
        """
        Screen a sector and find TOP 5 undervalued stocks ranked by COMPOSITE SCORE.
        
        Composite Score = 70% Undervaluation + 30% Catalyst Quality
        
        Includes WEEKLY AUTO-REFRESH: If data is older than 7 days, automatically
        refreshes sector database and clears screening cache.
        
        Args:
            sector: Sector name (e.g., "Technology")
            
        Returns:
            List of top 5 undervalued stocks with composite scores
        """
        # Check if weekly refresh is needed
        if self._check_refresh_needed():
            self._refresh_all_data()
        
        print(f"=" * 70)
        print(f"Screening Sector: {sector}")
        print(f"Ranking: {int(self.UNDERVALUATION_WEIGHT*100)}% Undervaluation + {int(self.CATALYST_WEIGHT*100)}% Catalyst - {int(self.DIVIDEND_PENALTY_WEIGHT*100)}% Dividend Penalty")
        print(f"=" * 70)
        print()
        
        # Get sector stocks
        symbols = self.screener.get_sector_stocks(sector)
        if not symbols:
            return []
        
        print(f"Found {len(symbols)} stocks in {sector} sector")
        print()
        
        # Step 1: Basic screening - Screen ALL stocks using simple metrics first (FAST)
        print("Step 1: Basic Screening - ALL Stocks (Simple Metrics Criteria)")
        print("Using fast checks only - no expensive operations yet")
        print("-" * 70)
        matches = self.screener.screen_stocks(symbols, max_matches=None)  # Screen ALL, no limit
        
        if not matches:
            print("No stocks passed basic screening criteria.")
            print()
            print("MODERATE criteria used:")
            print("  1. Market cap < $10B")
            print("  2. P/B ratio < 2.0")
            print("  3. P/E ratio < 25")
            print("  4. Shares outstanding < 3B")
            print("  5. Debt < 70%")
            print("  6. Profit stability (no >25% decline)")
            print()
            print("💡 Try a different sector!")
            return []
        
        print()
        print(f"Step 2: Advanced Analysis (Intrinsic Value) - {len(matches)} stocks")
        print("Now doing expensive operations on filtered set only")
        print("-" * 70)
        
        # Step 2: Calculate intrinsic value for ALL passing stocks (filtered set)
        # Track stocks at each layer to fill up to 5 if needed
        undervalued_stocks = []  # Passed all layers
        passed_basic_only = []   # Passed Step 1 but failed Step 2
        
        for match in matches:
            symbol = match['symbol']
            data = match['data']
            current_price = data.get('current_price')
            
            if not current_price:
                # Track as passed basic only
                match['missing_layers'] = ['intrinsic_value', 'catalyst']
                match['missing_criteria'] = ['Current price not available']
                passed_basic_only.append(match)
                continue
            
            intrinsic_value = self.valuator.calculate_intrinsic_value(symbol, data)
            
            if intrinsic_value and intrinsic_value > current_price:
                undervaluation_pct = ((intrinsic_value - current_price) / current_price) * 100
                
                match['intrinsic_value'] = intrinsic_value
                match['current_price'] = current_price
                match['undervaluation_pct'] = undervaluation_pct
                match['passed_layers'] = ['basic_criteria', 'intrinsic_value']
                
                undervalued_stocks.append(match)
                print(f"{symbol}: Intrinsic ${intrinsic_value:.2f} > Price ${current_price:.2f} ({undervaluation_pct:.1f}% undervalued)")
            else:
                # Passed basic but not undervalued
                match['missing_layers'] = ['intrinsic_value', 'catalyst']
                if intrinsic_value:
                    match['missing_criteria'] = [f"Intrinsic value ${intrinsic_value:.2f} <= Current price ${current_price:.2f}"]
                else:
                    match['missing_criteria'] = ['Intrinsic value calculation failed']
                passed_basic_only.append(match)
                intrinsic_str = f"${intrinsic_value:.2f}" if intrinsic_value else "N/A"
                print(f"{symbol}: Intrinsic {intrinsic_str} <= Price ${current_price:.2f} (not undervalued)")
        
        print()
        print(f"Step 3: Catalyst Search & Scoring - {len(undervalued_stocks)} undervalued stocks")
        print("Final expensive operation - LLM catalyst search on filtered set")
        print("-" * 70)
        
        # Step 3: Find and SCORE catalysts for ALL undervalued stocks (filtered set)
        for stock in undervalued_stocks:
            symbol = stock['symbol']
            print(f"Analyzing catalysts for {symbol}...", end=" ")
            catalyst_result = self.catalyst_finder.find_and_score_catalysts(symbol, stock['data'])
            stock['catalyst_score'] = catalyst_result.get('catalyst_score', 1)
            stock['catalysts'] = catalyst_result
            stock['passed_layers'].append('catalyst')
            print(f"Score: {stock['catalyst_score']}/10 ✅")
        
        print()
        print("Step 4: Composite Ranking & Filling to 5 Stocks")
        print("-" * 70)
        
        # Step 4: Calculate composite score for stocks that passed all layers
        for stock in undervalued_stocks:
            # Get dividend yield from stock data
            dividend_yield = stock.get('data', {}).get('dividend_yield', 0) or 0
            stock['dividend_yield'] = dividend_yield
            
            stock['composite_score'] = self._calculate_composite_score(
                stock['undervaluation_pct'],
                stock['catalyst_score'],
                dividend_yield
            )
            div_str = f"{dividend_yield:.2f}%" if dividend_yield else "0%"
            print(f"{stock['symbol']}: {stock['undervaluation_pct']:.1f}% underval + {stock['catalyst_score']}/10 catalyst - {div_str} div penalty = {stock['composite_score']:.1f} composite")
        
        # Sort by composite score (highest first)
        undervalued_stocks.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
        
        # Always try to return 5 stocks
        final_results = []
        
        # First, add stocks that passed all layers (up to 5)
        final_results.extend(undervalued_stocks[:self.TOP_N_RESULTS])
        
        # If we have fewer than 5, fill with stocks that passed basic criteria only
        if len(final_results) < self.TOP_N_RESULTS and passed_basic_only:
            needed = self.TOP_N_RESULTS - len(final_results)
            # Sort basic-only stocks by market cap (smaller = better for our criteria)
            passed_basic_only.sort(key=lambda x: x['data'].get('market_cap', float('inf')))
            final_results.extend(passed_basic_only[:needed])
        
        print()
        print(f"✅ Returning {len(final_results)} stocks:")
        print(f"   - {len(undervalued_stocks)} passed all layers")
        if len(final_results) > len(undervalued_stocks):
            print(f"   - {len(final_results) - len(undervalued_stocks)} passed basic criteria only (showing missing layers)")
        
        return final_results
    
    def format_results(self, stocks: List[Dict]) -> str:
        """Format screening results with layer status and missing criteria."""
        if not stocks:
            return "No stocks found matching basic criteria."
        
        output = []
        output.append("=" * 70)
        output.append(f"TOP {len(stocks)} STOCKS - RANKED BY COMPOSITE SCORE")
        output.append("Ranking: 70% Undervaluation + 30% Catalyst - 10% Dividend Penalty")
        output.append("=" * 70)
        output.append("")
        
        for i, stock in enumerate(stocks, 1):
            symbol = stock['symbol']
            data = stock['data']
            intrinsic = stock.get('intrinsic_value', 0)
            price = stock.get('current_price', 0)
            underval_pct = stock.get('undervaluation_pct', 0)
            catalyst_score = stock.get('catalyst_score', 1)
            composite_score = stock.get('composite_score', 0)
            passed_layers = stock.get('passed_layers', [])
            missing_layers = stock.get('missing_layers', [])
            missing_criteria = stock.get('missing_criteria', [])
            
            output.append(f"**{i}. {symbol}**")
            
            # Show layer status
            if 'catalyst' in passed_layers:
                output.append(f"   ✅ PASSED ALL LAYERS")
                output.append(f"   COMPOSITE SCORE: {composite_score:.1f}/100")
            elif 'intrinsic_value' in passed_layers:
                output.append(f"   ⚠️ PASSED: Basic Criteria + Intrinsic Value")
                output.append(f"   ❌ MISSING: Catalyst Search")
            else:
                output.append(f"   ⚠️ PASSED: Basic Criteria Only")
                output.append(f"   ❌ MISSING: Intrinsic Value + Catalyst Search")
            
            output.append("")
            
            # Show what passed
            if 'basic_criteria' in passed_layers:
                output.append(f"   ✅ Layer 1: Basic Criteria (6 metrics)")
            if 'intrinsic_value' in passed_layers:
                output.append(f"   ✅ Layer 2: Intrinsic Value")
                output.append(f"      Undervaluation: {underval_pct:.1f}%")
                output.append(f"      Intrinsic Value: ${intrinsic:.2f}")
                output.append(f"      Current Price: ${price:.2f}")
            if 'catalyst' in passed_layers:
                output.append(f"   ✅ Layer 3: Catalyst Search")
                output.append(f"      Catalyst Score: {catalyst_score}/10")
                catalysts = stock.get('catalysts', {})
                catalyst_summary = catalysts.get('summary', 'No significant catalysts found.')
                if len(catalyst_summary) > 150:
                    catalyst_summary = catalyst_summary[:147] + "..."
                output.append(f"      {catalyst_summary}")
            
            # Show what's missing
            if missing_layers:
                output.append("")
                output.append(f"   ❌ Missing Layers:")
                for layer in missing_layers:
                    if layer == 'intrinsic_value':
                        output.append(f"      - Layer 2: Intrinsic Value Calculation")
                    elif layer == 'catalyst':
                        output.append(f"      - Layer 3: Catalyst Search")
                
                if missing_criteria:
                    output.append(f"   ❌ Missing Criteria:")
                    for crit in missing_criteria:
                        output.append(f"      - {crit}")
            
            output.append("")
            output.append(f"   📈 Key Metrics:")
            output.append(f"      Market Cap: ${data.get('market_cap', 0)/1e9:.2f}B")
            output.append(f"      P/E Ratio: {data.get('pe_ratio', 0):.2f}")
            output.append(f"      P/B Ratio: {data.get('price_to_book', 0):.2f}")
            # Add dividend yield to Key Metrics
            div_yield = data.get('dividend_yield')
            div_str = f"{div_yield:.2f}%" if div_yield else "None"
            output.append(f"      Dividend Yield: {div_str}")
            output.append(f"      Sector: {data.get('sector', 'Unknown')}")
            output.append("")
            output.append("-" * 70)
            output.append("")
        
        output.append("")
        output.append("💡 Legend:")
        output.append("   ✅ = Passed this layer/criteria")
        output.append("   ❌ = Missing this layer/criteria")
        output.append("   Stocks are ranked by composite score (if available) or market cap")
        
        return "\n".join(output)


if __name__ == "__main__":
    # Example usage
    screening = FifthLayerScreening()
    results = screening.screen_sector("Technology")
    print(screening.format_results(results))
