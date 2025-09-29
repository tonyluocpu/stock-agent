
import polars as pl
import pandas as pd
from datetime import datetime, timedelta
import re
import requests
from pathlib import Path
import json
from typing import Dict, List, Tuple, Optional
import time
import investpy
import random
import numpy as np

class StockDataEvaluator:
    """
    Evaluates stock data quality and validates against expected patterns.
    """
    
    def __init__(self):
        """Initialize the evaluator."""
        self.validation_results = {}
        
    def validate_price_logic(self, file_path: str) -> Dict:
        """
        Validate that opening <= high and closing <= high for all rows.
        
        Args:
            file_path: Path to the CSV file to validate
            
        Returns:
            Dict with validation results
        """
        try:
            # Read data using polars for speed
            df = pl.read_csv(file_path)
            
            # Check if required columns exist (handle both original and renamed columns)
            required_cols = ['Open', 'High', 'Low', 'Close']
            renamed_cols = ['Opening_Price', 'High_Price', 'Low_Price', 'Closing_Price']
            
            # Check for either original or renamed columns
            available_cols = []
            for orig, renamed in zip(required_cols, renamed_cols):
                if orig in df.columns:
                    available_cols.append(orig)
                elif renamed in df.columns:
                    available_cols.append(renamed)
                else:
                    return {
                        'status': 'error',
                        'message': f'Missing required columns: {orig} or {renamed} not found',
                        'violations': []
                    }
            
            # Map column names for processing
            col_mapping = {}
            for orig, renamed in zip(required_cols, renamed_cols):
                if orig in df.columns:
                    col_mapping[orig] = orig
                elif renamed in df.columns:
                    col_mapping[orig] = renamed
            
            violations = []
            
            # Check opening <= high using mapped column names
            open_col = col_mapping['Open']
            high_col = col_mapping['High']
            close_col = col_mapping['Close']
            
            open_high_violations = df.filter(pl.col(open_col) > pl.col(high_col))
            if len(open_high_violations) > 0:
                violations.extend([
                    {
                        'type': 'opening_high_violation',
                        'date': row['Date'] if 'Date' in row else 'unknown',
                        'opening': row[open_col],
                        'high': row[high_col],
                        'row_index': idx
                    }
                    for idx, row in enumerate(open_high_violations.iter_rows(named=True))
                ])
            
            # Check closing <= high
            close_high_violations = df.filter(pl.col(close_col) > pl.col(high_col))
            if len(close_high_violations) > 0:
                violations.extend([
                    {
                        'type': 'closing_high_violation',
                        'date': row['Date'] if 'Date' in row else 'unknown',
                        'closing': row[close_col],
                        'high': row[high_col],
                        'row_index': idx
                    }
                    for idx, row in enumerate(close_high_violations.iter_rows(named=True))
                ])
            
            return {
                'status': 'success' if len(violations) == 0 else 'violations_found',
                'total_rows': len(df),
                'violations': violations,
                'violation_count': len(violations)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error reading file: {str(e)}',
                'violations': []
            }
    
    def validate_frequency(self, file_path: str, expected_frequency: str) -> Dict:
        """
        Validate that data intervals match expected frequency.
        
        Args:
            file_path: Path to the CSV file
            expected_frequency: 'daily', 'weekly', 'monthly', 'yearly'
            
        Returns:
            Dict with frequency validation results
        """
        try:
            df = pl.read_csv(file_path)
            
            if 'Date' not in df.columns:
                return {
                    'status': 'error',
                    'message': 'Date column not found',
                    'intervals': []
                }
            
            # Convert to datetime and sort
            df = df.with_columns(pl.col('Date').str.to_datetime())
            df = df.sort('Date')
            
            # Calculate intervals between consecutive dates
            dates = df['Date'].to_list()
            intervals = []
            
            for i in range(1, len(dates)):
                interval = (dates[i] - dates[i-1]).days
                intervals.append({
                    'from_date': dates[i-1],
                    'to_date': dates[i],
                    'days': interval
                })
            
            # Define expected intervals (in days)
            expected_intervals = {
                'daily': (1, 3),      # 1-3 days (accounting for weekends)
                'weekly': (5, 7),      # 5-7 days
                'monthly': (28, 31),   # 28-31 days
                'yearly': (365, 366)   # 365-366 days
            }
            
            if expected_frequency not in expected_intervals:
                return {
                    'status': 'error',
                    'message': f'Unknown frequency: {expected_frequency}',
                    'intervals': intervals
                }
            
            min_expected, max_expected = expected_intervals[expected_frequency]
            
            # Check for intervals outside expected range
            suspicious_intervals = [
                interval for interval in intervals
                if interval['days'] < min_expected or interval['days'] > max_expected
            ]
            
            return {
                'status': 'success' if len(suspicious_intervals) == 0 else 'suspicious_intervals',
                'expected_frequency': expected_frequency,
                'expected_range': f'{min_expected}-{max_expected} days',
                'total_intervals': len(intervals),
                'suspicious_intervals': suspicious_intervals,
                'all_intervals': intervals
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error validating frequency: {str(e)}',
                'intervals': []
            }
    
    def verify_trading_days(self, suspicious_dates: List[datetime]) -> Dict:
        """
        Use web search to verify if suspicious dates are actually non-trading days.
        
        Args:
            suspicious_dates: List of dates that might be non-trading days
            
        Returns:
            Dict with verification results
        """
        verification_results = {}
        
        for date in suspicious_dates:
            date_str = date.strftime('%Y-%m-%d')
            
            # Check if it's a weekend
            if date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                verification_results[date_str] = {
                    'is_trading_day': False,
                    'reason': 'Weekend',
                    'verified': True
                }
                continue
            
            # For now, we'll implement a simple check
            # In a full implementation, you'd use web search API
            verification_results[date_str] = {
                'is_trading_day': True,  # Default assumption
                'reason': 'Not verified via web search',
                'verified': False
            }
        
        return {
            'status': 'completed',
            'verifications': verification_results
        }
    
    def evaluate_data_file(self, file_path: str, expected_frequency: str) -> Dict:
        """
        Comprehensive evaluation of a stock data file.
        
        Args:
            file_path: Path to the CSV file
            expected_frequency: Expected frequency of the data
            
        Returns:
            Dict with complete evaluation results
        """
        print(f"Evaluating file: {file_path}")
        
        # Price logic validation
        price_results = self.validate_price_logic(file_path)
        print(f"Price logic: {price_results['status']}")
        
        # Frequency validation
        frequency_results = self.validate_frequency(file_path, expected_frequency)
        print(f"Frequency validation: {frequency_results['status']}")
        
        # Trading day verification for suspicious intervals
        trading_day_results = {}
        if frequency_results.get('suspicious_intervals'):
            suspicious_dates = [
                interval['from_date'] for interval in frequency_results['suspicious_intervals']
            ]
            trading_day_results = self.verify_trading_days(suspicious_dates)
        
        # Compile results
        evaluation = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'price_validation': price_results,
            'frequency_validation': frequency_results,
            'trading_day_verification': trading_day_results,
            'overall_status': self._determine_overall_status(price_results, frequency_results)
        }
        
        return evaluation
    
    def _determine_overall_status(self, price_results: Dict, frequency_results: Dict) -> str:
        """Determine overall evaluation status."""
        if price_results['status'] == 'error' or frequency_results['status'] == 'error':
            return 'error'
        elif price_results['status'] == 'violations_found' or frequency_results['status'] == 'suspicious_intervals':
            return 'issues_found'
        else:
            return 'passed'
    
    def generate_evaluation_report(self, evaluation_results: Dict) -> str:
        """
        Generate a human-readable evaluation report.
        
        Args:
            evaluation_results: Results from evaluate_data_file
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("STOCK DATA EVALUATION REPORT")
        report.append("=" * 60)
        report.append(f"File: {evaluation_results['file_path']}")
        report.append(f"Timestamp: {evaluation_results['timestamp']}")
        report.append(f"Overall Status: {evaluation_results['overall_status'].upper()}")
        report.append("")
        
        # Price validation results
        price = evaluation_results['price_validation']
        report.append("PRICE LOGIC VALIDATION:")
        if price['status'] == 'success':
            report.append("PASS: All price logic checks passed")
        elif price['status'] == 'violations_found':
            report.append(f"FAIL: Found {price['violation_count']} price logic violations:")
            for violation in price['violations'][:5]:  # Show first 5
                report.append(f"   - {violation['type']}: {violation}")
            if len(price['violations']) > 5:
                report.append(f"   ... and {len(price['violations']) - 5} more")
        else:
            report.append(f"ERROR: {price['message']}")
        
        report.append("")
        
        # Frequency validation results
        freq = evaluation_results['frequency_validation']
        report.append("FREQUENCY VALIDATION:")
        if freq['status'] == 'success':
            report.append(f"PASS: Frequency validation passed ({freq['expected_frequency']})")
        elif freq['status'] == 'suspicious_intervals':
            report.append(f"WARNING: Found {len(freq['suspicious_intervals'])} suspicious intervals:")
            for interval in freq['suspicious_intervals'][:3]:  # Show first 3
                report.append(f"   - {interval['from_date']} to {interval['to_date']}: {interval['days']} days")
            if len(freq['suspicious_intervals']) > 3:
                report.append(f"   ... and {len(freq['suspicious_intervals']) - 3} more")
        else:
            report.append(f"ERROR: {freq['message']}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

class WebScrapingValidator:
    """
    Validates stock data accuracy by comparing with investpy data source.
    Implements the 6-component validation process in order.
    """
    
    def __init__(self):
        """Initialize the web scraping validator."""
        self.validation_results = {}
        
    def validate_with_investpy(self, symbol: str, file_path: str, time_frame: Dict, data_frequency: str) -> Dict:
        """
        Complete web-scraping validation process.
        
        Args:
            symbol: Stock symbol
            file_path: Path to the CSV file to validate
            time_frame: Time frame dictionary with start_date and end_date
            data_frequency: Data frequency (daily, weekly, monthly, yearly)
            
        Returns:
            Dict with validation results
        """
        print(f"\nRunning web-scraping validation for {symbol}...")
        print("=" * 60)
        
        # Read the original data
        try:
            original_data = pl.read_csv(file_path)
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to read original data: {str(e)}',
                'component_failures': []
            }
        
        # Component 1: Symbol and Date Validation
        result1 = self._validate_symbol_and_dates(symbol, time_frame)
        if not result1['status'] == 'success':
            return self._handle_validation_failure(1, "Symbol and Date Validation", result1['message'])
        
        # Component 2: Row Count Validation
        result2 = self._validate_row_counts(original_data, symbol, time_frame, data_frequency)
        if not result2['status'] == 'success':
            return self._handle_validation_failure(2, "Row Count Validation", result2['message'])
        
        investpy_data = result2['investpy_data']  # Get the data for further validation
        
        # Component 3: Volume Validation
        result3 = self._validate_volume_data(original_data, investpy_data)
        if not result3['status'] == 'success':
            return self._handle_validation_failure(3, "Volume Data Validation", result3['message'])
        
        # Component 4: Opening Price Validation
        result4 = self._validate_price_data(original_data, investpy_data, 'Opening_Price', 'open', 0.8)
        if not result4['status'] == 'success':
            return self._handle_validation_failure(4, "Opening Price Validation", result4['message'])
        
        # Component 5: High Price Validation
        result5 = self._validate_price_data(original_data, investpy_data, 'High_Price', 'high', 0.8)
        if not result5['status'] == 'success':
            return self._handle_validation_failure(5, "High Price Validation", result5['message'])
        
        # Component 6: Closing Price Validation
        result6 = self._validate_price_data(original_data, investpy_data, 'Closing_Price', 'close', 0.8)
        if not result6['status'] == 'success':
            return self._handle_validation_failure(6, "Closing Price Validation", result6['message'])
        
        # All validations passed
        print("All web-scraping validations PASSED!")
        return {
            'status': 'success',
            'message': 'All validation components passed successfully',
            'component_results': [result1, result2, result3, result4, result5, result6]
        }
    
    def _validate_symbol_and_dates(self, symbol: str, time_frame: Dict) -> Dict:
        """Component 1: Validate symbol and dates with IPO awareness."""
        try:
            # Get stock info from investpy to check IPO date
            stock_info = investpy.get_stock_information(symbol, 'united states')
            
            # Extract IPO date if available
            ipo_date = None
            if 'IPO Date' in stock_info.index:
                ipo_date_str = stock_info.loc['IPO Date']
                if pd.notna(ipo_date_str) and ipo_date_str != 'N/A':
                    ipo_date = pd.to_datetime(ipo_date_str).date()
            
            # Check if requested start date is before IPO
            start_date = pd.to_datetime(time_frame['start_date']).date()
            if ipo_date and start_date < ipo_date:
                print(f"WARNING: Requested start date ({start_date}) is before IPO date ({ipo_date})")
                print(f"Data will start from IPO date: {ipo_date}")
            
            return {
                'status': 'success',
                'symbol_match': True,
                'ipo_date': ipo_date,
                'start_date': start_date
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Symbol validation failed: {str(e)}',
                'symbol_match': False
            }
    
    def _validate_row_counts(self, original_data: pl.DataFrame, symbol: str, time_frame: Dict, data_frequency: str) -> Dict:
        """Component 2: Validate row counts match exactly."""
        try:
            # Get data from investpy
            start_date = time_frame['start_date']
            end_date = time_frame['end_date']
            
            investpy_data = investpy.get_stock_historical_data(
                stock=symbol,
                country='united states',
                from_date=start_date,
                to_date=end_date,
                interval=data_frequency
            )
            
            original_rows = len(original_data)
            investpy_rows = len(investpy_data)
            
            if original_rows == investpy_rows:
                print(f"Row count validation PASSED: {original_rows} rows match")
                return {
                    'status': 'success',
                    'original_rows': original_rows,
                    'investpy_rows': investpy_rows,
                    'investpy_data': investpy_data
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Row count mismatch: Original={original_rows}, Investpy={investpy_rows}',
                    'original_rows': original_rows,
                    'investpy_rows': investpy_rows
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Row count validation failed: {str(e)}'
            }
    
    def _validate_volume_data(self, original_data: pl.DataFrame, investpy_data: pd.DataFrame) -> Dict:
        """Component 3: Validate volume data with 2% tolerance."""
        try:
            # Sample 10% of entries randomly
            total_rows = len(original_data)
            sample_size = max(1, int(total_rows * 0.1))
            sample_indices = random.sample(range(total_rows), sample_size)
            
            mismatches = []
            tolerance = 0.02  # 2%
            
            for idx in sample_indices:
                original_volume = original_data['Volume_Traded'][idx]
                
                # Find corresponding investpy row (assuming same order)
                if idx < len(investpy_data):
                    investpy_volume = investpy_data['volume'].iloc[idx]
                    
                    # Calculate percentage difference
                    if original_volume > 0 and investpy_volume > 0:
                        diff_percent = abs(original_volume - investpy_volume) / original_volume
                        if diff_percent > tolerance:
                            mismatches.append({
                                'index': idx,
                                'original': original_volume,
                                'investpy': investpy_volume,
                                'diff_percent': diff_percent * 100
                            })
            
            if len(mismatches) == 0:
                print(f"Volume validation PASSED: All {sample_size} samples within 2% tolerance")
                return {'status': 'success', 'sample_size': sample_size, 'mismatches': []}
            else:
                return {
                    'status': 'error',
                    'message': f'Volume validation failed: {len(mismatches)}/{sample_size} samples exceeded 2% tolerance',
                    'mismatches': mismatches
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Volume validation failed: {str(e)}'
            }
    
    def _validate_price_data(self, original_data: pl.DataFrame, investpy_data: pd.DataFrame, 
                           original_col: str, investpy_col: str, tolerance_percent: float) -> Dict:
        """Component 4-6: Validate price data with specified tolerance."""
        try:
            # Sample 10% of entries randomly
            total_rows = len(original_data)
            sample_size = max(1, int(total_rows * 0.1))
            sample_indices = random.sample(range(total_rows), sample_size)
            
            mismatches = []
            tolerance = tolerance_percent / 100  # Convert to decimal
            
            for idx in sample_indices:
                original_price = original_data[original_col][idx]
                
                # Find corresponding investpy row (assuming same order)
                if idx < len(investpy_data):
                    investpy_price = investpy_data[investpy_col].iloc[idx]
                    
                    # Calculate percentage difference
                    if original_price > 0 and investpy_price > 0:
                        diff_percent = abs(original_price - investpy_price) / original_price
                        if diff_percent > tolerance:
                            mismatches.append({
                                'index': idx,
                                'original': original_price,
                                'investpy': investpy_price,
                                'diff_percent': diff_percent * 100
                            })
            
            if len(mismatches) == 0:
                print(f"{original_col} validation PASSED: All {sample_size} samples within {tolerance_percent}% tolerance")
                return {'status': 'success', 'sample_size': sample_size, 'mismatches': []}
            else:
                return {
                    'status': 'error',
                    'message': f'{original_col} validation failed: {len(mismatches)}/{sample_size} samples exceeded {tolerance_percent}% tolerance',
                    'mismatches': mismatches
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'{original_col} validation failed: {str(e)}'
            }
    
    def _handle_validation_failure(self, component_num: int, component_name: str, failure_reason: str) -> Dict:
        """Handle validation failure by asking user for decision."""
        print(f"\nVALIDATION FAILURE in Component {component_num}: {component_name}")
        print(f"Reason: {failure_reason}")
        print("\nOptions:")
        print("1. Continue with remaining validations (y/yes)")
        print("2. Return to first layer to regenerate data (n/no)")
        
        while True:
            user_input = input("\nDo you want to proceed? (y/n): ").lower().strip()
            if user_input in ['y', 'yes']:
                print("Continuing with remaining validations...")
                return {
                    'status': 'continue',
                    'failed_component': component_num,
                    'component_name': component_name,
                    'failure_reason': failure_reason,
                    'user_decision': 'continue'
                }
            elif user_input in ['n', 'no']:
                print("Returning to first layer to regenerate data...")
                return {
                    'status': 'regenerate',
                    'failed_component': component_num,
                    'component_name': component_name,
                    'failure_reason': failure_reason,
                    'user_decision': 'regenerate'
                }
            else:
                print("Please enter 'y' for yes or 'n' for no.")

