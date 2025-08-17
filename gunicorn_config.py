# Gunicorn configuration for optimized WebSocket performance
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 1  # Single worker for WebSocket consistency
worker_class = 'eventlet'  # Eventlet for WebSocket support
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeouts
timeout = 120
keepalive = 5
graceful_timeout = 30

# Performance
preload_app = True
reuse_port = True

# Logging (minimal for performance)
loglevel = 'warning'
accesslog = None  # Disable access log for performance
errorlog = '-'

# SSL (if needed)
# keyfile = None
# certfile = None

# Process naming
proc_name = 'a1taxi-backend'

# Application callable
wsgi_module = 'main:app'