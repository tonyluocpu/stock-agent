#!/usr/bin/env python3
"""
Unified LLM Configuration System
================================

Allows users to choose between:
1. Free LLM (Hugging Face, Local, Ollama)
2. OpenRouter API (paid)

Usage:
    from llm_config import get_llm_client
    
    llm_client = get_llm_client()
    response = llm_client.call("Your prompt")
"""

import os
from typing import Optional, Dict, Any

# Configuration file path
CONFIG_FILE = "llm_config.json"

# Default configuration
# Default to OpenRouter (optimized for speed/quality) - Local LLM code preserved for future use
DEFAULT_CONFIG = {
    "llm_provider": "openrouter",  # "openrouter" (default, fast) or "free" (local, preserved)
    "free_backend": "local",  # Options: "huggingface", "local", "ollama" - preserved for future
    "free_model": "microsoft/Phi-3-mini-4k-instruct",  # Local model - preserved for future
    "openrouter_api_key": None,  # Set via env var OPENROUTER_API_KEY or config file
    "openrouter_model": "anthropic/claude-3.5-sonnet",  # OpenRouter model
    "temperature": 0.1,
    "max_tokens": 1000
}


def load_config() -> Dict[str, Any]:
    """Load configuration from file or environment variables."""
    import json
    
    # Try to load from file
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                final_config = {**DEFAULT_CONFIG, **config}
                return final_config
        except Exception as e:
            print(f"Warning: Could not load {CONFIG_FILE}: {e}")
            print("Using default configuration...")
    
    # Try environment variables
    config = DEFAULT_CONFIG.copy()
    
    # Check for LLM_PROVIDER env var
    if os.getenv("LLM_PROVIDER"):
        config["llm_provider"] = os.getenv("LLM_PROVIDER").lower()
    
    # Check for OpenRouter API key
    if os.getenv("OPENROUTER_API_KEY"):
        config["openrouter_api_key"] = os.getenv("OPENROUTER_API_KEY")
        config["llm_provider"] = "openrouter"  # Auto-select if key provided
    
    # Check for free backend
    if os.getenv("LLM_FREE_BACKEND"):
        config["free_backend"] = os.getenv("LLM_FREE_BACKEND").lower()
    
    # Try legacy config files for backward compatibility
    if config["llm_provider"] == "free":
        try:
            from api_config_free import LLM_BACKEND, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
            config["free_backend"] = LLM_BACKEND
            config["free_model"] = LLM_MODEL
            config["temperature"] = LLM_TEMPERATURE
            config["max_tokens"] = LLM_MAX_TOKENS
        except ImportError:
            pass
    
    if config["llm_provider"] == "openrouter" and not config["openrouter_api_key"]:
        try:
            from api_config import API_KEY, API_URL, MODEL
            config["openrouter_api_key"] = API_KEY
            config["openrouter_model"] = MODEL
        except ImportError:
            pass
    
    return config


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file."""
    import json
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_llm_client():
    """
    Get the appropriate LLM client based on configuration.
    
    Returns:
        LLM client instance (FreeLLMClient or OpenRouterClient)
    """
    config = load_config()
    
    if config["llm_provider"] == "free":
        # Use free LLM
        try:
            from llm_client_free import FreeLLMClient
            return FreeLLMClient(
                backend=config["free_backend"],
                model_name=config["free_model"]
            )
        except ImportError:
            print("ERROR: Free LLM client not found. Install dependencies or use OpenRouter.")
            raise
    
    elif config["llm_provider"] == "openrouter":
        # Use OpenRouter API
        if not config["openrouter_api_key"]:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY or update config.")
        
        try:
            from llm_client_openrouter import OpenRouterClient
            return OpenRouterClient(
                api_key=config["openrouter_api_key"],
                model=config["openrouter_model"]
            )
        except ImportError:
            # Fallback to direct API calls
            return OpenRouterClientDirect(
                api_key=config["openrouter_api_key"],
                model=config["openrouter_model"]
            )
    
    else:
        raise ValueError(f"Unknown LLM provider: {config['llm_provider']}")


class OpenRouterClientDirect:
    """Direct OpenRouter API client (fallback)."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def call(self, prompt: str, system_prompt: Optional[str] = None,
             temperature: float = 0.1, max_tokens: int = 1000) -> Optional[str]:
        """Call OpenRouter API."""
        import requests
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"ERROR: OpenRouter API error: {e}")
            return None


def setup_config_interactive():
    """Interactive setup to configure LLM provider."""
    print("=" * 60)
    print("LLM Configuration Setup")
    print("=" * 60)
    print("\nChoose your LLM provider:")
    print("1. Free LLM (Hugging Face, Local, or Ollama) - No API key needed")
    print("2. OpenRouter API (Paid) - Requires API key")
    
    while True:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            config = DEFAULT_CONFIG.copy()
            config["llm_provider"] = "free"
            
            print("\nChoose free backend:")
            print("1. Hugging Face Inference API (easiest, no setup)")
            print("2. Local model (runs on your machine)")
            print("3. Ollama (if installed)")
            
            backend_choice = input("Enter choice (1, 2, or 3): ").strip()
            if backend_choice == "1":
                config["free_backend"] = "huggingface"
            elif backend_choice == "2":
                config["free_backend"] = "local"
            elif backend_choice == "3":
                config["free_backend"] = "ollama"
            else:
                print("Invalid choice, using Hugging Face API")
                config["free_backend"] = "huggingface"
            
            break
        
        elif choice == "2":
            config = DEFAULT_CONFIG.copy()
            config["llm_provider"] = "openrouter"
            
            api_key = input("\nEnter your OpenRouter API key: ").strip()
            if not api_key:
                print("ERROR: API key required for OpenRouter")
                return False
            
            config["openrouter_api_key"] = api_key
            
            model = input("Enter model (default: anthropic/claude-3.5-sonnet): ").strip()
            if model:
                config["openrouter_model"] = model
            
            break
        
        else:
            print("Invalid choice. Please enter 1 or 2.")
    
    # Save configuration
    if save_config(config):
        print(f"\n✅ Configuration saved to {CONFIG_FILE}")
        print(f"   Provider: {config['llm_provider']}")
        if config["llm_provider"] == "free":
            print(f"   Backend: {config['free_backend']}")
        else:
            print(f"   Model: {config['openrouter_model']}")
        return True
    else:
        print("\n❌ Failed to save configuration")
        return False


if __name__ == "__main__":
    # Run interactive setup
    setup_config_interactive()



