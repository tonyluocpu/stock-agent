# Self-Improvement System

## Overview

The self-improvement system automatically analyzes conversations, identifies issues, and applies code improvements to prevent awkward conversations from happening again.

## How It Works

1. **Conversation Logging**: Every user-bot interaction is logged with metadata
2. **Session Tracking**: Heartbeat mechanism detects when frontend closes (240s timeout)
3. **Analysis**: LLM analyzes conversations to identify issues:
   - Off-topic responses (HIGH PRIORITY)
   - User confusion
   - Errors or failures
   - Missing functionality
   - Slow responses (>= 30s, except screening)
4. **Improvement Generation**: LLM generates smart, pattern-based code fixes
5. **Testing**: Validates improvements before applying
6. **Application**: Safely applies improvements with backup and rollback

## Features

- **Pattern-Based Fixes**: Never hardcodes specific responses
- **Spelling Error Handling**: Uses fuzzy matching or LLM fallback
- **Safety First**: Backups, validation, and rollback on failure
- **Limits**: Max 3 improvements per session, max 1 logic change
- **Cooldown**: 24-hour cooldown for same issue type

## API Endpoints

### Session Management
- `POST /api/session/start` - Start new session
- `POST /api/heartbeat` - Keep session alive (send every 120s)
- `POST /api/session/end` - Explicitly end session

### Improvements
- `GET /api/improvements` - List applied improvements
- `POST /api/improvements/rollback/<id>` - Rollback specific improvement

## Frontend Integration

### Starting a Session

```javascript
// On frontend load
const response = await fetch('http://localhost:5001/api/session/start', {
  method: 'POST'
});
const { session_id } = await response.json();

// Store session_id for heartbeat
```

### Sending Heartbeat

```javascript
// Every 120 seconds
setInterval(async () => {
  await fetch('http://localhost:5001/api/heartbeat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id })
  });
}, 120000); // 120 seconds
```

### Chat Requests

```javascript
// Include session_id in chat requests
const response = await fetch('http://localhost:5001/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "How is Apple doing?",
    session_id: session_id
  })
});
```

### Ending Session

```javascript
// On frontend close
window.addEventListener('beforeunload', async () => {
  await fetch('http://localhost:5001/api/session/end', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id })
  });
});
```

## Data Storage

- **Conversations**: `data/conversations/session_*.json`
- **Analysis**: `data/improvements/analysis_*.json`
- **Backups**: `data/improvements/backups/*.backup`
- **Applied**: `data/improvements/applied/*.json`
- **History**: `data/improvements/applied_history.json`

## Safety Features

1. **Backups**: Every change creates a backup
2. **Validation**: Syntax, imports, and regression tests
3. **Rollback**: Automatic rollback on test failure
4. **Fix Attempts**: System tries to fix issues before rolling back
5. **Audit Trail**: All changes logged with timestamps

## Limits

- **Max 3 improvements per session**
- **Max 1 logic change per session**
- **24-hour cooldown** for same issue type
- **Only analyzes sessions** with 2+ interactions

## Monitoring

Check improvement status:
```bash
curl http://localhost:5001/api/improvements
```

Rollback an improvement:
```bash
curl -X POST http://localhost:5001/api/improvements/rollback/imp_20240101_120000_abc123
```

## Troubleshooting

**Pipeline not running?**
- Check if LLM client is initialized
- Check logs for errors
- Verify session files are being created

**Improvements not applying?**
- Check validation errors in logs
- Verify file paths in improvements
- Check backup directory permissions

**Too many improvements?**
- System has built-in limits
- Check cooldown periods
- Review improvement history




