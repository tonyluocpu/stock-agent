#!/usr/bin/env python3
"""
Quick test script for free LLM backends
========================================

Run this to test if your free LLM setup is working correctly.
"""

import sys

def test_free_llm():
    """Test the free LLM client."""
    print("Testing Free LLM Client...")
    print("=" * 50)
    
    try:
        from llm_client_free import FreeLLMClient
        
        # Test Hugging Face API (easiest, no setup needed)
        print("\n1. Testing Hugging Face Inference API...")
        print("   (This may take 10-20 seconds on first run - model is loading)")
        try:
            client_hf = FreeLLMClient(backend="huggingface")
            response = client_hf.call("What is 2+2? Answer with just the number.")
            if response:
                print(f"   ✅ SUCCESS! Response: {response[:100]}")
            else:
                print("   ❌ FAILED: No response received")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
        
        # Test local (if transformers installed)
        print("\n2. Testing Local Model (if transformers installed)...")
        try:
            client_local = FreeLLMClient(backend="local", model_name="microsoft/Phi-3-mini-4k-instruct")
            print("   (Downloading model on first run - this may take a few minutes)")
            response = client_local.call("What is 2+2? Answer with just the number.")
            if response:
                print(f"   ✅ SUCCESS! Response: {response[:100]}")
            else:
                print("   ❌ FAILED: No response received")
        except ImportError:
            print("   ⚠️  SKIPPED: transformers not installed")
            print("   Install with: pip install transformers torch")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
        
        # Test Ollama (if installed)
        print("\n3. Testing Ollama (if installed)...")
        try:
            import requests
            test_response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if test_response.status_code == 200:
                client_ollama = FreeLLMClient(backend="ollama", model_name="mistral:7b")
                response = client_ollama.call("What is 2+2? Answer with just the number.")
                if response:
                    print(f"   ✅ SUCCESS! Response: {response[:100]}")
                else:
                    print("   ❌ FAILED: No response received")
            else:
                print("   ⚠️  SKIPPED: Ollama not running")
        except:
            print("   ⚠️  SKIPPED: Ollama not installed or not running")
            print("   Install from: https://ollama.ai/")
        
        print("\n" + "=" * 50)
        print("Test complete!")
        print("\nRecommended: Use Hugging Face API (option 1) for easiest setup.")
        print("No installation needed - just works!")
        
    except ImportError as e:
        print(f"ERROR: Could not import llm_client_free: {e}")
        print("Make sure llm_client_free.py is in the same directory.")
        sys.exit(1)

if __name__ == "__main__":
    test_free_llm()






