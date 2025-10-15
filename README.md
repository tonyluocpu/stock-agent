# LLM-Powered Stock Agent Chatbot

A sophisticated multi-layer stock analysis system powered by Large Language Models (Claude 3.5 Sonnet) that provides intelligent stock data management, validation, financial analysis, and conversational AI capabilities.

## Architecture Overview

The system implements a **four-layer architecture** for comprehensive stock intelligence:

**Layer 1**: Historical data collection with natural language processing
**Layer 2**: Multi-stage data validation and quality assurance
**Layer 3**: Context-aware conversation management
**Layer 4**: Comprehensive financial statement analysis and investment insights

---

## Layer 1: Intelligent Data Collection

### **Natural Language Understanding**
- **LLM-Powered Parsing**: Uses Claude 3.5 Sonnet for intelligent request interpretation
- **Smart Symbol Extraction**: Converts company names to tickers, handles misspellings
- **Intent Detection**: Classifies requests (data download, analysis, general questions, financial analysis)
- **Dynamic Date Handling**: Processes relative dates ("today", "last year", "from IPO")

### **Historical Data Download**
- **Flexible Frequencies**: Daily, weekly, monthly, yearly data
- **Time Range Flexibility**: "2020 to 2024", "last year", "10 years", "up to today"
- **Smart File Logic**: Differentiates "and" (multiple files) vs "to" (single date range)
- **Organized Storage**: Automatic directory structure by frequency and type
- **Multi-Symbol Support**: "Apple and Microsoft", "magnificent 7", batch downloads

### **Example Queries**
```
"Apple weekly data from 2020 to 2024"
"Microsoft and Google daily 2023 and 2024"  → Creates 4 files
"Magnificent 7 monthly from last year"
"NVDA from IPO to today"
```

### **Data Output Structure**
- Files saved to: `data/[frequency]/[opening|closing]/[SYMBOL]/`
- Naming: `[SYMBOL]_[FREQUENCY]_[YEAR].csv`
- Columns: Date, Opening_Price, High_Price, Low_Price, Closing_Price, Volume_Traded

---

## Layer 2: Data Validation & Quality Assurance

### **Initial Validation (Polars-Powered)**
- **Price Logic Checks**: Validates Opening ≤ High and Closing ≤ High for all data points
- **Frequency Validation**: Verifies correct intervals (daily, weekly, monthly, yearly)
- **Trading Day Verification**: Confirms weekends and holidays are excluded
- **Holiday Detection**: Uses web search to verify non-trading days

### **Web-Scraping Validation (InvestPy)**
Cross-validates data accuracy with external source:
- **Symbol Verification**: Exact symbol and IPO date matching
- **Row Count Matching**: Exact trading day count verification
- **Volume Validation**: 10% random sample, 2% tolerance
- **Price Validation**: 10% random sample, 0.8% tolerance for Open/High/Close
- **Statistical Accuracy**: Random sampling for performance

### **User Decision Flow**
- **Automatic Reports**: Generates detailed evaluation reports
- **Issue Detection**: Pauses on anomalies, displays clear error messages
- **User Control**: Choose to proceed or regenerate data
- **Comprehensive Logging**: All validations documented

### **Example Output**
```
✓ Price logic: PASSED (all 252 rows valid)
✓ Frequency: PASSED (daily intervals correct)
⚠ Volume validation: 1 discrepancy (within 2% tolerance)
→ Proceed with data? (y/n)
```

---

## Layer 3: Context-Aware Conversation

### **Context Management**
- **15-Turn Memory**: Maintains last 15 input/output pairs
- **Clarification Handling**: Tracks incomplete requests and user clarifications
- **Smart Combination**: Automatically combines multi-turn requests

### **Conversation Flow**
```
User: "nvidia data"
Bot: "What data frequency do you want (daily/weekly/monthly)?"
User: "what do you mean?"
Bot: "You need to specify the data interval."
User: "monthly"
Bot: [Combines context] "nvidia data monthly" → Processing...
```

### **Context Features**
- **Request Type Tracking**: stock_data, stock_analysis, general, clarification, financial_analysis
- **Sliding Window**: Automatically manages 15-entry limit
- **Intelligent Lookback**: Finds relevant context within conversation history

---

## Layer 4: Financial Statement Analysis

### **Comprehensive Fundamental Analysis**
Analyzes 4 years of financial statements with 18+ key metrics across income statement, balance sheet, and cash flow.

### **Income Statement Metrics**
- **Gross Margin**: Gross Profit / Revenue
- **R&D Ratio**: R&D Expenses / Gross Profit
- **SGA Ratio**: SG&A Expenses / Gross Profit (warns if >80%)
- **Net Margin**: Net Income / Revenue (warns if <10%, excellent if >20%)
- **EPS Trend**: 4-year earnings consistency and growth analysis

### **Balance Sheet Metrics**
- **Liquid Asset Ratio**: (Cash + Marketable Securities) / Total Assets
- **Long-term Debt Ratio**: Long-term Debt / Total Liabilities
- **Current Ratio**: Current Assets / Current Liabilities (liquidity health)

### **Cash Flow Metrics**
- **Operating Cash Flow**: Cash generated from operations
- **Owner's Cash**: Operating Cash Flow - Capital Expenditures
- **Repurchase/Dividend Ratio**: (Stock Buybacks + Dividends) / Total Cash Spending

### **Calculated Ratios**
- **Revenue Growth Rate**: Year-over-year revenue change
- **Sales Growth Rate**: Year-over-year sales change
- **Growth Ratio**: Sales Growth / Revenue Growth (warns if extreme)
- **Return on Assets (ROA)**: Net Income / Total Assets

### **Automated Warnings**
- SGA expenses >80% of gross profit
- Net margin <10%
- Extreme growth ratios (<0.1 or >10)

### **Investment Rating System**
Generates overall assessment based on multiple indicators:
- **Strong Investment Potential**: 80%+ positive indicators
- **Moderate Investment Potential**: 60-80% positive indicators
- **Weak Investment Potential**: <60% positive indicators

### **Example Queries**
```
"stock analysis of nvidia"
"should i buy tesla"
"important metrics of apple"
"financial analysis of microsoft"
```

### **Example Output**
```
Financial Analysis Report for AAPL
==================================================
Analysis Period: 2021-2024 (4 years)

Profitability Analysis:
• Gross Margin: 46.2%
  ✓ Good profitability
• Net Margin: 24.0%
  ✓ Excellent profitability (>20%)

Growth Analysis:
• Average Revenue Growth: 2.3% per year
  ⚠ Slow growth

Financial Health:
• Current Ratio: 1.05
  ✓ Adequate liquidity

Efficiency:
• Return on Assets: 25.7%
  ✓ Excellent asset efficiency

EPS Trend:
• EPS Growth: 7.8% over period
• Consistency: 3.4% volatility
  ✓ Consistent earnings

Investment Summary:
Moderate Investment Potential
Mixed financial signals. Consider carefully.

Data saved to: data/stock_trend/AAPL.csv
```

### **CSV Output**
4 years of historical data with 19 columns per year:
- Year, all metrics listed above, warning flags
- Enables trend analysis and historical comparison

---

## Quick Start

### Prerequisites
- Python 3.8+
- OpenRouter API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stock-agent-chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get Your API Key**
   - Go to [OpenRouter.ai](https://openrouter.ai/)
   - Sign up for an account (free)
   - Find your API key (starts with `sk-or-v1-`)

4. **Configure API**

#### Option A: Easy Method (Copy Template)
1. Copy the template file:
   ```bash
   cp api_config_template.py api_config.py
   ```
2. Open `api_config.py` in any editor
3. Replace `"your_openrouter_api_key_here"` with your actual API key:
   ```python
   API_KEY = "sk-or-v1-your-actual-key-goes-here"
   ```
4. Save the file

#### Option B: Manual Method
1. Create a new file called `api_config.py` in the project folder
2. Add these lines to the file:
   ```python
   #!/usr/bin/env python3
   """
   API Configuration for Stock Agent Chatbot
   """

   # OpenRouter API Key
   API_KEY = "sk-or-v1-your-actual-key-goes-here"
   API_URL = "https://openrouter.ai/api/v1/chat/completions"
   MODEL = "anthropic/claude-3.5-sonnet"
   ```
3. Replace `"sk-or-v1-your-actual-key-goes-here"` with your real API key
4. Save the file

5. **Run the Chatbot**
   ```bash
   python comprehensive_stock_chatbot.py --chat
   ```

## Usage Examples

### Layer 1: Historical Data Download
```
"Apple weekly data from 2020 to 2024"
"Microsoft and Google daily 2023 and 2024"
"Magnificent 7 monthly from last year"
```

### Layer 2: Real-Time Stock Analysis
```
"How is Apple performing today?"
"What does Tesla stock look like?"
"Compare Microsoft and Apple"
```

### Layer 4: Financial Statement Analysis
```
"stock analysis of nvidia"
"should i buy tesla"
"important metrics of apple"
```

### General Questions
```
"What date is it today?"
"Help me understand stock metrics"
```

---

## Troubleshooting

**Error: "Configuration files not found"**
- Make sure you created `api_config.py` in the correct folder
- Check that the file has the correct name (no typos)

**Error: "API_KEY not found"**
- Make sure your API key is in quotes: `"sk-or-v1-..."`
- Don't include any extra spaces or characters

**Error: "No module named 'yfinance'"**
- Run: `pip install -r requirements.txt`

**The chatbot starts but doesn't respond**
- Verify API key is valid at [OpenRouter.ai](https://openrouter.ai/)
- Ensure you have available credits

---

## Project Structure

```
stock-agent-chatbot/
├── comprehensive_stock_chatbot.py  # Main chatbot with layers 1-3
├── evaluation_module.py            # Layer 2: Data validation
├── financial_analysis_module.py    # Layer 4: Financial analysis
├── config.py                       # General configuration
├── api_config_template.py          # API key template
├── requirements.txt                # Python dependencies
├── README.md                       # Documentation
└── data/                          # Generated data storage
    ├── daily/opening/[SYMBOL]/
    ├── daily/closing/[SYMBOL]/
    ├── weekly/opening/[SYMBOL]/
    ├── weekly/closing/[SYMBOL]/
    └── stock_trend/[SYMBOL].csv
```

## Key Features

1. **Multi-Layer Architecture**: Four specialized layers for different analysis needs
2. **LLM-Powered Intelligence**: Natural language understanding with Claude 3.5 Sonnet
3. **Context Management**: 15-turn conversation memory for clarification handling
4. **Comprehensive Validation**: Dual-layer data quality assurance
5. **Financial Analysis**: 18+ fundamental metrics with automated warnings
6. **Modular Design**: Separate modules for maintainability
7. **Performance Optimized**: Polars for fast data processing

## Technical Stack

- **LLM**: Claude 3.5 Sonnet via OpenRouter API
- **Data Source**: Yahoo Finance (yfinance library)
- **Validation**: InvestPy for cross-validation
- **Data Processing**: Polars (high-performance), Pandas, NumPy
- **Testing**: Pytest with 95+ comprehensive tests

## License

MIT License