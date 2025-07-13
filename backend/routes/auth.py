"""
Authentication routes for A1 Taxi Hosur Dev
User registration, login, and token management
"""

from flask import Blueprint, request
from models.user import User
from models.driver_profile import DriverProfile
from utils.auth import generate_token, create_response
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        # Validate required fields
        required_fields = ['role', 'name', 'mobile_number', 'password']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return create_response(False, message=f"Missing fields: {', '.join(missing_fields)}", status_code=400)
        
        # Create user
        success, result = User.create_user(
            role=data['role'],
            name=data['name'],
            mobile_number=data['mobile_number'],
            password=data['password']
        )
        
        if not success:
            return create_response(False, message=result, status_code=400)
        
        user = result
        
        # If driver, create driver profile
        if user.role == 'driver':
            driver_data = data.get('driver_profile', {})
            required_driver_fields = ['car_type', 'car_number', 'license_number']
            missing_driver_fields = [field for field in required_driver_fields if not driver_data.get(field)]
            
            if missing_driver_fields:
                # Delete user if driver profile creation fails
                db.session.delete(user)
                db.session.commit()
                return create_response(False, message=f"Driver profile missing fields: {', '.join(missing_driver_fields)}", status_code=400)
            
            profile_success, profile_result = DriverProfile.create_profile(
                user_id=user.id,
                car_type=driver_data['car_type'],
                car_number=driver_data['car_number'],
                license_number=driver_data['license_number'],
                company_name=driver_data.get('company_name')
            )
            
            if not profile_success:
                # Delete user if driver profile creation fails
                db.session.delete(user)
                db.session.commit()
                return create_response(False, message=profile_result, status_code=400)
        
        # Generate token
        token = generate_token(user.id, user.role)
        
        response_data = {
            'user': user.to_dict(),
            'token': token
        }
        
        return create_response(True, data=response_data, message="User registered successfully")
        
    except Exception as e:
        return create_response(False, message=f"Registration failed: {str(e)}", status_code=500)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        mobile_number = data.get('mobile_number')
        password = data.get('password')
        
        if not mobile_number or not password:
            return create_response(False, message="Mobile number and password are required", status_code=400)
        
        # Validate mobile number format
        is_valid, result = User.validate_mobile_number(mobile_number)
        if not is_valid:
            return create_response(False, message=result, status_code=400)
        
        mobile_number = result
        
        # Find user
        user = User.query.filter_by(mobile_number=mobile_number).first()
        
        if not user or not user.check_password(password):
            return create_response(False, message="Invalid mobile number or password", status_code=401)
        
        if user.status != 'active':
            return create_response(False, message="Account is inactive", status_code=401)
        
        # Generate token
        token = generate_token(user.id, user.role)
        
        response_data = {
            'user': user.to_dict(),
            'token': token
        }
        
        # Add driver profile if user is a driver
        if user.role == 'driver' and user.driver_profile:
            response_data['driver_profile'] = user.driver_profile.to_dict()
        
        return create_response(True, data=response_data, message="Login successful")
        
    except Exception as e:
        return create_response(False, message=f"Login failed: {str(e)}", status_code=500)

@auth_bp.route('/change_password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        mobile_number = data.get('mobile_number')
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not all([mobile_number, old_password, new_password]):
            return create_response(False, message="All fields are required", status_code=400)
        
        # Validate mobile number format
        is_valid, result = User.validate_mobile_number(mobile_number)
        if not is_valid:
            return create_response(False, message=result, status_code=400)
        
        mobile_number = result
        
        # Find user
        user = User.query.filter_by(mobile_number=mobile_number).first()
        
        if not user or not user.check_password(old_password):
            return create_response(False, message="Invalid mobile number or password", status_code=401)
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return create_response(True, message="Password changed successfully")
        
    except Exception as e:
        db.session.rollback()
        return create_response(False, message=f"Password change failed: {str(e)}", status_code=500)