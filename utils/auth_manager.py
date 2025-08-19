"""
JWT Authentication Manager - Complete JWT-based authentication system
This module provides comprehensive JWT authentication for mobile apps and API access
"""

import os
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app

# Configuration constants
class AuthConfig:
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRY_HOURS = 24  # 24 hours for access tokens
    JWT_REFRESH_TOKEN_EXPIRY_DAYS = 30  # 30 days for refresh tokens
    
    # Authentication modes
    ENABLE_DEBUG_LOGGING = True
    
    @classmethod
    def set_debug_logging(cls, enabled):
        cls.ENABLE_DEBUG_LOGGING = enabled
        
    @classmethod
    def set_access_token_expiry(cls, hours):
        cls.JWT_ACCESS_TOKEN_EXPIRY_HOURS = hours
        
    @classmethod
    def set_refresh_token_expiry(cls, days):
        cls.JWT_REFRESH_TOKEN_EXPIRY_DAYS = days
    
    # Error messages (centralized for consistency)
    ERRORS = {
        "token_expired": "Your session has expired. Please login again to continue.",
        "token_invalid": "Authentication failed. Please login again.",
        "token_missing": "Authentication required. Please login to access this feature.",
        "token_format": "Invalid authentication format. Please login again.",
        "refresh_token_expired": "Your session has expired. Please login again.",
        "user_not_found": "User not found. Please login again.",
        "invalid_credentials": "Invalid phone number or password."
    }


class JWTAuthenticationManager:
    """JWT-based authentication management system"""
    
    @staticmethod
    def get_jwt_secret():
        """Get JWT secret key from environment with fallback"""
        return os.environ.get("JWT_SECRET_KEY") or current_app.config.get('SECRET_KEY') or "a1taxi-jwt-secret-key"
    
    @staticmethod
    def create_access_token(user_data):
        """
        Create JWT access token
        Args:
            user_data: dict with keys: user_id, username, user_type, phone
        Returns:
            JWT access token string
        """
        now = datetime.utcnow()
        payload = {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'user_type': user_data['user_type'],
            'phone': user_data['phone'],
            'token_type': 'access',
            'iat': now,
            'exp': now + timedelta(hours=AuthConfig.JWT_ACCESS_TOKEN_EXPIRY_HOURS)
        }
        
        try:
            token = jwt.encode(payload, JWTAuthenticationManager.get_jwt_secret(), algorithm=AuthConfig.JWT_ALGORITHM)
            if AuthConfig.ENABLE_DEBUG_LOGGING:
                logging.debug(f"Created access token for {user_data['user_type']} {user_data['username']}")
            return token
        except Exception as e:
            logging.error(f"Error creating access token: {str(e)}")
            return None
    
    @staticmethod
    def create_refresh_token(user_data):
        """
        Create JWT refresh token
        Args:
            user_data: dict with keys: user_id, username, user_type, phone
        Returns:
            JWT refresh token string
        """
        now = datetime.utcnow()
        payload = {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'user_type': user_data['user_type'],
            'phone': user_data['phone'],
            'token_type': 'refresh',
            'iat': now,
            'exp': now + timedelta(days=AuthConfig.JWT_REFRESH_TOKEN_EXPIRY_DAYS)
        }
        
        try:
            token = jwt.encode(payload, JWTAuthenticationManager.get_jwt_secret(), algorithm=AuthConfig.JWT_ALGORITHM)
            if AuthConfig.ENABLE_DEBUG_LOGGING:
                logging.debug(f"Created refresh token for {user_data['user_type']} {user_data['username']}")
            return token
        except Exception as e:
            logging.error(f"Error creating refresh token: {str(e)}")
            return None
    
    @staticmethod
    def create_token_pair(user_data):
        """
        Create both access and refresh tokens
        Returns:
            dict with access_token and refresh_token
        """
        access_token = JWTAuthenticationManager.create_access_token(user_data)
        refresh_token = JWTAuthenticationManager.create_refresh_token(user_data)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': AuthConfig.JWT_ACCESS_TOKEN_EXPIRY_HOURS * 3600,  # seconds
            'token_type': 'Bearer'
        }
    
    @staticmethod
    def decode_jwt_token(token, token_type='access'):
        """
        Decode and validate JWT token
        Args:
            token: JWT token string
            token_type: 'access' or 'refresh'
        Returns: (success, payload_or_error, error_type)
        """
        if not token:
            return False, "Token required", "token_missing"
            
        try:
            payload = jwt.decode(token, JWTAuthenticationManager.get_jwt_secret(), algorithms=[AuthConfig.JWT_ALGORITHM])
            
            # Validate token type
            if payload.get('token_type') != token_type:
                return False, f"Invalid token type. Expected {token_type}", "token_invalid"
            
            # Validate required fields
            required_fields = ['user_id', 'username', 'user_type', 'phone']
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
    def validate_user_credentials(phone, password, user_type):
        """
        Validate user credentials for login
        Args:
            phone: Phone number
            password: Password (optional for OTP-based auth)
            user_type: 'driver' or 'customer'
        Returns:
            (success, user_or_error, error_type)
        """
        try:
            if user_type == 'driver':
                from models import Driver
                user = Driver.query.filter_by(phone=phone).first()
                if not user:
                    return False, "Driver not found", "user_not_found"
                    
                # If password is provided, validate it
                if password and user.password_hash:
                    from werkzeug.security import check_password_hash
                    if not check_password_hash(user.password_hash, password):
                        return False, "Invalid credentials", "invalid_credentials"
                
                return True, user, None
                
            elif user_type == 'customer':
                from models import Customer
                user = Customer.query.filter_by(phone=phone).first()
                if not user:
                    return False, "Customer not found", "user_not_found"
                    
                return True, user, None
                
            else:
                return False, "Invalid user type", "token_invalid"
                
        except Exception as e:
            logging.error(f"Error validating user credentials: {str(e)}")
            return False, "Validation error", "token_invalid"
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """
        Generate new access token using refresh token
        Args:
            refresh_token: Valid refresh token
        Returns:
            dict with new access token or error
        """
        success, payload_or_error, error_type = JWTAuthenticationManager.decode_jwt_token(refresh_token, 'refresh')
        if not success:
            return {"success": False, "error": error_type, "message": payload_or_error}
        
        payload = payload_or_error
        user_data = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'user_type': payload['user_type'],
            'phone': payload['phone']
        }
        
        # Create new access token
        new_access_token = JWTAuthenticationManager.create_access_token(user_data)
        if not new_access_token:
            return {"success": False, "error": "token_invalid", "message": "Failed to create access token"}
        
        return {
            "success": True,
            "access_token": new_access_token,
            "expires_in": AuthConfig.JWT_ACCESS_TOKEN_EXPIRY_HOURS * 3600,
            "token_type": "Bearer"
        }
    
    @staticmethod
    def handle_auth_error(error_type="token_invalid"):
        """Handle authentication errors with consistent responses"""
        message = AuthConfig.ERRORS.get(error_type, "Authentication error. Please login again.")
        
        if AuthConfig.ENABLE_DEBUG_LOGGING:
            logging.warning(f"Authentication error: {error_type} - {message}")
        
        return jsonify({
            "success": False,
            "message": message,
            "data": {"auth_error": True, "error_type": error_type}
        }), 401


# Backward compatibility alias
class AuthenticationManager(JWTAuthenticationManager):
    """Alias for backward compatibility"""
    
    @staticmethod
    def create_jwt_token(user_data):
        """Create JWT access token (backward compatibility)"""
        return JWTAuthenticationManager.create_access_token(user_data)
    
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


# JWT token authentication decorator
def token_required(f):
    """
    JWT token authentication decorator
    Usage: @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract token from request
        token, error_type = JWTAuthenticationManager.extract_token_from_request()
        if error_type:
            return JWTAuthenticationManager.handle_auth_error(error_type)
        
        # Decode and validate JWT token
        success, payload_or_error, error_type = JWTAuthenticationManager.decode_jwt_token(token)
        if not success:
            return JWTAuthenticationManager.handle_auth_error(error_type or "token_invalid")
        
        payload = payload_or_error
        current_user_data = {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),  
            'user_type': payload.get('user_type'),
            'phone': payload.get('phone'),
            'exp': payload.get('exp'),
            'iat': payload.get('iat')
        }
        
        # Log successful authentication
        if AuthConfig.ENABLE_DEBUG_LOGGING:
            logging.info(f"JWT authenticated: {current_user_data['user_type']} {current_user_data['username']}")
        
        return f(current_user_data, *args, **kwargs)
    
    return decorated


# Easy configuration functions
def set_auth_debug(enabled=True):
    """Enable/disable authentication debug logging"""
    AuthConfig.set_debug_logging(enabled)

def set_access_token_expiry(hours=24):
    """Set access token expiry in hours (default: 24 hours)"""
    AuthConfig.set_access_token_expiry(hours)

def set_refresh_token_expiry(days=30):
    """Set refresh token expiry in days (default: 30 days)"""
    AuthConfig.set_refresh_token_expiry(days)