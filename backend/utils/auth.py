"""
Authentication utilities for A1 Taxi Hosur Dev
JWT token generation and validation
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from config import Config

def generate_token(user_id, role):
    """Generate JWT token for user"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + Config.JWT_ACCESS_TOKEN_EXPIRES,
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    return token

def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token has expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token"

def token_required(allowed_roles=None):
    """
    Decorator to require JWT token authentication
    allowed_roles: list of roles that can access the endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            
            # Check for token in Authorization header
            if 'Authorization' in request.headers:
                auth_header = request.headers['Authorization']
                try:
                    token = auth_header.split(" ")[1]  # Bearer <token>
                except IndexError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid authorization header format'
                    }), 401
            
            if not token:
                return jsonify({
                    'success': False,
                    'message': 'Token is missing'
                }), 401
            
            # Verify token
            is_valid, payload = verify_token(token)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'message': payload
                }), 401
            
            # Check role permissions
            if allowed_roles and payload.get('role') not in allowed_roles:
                return jsonify({
                    'success': False,
                    'message': 'Insufficient permissions'
                }), 403
            
            # Add user info to request context
            request.current_user = {
                'id': payload['user_id'],
                'role': payload['role']
            }
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_current_user():
    """Get current authenticated user from request context"""
    return getattr(request, 'current_user', None)

def create_response(success, data=None, message=None, status_code=200):
    """Create standardized API response"""
    response = {
        'success': success,
        'timestamp': datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return jsonify(response), status_code