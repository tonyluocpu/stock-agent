#!/bin/bash
# Start Stock Agent Frontend
# Waits for API server to be ready before opening browser

echo "🚀 Starting Stock Agent..."
echo ""

# Kill any existing API server
echo "📋 Checking for existing API server..."
pkill -f "python.*api_interface" 2>/dev/null
sleep 1

# Start API server in background
echo "🔧 Starting API server..."
cd "$(dirname "$0")"
python3 api_interface.py > /tmp/api_server.log 2>&1 &
API_PID=$!

echo "⏳ Waiting for server to be ready..."
echo ""

# Wait for server to be ready (max 30 seconds)
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
        echo "✅ API server is ready!"
        echo ""
        
        # Check if service is initialized
        sleep 2
        if curl -s http://localhost:5001/api/config > /dev/null 2>&1; then
            echo "✅ Service initialized!"
            echo ""
            echo "🌐 Opening frontend..."
            open test_frontend_openrouter.html
            echo ""
            echo "✅ Frontend opened!"
            echo ""
            echo "📊 Server logs: tail -f /tmp/api_server.log"
            echo "🛑 To stop: pkill -f 'python.*api_interface'"
            exit 0
        fi
    fi
    
    echo -n "."
    sleep 1
    WAITED=$((WAITED + 1))
done

echo ""
echo "❌ Server failed to start within $MAX_WAIT seconds"
echo "Check logs: tail -f /tmp/api_server.log"
exit 1




