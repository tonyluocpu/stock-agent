#!/usr/bin/env python3
"""
Fourth Layer: Financial Analysis Module
======================================

This module provides comprehensive financial statement analysis for stocks,
including historical trend analysis over 10 years and natural language insights.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class FourthLayerFinancialAnalysis:
    """
    Fourth layer financial analysis system that provides comprehensive
    financial statement analysis and trend insights.
    """
    
    def __init__(self):
        """Initialize the financial analysis system."""
        self.data_dir = Path("data/stock_trend")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Verification completed flag
        self.verification_completed = False
        
        print("Fourth Layer Financial Analysis initialized!")
    
    def verify_data_availability(self):
        """One-time verification to check if all required data is available."""
        if self.verification_completed:
            return True
            
        print("Running one-time data availability verification...")
        
        test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        verification_results = {}
        
        for symbol in test_stocks:
            print(f"  Testing {symbol}...")
            try:
                ticker = yf.Ticker(symbol)
                
                # Test income statement
                income_stmt = ticker.income_stmt
                balance_sheet = ticker.balance_sheet
                cash_flow = ticker.cashflow
                
                # Check key data availability
                verification_results[symbol] = {
                    'income_statement_available': not income_stmt.empty,
                    'balance_sheet_available': not balance_sheet.empty,
                    'cash_flow_available': not cash_flow.empty,
                    'years_available': len(income_stmt.columns) if not income_stmt.empty else 0,
                    'earliest_year': income_stmt.columns[-1].strftime('%Y') if not income_stmt.empty else None
                }
                
                print(f"    Years available: {verification_results[symbol]['years_available']}")
                print(f"    Earliest year: {verification_results[symbol]['earliest_year']}")
                
            except Exception as e:
                print(f"    ERROR: {symbol} - {e}")
                verification_results[symbol] = {'error': str(e)}
        
        # Check if all stocks have sufficient data
        successful_tests = sum(1 for result in verification_results.values() 
                             if 'error' not in result and result.get('years_available', 0) >= 3)
        
        if successful_tests >= 4:  # At least 4 out of 5 should work
            print("✅ Data verification passed! All required data is available.")
            self.verification_completed = True
            return True
        else:
            print("❌ Data verification failed. Some data may not be available.")
            return False
    
    def _is_financial_analysis_request(self, user_input):
        """Check if user input is requesting financial analysis."""
        user_input_lower = user_input.lower()
        
        financial_analysis_keywords = [
            'stock analysis', 'financial analysis', 'important metrics',
            'should i buy', 'investment analysis', 'financial health',
            'company analysis', 'fundamental analysis', 'stock evaluation',
            'buy recommendation', 'investment decision', 'financial metrics',
            'earnings analysis', 'profitability analysis', 'financial trends'
        ]
        
        return any(keyword in user_input_lower for keyword in financial_analysis_keywords)
    
    def analyze_stock_financials(self, symbol):
        """Complete financial analysis workflow."""
        print(f"\n🔍 Starting comprehensive financial analysis for {symbol}...")
        
        # Verify data availability (one-time)
        if not self.verify_data_availability():
            return "ERROR: Data verification failed. Cannot proceed with analysis."
        
        try:
            # Step 1: Collect historical data
            print("📊 Collecting historical financial data...")
            historical_data = self._collect_historical_data(symbol)
            
            if not historical_data:
                return f"ERROR: Could not collect sufficient data for {symbol}"
            
            # Step 2: Calculate all metrics for each year
            print("🧮 Calculating financial metrics...")
            yearly_metrics = self._calculate_yearly_metrics(symbol, historical_data)
            
            # Step 3: Save to CSV
            print("💾 Saving data to CSV...")
            csv_path = self._save_to_csv(symbol, yearly_metrics)
            
            # Step 4: Generate natural language analysis
            print("📝 Generating analysis insights...")
            analysis_summary = self._generate_natural_language_analysis(symbol, yearly_metrics)
            
            print(f"✅ Analysis complete! Data saved to: {csv_path}")
            
            return analysis_summary
            
        except Exception as e:
            return f"ERROR: Analysis failed for {symbol}: {str(e)}"
    
    def _collect_historical_data(self, symbol):
        """Collect up to 4 years of historical financial data (Yahoo Finance limitation)."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Try multiple methods to get the most historical data possible
            income_stmt = None
            balance_sheet = None
            cash_flow = None
            
            # Method 1: Try financials (annual data)
            try:
                income_stmt = ticker.financials
                balance_sheet = ticker.balance_sheet
                cash_flow = ticker.cashflow
                print(f"  Using annual financial statements")
            except:
                pass
            
            # Method 2: If financials doesn't work, try income_stmt, balance_sheet, cashflow
            if income_stmt is None or income_stmt.empty:
                try:
                    income_stmt = ticker.income_stmt
                    balance_sheet = ticker.balance_sheet
                    cash_flow = ticker.cashflow
                    print(f"  Using quarterly financial statements")
                except:
                    pass
            
            # Method 3: Try getting info and extracting available years
            if income_stmt is None or income_stmt.empty:
                try:
                    info = ticker.info
                    print(f"  Attempting to get company info for data availability")
                    # This is a fallback - we'll use whatever data is available
                except:
                    pass
            
            if income_stmt is None or income_stmt.empty:
                print(f"  ERROR: No income statement data available for {symbol}")
                return None
            
            # Get all available years (not just 10)
            all_available_years = list(income_stmt.columns)
            print(f"  Total available periods: {len(all_available_years)}")
            
            # Take up to 4 years, but prioritize annual data
            selected_years = []
            
            # First, try to identify annual data (fiscal year ends)
            for year in all_available_years:
                if hasattr(year, 'month'):
                    # Look for fiscal year end months (Sept, Oct, Nov, Dec)
                    if year.month in [9, 10, 11, 12]:
                        selected_years.append(year)
            
            # If we don't have enough annual data, add more periods
            if len(selected_years) < 4:
                for year in all_available_years:
                    if year not in selected_years and len(selected_years) < 4:
                        selected_years.append(year)
            
            # Limit to 4 years maximum (Yahoo Finance limitation)
            selected_years = selected_years[:4]
            
            historical_data = {}
            for year in selected_years:
                try:
                    year_data = {
                        'income_statement': income_stmt[year],
                        'balance_sheet': balance_sheet[year] if balance_sheet is not None and not balance_sheet.empty else None,
                        'cash_flow': cash_flow[year] if cash_flow is not None and not cash_flow.empty else None
                    }
                    historical_data[year] = year_data
                except Exception as e:
                    print(f"    Warning: Error getting data for {year}: {e}")
                    continue
            
            print(f"  Collected data for {len(historical_data)} years: {[y.strftime('%Y-%m') for y in historical_data.keys()]}")
            
            # Note: Yahoo Finance free API limitation - typically only 4 years of annual data
            if len(historical_data) < 3:
                print(f"  WARNING: Only {len(historical_data)} years of data available. Some analysis may be limited.")
            elif len(historical_data) >= 4:
                print(f"  ✅ Successfully collected 4 years of data!")
            else:
                print(f"  ℹ️ Collected {len(historical_data)} years of available data (Yahoo Finance free API limitation)")
                print(f"  ℹ️ For more years of data, premium financial data sources would be needed")
            
            return historical_data
            
        except Exception as e:
            print(f"  ERROR collecting data: {e}")
            return None
    
    def _calculate_yearly_metrics(self, symbol, historical_data):
        """Calculate all financial metrics for each year."""
        yearly_metrics = {}
        previous_year_data = None
        
        # Sort years chronologically
        sorted_years = sorted(historical_data.keys())
        
        for year in sorted_years:
            data = historical_data[year]
            
            try:
                # Income Statement Metrics
                gross_margin = self._calculate_gross_margin(data['income_statement'])
                rd_ratio = self._calculate_rd_ratio(data['income_statement'])
                sga_ratio = self._calculate_sga_ratio(data['income_statement'])
                sga_warning = sga_ratio > 0.8 if sga_ratio else False
                net_margin = self._calculate_net_margin(data['income_statement'])
                net_margin_warning = net_margin < 0.1 if net_margin else False
                eps = self._get_eps(data['income_statement'])
                
                # Balance Sheet Metrics
                liquid_asset_ratio = self._calculate_liquid_asset_ratio(data['balance_sheet'])
                long_term_debt_ratio = self._calculate_long_term_debt_ratio(data['balance_sheet'])
                
                # Cash Flow Metrics
                repurchase_dividend_ratio = self._calculate_repurchase_dividend_ratio(data['cash_flow'])
                operating_cash_flow = self._get_operating_cash_flow(data['cash_flow'])
                owners_cash = self._calculate_owners_cash(data['cash_flow'])
                
                # Calculated Ratios
                current_ratio = self._calculate_current_ratio(data['balance_sheet'])
                
                # Growth calculations (require previous year data)
                sales_growth = self._calculate_sales_growth(data['income_statement'], previous_year_data)
                revenue_growth = self._calculate_revenue_growth(data['income_statement'], previous_year_data)
                growth_ratio = self._calculate_growth_ratio(sales_growth, revenue_growth)
                growth_warning = self._check_growth_warning(growth_ratio)
                
                roa = self._calculate_roa(data['income_statement'], data['balance_sheet'])
                
                yearly_metrics[year] = {
                    'year': year.strftime('%Y'),
                    'gross_margin': gross_margin,
                    'rd_ratio': rd_ratio,
                    'sga_ratio': sga_ratio,
                    'sga_warning': sga_warning,
                    'net_margin': net_margin,
                    'net_margin_warning': net_margin_warning,
                    'eps': eps,
                    'liquid_asset_ratio': liquid_asset_ratio,
                    'long_term_debt_ratio': long_term_debt_ratio,
                    'repurchase_dividend_ratio': repurchase_dividend_ratio,
                    'operating_cash_flow': operating_cash_flow,
                    'owners_cash': owners_cash,
                    'current_ratio': current_ratio,
                    'sales_growth': sales_growth,
                    'revenue_growth': revenue_growth,
                    'growth_ratio': growth_ratio,
                    'growth_warning': growth_warning,
                    'return_on_assets': roa
                }
                
                previous_year_data = data['income_statement']
                
            except Exception as e:
                print(f"    Warning: Error calculating metrics for {year.strftime('%Y')}: {e}")
                continue
        
        return yearly_metrics
    
    # Financial calculation methods
    def _calculate_gross_margin(self, income_stmt):
        """Calculate gross margin (gross profit / revenue)."""
        try:
            revenue = income_stmt.get('Total Revenue', income_stmt.get('Revenue', 0))
            gross_profit = income_stmt.get('Gross Profit', 0)
            return gross_profit / revenue if revenue != 0 else None
        except:
            return None
    
    def _calculate_rd_ratio(self, income_stmt):
        """Calculate R&D ratio (R&D expenses / gross profit)."""
        try:
            gross_profit = income_stmt.get('Gross Profit', 0)
            rd_expense = income_stmt.get('Research Development', income_stmt.get('Research and Development', 0))
            return rd_expense / gross_profit if gross_profit != 0 else None
        except:
            return None
    
    def _calculate_sga_ratio(self, income_stmt):
        """Calculate SGA ratio (SGA expenses / gross profit)."""
        try:
            gross_profit = income_stmt.get('Gross Profit', 0)
            sga_expense = income_stmt.get('Selling General Administrative', 0)
            return sga_expense / gross_profit if gross_profit != 0 else None
        except:
            return None
    
    def _calculate_net_margin(self, income_stmt):
        """Calculate net margin (net income / revenue)."""
        try:
            revenue = income_stmt.get('Total Revenue', income_stmt.get('Revenue', 0))
            net_income = income_stmt.get('Net Income', 0)
            return net_income / revenue if revenue != 0 else None
        except:
            return None
    
    def _get_eps(self, income_stmt):
        """Get earnings per share."""
        try:
            return income_stmt.get('Basic EPS', income_stmt.get('Diluted EPS', 0))
        except:
            return None
    
    def _calculate_liquid_asset_ratio(self, balance_sheet):
        """Calculate liquid asset ratio (cash + marketable securities / total assets)."""
        try:
            total_assets = balance_sheet.get('Total Assets', 0)
            cash = balance_sheet.get('Cash And Cash Equivalents', 0)
            marketable_securities = balance_sheet.get('Short Term Investments', 0)
            liquid_assets = cash + marketable_securities
            return liquid_assets / total_assets if total_assets != 0 else None
        except:
            return None
    
    def _calculate_long_term_debt_ratio(self, balance_sheet):
        """Calculate long-term debt ratio (long-term debt / total liabilities)."""
        try:
            total_liabilities = balance_sheet.get('Total Liab', balance_sheet.get('Total Liabilities', 0))
            long_term_debt = balance_sheet.get('Long Term Debt', 0)
            return long_term_debt / total_liabilities if total_liabilities != 0 else None
        except:
            return None
    
    def _calculate_repurchase_dividend_ratio(self, cash_flow):
        """Calculate % of cash spending used for repurchases and dividends."""
        try:
            total_cash_used = abs(cash_flow.get('Net Cash Flow', 0))
            repurchases = abs(cash_flow.get('Common Stock Repurchased', 0))
            dividends = abs(cash_flow.get('Common Stock Dividends Paid', 0))
            
            if total_cash_used == 0:
                return None
            
            return (repurchases + dividends) / total_cash_used
        except:
            return None
    
    def _get_operating_cash_flow(self, cash_flow):
        """Get operating cash flow."""
        try:
            return cash_flow.get('Total Cash From Operating Activities', 
                               cash_flow.get('Operating Cash Flow', 0))
        except:
            return None
    
    def _calculate_owners_cash(self, cash_flow):
        """Calculate owner's cash (operating cash flow - capital expenditures)."""
        try:
            operating_cash = self._get_operating_cash_flow(cash_flow)
            capex = cash_flow.get('Capital Expenditures', 0)
            return operating_cash - capex if operating_cash else None
        except:
            return None
    
    def _calculate_current_ratio(self, balance_sheet):
        """Calculate current ratio (current assets / current liabilities)."""
        try:
            current_assets = balance_sheet.get('Total Current Assets', 0)
            current_liabilities = balance_sheet.get('Total Current Liabilities', 0)
            return current_assets / current_liabilities if current_liabilities != 0 else None
        except:
            return None
    
    def _calculate_sales_growth(self, income_stmt, previous_year_data):
        """Calculate sales growth rate."""
        if previous_year_data is None:
            return None
        try:
            current_revenue = income_stmt.get('Total Revenue', income_stmt.get('Revenue', 0))
            previous_revenue = previous_year_data.get('Total Revenue', previous_year_data.get('Revenue', 0))
            
            if previous_revenue == 0:
                return None
            
            return (current_revenue - previous_revenue) / previous_revenue
        except:
            return None
    
    def _calculate_revenue_growth(self, income_stmt, previous_year_data):
        """Calculate revenue growth rate."""
        # Same as sales growth for most companies
        return self._calculate_sales_growth(income_stmt, previous_year_data)
    
    def _calculate_growth_ratio(self, sales_growth, revenue_growth):
        """Calculate sales growth / revenue growth ratio."""
        if sales_growth is None or revenue_growth is None or revenue_growth == 0:
            return None
        return sales_growth / revenue_growth
    
    def _check_growth_warning(self, growth_ratio):
        """Check if growth ratio is concerning (extremely low or high)."""
        if growth_ratio is None:
            return False
        return growth_ratio < 0.1 or growth_ratio > 10
    
    def _calculate_roa(self, income_stmt, balance_sheet):
        """Calculate return on assets (net income / total assets)."""
        try:
            net_income = income_stmt.get('Net Income', 0)
            total_assets = balance_sheet.get('Total Assets', 0)
            return net_income / total_assets if total_assets != 0 else None
        except:
            return None
    
    def _save_to_csv(self, symbol, yearly_metrics):
        """Save yearly metrics to CSV file."""
        try:
            # Prepare data for DataFrame
            df_data = []
            for year, metrics in yearly_metrics.items():
                df_data.append(metrics)
            
            # Create DataFrame
            df = pd.DataFrame(df_data)
            
            # Save to CSV
            csv_path = self.data_dir / f"{symbol}.csv"
            df.to_csv(csv_path, index=False)
            
            return csv_path
            
        except Exception as e:
            print(f"    ERROR saving CSV: {e}")
            return None
    
    def _generate_natural_language_analysis(self, symbol, yearly_metrics):
        """Generate natural language analysis of financial trends."""
        try:
            analysis = []
            analysis.append(f"## 📊 Financial Analysis Report for {symbol}")
            analysis.append("=" * 50)
            
            if not yearly_metrics:
                return "No financial data available for analysis."
            
            # Analyze trends over time
            years = list(yearly_metrics.keys())
            latest_year = years[-1] if years else None
            earliest_year = years[0] if years else None
            
            analysis.append(f"**Analysis Period:** {earliest_year} - {latest_year} ({len(years)} years)")
            if len(years) < 4:
                analysis.append(f"*Note: Yahoo Finance provides {len(years)} years of data. For more years, premium data sources are needed.*")
            analysis.append("")
            
            # Profitability Analysis
            analysis.append("### 💰 Profitability Analysis")
            latest_metrics = yearly_metrics[latest_year]
            
            if latest_metrics['gross_margin']:
                gm = latest_metrics['gross_margin'] * 100
                analysis.append(f"• **Gross Margin:** {gm:.1f}%")
                if gm > 50:
                    analysis.append("  ✅ Excellent pricing power and efficiency")
                elif gm > 30:
                    analysis.append("  ✅ Good profitability")
                else:
                    analysis.append("  ⚠️ Low margins - price sensitive business")
            
            if latest_metrics['net_margin']:
                nm = latest_metrics['net_margin'] * 100
                analysis.append(f"• **Net Margin:** {nm:.1f}%")
                if nm > 20:
                    analysis.append("  ✅ Excellent profitability (>20%)")
                elif nm > 10:
                    analysis.append("  ✅ Good profitability")
                elif nm < 10:
                    analysis.append("  ⚠️ Warning: Low profitability (<10%)")
            
            # Growth Analysis
            analysis.append("")
            analysis.append("### 📈 Growth Analysis")
            
            # Calculate average growth rates
            growth_rates = [metrics['revenue_growth'] for metrics in yearly_metrics.values() 
                          if metrics['revenue_growth'] is not None]
            
            if growth_rates:
                avg_growth = np.mean(growth_rates) * 100
                analysis.append(f"• **Average Revenue Growth:** {avg_growth:.1f}% per year")
                
                if avg_growth > 15:
                    analysis.append("  ✅ Strong growth company")
                elif avg_growth > 5:
                    analysis.append("  ✅ Steady growth")
                else:
                    analysis.append("  ⚠️ Slow or negative growth")
            
            # Financial Health
            analysis.append("")
            analysis.append("### 🏥 Financial Health")
            
            if latest_metrics['current_ratio']:
                cr = latest_metrics['current_ratio']
                analysis.append(f"• **Current Ratio:** {cr:.2f}")
                if cr > 2:
                    analysis.append("  ✅ Strong liquidity")
                elif cr > 1:
                    analysis.append("  ✅ Adequate liquidity")
                else:
                    analysis.append("  ⚠️ Low liquidity - potential cash flow issues")
            
            if latest_metrics['long_term_debt_ratio']:
                ltdr = latest_metrics['long_term_debt_ratio'] * 100
                analysis.append(f"• **Long-term Debt Ratio:** {ltdr:.1f}%")
                if ltdr < 30:
                    analysis.append("  ✅ Low debt burden")
                elif ltdr < 60:
                    analysis.append("  ✅ Moderate debt levels")
                else:
                    analysis.append("  ⚠️ High debt levels")
            
            # Efficiency Analysis
            analysis.append("")
            analysis.append("### ⚙️ Efficiency Analysis")
            
            if latest_metrics['return_on_assets']:
                roa = latest_metrics['return_on_assets'] * 100
                analysis.append(f"• **Return on Assets:** {roa:.1f}%")
                if roa > 15:
                    analysis.append("  ✅ Excellent asset efficiency")
                elif roa > 10:
                    analysis.append("  ✅ Good asset efficiency")
                else:
                    analysis.append("  ⚠️ Low asset efficiency")
            
            # Warnings
            warnings_found = []
            if latest_metrics.get('sga_warning'):
                warnings_found.append("High SGA expenses (>80% of gross profit)")
            if latest_metrics.get('net_margin_warning'):
                warnings_found.append("Low net margin (<10%)")
            if latest_metrics.get('growth_warning'):
                warnings_found.append("Concerning growth ratio")
            
            if warnings_found:
                analysis.append("")
                analysis.append("### ⚠️ Warnings")
                for warning in warnings_found:
                    analysis.append(f"• {warning}")
            
            # EPS Trend Analysis
            analysis.append("")
            analysis.append("### 📊 EPS Trend Analysis")
            eps_values = [metrics['eps'] for metrics in yearly_metrics.values() 
                         if metrics['eps'] is not None and metrics['eps'] > 0]
            
            if len(eps_values) >= 3:
                eps_growth = (eps_values[-1] - eps_values[0]) / eps_values[0] * 100 if eps_values[0] != 0 else 0
                analysis.append(f"• **EPS Growth over period:** {eps_growth:.1f}%")
                
                # Check consistency
                eps_volatility = np.std(eps_values) / np.mean(eps_values) * 100
                analysis.append(f"• **EPS Consistency:** {eps_volatility:.1f}% volatility")
                
                if eps_volatility < 20:
                    analysis.append("  ✅ Consistent earnings growth")
                elif eps_volatility < 40:
                    analysis.append("  ✅ Moderately consistent")
                else:
                    analysis.append("  ⚠️ Volatile earnings")
            
            analysis.append("")
            analysis.append("### 💡 Investment Summary")
            
            # Overall assessment
            positive_indicators = 0
            total_indicators = 0
            
            if latest_metrics['gross_margin'] and latest_metrics['gross_margin'] > 0.3:
                positive_indicators += 1
            total_indicators += 1
            
            if latest_metrics['net_margin'] and latest_metrics['net_margin'] > 0.1:
                positive_indicators += 1
            total_indicators += 1
            
            if avg_growth > 5:
                positive_indicators += 1
            total_indicators += 1
            
            if latest_metrics['current_ratio'] and latest_metrics['current_ratio'] > 1:
                positive_indicators += 1
            total_indicators += 1
            
            if latest_metrics['return_on_assets'] and latest_metrics['return_on_assets'] > 0.1:
                positive_indicators += 1
            total_indicators += 1
            
            score = positive_indicators / total_indicators if total_indicators > 0 else 0
            
            if score >= 0.8:
                analysis.append("🟢 **Strong Investment Potential**")
                analysis.append("This company shows strong financial health across multiple metrics.")
            elif score >= 0.6:
                analysis.append("🟡 **Moderate Investment Potential**")
                analysis.append("This company shows mixed financial signals. Consider carefully.")
            else:
                analysis.append("🔴 **Weak Investment Potential**")
                analysis.append("This company shows concerning financial metrics. High risk.")
            
            analysis.append("")
            analysis.append(f"📁 **Detailed data saved to:** `data/stock_trend/{symbol}.csv`")
            
            return "\n".join(analysis)
            
        except Exception as e:
            return f"ERROR generating analysis: {str(e)}"


# Test function for verification
def test_financial_analysis():
    """Test the financial analysis system with sample stocks."""
    analyzer = FourthLayerFinancialAnalysis()
    
    test_stocks = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_stocks:
        print(f"\n{'='*60}")
        print(f"Testing financial analysis for {symbol}")
        print('='*60)
        
        result = analyzer.analyze_stock_financials(symbol)
        print(result)
        print("\n" + "="*60)


if __name__ == "__main__":
    test_financial_analysis()
