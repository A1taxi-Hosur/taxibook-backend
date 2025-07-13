"""
Customer routes for A1 Taxi Hosur Dev
Customer-specific booking and profile management
"""

from flask import Blueprint, request
from models.user import User
from models.booking import Booking
from models.fare_matrix import FareMatrix
from utils.auth import token_required, get_current_user, create_response
from datetime import datetime, date, time

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/profile', methods=['GET'])
@token_required(allowed_roles=['customer'])
def get_profile():
    """Get customer profile"""
    try:
        current_user = get_current_user()
        user = User.query.get(current_user['id'])
        
        if not user:
            return create_response(False, message="User not found", status_code=404)
        
        return create_response(True, data=user.to_dict(), message="Profile retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving profile: {str(e)}", status_code=500)

@customer_bp.route('/bookings', methods=['GET'])
@token_required(allowed_roles=['customer'])
def get_bookings():
    """Get customer bookings"""
    try:
        current_user = get_current_user()
        
        # Get query parameters
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Build query
        query = Booking.query.filter_by(customer_id=current_user['id'])
        
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

@customer_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@token_required(allowed_roles=['customer'])
def get_booking(booking_id):
    """Get specific booking details"""
    try:
        current_user = get_current_user()
        
        booking = Booking.query.filter_by(id=booking_id, customer_id=current_user['id']).first()
        
        if not booking:
            return create_response(False, message="Booking not found", status_code=404)
        
        return create_response(True, data=booking.to_dict(), message="Booking retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving booking: {str(e)}", status_code=500)

@customer_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@token_required(allowed_roles=['customer'])
def cancel_booking(booking_id):
    """Cancel a booking"""
    try:
        current_user = get_current_user()
        
        booking = Booking.query.filter_by(id=booking_id, customer_id=current_user['id']).first()
        
        if not booking:
            return create_response(False, message="Booking not found", status_code=404)
        
        success, message = booking.cancel_ride()
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=booking.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error cancelling booking: {str(e)}", status_code=500)

@customer_bp.route('/fare_estimate', methods=['POST'])
@token_required(allowed_roles=['customer'])
def get_fare_estimate():
    """Get fare estimate for a ride"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        ride_category = data.get('ride_category')
        pickup_lat = data.get('pickup_lat')
        pickup_lng = data.get('pickup_lng')
        drop_lat = data.get('drop_lat')
        drop_lng = data.get('drop_lng')
        
        if not ride_category:
            return create_response(False, message="Ride category is required", status_code=400)
        
        # Get fare matrix for all car types
        from config import Config
        estimates = []
        
        car_types = Config.CAR_TYPES
        if ride_category == 'airport':
            car_types = Config.AIRPORT_CAR_TYPES
        
        for car_type in car_types:
            fare_matrix = FareMatrix.get_fare(ride_category, car_type)
            
            if fare_matrix:
                estimated_fare = fare_matrix.base_fare
                
                # Calculate distance-based fare if coordinates provided
                if pickup_lat and pickup_lng and drop_lat and drop_lng:
                    from utils.geo import calculate_distance
                    distance_km = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
                    estimated_fare = fare_matrix.base_fare + (distance_km * fare_matrix.per_km)
                elif fare_matrix.flat_rate:
                    estimated_fare = fare_matrix.flat_rate
                
                estimates.append({
                    'car_type': car_type,
                    'base_fare': fare_matrix.base_fare,
                    'per_km': fare_matrix.per_km,
                    'estimated_fare': round(estimated_fare, 2),
                    'currency': '₹'
                })
        
        if not estimates:
            return create_response(False, message="No fare available for this ride category", status_code=400)
        
        return create_response(True, data={'estimates': estimates}, message="Fare estimates retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error getting fare estimate: {str(e)}", status_code=500)