# Frontend Stock Screening Guide

## ✅ Fifth Layer Screening is Ready!

The frontend can now access the fifth layer stock screening functionality through the chat interface.

## How to Use via Frontend

### Example Queries:

1. **Screen a Sector:**
   - "Screen technology sector for undervalued stocks"
   - "Find undervalued stocks in healthcare"
   - "Screen financials sector"

2. **Natural Language:**
   - "I want to find good stocks to invest in the tech sector"
   - "Show me undervalued healthcare stocks"
   - "Screen the technology industry"

## What Happens When You Request Screening

1. **Intent Detection** - System detects this is a screening request
2. **Sector Extraction** - Extracts sector from your message
3. **Stock List** - Gets stocks in that sector (50-300 stocks)
4. **Basic Screening** - Checks 6 criteria:
   - Market cap < $2B
   - Price-to-book < 1
   - P/E < 15
   - Shares float < 1B
   - Debt < 50%
   - Profit stability (no >10% decline in 5 years)
5. **Advanced Analysis** - Calculates intrinsic value (DCF + Relative)
6. **Catalyst Search** - Finds partnerships, management changes, mergers, etc.
7. **Ranked Results** - Returns top 15 undervalued stocks

## Available Sectors

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

## Response Format

The screening results will show:
- Ranked list (most to least undervalued)
- Stock symbol and name
- Key metrics (price, intrinsic value, undervaluation %)
- Catalysts found
- All criteria results

## Time Estimates

- **Sector Screening**: 2-7 minutes (screening 50-300 stocks)
- **Basic Screening**: ~1-3 minutes
- **Intrinsic Value**: ~1-2 minutes
- **Catalyst Search**: ~1-2 minutes

## Notes

- Uses **local LLM** (free) for all analysis
- Uses **yfinance** (free API) for stock data
- No API keys needed
- Results are ranked by undervaluation percentage
- Can analyze downloaded data from layers 1-4

## Example Frontend Query

```javascript
// User types: "Screen technology sector for undervalued stocks"

// API call:
fetch('http://localhost:5001/api/chat', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'Screen technology sector for undervalued stocks'
  })
})

// Response will have:
// {
//   "type": "stock_screening",
//   "success": true,
//   "response": "Formatted ranked list...",
//   "data": [/* array of stocks */]
// }
```

## Integration Status

✅ Fifth layer module imported  
✅ Sector extraction working  
✅ Screening handler integrated  
✅ API endpoint ready  
✅ Frontend can trigger screening  

Everything is connected and ready to use!




