#!/usr/bin/env python3
"""
Free LLM Client for Stock Agent
================================

Supports multiple free LLM backends:
1. Hugging Face Inference API (free, no API key needed)
2. Local inference using transformers (completely free)
3. Ollama (if installed, completely free)

Usage:
    from llm_client_free import FreeLLMClient
    
    client = FreeLLMClient(backend="huggingface")  # or "local" or "ollama"
    response = client.call(prompt, system_prompt)
"""

import requests
import json
import os
from typing import Optional, Dict, List
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class FreeLLMClient:
    """
    Free LLM client that supports multiple backends.
    """
    
    def __init__(self, backend: str = "huggingface", model_name: Optional[str] = None):
        """
        Initialize the free LLM client.
        
        Args:
            backend: "huggingface", "local", or "ollama"
            model_name: Specific model name (optional, uses defaults if not provided)
        """
        self.backend = backend.lower()
        self.model_name = model_name
        self.local_model = None
        self.local_tokenizer = None
        
        # Default models for each backend
        self.default_models = {
            "huggingface": "mistralai/Mistral-7B-Instruct-v0.2",  # Free Inference API
            "local": "microsoft/Phi-3-mini-4k-instruct",  # Small, fast, good for structured tasks
            "ollama": "mistral:7b"  # Default Ollama model
        }
        
        if not model_name:
            self.model_name = self.default_models.get(self.backend, self.default_models["huggingface"])
        
        # Initialize backend
        if self.backend == "local":
            self._init_local_model()
        elif self.backend == "ollama":
            self._check_ollama()
    
    def _init_local_model(self):
        """Initialize local model using transformers."""
        try:
            print(f"Loading local model: {self.model_name}")
            print("This may take a few minutes on first run (downloading model)...")
            
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            # Detect available device (prioritize GPU acceleration)
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                device = "mps"  # Apple Silicon GPU (M1/M2/M3)
            else:
                device = "cpu"
            
            # Store device for later use
            self.device = device
            print(f"Using device: {device}")
            
            # Load tokenizer
            self.local_tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            
            # Load model with appropriate settings
            if device == "cpu":
                # Use 8-bit quantization for CPU to save memory
                try:
                    from transformers import BitsAndBytesConfig
                    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                    self.local_model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        quantization_config=quantization_config,
                        trust_remote_code=True,
                        device_map="auto"
                    )
                except:
                    # Fallback to regular loading if quantization fails
                    self.local_model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        trust_remote_code=True,
                        torch_dtype=torch.float32
                    ).to(device)
            elif device == "mps":
                # Apple Silicon GPU - use float16 for better performance
                self.local_model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                ).to(device)
            else:  # CUDA
                self.local_model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                ).to(device)
            
            print(f"✅ Local model loaded successfully!")
            
        except ImportError:
            print("ERROR: transformers library not installed.")
            print("Install with: pip install transformers torch")
            raise
        except Exception as e:
            print(f"ERROR: Failed to load local model: {e}")
            print("Falling back to Hugging Face Inference API...")
            self.backend = "huggingface"
            self.model_name = self.default_models["huggingface"]
    
    def _check_ollama(self):
        """Check if Ollama is available."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print("✅ Ollama is running!")
                return True
        except:
            pass
        
        print("⚠️  Ollama not detected. Install from: https://ollama.ai/")
        print("Or use: ollama pull mistral:7b")
        return False
    
    def call(self, prompt: str, system_prompt: Optional[str] = None, 
             temperature: float = 0.1, max_tokens: int = 1000) -> Optional[str]:
        """
        Call the LLM with a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or None if error
        """
        if self.backend == "huggingface":
            return self._call_huggingface_api(prompt, system_prompt, temperature, max_tokens)
        elif self.backend == "local":
            return self._call_local(prompt, system_prompt, temperature, max_tokens)
        elif self.backend == "ollama":
            return self._call_ollama(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def _call_huggingface_api(self, prompt: str, system_prompt: Optional[str], 
                              temperature: float, max_tokens: int) -> Optional[str]:
        """Call Hugging Face Inference API (free, no API key needed)."""
        try:
            # Format prompt for Hugging Face
            if system_prompt:
                formatted_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
            else:
                formatted_prompt = f"<s>[INST] {prompt} [/INST]"
            
            # Use Hugging Face Inference API (free tier)
            api_url = f"https://router.huggingface.co/hf-inference/models/{self.model_name}"
            headers = {}
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                headers["Authorization"] = f"Bearer {hf_token}"
            
            payload = {
                "inputs": formatted_prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "return_full_text": False
                }
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 503:
                # Model is loading, wait and retry
                print("⏳ Model is loading, please wait (this may take 10-20 seconds)...")
                import time
                time.sleep(15)
                response = requests.post(api_url, json=payload, headers=headers, timeout=60)
            
            if response.status_code != 200:
                error_msg = response.text
                print(f"ERROR: Hugging Face API returned {response.status_code}: {error_msg}")
                return None
            
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                if "generated_text" in result[0]:
                    return result[0]["generated_text"].strip()
                elif "text" in result[0]:
                    return result[0]["text"].strip()
            
            # Try direct text extraction
            if isinstance(result, dict):
                if "generated_text" in result:
                    return result["generated_text"].strip()
                elif "text" in result:
                    return result["text"].strip()
            
            # Fallback: return string representation
            return str(result).strip()
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Hugging Face API error: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return None
    
    def _format_messages_for_hf(self, messages: List[Dict]) -> str:
        """Format messages for Hugging Face models."""
        formatted = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                formatted.append(f"System: {content}")
            elif role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")
        
        return "\n\n".join(formatted) + "\n\nAssistant:"
    
    def _call_local(self, prompt: str, system_prompt: Optional[str],
                   temperature: float, max_tokens: int) -> Optional[str]:
        """Call local model using transformers - memory efficient."""
        if self.local_model is None or self.local_tokenizer is None:
            return None
        
        try:
            import torch
            
            # Format prompt efficiently
            if system_prompt:
                full_prompt = f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
            else:
                full_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
            
            # Tokenize with proper attention mask
            inputs = self.local_tokenizer(
                full_prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=2048,
                padding=False
            )
            
            # Move tensors to the correct device (MPS/CUDA/CPU)
            device = getattr(self, 'device', 'cpu')
            input_ids = inputs.input_ids.to(device)
            attention_mask = inputs.get('attention_mask', torch.ones_like(input_ids)).to(device)
            
            # Memory-efficient generation with proper error handling
            with torch.no_grad():
                try:
                    # Try standard generation first
                    outputs = self.local_model.generate(
                        input_ids,
                        attention_mask=attention_mask,
                        max_new_tokens=min(max_tokens, 512),  # Limit for memory efficiency
                        temperature=temperature if temperature > 0 else 1.0,
                        do_sample=temperature > 0,
                        pad_token_id=self.local_tokenizer.eos_token_id,
                        eos_token_id=self.local_tokenizer.eos_token_id,
                        repetition_penalty=1.1
                    )
                except (AttributeError, TypeError) as e:
                    # Fallback: manual generation (more memory efficient)
                    generated = input_ids.clone().to(device)
                    eos_token_id = self.local_tokenizer.eos_token_id
                    
                    for step in range(min(max_tokens, 512)):
                        # Forward pass
                        model_outputs = self.local_model(generated, use_cache=False)
                        logits = model_outputs.logits[:, -1, :]
                        
                        # Sample next token
                        if temperature > 0:
                            logits = logits / temperature
                            probs = torch.softmax(logits, dim=-1)
                            next_token = torch.multinomial(probs, 1).to(device)
                        else:
                            next_token = torch.argmax(logits, dim=-1, keepdim=True).to(device)
                        
                        generated = torch.cat([generated, next_token], dim=1)
                        
                        # Stop on EOS
                        if next_token.item() == eos_token_id:
                            break
                    
                    outputs = generated
                
                # Decode only new tokens (memory efficient)
                # Move outputs back to CPU for decoding
                if outputs.device.type != 'cpu':
                    new_tokens = outputs[0, input_ids.shape[1]:].cpu()
                else:
                    new_tokens = outputs[0, input_ids.shape[1]:]
                
                generated_text = self.local_tokenizer.decode(new_tokens, skip_special_tokens=True)
                
                # Clean up tensors (memory efficient)
                del outputs, input_ids, attention_mask
                if 'generated' in locals():
                    del generated
                if 'new_tokens' in locals() and new_tokens.device.type != 'cpu':
                    del new_tokens
                
                # Clear GPU cache if available
                if device == "cuda" and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                elif device == "mps" and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    torch.mps.empty_cache()
                
                return generated_text.strip()
            
        except Exception as e:
            print(f"ERROR: Local model inference error: {e}")
            return None
    
    def _call_ollama(self, prompt: str, system_prompt: Optional[str],
                    temperature: float, max_tokens: int) -> Optional[str]:
        """Call Ollama API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                "http://localhost:11434/api/chat",
                json=payload,
                timeout=120
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result.get("message", {}).get("content", "")
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Ollama API error: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error: {e}")
            return None


# Convenience function for easy usage
def create_llm_client(backend: str = "huggingface", model: Optional[str] = None) -> FreeLLMClient:
    """
    Create a free LLM client.
    
    Args:
        backend: "huggingface" (default), "local", or "ollama"
        model: Optional model name
    
    Returns:
        FreeLLMClient instance
    """
    return FreeLLMClient(backend=backend, model_name=model)


if __name__ == "__main__":
    # Test the client
    print("Testing Free LLM Client...")
    print("=" * 50)
    
    # Test Hugging Face API
    print("\n1. Testing Hugging Face Inference API...")
    client_hf = create_llm_client("huggingface")
    response = client_hf.call("What is 2+2? Answer in one word.")
    print(f"Response: {response}")
    
    # Test local (if transformers installed)
    try:
        print("\n2. Testing Local Model...")
        client_local = create_llm_client("local", "microsoft/Phi-3-mini-4k-instruct")
        response = client_local.call("What is 2+2? Answer in one word.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Local model test skipped: {e}")
    
    # Test Ollama (if available)
    try:
        print("\n3. Testing Ollama...")
        client_ollama = create_llm_client("ollama")
        response = client_ollama.call("What is 2+2? Answer in one word.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Ollama test skipped: {e}")
