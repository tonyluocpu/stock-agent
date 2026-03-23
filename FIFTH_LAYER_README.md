# Fifth Layer: Stock Screening & Valuation System

## Overview

The fifth layer implements comprehensive stock screening to find undervalued investment opportunities based on your specific criteria.

## Features

✅ **Modular Criteria System** - Easy to add new criteria  
✅ **Fast Screening** - Efficient data fetching with caching  
✅ **Intrinsic Value Calculation** - DCF + Relative Valuation  
✅ **Catalyst Search** - LLM-powered catalyst discovery  
✅ **Sector-Based** - Screen by GICS sectors  

## Quick Start

### Via Chatbot
```
"Screen technology sector for undervalued stocks"
"Find undervalued stocks in healthcare"
"Screen financials sector"
```

### Via Code
```python
from fifth_layer_screening import FifthLayerScreening

screening = FifthLayerScreening()
results = screening.screen_sector("Technology")
print(screening.format_results(results))
```

## Investment Criteria

### Basic Screening (All Must Pass)
1. Market cap < $2B
2. P/B ratio < 1.0
3. P/E ratio < 15
4. Shares outstanding < 1B
5. Debt < 50% of assets
6. Profit decline < 10% (past 5 years)

### Advanced Analysis
7. Intrinsic value calculation (DCF + Relative)
8. Warren Buffett comparison (intrinsic > price)

### Catalyst Search
9. Partnerships/agreements
10. Management changes
11. M&A potential
12. Industry catalysts

## Architecture

### Modular Design
- **StockScreener**: Handles criteria checking (extensible)
- **ValuationEngine**: Calculates intrinsic value
- **CatalystFinder**: Searches for catalysts
- **SectorDatabaseBuilder**: Builds sector lists

### Adding New Criteria

```python
screener = StockScreener()

# Add custom criterion
def check_custom_criterion(symbol, data):
    # Your logic here
    passed = data.get('some_metric') < threshold
    reason = f"Custom check: {passed}"
    return passed, reason

screener.add_criterion('custom', check_custom_criterion)
```

## Data Management

### Caching Strategy
- **Prices/Basic Info**: Cached 1 day
- **Financials**: Cached 30 days
- **Sector Database**: Updated monthly

### Efficient Fetching
- Fetches data on-demand (not bulk)
- Uses cached data when fresh
- Auto-refreshes stale data

## Performance

- **Sector Screening**: 2-7 minutes (200 stocks)
- **Data Fetching**: ~0.1s per stock (with caching)
- **Intrinsic Value**: ~1-2s per stock
- **Catalyst Search**: ~2-5s per stock (LLM)

## Files

- `fifth_layer_screening.py` - Main screening system
- `sector_database.py` - Sector list builder
- `INVESTMENT_CRITERIA_SUMMARY.md` - Complete criteria list

## Future Enhancements

- More sophisticated DCF models
- Better relative valuation (actual peer comparison)
- Enhanced catalyst search (web scraping)
- Additional criteria (ROE, ROA, etc.)
- Portfolio optimization




