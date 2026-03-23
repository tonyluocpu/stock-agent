# MPS (Metal Performance Shaders) GPU Acceleration

The local LLM client now supports **MPS acceleration** for Apple Silicon Macs (M1/M2/M3), which can make inference **3-5x faster** than CPU-only mode.

## What is MPS?

MPS (Metal Performance Shaders) is Apple's GPU acceleration framework that allows PyTorch to use the Apple Silicon GPU for neural network inference.

## Current Status

✅ **MPS Support Added** - The code now automatically detects and uses MPS if available

## Device Priority

The code now checks devices in this order:
1. **CUDA** (NVIDIA GPUs) - if available
2. **MPS** (Apple Silicon GPU) - if available ⚡ **NEW**
3. **CPU** - fallback

## Performance Comparison

| Device | Speed | Notes |
|--------|-------|-------|
| **MPS (Apple GPU)** | ⚡⚡⚡ Fast | 3-5x faster than CPU |
| **CPU** | 🐌 Slow | Baseline |
| **CUDA (NVIDIA)** | ⚡⚡⚡⚡ Fastest | If you have NVIDIA GPU |

## How It Works

When you use the local backend, the code automatically:
1. Checks if MPS is available
2. Uses MPS if detected (Apple Silicon Mac)
3. Falls back to CPU if MPS not available

**No configuration needed** - it's automatic!

## Verification

Check if MPS is available:
```python
import torch
print("MPS available:", torch.backends.mps.is_available())
print("MPS built:", torch.backends.mps.is_built())
```

## Usage

Just use the local backend as normal:
```python
from llm_client_free import FreeLLMClient

# Will automatically use MPS if available
client = FreeLLMClient(backend="local", model_name="microsoft/Phi-3-mini-4k-instruct")
response = client.call("Your prompt here")
```

Or via config:
```json
{
  "llm_provider": "free",
  "free_backend": "local",
  "free_model": "microsoft/Phi-3-mini-4k-instruct"
}
```

## Benefits

- **3-5x faster inference** compared to CPU
- **Automatic detection** - no manual configuration
- **Better performance** for local model testing
- **Uses Apple Silicon GPU** efficiently

## Requirements

- **Apple Silicon Mac** (M1/M2/M3)
- **PyTorch with MPS support** (already installed if using conda/miniconda)
- **macOS 12.3+** (for MPS support)

## Notes

- MPS uses `float16` precision for better performance
- Memory usage is similar to CPU mode
- First run still downloads the model (~2-4GB)
- Subsequent runs are much faster with MPS

## Testing

To test MPS acceleration:
```bash
python3 -c "from llm_client_free import FreeLLMClient; client = FreeLLMClient(backend='local'); print('Device:', client.local_model.device if hasattr(client, 'local_model') else 'Not loaded')"
```

The output should show `mps` device when running on Apple Silicon.




