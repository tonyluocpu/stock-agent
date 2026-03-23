#!/usr/bin/env python3
"""
Free LLM Configuration for Stock Agent Chatbot
===============================================

This configuration uses free LLM backends - no API keys needed!

Backend Options:
1. "huggingface" - Uses Hugging Face Inference API (free, no key needed)
2. "local" - Uses local transformers library (completely free, runs on your machine)
3. "ollama" - Uses Ollama if installed (completely free, local)

Default: "huggingface" (easiest to use, no setup needed)
"""

# LLM Backend Configuration
LLM_BACKEND = "huggingface"  # Options: "huggingface", "local", "ollama"

# Model Configuration (optional - uses defaults if not specified)
# Hugging Face models (free Inference API):
# - "mistralai/Mistral-7B-Instruct-v0.2" (default)
# - "meta-llama/Llama-3.1-8B-Instruct"
# - "Qwen/Qwen2.5-7B-Instruct"

# Local models (smaller, faster):
# - "microsoft/Phi-3-mini-4k-instruct" (default for local)
# - "TinyLlama/TinyLlama-1.1B-Chat-v1.0" (very small, very fast)

# Ollama models (if using Ollama):
# - "mistral:7b" (default)
# - "llama3.1:8b"
# - "qwen2.5:7b"

LLM_MODEL = None  # None = use default for selected backend

# LLM Parameters
LLM_TEMPERATURE = 0.1  # Lower = more deterministic (good for structured tasks)
LLM_MAX_TOKENS = 1000  # Maximum response length






