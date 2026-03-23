#!/bin/bash
# Check results after session ends

echo "============================================================"
echo "SESSION RESULTS CHECK"
echo "============================================================"
echo ""

# Check for new conversation logs
echo "📊 LOGGING STATUS:"
echo "-------------------"
NEWEST_SESSION=$(ls -t data/conversations/*.json 2>/dev/null | head -1)
if [ -n "$NEWEST_SESSION" ]; then
    echo "✅ Latest session: $(basename $NEWEST_SESSION)"
    echo "   Modified: $(stat -f "%Sm" "$NEWEST_SESSION" 2>/dev/null || stat -c "%y" "$NEWEST_SESSION" 2>/dev/null)"
    
    # Count interactions
    INTERACTIONS=$(python3 -c "import json; d=json.load(open('$NEWEST_SESSION')); print(d.get('total_interactions', 0))" 2>/dev/null)
    echo "   Interactions: $INTERACTIONS"
else
    echo "❌ No sessions found"
fi
echo ""

# Check for problems found
echo "🔍 PROBLEMS FOUND:"
echo "-------------------"
if grep -q "Found.*issues\|issue\|Issue" /tmp/api_server.log 2>/dev/null; then
    echo "✅ Issues detected in logs:"
    grep -E "Found.*issues|issue.*type|Issue" /tmp/api_server.log 2>/dev/null | tail -5
else
    echo "ℹ️  No issues detected yet (or session hasn't ended)"
fi
echo ""

# Check for fixes applied
echo "✨ FIXES APPLIED:"
echo "-------------------"
IMPROVEMENTS=$(ls data/improvements/applied/*.json 2>/dev/null | wc -l | tr -d ' ')
if [ "$IMPROVEMENTS" -gt 0 ]; then
    echo "✅ Total improvements: $IMPROVEMENTS"
    LATEST_IMPROVEMENT=$(ls -t data/improvements/applied/*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_IMPROVEMENT" ]; then
        echo "   Latest: $(basename $LATEST_IMPROVEMENT)"
    fi
else
    echo "ℹ️  No improvements applied yet"
fi

# Check for rollbacks
if grep -q "Rolled back\|rollback" /tmp/api_server.log 2>/dev/null; then
    echo "⚠️  Rollbacks detected:"
    grep -E "Rolled back|rollback" /tmp/api_server.log 2>/dev/null | tail -3
fi
echo ""

# Check pipeline activity
echo "🔄 PIPELINE ACTIVITY:"
echo "-------------------"
if grep -q "pipeline\|Pipeline\|analyzing\|Analyzing\|Generated.*improvements" /tmp/api_server.log 2>/dev/null; then
    echo "✅ Pipeline activity detected:"
    grep -E "pipeline|Pipeline|analyzing|Analyzing|Generated.*improvements|Testing improvement|Successfully applied" /tmp/api_server.log 2>/dev/null | tail -10
else
    echo "ℹ️  No pipeline activity yet (waiting for session end)"
fi
echo ""

echo "============================================================"




