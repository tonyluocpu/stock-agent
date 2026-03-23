# Frontend Test with OpenRouter

Quick guide to test the frontend with OpenRouter API.

## Setup

1. **Configuration is already set to OpenRouter** ✅
   - The `llm_config.json` is configured to use OpenRouter
   - API key is loaded from `api_config.py`

2. **Install Flask (if not already installed):**
   ```bash
   pip3 install flask flask-cors
   ```

3. **Start the API Server:**
   ```bash
   cd "stock agent"
   python3 api_interface.py
   ```
   
   You should see:
   ```
   ============================================================
   Stock Agent API Server
   ============================================================
   ✅ Stock Agent Service initialized!
      LLM Provider: openrouter
   
   🚀 Starting API server on http://localhost:5000
   Endpoints:
     POST /api/chat - Send chat messages
     GET  /api/context - Get conversation context
     GET  /api/config - Get configuration
     GET  /api/health - Health check
   ```

4. **Open the Test Frontend:**
   - Open `test_frontend_openrouter.html` in your browser
   - Or serve it with a simple HTTP server:
     ```bash
     # Python 3
     python3 -m http.server 8000
     # Then open http://localhost:8000/test_frontend_openrouter.html
     ```

## Testing

### Using the HTML Test Page

1. Make sure the API server is running (`python3 api_interface.py`)
2. Open `test_frontend_openrouter.html` in your browser
3. Try these queries:
   - "Apple weekly data from 2020 to 2024"
   - "How is Tesla performing today?"
   - "Stock analysis of NVIDIA"

### Using curl (Command Line)

```bash
# Health check
curl http://localhost:5000/api/health

# Send a message
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How is Apple performing today?"}'

# Get conversation context
curl http://localhost:5000/api/context

# Get configuration
curl http://localhost:5000/api/config
```

### Using Python

```python
import requests

# Send a message
response = requests.post(
    'http://localhost:5000/api/chat',
    json={'message': 'Apple weekly data from 2020 to 2024'}
)

data = response.json()
print(f"Type: {data['type']}")
print(f"Response: {data['response']}")
```

## API Endpoints

### POST /api/chat
Send a chat message to the stock agent.

**Request:**
```json
{
  "message": "Your question here",
  "context": []  // Optional: conversation history
}
```

**Response:**
```json
{
  "type": "stock_data|stock_analysis|financial_analysis|general",
  "response": "Response text",
  "success": true,
  "data": {}  // Optional structured data
}
```

### GET /api/health
Check if the API server is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "Stock Agent API"
}
```

### GET /api/context
Get the current conversation context.

**Response:**
```json
{
  "context": [...],
  "success": true
}
```

### GET /api/config
Get the current configuration (without sensitive data).

**Response:**
```json
{
  "llm_provider": "openrouter",
  "openrouter_model": "anthropic/claude-3.5-sonnet"
}
```

## Troubleshooting

**Error: "API server not running"**
- Make sure `python3 api_interface.py` is running
- Check that port 5000 is not in use

**Error: "OpenRouter API key not found"**
- Check that `api_config.py` has a valid API key
- Or set `OPENROUTER_API_KEY` environment variable

**CORS errors in browser**
- The API server has CORS enabled, so this shouldn't happen
- Make sure you're accessing the HTML file via `http://` not `file://`

**Connection refused**
- Make sure the API server is running
- Check firewall settings
- Try `http://127.0.0.1:5000` instead of `localhost:5000`

## Next Steps

Once you've verified the frontend works with OpenRouter:

1. **Build your own frontend** - Use the API endpoints in your React/Vue/Angular app
2. **Customize the API** - Add more endpoints in `api_interface.py`
3. **Deploy** - Use Gunicorn or similar for production

See `FRONTEND_INTEGRATION.md` for more details on building a full frontend.






