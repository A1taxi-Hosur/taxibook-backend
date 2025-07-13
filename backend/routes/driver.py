"""
Driver routes for A1 Taxi Hosur Dev
Driver-specific functionality and location updates
"""

from flask import Blueprint, request
from models.user import User
from models.driver_profile import DriverProfile
from models.booking import Booking
from utils.auth import token_required, get_current_user, create_response
from utils.geo import validate_coordinates

driver_bp = Blueprint('driver', __name__)

@driver_bp.route('/profile', methods=['GET'])
@token_required(allowed_roles=['driver'])
def get_profile():
    """Get driver profile"""
    try:
        current_user = get_current_user()
        user = User.query.get(current_user['id'])
        
        if not user:
            return create_response(False, message="User not found", status_code=404)
        
        response_data = {
            'user': user.to_dict(),
            'driver_profile': user.driver_profile.to_dict() if user.driver_profile else None
        }
        
        return create_response(True, data=response_data, message="Profile retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving profile: {str(e)}", status_code=500)

@driver_bp.route('/update_location', methods=['POST'])
@token_required(allowed_roles=['driver'])
def update_location():
    """Update driver location"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        if lat is None or lng is None:
            return create_response(False, message="Latitude and longitude are required", status_code=400)
        
        # Validate coordinates
        is_valid, error_message = validate_coordinates(lat, lng)
        if not is_valid:
            return create_response(False, message=error_message, status_code=400)
        
        # Get driver profile
        user = User.query.get(current_user['id'])
        if not user or not user.driver_profile:
            return create_response(False, message="Driver profile not found", status_code=404)
        
        # Update location
        success, message = user.driver_profile.update_location(float(lat), float(lng))
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=user.driver_profile.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error updating location: {str(e)}", status_code=500)

@driver_bp.route('/toggle_availability', methods=['POST'])
@token_required(allowed_roles=['driver'])
def toggle_availability():
    """Toggle driver availability"""
    try:
        current_user = get_current_user()
        
        # Get driver profile
        user = User.query.get(current_user['id'])
        if not user or not user.driver_profile:
            return create_response(False, message="Driver profile not found", status_code=404)
        
        # Toggle availability
        success, message = user.driver_profile.toggle_availability()
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=user.driver_profile.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error toggling availability: {str(e)}", status_code=500)

@driver_bp.route('/bookings', methods=['GET'])
@token_required(allowed_roles=['driver'])
def get_bookings():
    """Get driver bookings"""
    try:
        current_user = get_current_user()
        
        # Get query parameters
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Build query
        query = Booking.query.filter_by(driver_id=current_user['id'])
        
        if status:
            query = query.filter_by(status=status)
        
        # Order by creation date (newest first)
        query = query.order_by(Booking.created_at.desc())
        
        # Paginate
        bookings = query.paginate(page=page, per_page=per_page, error_out=False)
        
        response_data = {
            'bookings': [booking.to_dict() for booking in bookings.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': bookings.total,
                'pages': bookings.pages,
                'has_next': bookings.has_next,
                'has_prev': bookings.has_prev
            }
        }
        
        return create_response(True, data=response_data, message="Bookings retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving bookings: {str(e)}", status_code=500)

@driver_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@token_required(allowed_roles=['driver'])
def get_booking(booking_id):
    """Get specific booking details"""
    try:
        current_user = get_current_user()
        
        booking = Booking.query.filter_by(id=booking_id, driver_id=current_user['id']).first()
        
        if not booking:
            return create_response(False, message="Booking not found", status_code=404)
        
        return create_response(True, data=booking.to_dict(), message="Booking retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving booking: {str(e)}", status_code=500)

@driver_bp.route('/bookings/<int:booking_id>/complete', methods=['POST'])
@token_required(allowed_roles=['driver'])
def complete_booking(booking_id):
    """Complete a booking"""
    try:
        current_user = get_current_user()
        
        booking = Booking.query.filter_by(id=booking_id, driver_id=current_user['id']).first()
        
        if not booking:
            return create_response(False, message="Booking not found", status_code=404)
        
        success, message = booking.complete_ride()
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=booking.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error completing booking: {str(e)}", status_code=500)