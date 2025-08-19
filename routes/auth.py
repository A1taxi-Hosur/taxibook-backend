"""
JWT Authentication Routes - Login, refresh, and logout endpoints
"""

import logging
from flask import Blueprint, request, jsonify
from utils.validators import create_success_response, create_error_response, validate_phone
from utils.auth_manager import JWTAuthenticationManager
from models import db

# Create blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def jwt_login():
    """
    JWT-based login endpoint for both drivers and customers
    Supports phone-based authentication with optional password
    """
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        phone = data.get('phone')
        password = data.get('password')  # Optional for OTP-based auth
        user_type = data.get('user_type', 'driver')  # Default to driver
        
        if not phone:
            return create_error_response("Phone number is required")
        
        if user_type not in ['driver', 'customer']:
            return create_error_response("Invalid user type. Must be 'driver' or 'customer'")
        
        # Validate phone number format
        valid, phone_or_error = validate_phone(phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Validate user credentials
        success, user_or_error, error_type = JWTAuthenticationManager.validate_user_credentials(
            phone, password, user_type
        )
        
        if not success:
            logging.warning(f"Login failed for {user_type} {phone}: {user_or_error}")
            return create_error_response(user_or_error)
        
        user = user_or_error
        
        # Create user data for JWT token
        user_data = {
            'user_id': user.id,
            'username': user.name,
            'user_type': user_type,
            'phone': user.phone
        }
        
        # Generate JWT token pair
        token_data = JWTAuthenticationManager.create_token_pair(user_data)
        if not token_data['access_token']:
            return create_error_response("Failed to create authentication token")
        
        # Update user online status
        user.is_online = True
        user.last_seen = db.func.now()
        db.session.commit()
        
        # Log successful login
        logging.info(f"JWT login successful: {user_type} {user.name} ({phone})")
        
        # Return response with tokens
        response_data = {
            'user': {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'user_type': user_type
            },
            'auth': token_data
        }
        
        return create_success_response(response_data, "Login successful")
        
    except Exception as e:
        logging.error(f"Error in JWT login: {str(e)}")
        return create_error_response("Login failed. Please try again.")


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token using refresh token
    """
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return create_error_response("Refresh token is required")
        
        # Generate new access token
        result = JWTAuthenticationManager.refresh_access_token(refresh_token)
        
        if not result.get('success'):
            error_type = result.get('error', 'token_invalid')
            message = result.get('message', 'Invalid refresh token')
            logging.warning(f"Token refresh failed: {error_type} - {message}")
            return create_error_response(message)
        
        # Log successful token refresh
        logging.debug("Access token refreshed successfully")
        
        return create_success_response({
            'access_token': result['access_token'],
            'expires_in': result['expires_in'],
            'token_type': result['token_type']
        }, "Token refreshed successfully")
        
    except Exception as e:
        logging.error(f"Error refreshing token: {str(e)}")
        return create_error_response("Token refresh failed. Please login again.")


@auth_bp.route('/logout', methods=['POST'])
def jwt_logout():
    """
    JWT-based logout endpoint
    Since JWTs are stateless, this mainly updates user online status
    """
    try:
        # Extract token from request
        token, error_type = JWTAuthenticationManager.extract_token_from_request()
        if error_type:
            return create_error_response("Authentication required for logout")
        
        # Decode token to get user info
        success, payload_or_error, error_type = JWTAuthenticationManager.decode_jwt_token(token)
        if not success:
            return create_error_response("Invalid authentication token")
        
        payload = payload_or_error
        user_id = payload.get('user_id')
        user_type = payload.get('user_type')
        
        # Update user online status
        if user_type == 'driver':
            from models import Driver
            user = Driver.query.get(user_id)
        elif user_type == 'customer':
            from models import Customer
            user = Customer.query.get(user_id)
        else:
            return create_error_response("Invalid user type")
        
        if user:
            user.is_online = False
            db.session.commit()
            logging.info(f"JWT logout: {user_type} {user.name} ({user.phone})")
        
        return create_success_response({}, "Logout successful")
        
    except Exception as e:
        logging.error(f"Error in JWT logout: {str(e)}")
        return create_error_response("Logout failed")


@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """
    Verify if current JWT token is valid
    """
    try:
        # Extract token from request
        token, error_type = JWTAuthenticationManager.extract_token_from_request()
        if error_type:
            return create_error_response("No authentication token provided")
        
        # Decode and validate token
        success, payload_or_error, error_type = JWTAuthenticationManager.decode_jwt_token(token)
        if not success:
            return create_error_response("Invalid or expired token")
        
        payload = payload_or_error
        
        # Return token information
        token_info = {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'user_type': payload.get('user_type'),
            'phone': payload.get('phone'),
            'expires_at': payload.get('exp'),
            'issued_at': payload.get('iat')
        }
        
        return create_success_response(token_info, "Token is valid")
        
    except Exception as e:
        logging.error(f"Error verifying token: {str(e)}")
        return create_error_response("Token verification failed")