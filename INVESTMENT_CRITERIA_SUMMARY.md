# Investment Criteria Summary
## Complete List of What We're Looking For

---

## 📋 BASIC SCREENING CRITERIA (Must Meet All)

### 1. Market Capitalization
- **Requirement**: Under $2 billion
- **Why**: Focus on smaller companies with growth potential
- **Data Source**: yfinance (real-time)
- **Update**: Daily

### 2. Price-to-Book (P/B) Ratio
- **Requirement**: Below 1.0
- **Why**: Stock trading below book value = potentially undervalued
- **Data Source**: yfinance (price daily, book value quarterly)
- **Update**: Daily (recalculate with fresh price)

### 3. Price-to-Earnings (P/E) Ratio
- **Requirement**: Less than 15
- **Why**: Low P/E = potentially undervalued relative to earnings
- **Data Source**: yfinance (real-time)
- **Update**: Daily

### 4. Shares Float
- **Requirement**: Less than 1 billion shares
- **Why**: Lower float = less dilution, more price impact potential
- **Data Source**: yfinance (shares outstanding)
- **Update**: Weekly/Monthly (changes infrequently)

### 5. Debt Structure
- **Requirement**: Must NOT have high debt (exclude companies with 50%+ debt)
- **Why**: High debt = financial risk, less flexibility
- **Calculation**: Debt / Total Assets or Debt / Equity ratio
- **Data Source**: yfinance balance sheet
- **Update**: Monthly (quarterly financials)

### 6. Profit Stability
- **Requirement**: Must NOT have profit declined by more than 10% in any year for the past 5 years
- **Why**: Consistent profitability = stable business
- **Data Source**: yfinance income statement (5 years history)
- **Update**: Quarterly (when new filings available)

---

## 🔍 ADVANCED ANALYSIS (For Stocks Passing Basic Criteria)

### 7. Intrinsic Value Calculation
**Purpose**: Determine true value of the company

#### Method 1: DCF (Discounted Cash Flow) Valuation
- **What**: Calculate value based on expected future cash flows
- **Principle**: Companies with stable, high cash flows = higher value
- **Data Needed**: 
  - Historical cash flows (5+ years)
  - Growth projections
  - Discount rate (WACC)
- **Output**: DCF intrinsic value per share

#### Method 2: Relative Valuation
- **What**: Compare to similar companies in same industry
- **Principle**: Value by comparing to peer group
- **Data Needed**:
  - Peer company valuations
  - Industry averages
  - Comparable metrics (P/E, P/B, EV/EBITDA)
- **Output**: Relative intrinsic value per share

#### Final Intrinsic Value
- **Method**: Average of DCF + Relative Valuation
- **Why**: Combines absolute and relative methods for accuracy

### 8. Warren Buffett Value Comparison
- **Requirement**: Intrinsic value > Current stock price (yesterday's closing)
- **Why**: Only invest if stock is undervalued
- **Comparison**: 
  - Intrinsic value (calculated) vs.
  - Stock price (yesterday's closing price)
- **Result**: Stock is considered "undervalued" if intrinsic value > price

---

## 🎯 CATALYST SEARCH (For Undervalued Stocks)

After finding undervalued stocks, search for catalysts that could drive price appreciation:

### 9. New Partnerships or Agreements
- **What to Look For**: 
  - Strategic partnerships
  - New contracts
  - Joint ventures
  - Supply agreements
- **Why**: Can drive revenue growth
- **Source**: News, press releases, SEC filings

### 10. Management Changes / Restructuring
- **What to Look For**:
  - New CEO/executive team
  - Management restructuring
  - Strategic shifts
  - Turnaround plans
- **Why**: New leadership can unlock value
- **Source**: SEC filings, news, company announcements

### 11. Acquisition Target / Merger Potential
- **What to Look For**:
  - M&A rumors
  - Takeover potential
  - Strategic value to acquirers
  - Industry consolidation trends
- **Why**: M&A can provide premium exit
- **Source**: News, analyst reports, industry trends

### 12. Industry-Wide Catalysts
- **What to Look For**:
  - New government policies
  - Federal Reserve policy changes
  - Regulatory changes
  - Global market adoption of industry
  - Technology shifts
  - Market trends
- **Why**: Industry tailwinds benefit all players
- **Source**: News, government websites, industry reports

---

## 📊 SCREENING WORKFLOW

### Step 1: Sector Selection
- **User Choice**: Select from 11 GICS sectors
- **Options**: 
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
- **Default**: Show list, user picks one

### Step 2: Sector Stock List
- **Source**: SEC EDGAR + yfinance sector mapping
- **Size**: 50-300 stocks per sector
- **Cached**: Locally, updated monthly

### Step 3: Basic Screening (Criteria 1-6)
- **Process**: Check each stock against all 6 basic criteria
- **Stop Condition**: Collect 15 stocks that pass all criteria
- **Order**: Process stocks one by one until 15 matches found

### Step 4: Advanced Analysis (Criteria 7-8)
- **For each of the 15 stocks**:
  1. Calculate DCF intrinsic value
  2. Calculate Relative intrinsic value
  3. Average the two = Final intrinsic value
  4. Compare to yesterday's closing price
  5. Keep only if intrinsic value > stock price
- **Result**: List of truly undervalued stocks

### Step 5: Catalyst Search (Criteria 9-12)
- **For each undervalued stock**:
  1. Search for partnerships/agreements
  2. Search for management changes
  3. Search for M&A potential
  4. Search for industry catalysts
- **Output**: Report with any catalysts found (or note if none found)

### Step 6: Final Output
- **Format**: Ranked list (most to least undervalued)
- **Display**: In chatbot conversation
- **Include**:
  - Stock symbol
  - Intrinsic value vs. current price
  - Key metrics (P/E, P/B, market cap, etc.)
  - Catalysts found (if any)
  - Investment potential score

---

## 📈 DATA REQUIREMENTS SUMMARY

### Daily Updates (Critical)
- Stock prices
- Market cap
- P/E ratio
- Current price (for comparison)

### Weekly/Monthly Updates
- P/B ratio (recalculate with fresh price)
- Shares outstanding
- Debt structure
- Financial statements (if new filings)

### Quarterly Updates
- Full financial statements
- Profit history (5 years)
- Cash flow history

---

## 🎯 FINAL GOAL

**Find 15 undervalued stocks** that:
1. ✅ Meet all 6 basic criteria
2. ✅ Have intrinsic value > current price
3. ✅ Have potential catalysts for growth

**Output**: Ranked list ready for investment decision

---

## 📝 NOTES

- **Industry Best Practices**: Use for any choosing/selection problems
- **Follow-up Analysis**: Users may want to do Layer 1-4 analysis on selected stocks
- **Data Freshness**: Critical metrics updated daily, financials monthly
- **LLM Integration**: Use local LLM for intelligent analysis and catalyst search




