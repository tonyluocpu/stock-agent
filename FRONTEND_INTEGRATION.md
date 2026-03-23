# Frontend Integration Guide

This guide explains how to integrate a frontend with the Stock Agent backend.

## Architecture

The codebase is now structured for easy frontend integration:

```
stock-agent/
├── stock_agent_service.py    # Backend service layer (core logic)
├── llm_config.py             # Unified LLM configuration
├── api_interface.py         # REST API server (Flask)
├── comprehensive_stock_chatbot_v2.py  # CLI interface
└── comprehensive_stock_chatbot.py      # Legacy CLI (still works)
```

## Backend Structure

### 1. Service Layer (`stock_agent_service.py`)

The service layer contains all backend logic and can be used by any frontend:

```python
from stock_agent_service import StockAgentService

service = StockAgentService()

# Process a request
result = service.process_request("Apple weekly data 2020-2024")

# Result structure:
{
    "type": "stock_data|stock_analysis|financial_analysis|general",
    "response": "Response text",
    "success": True/False,
    "data": {...}  # Optional structured data
}
```

### 2. REST API (`api_interface.py`)

A simple Flask API server ready for frontend integration:

```bash
# Start the API server
python api_interface.py

# Server runs on http://localhost:5000
```

**Endpoints:**

- `POST /api/chat` - Send chat messages
  ```json
  {
    "message": "Apple weekly data 2020-2024",
    "context": []  // Optional conversation context
  }
  ```

- `GET /api/context` - Get conversation context

- `GET /api/config` - Get current configuration

- `GET /api/health` - Health check

### 3. Configuration (`llm_config.py`)

Unified configuration system supporting both free and paid LLM options:

```python
from llm_config import get_llm_client, setup_config_interactive

# Interactive setup
setup_config_interactive()

# Get configured client
llm_client = get_llm_client()
```

## Frontend Integration Options

### Option 1: REST API (Recommended)

Use the Flask API server:

1. **Start the API server:**
   ```bash
   python api_interface.py
   ```

2. **Frontend makes HTTP requests:**
   ```javascript
   // Example JavaScript fetch
   fetch('http://localhost:5000/api/chat', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       message: 'Apple weekly data 2020-2024'
     })
   })
   .then(response => response.json())
   .then(data => console.log(data));
   ```

3. **Handle responses:**
   ```javascript
   {
     type: "stock_data",
     response: "Stock data processed...",
     success: true,
     data: {...}
   }
   ```

### Option 2: Direct Service Integration

Import the service directly (for Python-based frontends):

```python
from stock_agent_service import StockAgentService

service = StockAgentService()
result = service.process_request(user_input)
```

### Option 3: WebSocket (Future Enhancement)

For real-time streaming responses, you can extend `api_interface.py` with WebSocket support.

## Configuration for Frontend

Users can choose their LLM provider:

1. **Free LLM** (no API key needed)
   - Hugging Face Inference API
   - Local models
   - Ollama

2. **OpenRouter API** (requires API key)
   - Claude, GPT, etc.

Configuration is stored in `llm_config.json`:

```json
{
  "llm_provider": "free",
  "free_backend": "huggingface",
  "free_model": null,
  "openrouter_api_key": null,
  "openrouter_model": "anthropic/claude-3.5-sonnet"
}
```

## Frontend Features to Implement

### 1. Chat Interface
- Input field for user messages
- Display responses
- Show loading states
- Handle errors gracefully

### 2. Configuration UI
- Let users choose LLM provider
- Input API key (if using OpenRouter)
- Select backend (if using free LLM)

### 3. Request Types
Handle different response types:
- `stock_data` - Show download progress, file locations
- `stock_analysis` - Display charts, metrics
- `financial_analysis` - Show financial reports
- `general` - Display text response

### 4. Context Management
- Maintain conversation history
- Send context with each request
- Display conversation thread

## Example Frontend Code

### React Example

```jsx
import React, { useState } from 'react';

function StockAgentChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    setLoading(true);
    
    const response = await fetch('http://localhost:5000/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        message: input,
        context: messages
      })
    });
    
    const data = await response.json();
    
    setMessages([...messages, {
      user: input,
      bot: data.response,
      type: data.type
    }]);
    
    setInput('');
    setLoading(false);
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i}>
            <div>User: {msg.user}</div>
            <div>Bot: {msg.bot}</div>
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button onClick={sendMessage} disabled={loading}>
        Send
      </button>
    </div>
  );
}
```

### Vue Example

```vue
<template>
  <div>
    <div v-for="(msg, i) in messages" :key="i">
      <div>User: {{ msg.user }}</div>
      <div>Bot: {{ msg.bot }}</div>
    </div>
    <input v-model="input" @keyup.enter="sendMessage" />
    <button @click="sendMessage" :disabled="loading">Send</button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      messages: [],
      input: '',
      loading: false
    };
  },
  methods: {
    async sendMessage() {
      this.loading = true;
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: this.input })
      });
      const data = await response.json();
      this.messages.push({
        user: this.input,
        bot: data.response
      });
      this.input = '';
      this.loading = false;
    }
  }
};
</script>
```

## Next Steps

1. **Choose your frontend framework** (React, Vue, Angular, etc.)
2. **Set up the API server** (`python api_interface.py`)
3. **Implement chat interface** using the REST API
4. **Add configuration UI** for LLM provider selection
5. **Handle different response types** (stock data, analysis, etc.)

## Extending the API

To add more endpoints, edit `api_interface.py`:

```python
@app.route('/api/custom', methods=['POST'])
def custom_endpoint():
    # Your custom logic
    return jsonify({"result": "success"})
```

## Deployment

For production:

1. Use a production WSGI server (Gunicorn, uWSGI)
2. Add authentication/rate limiting
3. Use environment variables for sensitive config
4. Set up proper CORS policies
5. Add logging and monitoring

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_interface:app
```






