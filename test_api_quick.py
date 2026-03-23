#!/usr/bin/env python3
"""
Quick test script to verify the API server works with OpenRouter
"""

import requests
import json
import time
import os

API_BASE = os.getenv("STOCK_AGENT_API_BASE", "http://localhost:5001")

def test_api():
    """Test the API endpoints."""
    print("=" * 60)
    print("Testing Stock Agent API with OpenRouter")
    print("=" * 60)
    print()
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to API server")
        print("   Make sure to run: python3 api_interface.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print()
    
    # Test 2: Config check
    print("2. Testing config endpoint...")
    try:
        response = requests.get(f"{API_BASE}/api/config", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print("   ✅ Config retrieved")
            print(f"   Provider: {config.get('llm_provider')}")
            print(f"   Model: {config.get('openrouter_model')}")
        else:
            print(f"   ❌ Config check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # Test 3: Simple chat message
    print("3. Testing chat endpoint...")
    test_message = "How is Apple performing today?"
    print(f"   Sending: '{test_message}'")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/chat",
            json={"message": test_message},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Chat request successful")
                print(f"   Type: {data.get('type')}")
                print(f"   Response preview: {data.get('response', '')[:100]}...")
            else:
                print(f"   ❌ Chat request failed: {data.get('error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except requests.exceptions.Timeout:
        print("   ⚠️  Request timed out (this might be normal for first request)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("Test complete!")
    print("=" * 60)
    print()
    print("If all tests passed, you can:")
    print("1. Open test_frontend_openrouter.html in your browser")
    print("2. Or use the API endpoints in your own frontend")
    print()
    print("API is running at: http://localhost:5000")

if __name__ == "__main__":
    test_api()





