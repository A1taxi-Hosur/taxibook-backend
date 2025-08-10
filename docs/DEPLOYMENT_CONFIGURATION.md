# Deployment Configuration - Gunicorn + Eventlet Setup

**Date**: August 10, 2025
**Status**: Configured for consistent deployment across Replit and Railway

## Updated Configuration

### 1. main.py Updated
```python
from app import app, socketio

if __name__ == '__main__':
    # Local development
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

# Production (Gunicorn + Eventlet)
# This block is only used when running via `gunicorn -k eventlet ...`
# Do NOT call socketio.run() here in production
```

### 2. Dependencies Updated (pyproject.toml)
```toml
"gunicorn==22.0.0",
"eventlet==0.36.1",
```

### 3. Required .replit Workflow Configuration
**The workflow command needs to be updated to:**
```bash
gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 main:app
```

**Current Status**: 
- ✅ Dependencies installed correctly
- ✅ main.py updated for production compatibility
- ⚠️  Workflow command needs manual update (cannot be automated)

## Manual Step Required

**To complete the setup, manually update the .replit file workflow command:**

1. Open `.replit` file
2. Find line 29: `args = "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"`
3. Replace with: `args = "gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 main:app"`

## Benefits of This Configuration

### Consistency Across Platforms
- **Replit**: Uses Gunicorn + Eventlet (same as Railway)
- **Railway**: Uses Gunicorn + Eventlet
- **No deployment differences**: Identical runtime behavior

### WebSocket Support
- **Eventlet Worker**: Proper WebSocket handling with async support
- **Single Worker**: Prevents session/memory conflicts
- **Production Ready**: Handles concurrent WebSocket connections

### Performance Improvements
- **Async I/O**: Eventlet provides async capabilities for WebSocket
- **Better Resource Usage**: More efficient than sync workers for real-time features
- **Stable Connections**: Reduces WebSocket disconnection errors

## Current WebSocket Issues

The frequent WebSocket disconnections seen in logs:
```
[WebSocket] Disconnected from WebSocket server: transport error
```

**Root Cause**: Using sync worker instead of eventlet worker
**Solution**: Update workflow command to use `-k eventlet` flag

## Verification

After updating the workflow command, verify:
1. WebSocket connections become stable
2. No more transport errors in logs
3. Real-time features work consistently
4. Same behavior as Railway deployment

## Railway Command Reference
Railway uses: `gunicorn -k eventlet -w 1 -b 0.0.0.0:$PORT main:app`
Replit should use: `gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 main:app`