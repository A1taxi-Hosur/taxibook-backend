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

@auth_bp.route('/driver/login', methods=['POST'])
def driver_login():
    """
    Driver login endpoint - requires username/phone + password
    """
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return create_error_response("Username and password are required")
        
        # Try to find driver by username or phone
        from models import Driver
        driver = Driver.query.filter(
            (Driver.username == username) | (Driver.phone == username)
        ).first()
        
        if not driver:
            return create_error_response("Invalid username or password")
        
        # Verify password if driver has one
        if driver.password_hash:
            from werkzeug.security import check_password_hash
            if not check_password_hash(driver.password_hash, password):
                return create_error_response("Invalid username or password")
        else:
            return create_error_response("Driver account not properly configured")
        
        # Create user data for JWT token
        user_data = {
            'user_id': driver.id,
            'username': driver.name,
            'user_type': 'driver',
            'phone': driver.phone
        }
        
        # Generate JWT token pair
        token_data = JWTAuthenticationManager.create_token_pair(user_data)
        if not token_data['access_token']:
            return create_error_response("Failed to create authentication token")
        
        # Update driver online status
        driver.is_online = True
        driver.last_seen = db.func.now()
        db.session.commit()
        
        # Log successful login
        logging.info(f"Driver login successful: {driver.name} ({driver.phone})")
        
        # Return response with tokens
        response_data = {
            'user': {
                'id': driver.id,
                'name': driver.name,
                'phone': driver.phone,
                'username': driver.username,
                'user_type': 'driver',
                'car_type': driver.car_type,
                'car_number': driver.car_number
            },
            'auth': token_data
        }
        
        return create_success_response(response_data, "Login successful")
        
    except Exception as e:
        logging.error(f"Driver login error: {str(e)}")
        return create_error_response("An error occurred during login")

@auth_bp.route('/customer/login', methods=['POST'])
def customer_login():
    """
    Customer login/registration endpoint - requires name + phone (auto-registers if not exists)
    """
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        name = data.get('name')
        phone = data.get('phone')
        
        if not name or not phone:
            return create_error_response("Name and phone number are required")
        
        # Validate phone number format
        valid, phone_or_error = validate_phone(phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find or create customer
        from models import Customer
        customer = Customer.query.filter_by(phone=phone).first()
        
        if not customer:
            # Auto-register new customer
            customer = Customer(name=name, phone=phone)
            db.session.add(customer)
            db.session.commit()
            logging.info(f"New customer registered: {name} ({phone})")
        else:
            # Update name if different
            if customer.name != name:
                customer.name = name
                db.session.commit()
        
        # Create user data for JWT token
        user_data = {
            'user_id': customer.id,
            'username': customer.name,
            'user_type': 'customer',
            'phone': customer.phone
        }
        
        # Generate JWT token pair
        token_data = JWTAuthenticationManager.create_token_pair(user_data)
        if not token_data['access_token']:
            return create_error_response("Failed to create authentication token")
        
        # Update customer online status
        customer.is_online = True
        customer.last_seen = db.func.now()
        db.session.commit()
        
        # Log successful login
        logging.info(f"Customer login successful: {customer.name} ({phone})")
        
        # Return response with tokens
        response_data = {
            'user': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'user_type': 'customer'
            },
            'auth': token_data
        }
        
        return create_success_response(response_data, "Login successful")
        
    except Exception as e:
        logging.error(f"Customer login error: {str(e)}")
        return create_error_response("An error occurred during login")

@auth_bp.route('/login', methods=['POST'])
def unified_login():
    """
    DEPRECATED: Unified login endpoint - Use /auth/driver/login or /auth/customer/login instead
    """
    return create_error_response("This endpoint is deprecated. Use /auth/driver/login for drivers or /auth/customer/login for customers.")


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