# Stock Agent - Complete Functionality Summary

## System Overview

The Stock Agent is a sophisticated multi-layer stock analysis system powered by Large Language Models (Claude 3.5 Sonnet or free local LLMs) that provides intelligent stock data management, validation, financial analysis, conversational AI, stock screening, and self-improvement capabilities.

---

## Architecture: 5-Layer System

### **Layer 1: Intelligent Data Collection**
### **Layer 2: Data Validation & Quality Assurance**
### **Layer 3: Context-Aware Conversation Management**
### **Layer 4: Financial Statement Analysis**
### **Layer 5: Stock Screening & Valuation**

---

## Layer 1: Intelligent Data Collection

### Natural Language Understanding
- **LLM-Powered Parsing**: Uses LLM (Claude 3.5 Sonnet or local) for intelligent request interpretation
- **Smart Symbol Extraction**: Converts company names to tickers, handles misspellings
- **Intent Detection**: Classifies requests (data download, analysis, general questions, financial analysis, screening)
- **Dynamic Date Handling**: Processes relative dates ("today", "last year", "from IPO")

### Historical Data Download
- **Flexible Frequencies**: Daily, weekly, monthly, yearly data
- **Time Range Flexibility**: "2020 to 2024", "last year", "10 years", "up to today"
- **Smart File Logic**: Differentiates "and" (multiple files) vs "to" (single date range)
- **Organized Storage**: Automatic directory structure by frequency and type
- **Multi-Symbol Support**: "Apple and Microsoft", "magnificent 7", batch downloads
- **Data Types**: Opening prices, closing prices, high, low, volume

### Example Queries
```
"Apple weekly data from 2020 to 2024"
"Microsoft and Google daily 2023 and 2024"
"Magnificent 7 monthly from last year"
"NVDA from IPO to today"
```

### Data Output Structure
- Files saved to: `data/[frequency]/[opening|closing]/[SYMBOL]/`
- Naming: `[SYMBOL]_[FREQUENCY]_[YEAR].csv`
- Columns: Date, Opening_Price, High_Price, Low_Price, Closing_Price, Volume_Traded

---

## Layer 2: Data Validation & Quality Assurance

### Initial Validation (Polars-Powered)
- **Price Logic Checks**: Validates Opening ≤ High and Closing ≤ High for all data points
- **Frequency Validation**: Verifies correct intervals (daily, weekly, monthly, yearly)
- **Trading Day Verification**: Confirms weekends and holidays are excluded
- **Holiday Detection**: Uses web search to verify non-trading days

### Web-Scraping Validation (InvestPy)
Cross-validates data accuracy with external source:
- **Symbol Verification**: Exact symbol and IPO date matching
- **Row Count Matching**: Exact trading day count verification
- **Volume Validation**: 10% random sample, 2% tolerance
- **Price Validation**: 10% random sample, 0.8% tolerance for Open/High/Close
- **Statistical Accuracy**: Random sampling for performance

### User Decision Flow
- **Automatic Reports**: Generates detailed evaluation reports
- **Issue Detection**: Pauses on anomalies, displays clear error messages
- **User Control**: Choose to proceed or regenerate data
- **Comprehensive Logging**: All validations documented

---

## Layer 3: Context-Aware Conversation

### Context Management
- **15-Turn Memory**: Maintains last 15 input/output pairs
- **Clarification Handling**: Tracks incomplete requests and user clarifications
- **Smart Combination**: Automatically combines multi-turn requests

### Fast Path Responses
Instant responses (no LLM call) for:
- Greetings (hello, hi, hey, etc.)
- Help requests
- Thank you messages
- Exit commands

### Conversation Flow
```
User: "nvidia data"
Bot: "What data frequency do you want (daily/weekly/monthly)?"
User: "what do you mean?"
Bot: "You need to specify the data interval."
User: "monthly"
Bot: [Combines context] "nvidia data monthly" → Processing...
```

---

## Layer 4: Financial Statement Analysis

### Comprehensive Fundamental Analysis
Analyzes 4 years of financial statements with 18+ key metrics across income statement, balance sheet, and cash flow.

### Income Statement Metrics
- **Gross Margin**: Gross Profit / Revenue
- **R&D Ratio**: R&D Expenses / Gross Profit
- **SGA Ratio**: SG&A Expenses / Gross Profit (warns if >80%)
- **Net Margin**: Net Income / Revenue (warns if <10%, excellent if >20%)
- **EPS Trend**: 4-year earnings consistency and growth analysis

### Balance Sheet Metrics
- **Liquid Asset Ratio**: (Cash + Marketable Securities) / Total Assets
- **Long-term Debt Ratio**: Long-term Debt / Total Liabilities
- **Current Ratio**: Current Assets / Current Liabilities (liquidity health)

### Cash Flow Metrics
- **Operating Cash Flow**: Cash generated from operations
- **Owner's Cash**: Operating Cash Flow - Capital Expenditures
- **Repurchase/Dividend Ratio**: (Stock Buybacks + Dividends) / Total Cash Spending

### Calculated Ratios
- **Revenue Growth Rate**: Year-over-year revenue change
- **Sales Growth Rate**: Year-over-year sales change
- **Growth Ratio**: Sales Growth / Revenue Growth (warns if extreme)
- **Return on Assets (ROA)**: Net Income / Total Assets

### Automated Warnings
- SGA expenses >80% of gross profit
- Net margin <10%
- Extreme growth ratios (<0.1 or >10)

### Investment Rating System
Generates overall assessment based on multiple indicators:
- **Strong Investment Potential**: 80%+ positive indicators
- **Moderate Investment Potential**: 60-80% positive indicators
- **Weak Investment Potential**: <60% positive indicators

### Example Queries
```
"stock analysis of nvidia"
"should i buy tesla"
"important metrics of apple"
"financial analysis of microsoft"
```

---

## Layer 5: Stock Screening & Valuation System

### Overview
Comprehensive stock screening to find undervalued investment opportunities based on 12 investment criteria.

### Basic Screening Criteria (All Must Pass)
1. **Market Capitalization**: Under $2 billion
2. **Price-to-Book (P/B) Ratio**: Below 1.0
3. **Price-to-Earnings (P/E) Ratio**: Less than 15
4. **Shares Float**: Less than 1 billion shares
5. **Debt Structure**: Must NOT have high debt (exclude companies with 50%+ debt)
6. **Profit Stability**: Must NOT have profit declined by more than 10% in any year for the past 5 years

### Advanced Analysis (For Stocks Passing Basic Criteria)
7. **Intrinsic Value Calculation (DCF)**: Calculate value based on expected future cash flows
8. **Relative Valuation**: Compare to similar companies in same industry
9. **Final Intrinsic Value**: Average of DCF + Relative Valuation
10. **Warren Buffett Value Comparison**: Intrinsic value > Current stock price

### Catalyst Search (For Undervalued Stocks)
11. **New Partnerships or Agreements**: Strategic partnerships, new contracts, joint ventures
12. **Management Changes / Restructuring**: New CEO/executive team, strategic shifts
13. **Acquisition Target / Merger Potential**: M&A rumors, takeover potential
14. **Industry-Wide Catalysts**: Government policies, regulatory changes, technology shifts

### Screening Workflow
1. **Sector Selection**: User selects from 11 GICS sectors
2. **Stock List**: Gets 50-300 stocks per sector (from SEC EDGAR + yfinance)
3. **Basic Screening**: Checks each stock against all 6 basic criteria (stops at 15 matches)
4. **Advanced Analysis**: Calculates intrinsic value for 15 stocks
5. **Catalyst Search**: Finds catalysts for undervalued stocks
6. **Final Output**: Ranked list (most to least undervalued)

### Available Sectors
- Technology
- Healthcare
- Financials
- Consumer Discretionary
- Communication Services
- Industrials
- Consumer Staples
- Energy
- Utilities
- Real Estate
- Materials

### Example Queries
```
"Screen technology sector for undervalued stocks"
"Find undervalued healthcare stocks"
"Screen financials sector"
```

### Performance
- **Sector Screening**: 2-7 minutes (50-300 stocks)
- **Data Fetching**: ~0.1s per stock (with caching)
- **Intrinsic Value**: ~1-2s per stock
- **Catalyst Search**: ~2-5s per stock (LLM)

---

## Self-Improvement System

### Overview
Automatically analyzes conversations, identifies issues, and applies code improvements to prevent awkward conversations from happening again.

### How It Works
1. **Conversation Logging**: Every user-bot interaction is logged with metadata
2. **Session Tracking**: Heartbeat mechanism detects when frontend closes (240s timeout)
3. **Analysis**: LLM analyzes conversations to identify issues:
   - Off-topic responses (HIGH PRIORITY)
   - User confusion
   - Errors or failures
   - Missing functionality
   - Slow responses (>= 30s, except screening)
4. **Improvement Generation**: LLM generates smart, pattern-based code fixes
5. **Testing**: Validates improvements before applying
6. **Application**: Safely applies improvements with backup and rollback

### Features
- **Pattern-Based Fixes**: Never hardcodes specific responses
- **Spelling Error Handling**: Uses fuzzy matching or LLM fallback
- **Safety First**: Backups, validation, and rollback on failure
- **Limits**: Max 3 improvements per session, max 1 logic change
- **Cooldown**: 24-hour cooldown for same issue type

### Safety Features
1. **Backups**: Every change creates a backup
2. **Validation**: Syntax, imports, and regression tests
3. **Rollback**: Automatic rollback on test failure
4. **Fix Attempts**: System tries to fix issues before rolling back
5. **Audit Trail**: All changes logged with timestamps

---

## API Interface (REST API)

### Endpoints

#### `/api/chat` (POST)
Main chat endpoint for processing user requests.

**Request:**
```json
{
  "message": "Apple weekly data 2020-2024",
  "context": [],  // Optional conversation context
  "session_id": "uuid"  // Optional session ID
}
```

**Response:**
```json
{
  "type": "stock_data|stock_analysis|financial_analysis|general|stock_screening",
  "response": "Response text",
  "success": true,
  "data": {...},  // Optional structured data
  "session_id": "uuid"  // Session ID for heartbeat
}
```

#### `/api/health` (GET)
Health check endpoint.

#### `/api/context` (GET)
Get conversation context.

#### `/api/config` (GET)
Get current configuration.

#### Session Management Endpoints
- `POST /api/session/start` - Start new session
- `POST /api/heartbeat` - Keep session alive (send every 120s)
- `POST /api/session/end` - Explicitly end session

#### Improvement Endpoints
- `GET /api/improvements` - List applied improvements
- `POST /api/improvements/rollback/<id>` - Rollback specific improvement

---

## Data Storage Structure

### Historical Data
```
data/
├── daily/
│   ├── beginning/[SYMBOL]/
│   └── closing/[SYMBOL]/
├── weekly/
│   ├── beginning/[SYMBOL]/
│   └── closing/[SYMBOL]/
├── monthly/
│   ├── beginning/[SYMBOL]/
│   └── closing/[SYMBOL]/
└── yearly/
    ├── beginning/[SYMBOL]/
    └── closing/[SYMBOL]/
```

### Analysis Data
```
data/
├── stock_trend/[SYMBOL].csv  # Financial analysis results
├── conversations/  # Conversation logs
│   └── session_*.json
└── improvements/  # Self-improvement data
    ├── analysis_*.json
    ├── backups/
    └── applied/
```

### Screening Data
```
data/
├── screening/  # Screening results
├── stock_lists/
│   └── sector_database.json  # Sector stock lists
└── (various cache files)
```

---

## Technical Stack

### LLM Providers
- **Primary**: Claude 3.5 Sonnet via OpenRouter API
- **Alternative**: Free local LLMs (via Hugging Face)
- **Configuration**: Unified LLM config system (`llm_config.py`)

### Data Sources
- **Stock Data**: Yahoo Finance (yfinance library)
- **Validation**: InvestPy for cross-validation
- **Sector Lists**: SEC EDGAR + yfinance sector mapping
- **Financial Data**: yfinance (financial statements, metrics)

### Data Processing
- **Polars**: High-performance data processing
- **Pandas**: Data manipulation
- **NumPy**: Numerical operations

### Framework
- **Flask**: REST API server
- **CORS**: Enabled for frontend integration

### Testing
- **Pytest**: Comprehensive test suite (95+ tests)
- **Test Modules**: Separate tests for each layer

---

## Key Features Summary

### Core Capabilities
1. **Multi-Layer Architecture**: Five specialized layers for different analysis needs
2. **LLM-Powered Intelligence**: Natural language understanding with Claude 3.5 Sonnet or local LLMs
3. **Context Management**: 15-turn conversation memory for clarification handling
4. **Comprehensive Validation**: Dual-layer data quality assurance
5. **Financial Analysis**: 18+ fundamental metrics with automated warnings
6. **Stock Screening**: 12-criteria screening system for undervalued stocks
7. **Self-Improvement**: Automatic code improvements based on conversation analysis
8. **REST API**: Full API interface for frontend integration
9. **Modular Design**: Separate modules for maintainability
10. **Performance Optimized**: Polars for fast data processing, smart caching

### Advanced Features
- **Fast Path Responses**: Instant responses for common queries (no LLM call)
- **Smart Context Combination**: Automatically combines multi-turn requests
- **Sector-Based Screening**: Screen by GICS sectors with comprehensive stock lists
- **Intrinsic Value Calculation**: DCF + Relative valuation methods
- **Catalyst Discovery**: LLM-powered search for investment catalysts
- **Session Management**: Frontend session tracking with heartbeat mechanism
- **Data Caching**: Smart caching for performance (daily/monthly refresh)
- **Background Screening**: Can screen all sectors in background

---

## Usage Examples

### Layer 1: Historical Data Download
```
"Apple weekly data from 2020 to 2024"
"Microsoft and Google daily 2023 and 2024"
"Magnificent 7 monthly from last year"
```

### Layer 2: Data Analysis
```
"How is Apple performing today?"
"What does Tesla stock look like?"
"Compare Microsoft and Apple"
```

### Layer 4: Financial Analysis
```
"stock analysis of nvidia"
"should i buy tesla"
"important metrics of apple"
```

### Layer 5: Stock Screening
```
"Screen technology sector for undervalued stocks"
"Find undervalued healthcare stocks"
"Screen financials sector"
```

### General Questions
```
"What date is it today?"
"Help me understand stock metrics"
```

---

## Configuration Options

### LLM Configuration
- **Provider Selection**: OpenRouter (paid) or local LLM (free)
- **Model Selection**: Configurable model per provider
- **Temperature**: Adjustable (default 0.1 for consistency)
- **Max Tokens**: Configurable response length

### Data Configuration
- **Cache Duration**: Daily for prices, monthly for financials
- **Validation Tolerance**: Configurable thresholds
- **Screening Limits**: 15 stocks per screening, early exit

### Self-Improvement Configuration
- **Max Improvements**: 3 per session
- **Max Logic Changes**: 1 per session
- **Cooldown Period**: 24 hours for same issue type
- **Session Timeout**: 240 seconds

---

## Performance Characteristics

### Data Operations
- **Data Download**: ~1-5 seconds per symbol/year
- **Data Validation**: ~2-10 seconds per file
- **Financial Analysis**: ~5-15 seconds per stock

### Screening Operations
- **Basic Screening**: ~1-3 minutes (50-300 stocks)
- **Intrinsic Value**: ~1-2 minutes (15 stocks)
- **Catalyst Search**: ~1-2 minutes (15 stocks)
- **Total Screening**: 2-7 minutes per sector

### API Response Times
- **Fast Path**: < 100ms (instant responses)
- **Data Requests**: 1-10 seconds
- **Financial Analysis**: 5-15 seconds
- **Screening**: 2-7 minutes

---

## File Structure

### Core Files
- `stock_agent_service.py` - Main service layer (core logic)
- `comprehensive_stock_chatbot.py` - CLI interface (legacy)
- `comprehensive_stock_chatbot_v2.py` - CLI interface (updated)
- `api_interface.py` - REST API server (Flask)
- `llm_config.py` - Unified LLM configuration

### Layer Modules
- `evaluation_module.py` - Layer 2: Data validation
- `financial_analysis_module.py` - Layer 4: Financial analysis
- `fifth_layer_screening.py` - Layer 5: Stock screening
- `sector_database.py` - Sector database builder

### Self-Improvement
- `self_improvement/conversation_logger.py` - Conversation logging
- `self_improvement/conversation_analyzer.py` - Conversation analysis
- `self_improvement/improvement_generator.py` - Improvement generation
- `self_improvement/improvement_applier.py` - Code application
- `self_improvement/improvement_pipeline.py` - Main pipeline
- `self_improvement/session_tracker.py` - Session management

### Configuration
- `config.py` - General configuration
- `api_config.py` - API key configuration (OpenRouter)
- `api_config_free.py` - Free LLM configuration
- `llm_config.json` - LLM configuration file

---

## Documentation Files

- `README.md` - Main documentation (Layers 1-4)
- `FIFTH_LAYER_README.md` - Layer 5 documentation
- `SELF_IMPROVEMENT_README.md` - Self-improvement documentation
- `INVESTMENT_CRITERIA_SUMMARY.md` - Complete screening criteria
- `FRONTEND_INTEGRATION.md` - Frontend integration guide
- `QUICK_START.md` - Quick start guide
- `IMPLEMENTATION_SUMMARY.md` - Implementation details

---

## Summary

The Stock Agent is a comprehensive, multi-layer stock analysis system that combines:
- **Intelligent data collection** with natural language understanding
- **Rigorous data validation** with dual-layer quality assurance
- **Context-aware conversations** with 15-turn memory
- **Comprehensive financial analysis** with 18+ metrics
- **Advanced stock screening** with 12 investment criteria
- **Self-improvement capabilities** that learn from conversations
- **Full REST API** for frontend integration
- **Flexible LLM support** (paid or free options)

All integrated into a cohesive system that provides professional-grade stock analysis and investment screening capabilities.

