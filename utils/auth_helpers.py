"""
Authentication helpers for consistent error handling across all customer API endpoints
"""
import jwt
import logging
from functools import wraps
from flask import request, jsonify, current_app


def standardized_auth_response(success=False, message="", data=None, status_code=200):
    """
    Standardized API response format for all customer endpoints
    """
    response = {
        "success": success,
        "message": message
    }
    if data is not None:
        response["data"] = data
    
    return jsonify(response), status_code


def handle_auth_error(error_type="token_expired"):
    """
    Centralized authentication error handler
    """
    error_messages = {
        "token_expired": "Your session has expired. Please login again to continue.",
        "token_invalid": "Authentication failed. Please login again.",
        "token_missing": "Authentication required. Please login to access this feature.",
        "token_format": "Invalid authentication format. Please login again."
    }
    
    message = error_messages.get(error_type, "Authentication error. Please login again.")
    
    # Log the authentication error for debugging
    logging.warning(f"Authentication error: {error_type} - {message}")
    
    return standardized_auth_response(
        success=False,
        message=message,
        data={"auth_error": True, "error_type": error_type},
        status_code=401
    )


def enhanced_token_required(f):
    """
    Enhanced JWT token authentication decorator with consistent error handling
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header (Bearer token)
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                if not auth_header.startswith('Bearer '):
                    return handle_auth_error("token_format")
                token = auth_header.split(" ")[1]
            except IndexError:
                return handle_auth_error("token_format")
        
        # Check for token in request body (fallback for mobile apps)
        elif request.is_json:
            data = request.get_json()
            if data and 'token' in data:
                token = data['token']
        
        # Check for token in form data (fallback)
        elif request.form and 'token' in request.form:
            token = request.form['token']
        
        if not token:
            return handle_auth_error("token_missing")
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            
            # Validate required fields
            required_fields = ['user_id', 'username', 'user_type']
            for field in required_fields:
                if field not in payload:
                    logging.error(f"Token missing required field: {field}")
                    return handle_auth_error("token_invalid")
            
            current_user_data = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'user_type': payload['user_type'],
                'session_token': payload.get('session_token'),
                'exp': payload.get('exp'),
                'iat': payload.get('iat')
            }
            
            # Validate session if session_token is present
            if current_user_data['session_token']:
                from utils.auth_manager import AuthenticationManager
                
                user_type = current_user_data['user_type']
                session_token = current_user_data['session_token']
                
                if user_type == 'driver':
                    user = AuthenticationManager.validate_driver_session(session_token)
                elif user_type == 'customer':
                    user = AuthenticationManager.validate_customer_session(session_token)
                else:
                    user = None
                
                if not user:
                    return handle_auth_error("token_expired")  # Session expired or invalid
            
            # Log successful token validation
            logging.info(f"JWT token validated for {current_user_data['user_type']} {current_user_data['username']}")
            
            return f(current_user_data, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            logging.warning(f"Expired JWT token attempt from {request.remote_addr}")
            return handle_auth_error("token_expired")
        except jwt.InvalidTokenError as e:
            logging.warning(f"Invalid JWT token attempt from {request.remote_addr}: {str(e)}")
            return handle_auth_error("token_invalid")
        except Exception as e:
            logging.error(f"JWT token validation error: {str(e)}")
            return handle_auth_error("token_invalid")
    
    return decorated


def check_token_validity(token):
    """
    Check if a token is valid without requiring a decorator
    Returns: (is_valid, user_data, error_type)
    """
    if not token:
        return False, None, "token_missing"
    
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        
        required_fields = ['user_id', 'username', 'user_type']
        for field in required_fields:
            if field not in payload:
                return False, None, "token_invalid"
        
        user_data = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'user_type': payload['user_type'],
            'exp': payload.get('exp'),
            'iat': payload.get('iat')
        }
        
        return True, user_data, None
        
    except jwt.ExpiredSignatureError:
        return False, None, "token_expired"
    except jwt.InvalidTokenError:
        return False, None, "token_invalid"
    except Exception:
        return False, None, "token_invalid"


def get_auth_header():
    """
    Extract and validate auth header from request
    Returns: (token, error_response)
    """
    if 'Authorization' not in request.headers:
        return None, handle_auth_error("token_missing")
    
    auth_header = request.headers['Authorization']
    
    if not auth_header.startswith('Bearer '):
        return None, handle_auth_error("token_format")
    
    try:
        token = auth_header.split(" ")[1]
        return token, None
    except IndexError:
        return None, handle_auth_error("token_format")