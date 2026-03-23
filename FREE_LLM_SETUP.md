# Free LLM Setup Guide 🆓

This guide shows you how to use **completely free** LLM backends instead of the paid OpenRouter API. No API keys needed!

## Quick Start (Easiest - Hugging Face Inference API)

The easiest option uses Hugging Face's free Inference API. **No setup needed!**

1. **Copy the free config file:**
   ```bash
   cp api_config_free.py api_config.py
   ```
   (Actually, just rename `api_config_free.py` to `api_config.py` or keep both)

2. **That's it!** The chatbot will automatically use the free Hugging Face API.

The default backend is `"huggingface"` which uses Mistral-7B-Instruct via Hugging Face's free Inference API.

## Backend Options

### 1. Hugging Face Inference API (Recommended - Easiest) ✅

**Pros:**
- ✅ No setup needed
- ✅ No API keys required
- ✅ Works immediately
- ✅ Free tier available

**Cons:**
- ⚠️ May have rate limits
- ⚠️ Requires internet connection
- ⚠️ First request may take 10-20 seconds (model loading)

**Setup:**
```python
# In api_config_free.py (or api_config.py)
LLM_BACKEND = "huggingface"
LLM_MODEL = None  # Uses default: mistralai/Mistral-7B-Instruct-v0.2
```

**Available Models:**
- `"mistralai/Mistral-7B-Instruct-v0.2"` (default)
- `"meta-llama/Llama-3.1-8B-Instruct"`
- `"Qwen/Qwen2.5-7B-Instruct"`

### 2. Local Inference (Completely Free, Runs on Your Machine) 🖥️

**Pros:**
- ✅ Completely free
- ✅ No internet needed after download
- ✅ No rate limits
- ✅ Privacy (data stays local)

**Cons:**
- ⚠️ Requires ~4-8GB RAM
- ⚠️ First run downloads model (~2-4GB)
- ⚠️ Slower than API (but still usable)

**Setup:**

1. **Install dependencies:**
   ```bash
   pip install transformers torch accelerate
   ```

2. **Configure:**
   ```python
   # In api_config_free.py
   LLM_BACKEND = "local"
   LLM_MODEL = "microsoft/Phi-3-mini-4k-instruct"  # Small, fast model
   ```

3. **Run the chatbot:**
   ```bash
   python comprehensive_stock_chatbot.py --chat
   ```

   First run will download the model (~2GB). Subsequent runs are instant!

**Recommended Local Models:**
- `"microsoft/Phi-3-mini-4k-instruct"` - Smallest, fastest (2GB)
- `"TinyLlama/TinyLlama-1.1B-Chat-v1.0"` - Very small (600MB), very fast
- `"mistralai/Mistral-7B-Instruct-v0.2"` - Better quality, larger (4GB)

### 3. Ollama (Easy Local Setup) 🦙

**Pros:**
- ✅ Easy installation
- ✅ Optimized for local inference
- ✅ Fast performance
- ✅ No Python dependencies needed

**Cons:**
- ⚠️ Requires separate installation
- ⚠️ Needs ~4-8GB RAM

**Setup:**

1. **Install Ollama:**
   - Visit: https://ollama.ai/
   - Download and install for your OS

2. **Pull a model:**
   ```bash
   ollama pull mistral:7b
   # or
   ollama pull llama3.1:8b
   ```

3. **Configure:**
   ```python
   # In api_config_free.py
   LLM_BACKEND = "ollama"
   LLM_MODEL = "mistral:7b"  # or "llama3.1:8b"
   ```

4. **Run the chatbot:**
   ```bash
   python comprehensive_stock_chatbot.py --chat
   ```

## Switching Between Backends

The chatbot automatically detects which config file you're using:

- **`api_config_free.py`** → Uses free LLM backends
- **`api_config.py`** (with OpenRouter) → Uses paid API

To switch, just rename the files or modify the import in `comprehensive_stock_chatbot.py`.

## Performance Comparison

| Backend | Speed | Quality | Setup Difficulty | Cost |
|---------|-------|---------|-------------------|------|
| Hugging Face API | Fast | High | ⭐ Easy | Free |
| Local (Phi-3) | Medium | Good | ⭐⭐ Medium | Free |
| Local (Mistral) | Medium | High | ⭐⭐ Medium | Free |
| Ollama | Fast | High | ⭐⭐ Medium | Free |
| OpenRouter API | Fastest | Highest | ⭐ Easy | Paid |

## Troubleshooting

### Hugging Face API Issues

**Problem:** "Model is loading" message
- **Solution:** Wait 10-20 seconds and try again. First request loads the model.

**Problem:** Rate limit errors
- **Solution:** Switch to local backend or wait a few minutes.

### Local Model Issues

**Problem:** Out of memory errors
- **Solution:** Use a smaller model like `Phi-3-mini` or `TinyLlama`

**Problem:** Slow inference
- **Solution:** 
  - Use CPU-optimized models (Phi-3-mini)
  - Reduce `LLM_MAX_TOKENS` in config
  - Consider using Ollama instead

### Ollama Issues

**Problem:** "Connection refused" error
- **Solution:** Make sure Ollama is running: `ollama serve`

**Problem:** Model not found
- **Solution:** Pull the model first: `ollama pull mistral:7b`

## Recommended Setup

**For most users:** Use Hugging Face Inference API (default)
- No setup needed
- Works immediately
- Good quality

**For privacy-conscious users:** Use local inference
- Data stays on your machine
- No internet needed
- Install: `pip install transformers torch`

**For best performance:** Use Ollama
- Fastest local option
- Easy to set up
- Install from: https://ollama.ai/

## Example Usage

```python
# Test the free LLM client
from llm_client_free import FreeLLMClient

# Hugging Face API (easiest)
client = FreeLLMClient(backend="huggingface")
response = client.call("What is 2+2?")
print(response)

# Local model
client = FreeLLMClient(backend="local", model_name="microsoft/Phi-3-mini-4k-instruct")
response = client.call("What is 2+2?")
print(response)

# Ollama
client = FreeLLMClient(backend="ollama", model_name="mistral:7b")
response = client.call("What is 2+2?")
print(response)
```

## Next Steps

1. Choose your backend (recommend Hugging Face API for easiest setup)
2. Update `api_config_free.py` with your choice
3. Run: `python comprehensive_stock_chatbot.py --chat`
4. Enjoy your free LLM-powered stock agent! 🚀






