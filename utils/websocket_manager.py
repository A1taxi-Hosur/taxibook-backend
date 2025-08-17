"""
WebSocket Manager for real-time communication
Handles driver location updates, ride status changes, and admin dashboard updates
"""

import logging
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
from functools import wraps
import jwt
import os
from datetime import datetime, timedelta

# SocketIO instance will be injected from app
socketio = None

# Active connections tracking
active_connections = {
    'drivers': {},      # driver_id: socket_id
    'customers': {},    # customer_id: socket_id  
    'admin': [],        # list of admin socket_ids
    'live_map': []      # list of live map viewer socket_ids
}

def init_websocket_handlers(socketio_instance):
    """Initialize WebSocket handlers with the SocketIO instance"""
    global socketio
    socketio = socketio_instance
    
    # Register handlers directly on the socketio instance
    socketio.on_event('connect', handle_connect)
    socketio.on_event('disconnect', handle_disconnect)
    socketio.on_event('driver_connect', handle_driver_connect)
    socketio.on_event('driver_location_update', handle_driver_location_update)
    socketio.on_event('admin_connect', handle_admin_connect)
    socketio.on_event('live_map_connect', handle_live_map_connect)

def handle_connect():
    """Handle client connection - minimal logging for performance"""
    logging.debug(f"Client connected: {request.sid}")

def handle_disconnect():
    """Handle client disconnection - minimal logging for performance"""
    logging.debug(f"Client disconnected: {request.sid}")
    cleanup_connection(request.sid)

def handle_driver_connect(data):
    """Handle driver connection"""
    try:
        # Accept both driver_id and driver_phone for flexibility
        driver_id = data.get('driver_id')
        driver_phone = data.get('driver_phone') or data.get('phone')
        socket_id = request.sid
        
        # Find driver by phone if driver_id not provided
        if not driver_id and driver_phone:
            from models import Driver
            driver = Driver.query.filter_by(phone=driver_phone).first()
            if driver:
                driver_id = driver.id
                
        if not driver_id:
            socketio.emit('error', {'message': 'Driver identification required'})
            return
            
        # Store connection
        active_connections['drivers'][driver_id] = socket_id
        socketio.server.enter_room(socket_id, f'driver_{driver_id}')
        
        logging.info(f"Driver {driver_id} connected via WebSocket (socket: {socket_id})")
        socketio.emit('connection_established', {'status': 'connected', 'driver_id': driver_id})
        
        # Notify admin about new driver connection
        socketio.emit('driver_connected', {
            'driver_id': driver_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room='admin')
        
    except Exception as e:
        logging.error(f"Error in driver_connect: {str(e)}")
        socketio.emit('error', {'message': 'Connection failed'})

def handle_driver_location_update(data):
    """Handle real-time driver location updates via WebSocket"""
    try:
        logging.info(f"=== WEBSOCKET LOCATION UPDATE ===")
        logging.info(f"Received WebSocket location data: {data}")
        
        # Extract location data
        latitude = data.get('latitude') or data.get('lat')
        longitude = data.get('longitude') or data.get('lng')
        driver_phone = data.get('driver_phone') or data.get('phone')
        driver_id = data.get('driver_id')
        
        if not latitude or not longitude:
            socketio.emit('error', {'message': 'Missing latitude or longitude'})
            return
            
        # Find driver by phone if driver_id not provided
        if not driver_id and driver_phone:
            from models import Driver
            driver = Driver.query.filter_by(phone=driver_phone).first()
            if driver:
                driver_id = driver.id
                
        if not driver_id:
            socketio.emit('error', {'message': 'Driver identification required'})
            return
            
        # Import models here to avoid circular imports
        from models import Driver, RideLocation, Ride
        from app import db, get_ist_time
        
        driver = Driver.query.get(driver_id)
        if not driver:
            socketio.emit('error', {'message': 'Driver not found'})
            return
            
        # Update driver location
        driver.current_lat = float(latitude)
        driver.current_lng = float(longitude) 
        driver.location_updated_at = get_ist_time()
        driver.is_online = True
        driver.last_seen = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"✅ WEBSOCKET: Updated location for driver {driver.name} ({driver.phone})")
        logging.info(f"✅ WEBSOCKET: Location: ({latitude}, {longitude})")
        
        # Broadcast to admin dashboard and live map
        broadcast_driver_location_update(driver)
        
        # Confirm successful update to driver app
        socketio.emit('location_update_success', {
            'driver_id': driver_id,
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': driver.location_updated_at.isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error in WebSocket location update: {str(e)}")
        socketio.emit('error', {'message': 'Location update failed'})

def handle_admin_connect(data):
    """Handle admin dashboard connection"""
    try:
        socket_id = request.sid
        
        # Store connection (no auth required for admin in same session)
        active_connections['admin'].append(socket_id)
        socketio.server.enter_room(socket_id, 'admin')
        
        logging.info(f"Admin connected via WebSocket (socket: {socket_id})")
        socketio.emit('connection_established', {'status': 'connected', 'type': 'admin'})
        
    except Exception as e:
        logging.error(f"Error in admin_connect: {str(e)}")
        socketio.emit('error', {'message': 'Connection failed'})

def handle_live_map_connect(data):
    """Handle live map viewer connection"""
    try:
        socket_id = request.sid
        
        # Store connection
        active_connections['live_map'].append(socket_id)
        socketio.server.enter_room(socket_id, 'live_map')
        
        logging.info(f"Live map viewer connected via WebSocket")
        socketio.emit('connection_established', {'status': 'connected', 'type': 'live_map'})
        
    except Exception as e:
        logging.error(f"Error in live_map_connect: {str(e)}")
        socketio.emit('error', {'message': 'Connection failed'})

def authenticate_socket(token_required=True):
    """Decorator to authenticate WebSocket connections"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not token_required:
                return f(*args, **kwargs)
                
            # Get token from handshake auth
            token = None
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                logging.warning(f"WebSocket: No token provided for {f.__name__}")
                emit('error', {'message': 'Authentication required'})
                return False
                
            try:
                # Decode JWT token
                secret_key = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-here')
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                
                # Add user info to request context
                request.user_id = payload.get('user_id')
                request.user_type = payload.get('user_type')
                
                return f(*args, **kwargs)
                
            except jwt.ExpiredSignatureError:
                logging.warning(f"WebSocket: Token expired for {f.__name__}")
                emit('error', {'message': 'Token expired'})
                return False
            except jwt.InvalidTokenError:
                logging.warning(f"WebSocket: Invalid token for {f.__name__}")
                emit('error', {'message': 'Invalid token'})
                return False
                
        return decorated
    return decorator

# These functions are registered dynamically in init_websocket_handlers()

# Ride Status Events (broadcasted from backend)
def broadcast_ride_status_update(ride_data):
    """Broadcast ride status updates to relevant clients"""
    try:
        # Notify customer
        if ride_data.get('customer_id'):
            socketio.emit('ride_status_updated', ride_data, 
                         room=f'customer_{ride_data["customer_id"]}')
        
        # Notify driver
        if ride_data.get('driver_id'):
            socketio.emit('ride_status_updated', ride_data,
                         room=f'driver_{ride_data["driver_id"]}')
        
        # Notify admin dashboard
        socketio.emit('ride_status_updated', ride_data, room='admin')
        
        logging.info(f"Broadcasted ride status update for ride {ride_data.get('ride_id')}")
        
    except Exception as e:
        logging.error(f"Error broadcasting ride status: {str(e)}")

def broadcast_new_ride_request(ride_data, eligible_drivers):
    """Broadcast new ride requests to eligible drivers"""
    try:
        for driver_id in eligible_drivers:
            socket_id = active_connections['drivers'].get(driver_id)
            if socket_id:
                socketio.emit('new_ride_request', ride_data, 
                             room=f'driver_{driver_id}')
                logging.info(f"Sent ride request to driver {driver_id} via WebSocket")
        
        # Also notify admin
        socketio.emit('new_ride_created', ride_data, room='admin')
        
    except Exception as e:
        logging.error(f"Error broadcasting new ride request: {str(e)}")

# Connection management
def cleanup_connection(socket_id):
    """Clean up connection tracking for a disconnected socket"""
    try:
        # Remove from all connection tracking
        for driver_id, sid in list(active_connections['drivers'].items()):
            if sid == socket_id:
                del active_connections['drivers'][driver_id]
                logging.info(f"Driver {driver_id} disconnected")
                break
                
        for customer_id, sid in list(active_connections['customers'].items()):
            if sid == socket_id:
                del active_connections['customers'][customer_id]
                logging.info(f"Customer {customer_id} disconnected")
                break
                
        if socket_id in active_connections['admin']:
            active_connections['admin'].remove(socket_id)
            logging.info("Admin disconnected")
            
        if socket_id in active_connections['live_map']:
            active_connections['live_map'].remove(socket_id)
            logging.info("Live map viewer disconnected")
            
    except Exception as e:
        logging.error(f"Error handling disconnect: {str(e)}")

# Utility functions
def get_connected_drivers():
    """Get list of currently connected driver IDs"""
    return list(active_connections['drivers'].keys())

def get_connected_customers():
    """Get list of currently connected customer IDs"""
    return list(active_connections['customers'].keys())

def is_driver_connected(driver_id):
    """Check if a driver is currently connected"""
    return driver_id in active_connections['drivers']

def is_customer_connected(customer_id):
    """Check if a customer is currently connected"""
    return customer_id in active_connections['customers']

# Dashboard stats broadcasting
def broadcast_dashboard_stats(stats_data):
    """Broadcast updated dashboard statistics to admin clients"""
    try:
        if socketio:
            socketio.emit('dashboard_stats_updated', stats_data, room='admin')
            logging.debug("Broadcasted dashboard stats update")
    except Exception as e:
        logging.error(f"Error broadcasting dashboard stats: {str(e)}")

def broadcast_driver_list_update(drivers_data):
    """Broadcast updated driver list to live map viewers"""
    try:
        if socketio:
            socketio.emit('driver_list_updated', drivers_data, room='live_map')
            logging.debug("Broadcasted driver list update to live map")
    except Exception as e:
        logging.error(f"Error broadcasting driver list: {str(e)}")

def broadcast_driver_location_update(location_data):
    """Broadcast driver location update to admin and live map"""
    try:
        if socketio:
            socketio.emit('driver_location_updated', location_data, room='admin')
            socketio.emit('driver_location_updated', location_data, room='live_map')
            logging.debug(f"Broadcasted location update for driver {location_data.get('driver_id')}")
    except Exception as e:
        logging.error(f"Error broadcasting driver location: {str(e)}")

def broadcast_ride_status_update(ride_data):
    """Broadcast ride status updates to relevant clients"""
    try:
        if socketio:
            # Broadcast to admin dashboard
            socketio.emit('ride_status_updated', ride_data, room='admin')
            
            # Broadcast to specific driver if assigned
            if ride_data.get('driver_id'):
                socketio.emit('ride_status_updated', ride_data, room=f'driver_{ride_data["driver_id"]}')
            
            # Broadcast to specific customer
            if ride_data.get('customer_id'):
                socketio.emit('ride_status_updated', ride_data, room=f'customer_{ride_data["customer_id"]}')
            
            logging.debug(f"Broadcasted ride status update for ride {ride_data.get('ride_id')}")
    except Exception as e:
        logging.error(f"Error broadcasting ride status: {str(e)}")

def broadcast_new_ride_request(ride_data, target_drivers=None):
    """Broadcast new ride request to available drivers"""
    try:
        if socketio and target_drivers:
            for driver_id in target_drivers:
                socketio.emit('new_ride_request', ride_data, room=f'driver_{driver_id}')
            logging.debug(f"Broadcasted new ride request to {len(target_drivers)} drivers")
    except Exception as e:
        logging.error(f"Error broadcasting new ride request: {str(e)}")