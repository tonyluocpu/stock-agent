# Quick Start Guide 🚀

## Choose Your LLM Provider (3 Steps)

### Step 1: Run Configuration Setup
```bash
python llm_config.py
```

Choose:
- **Option 1**: Free LLM (Hugging Face, Local, or Ollama) - No API key needed
- **Option 2**: OpenRouter API (Paid) - Requires API key

### Step 2: Run the Chatbot
```bash
# New version (recommended)
python comprehensive_stock_chatbot_v2.py --chat

# Or original version (still works)
python comprehensive_stock_chatbot.py --chat
```

### Step 3: Start Using!
```
Stock Agent> Apple weekly data 2020-2024
Stock Agent> How is Tesla performing?
Stock Agent> Stock analysis of NVIDIA
```

## For Frontend Development

### Start API Server
```bash
python api_interface.py
```

### Make API Calls
```bash
# Example curl request
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Apple weekly data 2020-2024"}'
```

See `FRONTEND_INTEGRATION.md` for full frontend guide.

## Switching Between Providers

### Change Config Anytime
```bash
python comprehensive_stock_chatbot_v2.py --config
```

Or edit `llm_config.json`:
```json
{
  "llm_provider": "free",  // or "openrouter"
  "free_backend": "huggingface"
}
```

## Files Overview

- **`llm_config.py`** - Unified configuration (choose free or paid)
- **`stock_agent_service.py`** - Backend logic (for frontend)
- **`api_interface.py`** - REST API server
- **`comprehensive_stock_chatbot_v2.py`** - New CLI
- **`comprehensive_stock_chatbot.py`** - Original CLI (still works)

## That's It! 🎉

Your stock agent now supports:
- ✅ Free LLM (no API keys)
- ✅ OpenRouter API (paid)
- ✅ User choice (easy switching)
- ✅ Frontend-ready (REST API included)






