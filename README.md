# LLM-Powered Stock Agent Chatbot

An intelligent stock analysis chatbot that uses Large Language Models (LLM) for natural language processing to provide real-time stock data saving, analysis, and general question answering.

## Features

### **LLM-Driven Intelligence**
- **Natural Language Understanding**: Uses Claude 3.5 Sonnet for intelligent request parsing
- **Smart Symbol Extraction**: Automatically converts company names and handles misspellings
- **Intent Detection**: Intelligently classifies requests (analysis, data download, general questions)
- **Dynamic Date Handling**: Understands relative dates like "today", "last year", "up to today"

### **Stock Analysis**
- **Real-time Stock Data**: Current prices, changes, volume, market cap, P/E ratios
- **AI-Powered Insights**: analysis of stock performance and market context
- **Multi-symbol Support**: Analyze multiple stocks simultaneously
- **TIMEOUT-Free Output**: responses without API error spam

### **Historical Data Download**
- **Flexible Time Ranges**: Daily, weekly, monthly, yearly data
- **Smart File Management**: Organized storage with automatic file naming
- **Multiple Outputs**: Handle "and" vs "to" logic for separate files vs date ranges
- **Data Validation**: 30-day limitation handling for minute/hourly data

### **General Question Answering**
- **Broad Scope**: Answer questions beyond stock
- **Current Date/Time**: Real-time date and time information to verify
- **Conversational**: chat with AI!

### **Data Evaluation** 🆕
- **Price Logic Validation**: Ensures opening ≤ high and closing ≤ high for all data points
- **Frequency Validation**: Verifies correct intervals between data points (daily, weekly, monthly, yearly)
- **Trading Day Verification**: Uses web search to confirm non-trading days (weekends, holidays)
- **Web-Scraping Validation**: Cross-validates data accuracy using investpy library
- **Comprehensive Reporting**: Generates detailed evaluation reports for data quality assurance
- **User Decision Support**: Allows users to proceed or regenerate data based on validation results

#### **Evaluation Components:**
1. **Initial Evaluation** (Local):
   - Price logic checks using Polars for high-performance data processing
   - Frequency interval validation with holiday/weekend awareness
   - Trading day verification using web search APIs

2. **Web-Scraping Validation** (External):
   - Symbol and IPO date validation
   - Row count matching (exact trading day counts)
   - Volume data validation (2% tolerance)
   - Price data validation (0.8% tolerance for opening/high/closing prices)
   - Random sampling (10% of entries) for statistical accuracy

## Quick Start

### Prerequisites
- Python 3.8+
- OpenRouter API key ([Get one here](https://openrouter.ai/))

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

3. **Configure API access** (See detailed setup below)

4. **Run the chatbot**
   ```bash
   python comprehensive_stock_chatbot.py --chat
   ```

## Detailed Setup Guide

### Step 1: Get Your API Key
1. Go to [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for an account (it's free)
3. Go to your account settings/dashboard
4. Find your API key (starts with `sk-or-v1-`)
5. Copy it - you'll need it in the next step

### Step 2: Create Configuration Files

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

### Step 3: Verify Setup
Run this command to test if everything is working:
```bash
python setup.py
```

If you see "Setup complete!" you're ready to go!

### Step 4: Run the Chatbot
```bash
python comprehensive_stock_chatbot.py --chat
```

### Troubleshooting

**Error: "Configuration files not found"**
- Make sure you created `api_config.py` in the correct folder
- Check that the file has the correct name (no typos)

**Error: "API_KEY not found"**
- Make sure your API key is in quotes: `"sk-or-v1-..."`
- Don't include any extra spaces or characters

**Error: "No module named 'yfinance'"**
- Run: `pip install -r requirements.txt`

**The chatbot starts but doesn't respond to questions**
- Check your API key is valid at [OpenRouter.ai](https://openrouter.ai/)
- Make sure you have credits/usage available

## Usage Examples

### Stock Analysis
```bash
# Real-time stock analysis
"How is Apple performing today?"
"What does Tesla stock look like?"
"Compare Microsoft and Apple"
"How is NVDA looking in the past 10 minutes?"
```

### Historical Data Download
```bash
# Single stock data
"Apple weekly data from 2020 to 2023"
"Tesla daily data last year"

# Multiple stocks with "and" logic
"Apple and Microsoft weekly 2019 and 2021"
"magnificent 7 daily data from 2020 to today"

# Complex requests
"Apple daily and weekly 2024"  # Creates 2 separate files
```

### General Questions
```bash
# Non-stock related questions
"What date is it today?"
"Do you like cheese?"
"What is the 13th amendment?"
```

### Data Evaluation Features
```bash
# Automatic evaluation runs after data download
"Apple weekly data from 2020 to 2023"  # Triggers evaluation automatically
```

### Data Organization
```
data/
daily/
opening/
    [SYMBOL]/
        [FILENAME].csv
closing/
    [SYMBOL]/
        [FILENAME].csv
weekly/
monthly/
yearly/
```

### General Configuration (`config.py`)
- Data directory settings
- File naming conventions
- API validation
- Minimal essential configuration only

## Testing

```bash
# Test stock analysis
echo "how is apple performing today" | python comprehensive_stock_chatbot.py --chat

# Test data download
echo -e "apple daily data 2024\ny\ngoodbye" | python comprehensive_stock_chatbot.py --chat

# Test general questions
echo "what date is it today" | python comprehensive_stock_chatbot.py --chat
```

## Project Structure

```
stock-agent-chatbot/
comprehensive_stock_chatbot.py  # Main chatbot application
evaluation_module.py            # data validation features
config.py                       # General configuration direction
api_config.py                   # API configuration (personal)
requirements.txt                # Python dependencies
README.md                       # This file
.gitignore                      # Git ignore rules
data/                          # Stock data storage (personal)
```

## Key Improvements Over Traditional Approaches

1. **LLM vs Hardcoding**: Dynamic understanding vs static keyword matching
2. **Date Handling**: Dynamic current date awareness
3. **Flexible Symbol Extraction**: Handles misspellings and variations intelligently
4. **Intent Classification**: Intelligent request routing
5. **Multi-Layer Data Validation**: Comprehensive quality assurance with local and external validation
6. **Statistical Accuracy**: Random sampling and tolerance-based validation for data integrity

## License

This project is licensed under the MIT License - see the LICENSE file for details.