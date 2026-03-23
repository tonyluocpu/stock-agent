# Switching Between LLM Providers

The stock agent supports **easy switching** between different LLM providers:

## Available Providers

### 1. OpenRouter (Paid API)
- **Provider**: `"openrouter"`
- **Models**: Claude 3.5 Sonnet, GPT-4, etc.
- **Requires**: API key
- **Cost**: Pay per use

### 2. Free LLM Options

#### Option A: Hugging Face Inference API (Easiest)
- **Backend**: `"huggingface"`
- **No download needed** - uses cloud API
- **Free tier available**

#### Option B: Local Model (Downloaded)
- **Backend**: `"local"`
- **Model**: `"microsoft/Phi-3-mini-4k-instruct"` (or others)
- **Requires**: transformers library installed
- **Completely free** - runs on your machine
- **First run**: Downloads model (~2-4GB)
- **Subsequent runs**: Instant (uses cached model)

#### Option C: Ollama
- **Backend**: `"ollama"`
- **Requires**: Ollama installed separately
- **Completely free** - runs locally

## How to Switch

### Method 1: Edit `llm_config.json` (Easiest)

**To use OpenRouter:**
```json
{
  "llm_provider": "openrouter",
  "openrouter_api_key": "sk-or-v1-your-key-here",
  "openrouter_model": "anthropic/claude-3.5-sonnet"
}
```

**To use Local Downloaded Model:**
```json
{
  "llm_provider": "free",
  "free_backend": "local",
  "free_model": "microsoft/Phi-3-mini-4k-instruct"
}
```

**To use Hugging Face API (no download):**
```json
{
  "llm_provider": "free",
  "free_backend": "huggingface",
  "free_model": null
}
```

### Method 2: Interactive Setup

Run:
```bash
python3 llm_config.py
```

Follow the prompts to choose your provider.

### Method 3: Environment Variables

```bash
# Use OpenRouter
export LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY=sk-or-v1-your-key

# Use Local Model
export LLM_PROVIDER=free
export LLM_FREE_BACKEND=local
```

## Current Configuration

Check your current setup:
```bash
cat llm_config.json
```

## After Switching

**For API Server:**
```bash
# Restart the API server
pkill -f api_interface.py
python3 api_interface.py
```

**For CLI:**
```bash
# Just run - it will use new config automatically
python3 comprehensive_stock_chatbot.py --chat
```

## Notes

- **Local model** requires `transformers` and `torch` installed
- **First download** of local model takes time (~2-4GB)
- **OpenRouter** requires valid API key and credits
- **Hugging Face API** is easiest - no setup, no download
- Configuration is read on startup - restart server after changing

## Quick Switch Examples

**Switch to Local Model (once downloaded):**
```bash
python3 -c "import json; c=json.load(open('llm_config.json')); c['llm_provider']='free'; c['free_backend']='local'; json.dump(c, open('llm_config.json','w'), indent=2)"
```

**Switch to OpenRouter:**
```bash
python3 -c "import json; c=json.load(open('llm_config.json')); c['llm_provider']='openrouter'; json.dump(c, open('llm_config.json','w'), indent=2)"
```

**Switch to Hugging Face API:**
```bash
python3 -c "import json; c=json.load(open('llm_config.json')); c['llm_provider']='free'; c['free_backend']='huggingface'; json.dump(c, open('llm_config.json','w'), indent=2)"
```




