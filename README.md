# 🤖 LLM-Powered Stock Agent Chatbot

An intelligent stock analysis chatbot that uses Large Language Models (LLM) for natural language processing to provide real-time stock data, analysis, and general question answering.

## ✨ Features

### 🧠 **LLM-Driven Intelligence**
- **Natural Language Understanding**: Uses Claude 3.5 Sonnet for intelligent request parsing
- **Smart Symbol Extraction**: Automatically converts company names and handles misspellings
- **Intent Detection**: Intelligently classifies requests (analysis, data download, general questions)
- **Dynamic Date Handling**: Understands relative dates like "today", "last year", "up to today"

### 📊 **Stock Analysis**
- **Real-time Stock Data**: Current prices, changes, volume, market cap, P/E ratios
- **AI-Powered Insights**: Intelligent analysis of stock performance and market context
- **Multi-symbol Support**: Analyze multiple stocks simultaneously
- **Error-Free Output**: Clean, professional responses without API error spam

### 📈 **Historical Data Download**
- **Flexible Time Ranges**: Daily, weekly, monthly, yearly data
- **Smart File Management**: Organized storage with automatic file naming
- **Multiple Outputs**: Handle "and" vs "to" logic for separate files vs date ranges
- **Data Validation**: 30-day limitation handling for minute/hourly data

### 💬 **General Question Answering**
- **Broad Knowledge**: Answer questions beyond stock data
- **Current Date/Time**: Real-time date and time information
- **Conversational**: Natural chat interface

## 🚀 Quick Start

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

3. **Configure API access**
   ```bash
   # Create api_config.py with your API key
   echo 'API_KEY = "your_openrouter_api_key_here"' > api_config.py
   ```

4. **Run the chatbot**
   ```bash
   python comprehensive_stock_chatbot.py --chat
   ```

## 📖 Usage Examples

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

## 🏗️ Architecture

### LLM-Driven Design
- **No Hardcoding**: All symbol extraction, frequency mapping, and intent detection uses LLM
- **Dynamic Configuration**: Handles new companies, misspellings, and variations automatically
- **Context-Aware**: Understands current date and relative time references

### Configuration System
- **Secure**: API keys in separate config files (gitignored)
- **Modular**: Clean separation of configuration and logic
- **Extensible**: Easy to add new features and mappings

### Data Organization
```
data/
├── daily/
│   ├── opening/
│   │   └── [SYMBOL]/
│   │       └── [FILENAME].csv
│   └── closing/
│       └── [SYMBOL]/
│           └── [FILENAME].csv
├── weekly/
├── monthly/
└── yearly/
```

## 🔧 Configuration

### API Configuration (`api_config.py`)
```python
API_KEY = "your_openrouter_api_key_here"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3.5-sonnet"
```

### General Configuration (`config.py`)
- Stock symbols and mappings
- Yahoo Finance interval mappings
- File naming conventions
- Common words filters

## 🧪 Testing

```bash
# Test stock analysis
echo "how is apple performing today" | python comprehensive_stock_chatbot.py --chat

# Test data download
echo -e "apple daily data 2024\ny\ngoodbye" | python comprehensive_stock_chatbot.py --chat

# Test general questions
echo "what date is it today" | python comprehensive_stock_chatbot.py --chat
```

## 🛡️ Security

- **API Keys**: Stored in gitignored configuration files
- **Sensitive Data**: All sensitive information excluded from version control
- **Error Suppression**: Clean output without exposing API errors

## 📁 Project Structure

```
stock-agent-chatbot/
├── comprehensive_stock_chatbot.py  # Main chatbot application
├── config.py                       # General configuration
├── api_config.py                   # API configuration (gitignored)
├── agent_instruction.txt           # Core requirements
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
└── data/                          # Stock data storage (gitignored)
```

## 🔄 Key Improvements Over Traditional Approaches

1. **LLM vs Hardcoding**: Dynamic understanding vs static keyword matching
2. **Error-Free Output**: Suppressed API errors for clean user experience
3. **Smart Date Handling**: Dynamic current date awareness
4. **Flexible Symbol Extraction**: Handles misspellings and variations
5. **Intent Classification**: Intelligent request routing
6. **Secure Configuration**: Proper separation of sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the existing issues
2. Create a new issue with detailed description
3. Include error logs and configuration details

---

**Built with ❤️ using LLM intelligence for truly natural language stock analysis**