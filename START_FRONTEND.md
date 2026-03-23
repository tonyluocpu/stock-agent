# Starting the Frontend

## Quick Start

Use the startup script that waits for the server to be ready:

```bash
./start_frontend.sh
```

This script will:
1. ✅ Start the API server
2. ⏳ Wait for it to be fully initialized
3. 🌐 Open the frontend only when ready

## Manual Start

If you prefer to start manually:

1. **Start API server:**
   ```bash
   python3 api_interface.py
   ```

2. **Wait for this message:**
   ```
   ✅ Stock Agent Service initialized!
   ✅ Self-improvement pipeline initialized!
   🚀 Starting API server on http://localhost:5001
   ```

3. **Then open frontend:**
   ```bash
   open test_frontend_openrouter.html
   ```

## Frontend Auto-Retry

The frontend now automatically retries connecting to the server (up to 10 times) if it's not ready yet. You'll see:
- ⏳ "Waiting for server... (1/10)" while retrying
- ✅ "Connected to API server" when ready
- ❌ Error message if server doesn't start

## Troubleshooting

**Server not starting?**
- Check logs: `tail -f /tmp/api_server.log`
- Check dependencies: `python3 -m pip install -r requirements.txt`

**Frontend shows errors?**
- Refresh the page (Cmd+R or F5)
- Check if server is running: `curl http://localhost:5001/api/health`

**Stop the server:**
```bash
pkill -f "python.*api_interface"
```




