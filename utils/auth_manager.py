"""
Centralized Authentication Manager - Complete token and session management system
This module consolidates all authentication logic in one place for easy management
"""

import os
import jwt
import logging
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
# Import will be done inside functions to avoid circular imports

# Configuration constants (easy to modify)
class AuthConfig:
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRY_HOURS = 24 * 7  # 7 days for mobile apps
    SESSION_DURATION_HOURS = 24 * 30  # 30 days for session tokens
    HEARTBEAT_TIMEOUT_MINUTES = 30  # Driver considered offline after this
    
    # Authentication modes - can be easily toggled
    REQUIRE_SESSION_VALIDATION = True
    ENABLE_JWT_TOKENS = False  # DISABLED FOR TESTING
    ENABLE_DEBUG_LOGGING = True
    
    @classmethod
    def set_debug_logging(cls, enabled):
        cls.ENABLE_DEBUG_LOGGING = enabled
    
    @classmethod
    def set_session_validation(cls, enabled):
        cls.REQUIRE_SESSION_VALIDATION = enabled
        
    @classmethod
    def set_jwt_tokens(cls, enabled):
        cls.ENABLE_JWT_TOKENS = enabled
        
    @classmethod
    def set_session_duration(cls, hours):
        cls.SESSION_DURATION_HOURS = hours
        
    @classmethod
    def set_jwt_expiry(cls, hours):
        cls.JWT_EXPIRY_HOURS = hours
    
    # Error messages (centralized for consistency)
    ERRORS = {
        "token_expired": "Your session has expired. Please login again to continue.",
        "token_invalid": "Authentication failed. Please login again.",
        "token_missing": "Authentication required. Please login to access this feature.",
        "token_format": "Invalid authentication format. Please login again.",
        "session_expired": "Your session has expired. Please login again.",
        "user_not_found": "User not found. Please login again."
    }


class AuthenticationManager:
    """Centralized authentication management system"""
    
    @staticmethod
    def get_jwt_secret():
        """Get JWT secret key from environment with fallback"""
        return os.environ.get("JWT_SECRET_KEY") or current_app.config.get('SECRET_KEY') or "a1taxi-jwt-secret-key"
    
    @staticmethod
    def generate_session_token():
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_jwt_token(user_data):
        """
        Create JWT token with standardized payload
        Args:
            user_data: dict with keys: user_id, username, user_type, session_token (optional)
        """
        if not AuthConfig.ENABLE_JWT_TOKENS:
            return None
            
        now = datetime.utcnow()
        payload = {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'user_type': user_data['user_type'],
            'iat': now,
            'exp': now + timedelta(hours=AuthConfig.JWT_EXPIRY_HOURS)
        }
        
        # Add session token if provided
        if user_data.get('session_token'):
            payload['session_token'] = user_data['session_token']
            
        try:
            token = jwt.encode(payload, AuthenticationManager.get_jwt_secret(), algorithm=AuthConfig.JWT_ALGORITHM)
            if AuthConfig.ENABLE_DEBUG_LOGGING:
                logging.debug(f"Created JWT token for {user_data['user_type']} {user_data['username']}")
            return token
        except Exception as e:
            logging.error(f"Error creating JWT token: {str(e)}")
            return None
    
    @staticmethod
    def decode_jwt_token(token):
        """
        Decode and validate JWT token
        Returns: (success, payload_or_error, error_type)
        """
        if not token or not AuthConfig.ENABLE_JWT_TOKENS:
            return False, "Token required", "token_missing"
            
        try:
            payload = jwt.decode(token, AuthenticationManager.get_jwt_secret(), algorithms=[AuthConfig.JWT_ALGORITHM])
            
            # Validate required fields
            required_fields = ['user_id', 'username', 'user_type']
            for field in required_fields:
                if field not in payload:
                    logging.error(f"Token missing required field: {field}")
                    return False, f"Invalid token: missing {field}", "token_invalid"
            
            return True, payload, None
            
        except jwt.ExpiredSignatureError:
            if AuthConfig.ENABLE_DEBUG_LOGGING:
                logging.warning(f"Expired JWT token from {request.remote_addr if request else 'unknown'}")
            return False, "Token expired", "token_expired"
        except jwt.InvalidTokenError as e:
            if AuthConfig.ENABLE_DEBUG_LOGGING:
                logging.warning(f"Invalid JWT token: {str(e)}")
            return False, "Invalid token", "token_invalid"
        except Exception as e:
            logging.error(f"JWT token validation error: {str(e)}")
            return False, "Token validation failed", "token_invalid"
    
    @staticmethod
    def extract_token_from_request():
        """
        Extract JWT token from request (multiple sources)
        Returns: (token, error_type)
        """
        token = None
        
        # Priority 1: Authorization header (Bearer token)
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                if not auth_header.startswith('Bearer '):
                    return None, "token_format"
                token = auth_header.split(" ")[1]
            except IndexError:
                return None, "token_format"
                
        # Priority 2: Request body (for mobile apps)
        elif request.is_json:
            data = request.get_json()
            if data and 'token' in data:
                token = data['token']
                
        # Priority 3: Form data (fallback)
        elif request.form and 'token' in request.form:
            token = request.form['token']
            
        if not token:
            return None, "token_missing"
            
        return token, None
    
    @staticmethod
    def create_driver_session(driver):
        """Create new driver session, invalidating existing ones"""
        # Invalidate existing sessions
        AuthenticationManager.invalidate_driver_sessions(driver.id)
        
        # Create new session
        session_token = AuthenticationManager.generate_session_token()
        from app import get_ist_time
        from models import db
        now = get_ist_time()
        expires = now + timedelta(hours=AuthConfig.SESSION_DURATION_HOURS)
        
        driver.session_token = session_token
        driver.last_seen = now
        driver.session_expires = expires
        driver.is_online = True
        
        db.session.commit()
        logging.info(f"Created new session for driver {driver.name} (ID: {driver.id})")
        
        return session_token
    
    @staticmethod
    def create_customer_session(customer):
        """Create new customer session, invalidating existing ones"""
        # Invalidate existing sessions
        AuthenticationManager.invalidate_customer_sessions(customer.id)
        
        # Create new session
        session_token = AuthenticationManager.generate_session_token()
        from app import get_ist_time
        from models import db
        now = get_ist_time()
        expires = now + timedelta(hours=AuthConfig.SESSION_DURATION_HOURS)
        
        customer.session_token = session_token
        customer.last_seen = now
        customer.session_expires = expires
        customer.is_online = True
        
        db.session.commit()
        logging.info(f"Created new session for customer {customer.name} (ID: {customer.id})")
        
        return session_token
    
    @staticmethod
    def validate_driver_session(session_token):
        """Validate driver session and return driver if valid"""
        if not session_token or not AuthConfig.REQUIRE_SESSION_VALIDATION:
            return None
            
        from models import Driver, db
        from app import get_ist_time
        
        driver = Driver.query.filter_by(session_token=session_token).first()
        if not driver:
            return None
            
        # Check if session expired
        now = get_ist_time()
        if not driver.session_expires or now >= driver.session_expires:
            # Session expired, mark offline
            AuthenticationManager.invalidate_driver_sessions(driver.id)
            return None
            
        # Update last seen (heartbeat)
        driver.last_seen = now
        db.session.commit()
        
        return driver
    
    @staticmethod
    def validate_customer_session(session_token):
        """Validate customer session and return customer if valid"""
        if not session_token or not AuthConfig.REQUIRE_SESSION_VALIDATION:
            return None
            
        from models import Customer, db
        from app import get_ist_time
        
        customer = Customer.query.filter_by(session_token=session_token).first()
        if not customer:
            return None
            
        # Check if session expired
        now = get_ist_time()
        if not customer.session_expires or now >= customer.session_expires:
            # Session expired, mark offline
            AuthenticationManager.invalidate_customer_sessions(customer.id)
            return None
            
        # Update last seen
        customer.last_seen = now
        db.session.commit()
        
        return customer
    
    @staticmethod
    def invalidate_driver_sessions(driver_id):
        """Invalidate all sessions for a driver"""
        from models import Driver, db
        driver = Driver.query.get(driver_id)
        if driver:
            driver.session_token = None
            driver.session_expires = None
            driver.is_online = False
            db.session.commit()
            logging.info(f"Invalidated sessions for driver {driver.name} (ID: {driver_id})")
    
    @staticmethod
    def invalidate_customer_sessions(customer_id):
        """Invalidate all sessions for a customer"""
        from models import Customer, db
        customer = Customer.query.get(customer_id)
        if customer:
            customer.session_token = None
            customer.session_expires = None
            customer.is_online = False
            db.session.commit()
            logging.info(f"Invalidated sessions for customer {customer.name} (ID: {customer_id})")
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired sessions (background task)"""
        from models import Driver, Customer
        from app import get_ist_time
        
        now = get_ist_time()
        
        # Find expired driver sessions
        expired_drivers = Driver.query.filter(
            Driver.session_expires.isnot(None),
            Driver.session_expires < now
        ).all()
        
        # Find expired customer sessions
        expired_customers = Customer.query.filter(
            Customer.session_expires.isnot(None),
            Customer.session_expires < now
        ).all()
        
        # Cleanup expired sessions
        for driver in expired_drivers:
            AuthenticationManager.invalidate_driver_sessions(driver.id)
            
        for customer in expired_customers:
            AuthenticationManager.invalidate_customer_sessions(customer.id)
            
        if expired_drivers or expired_customers:
            logging.info(f"Cleaned up {len(expired_drivers)} expired driver sessions and {len(expired_customers)} expired customer sessions")
    
    @staticmethod
    def create_auth_response(success=False, message="", data=None, status_code=200):
        """Standardized authentication response format"""
        response = {
            "success": success,
            "message": message
        }
        if data is not None:
            response["data"] = data
        return jsonify(response), status_code
    
    @staticmethod
    def handle_auth_error(error_type="token_invalid"):
        """Handle authentication errors with consistent responses"""
        message = AuthConfig.ERRORS.get(error_type, "Authentication error. Please login again.")
        
        if AuthConfig.ENABLE_DEBUG_LOGGING:
            logging.warning(f"Authentication error: {error_type} - {message}")
        
        return AuthenticationManager.create_auth_response(
            success=False,
            message=message,
            data={"auth_error": True, "error_type": error_type},
            status_code=401
        )


# Centralized decorator for token authentication
def token_required(f):
    """
    Centralized JWT token authentication decorator
    Usage: @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract token from request
        token, error_type = AuthenticationManager.extract_token_from_request()
        if error_type:
            return AuthenticationManager.handle_auth_error(error_type)
        
        # Decode and validate JWT token
        success, payload_or_error, error_type = AuthenticationManager.decode_jwt_token(token)
        if not success:
            if error_type:
                return AuthenticationManager.handle_auth_error(error_type)
            else:
                return AuthenticationManager.handle_auth_error("token_invalid")
        
        payload = payload_or_error
        current_user_data = {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),  
            'user_type': payload.get('user_type'),
            'session_token': payload.get('session_token'),
            'exp': payload.get('exp'),
            'iat': payload.get('iat')
        }
        
        # Validate session if session_token is present and validation is enabled
        if AuthConfig.REQUIRE_SESSION_VALIDATION and current_user_data.get('session_token'):
            session_token = current_user_data['session_token']
            user_type = current_user_data['user_type']
            
            if user_type == 'driver':
                user = AuthenticationManager.validate_driver_session(session_token)
            elif user_type == 'customer':
                user = AuthenticationManager.validate_customer_session(session_token)
            else:
                user = None
                
            if not user:
                return AuthenticationManager.handle_auth_error("session_expired")
        
        # Log successful authentication
        if AuthConfig.ENABLE_DEBUG_LOGGING:
            logging.info(f"JWT authenticated: {current_user_data['user_type']} {current_user_data['username']}")
        
        return f(current_user_data, *args, **kwargs)
    
    return decorated


# Easy configuration functions
def set_auth_debug(enabled=True):
    """Enable/disable authentication debug logging"""
    AuthConfig.set_debug_logging(enabled)

def set_session_validation(enabled=True):
    """Enable/disable session validation"""
    AuthConfig.set_session_validation(enabled)

def set_jwt_tokens(enabled=True):
    """Enable/disable JWT token system"""
    AuthConfig.set_jwt_tokens(enabled)

def set_session_duration(hours=720):
    """Set session duration in hours (default: 30 days)"""
    AuthConfig.set_session_duration(hours)

def set_jwt_expiry(hours=168):
    """Set JWT token expiry in hours (default: 7 days)"""
    AuthConfig.set_jwt_expiry(hours)