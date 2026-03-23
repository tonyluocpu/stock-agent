#!/usr/bin/env python3
"""Quick test to verify MPS integration works correctly."""

import torch
from llm_client_free import FreeLLMClient

print("=" * 60)
print("Testing MPS (Apple Silicon GPU) Integration")
print("=" * 60)
print()

# Check device availability
if torch.cuda.is_available():
    print("✅ CUDA available")
elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    print("✅ MPS (Apple Silicon GPU) available")
else:
    print("⚠️  Using CPU (no GPU acceleration)")

print()

# Initialize client
print("Initializing local LLM client...")
client = FreeLLMClient(backend="local", model_name="microsoft/Phi-3-mini-4k-instruct")

# Check device
device = getattr(client, 'device', 'unknown')
print(f"Device being used: {device}")
print()

# Test a simple query
print("Testing inference...")
test_query = "What is Apple's stock symbol? Answer:"
result = client.call(test_query)

if result:
    print(f"✅ Success! Response: {result[:100]}")
    print(f"   Device: {device}")
else:
    print("❌ Failed to get response")

print()
print("=" * 60)
print("Test Complete!")
print("=" * 60)




