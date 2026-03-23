#!/bin/bash
# Monitor logging, problems found, and fixes applied

echo "============================================================"
echo "MONITORING: Logging, Problems Found, and Fixes Applied"
echo "============================================================"
echo ""
echo "Watching for:"
echo "  1. 📊 Conversation logging"
echo "  2. 🔍 Problems found in analysis"
echo "  3. ✨ Fixes applied"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo "============================================================"
echo ""

# Monitor API server log
tail -f /tmp/api_server.log 2>&1 | while IFS= read -r line; do
    # Logging indicators
    if echo "$line" | grep -qE "Started new conversation|Logged interaction|Session.*ended|Conversation saved"; then
        echo "📊 LOGGING: $line"
    fi
    
    # Problem detection indicators
    if echo "$line" | grep -qE "Found.*issues|issue|Issue|analyzing|Analyzing|⚠️"; then
        echo "🔍 PROBLEM: $line"
    fi
    
    # Fix application indicators
    if echo "$line" | grep -qE "Generated.*improvements|Testing improvement|Successfully applied|Rolled back|pipeline|Pipeline"; then
        echo "✨ FIXING: $line"
    fi
    
    # Error indicators
    if echo "$line" | grep -qE "ERROR|Error|error|Traceback|Failed|failed"; then
        echo "❌ ERROR: $line"
    fi
done




