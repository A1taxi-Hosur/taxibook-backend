from app import app, socketio

if __name__ == '__main__':
    # Local development
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

# Production (Gunicorn + Eventlet)
# This block is only used when running via `gunicorn -k eventlet ...`
# Do NOT call socketio.run() here in production
