import re
from flask import jsonify

def validate_phone(phone):
    """Validate Indian phone number format"""
    if not phone:
        return False, "Phone number is required"
    
    # Remove +91 prefix if present
    phone = phone.strip()
    if phone.startswith('+91'):
        phone = phone[3:]
    elif phone.startswith('91') and len(phone) == 12:
        phone = phone[2:]
    
    # Check if it's a valid 10-digit Indian mobile number
    if not re.match(r'^[6-9]\d{9}$', phone):
        return False, "Invalid phone number format. Must be a 10-digit Indian mobile number starting with 6-9"
    
    return True, phone

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None

def create_error_response(message, status_code=400):
    """Create standardized error response"""
    return jsonify({
        'success': False,
        'message': message
    }), status_code

def validate_ride_type(ride_type):
    """Validate ride type selection"""
    if not ride_type:
        return False, "Ride type is required"
    
    # Valid ride types: hatchback, sedan, suv
    valid_types = ['hatchback', 'sedan', 'suv']
    if ride_type.lower() not in valid_types:
        return False, f"Invalid ride type. Must be one of: {', '.join(valid_types)}"
    
    return True, ride_type.lower()

def create_success_response(data=None, message="Success"):
    """Create standardized success response"""
    response = {
        'status': 'success',
        'message': message
    }
    if data:
        response['data'] = data
    return jsonify(response)
