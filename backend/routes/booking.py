"""
Booking routes for A1 Taxi Hosur Dev
Booking creation and management
"""

from flask import Blueprint, request
from models.booking import Booking
from models.fare_matrix import FareMatrix
from utils.auth import token_required, get_current_user, create_response
from datetime import datetime, date, time

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/create', methods=['POST'])
@token_required(allowed_roles=['customer'])
def create_booking():
    """Create a new booking"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        # Validate required fields
        required_fields = ['ride_category', 'car_type', 'pickup_address', 'scheduled_date', 'scheduled_time']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return create_response(False, message=f"Missing fields: {', '.join(missing_fields)}", status_code=400)
        
        # Parse scheduled date and time
        try:
            scheduled_date = datetime.strptime(data['scheduled_date'], '%d/%m/%Y').date()
            scheduled_time = datetime.strptime(data['scheduled_time'], '%H:%M').time()
        except ValueError:
            return create_response(False, message="Invalid date/time format. Use DD/MM/YYYY for date and HH:MM for time", status_code=400)
        
        # Validate scheduled time is in the future
        scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)
        if scheduled_datetime <= datetime.now():
            return create_response(False, message="Scheduled time must be in the future", status_code=400)
        
        # Create booking
        success, result = Booking.create_booking(
            customer_id=current_user['id'],
            ride_category=data['ride_category'],
            car_type=data['car_type'],
            pickup_address=data['pickup_address'],
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            drop_address=data.get('drop_address'),
            pickup_lat=data.get('pickup_lat'),
            pickup_lng=data.get('pickup_lng'),
            drop_lat=data.get('drop_lat'),
            drop_lng=data.get('drop_lng'),
            additional_info=data.get('additional_info')
        )
        
        if not success:
            return create_response(False, message=result, status_code=400)
        
        booking = result
        
        return create_response(True, data=booking.to_dict(), message="Booking created successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error creating booking: {str(e)}", status_code=500)

@booking_bp.route('/<int:booking_id>', methods=['GET'])
@token_required(allowed_roles=['customer', 'driver', 'admin'])
def get_booking(booking_id):
    """Get specific booking details"""
    try:
        current_user = get_current_user()
        
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return create_response(False, message="Booking not found", status_code=404)
        
        # Check permissions
        if current_user['role'] == 'customer' and booking.customer_id != current_user['id']:
            return create_response(False, message="Access denied", status_code=403)
        
        if current_user['role'] == 'driver' and booking.driver_id != current_user['id']:
            return create_response(False, message="Access denied", status_code=403)
        
        return create_response(True, data=booking.to_dict(), message="Booking retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving booking: {str(e)}", status_code=500)

@booking_bp.route('/customer/<int:customer_id>', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_customer_bookings(customer_id):
    """Get bookings for a specific customer (admin only)"""
    try:
        # Get query parameters
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Build query
        query = Booking.query.filter_by(customer_id=customer_id)
        
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
        
        return create_response(True, data=response_data, message="Customer bookings retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving customer bookings: {str(e)}", status_code=500)

@booking_bp.route('/admin_all', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_admin_all_bookings():
    """Get all bookings for admin dashboard"""
    try:
        # Get query parameters
        tab = request.args.get('tab', 'bookings')  # bookings, ongoing, history
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query based on tab
        if tab == 'bookings':
            # All new and scheduled rides
            query = Booking.query.filter(Booking.status.in_(['new', 'assigned']))
        elif tab == 'ongoing':
            # Rides within 30 minutes or in progress
            query = Booking.query.filter_by(status='active')
        elif tab == 'history':
            # Completed rides
            query = Booking.query.filter(Booking.status.in_(['completed', 'cancelled']))
        else:
            # Default to all bookings
            query = Booking.query
        
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
            },
            'tab': tab
        }
        
        return create_response(True, data=response_data, message="Admin bookings retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving admin bookings: {str(e)}", status_code=500)

@booking_bp.route('/<int:booking_id>/activate', methods=['POST'])
@token_required(allowed_roles=['admin'])
def activate_booking(booking_id):
    """Activate a booking (admin only)"""
    try:
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return create_response(False, message="Booking not found", status_code=404)
        
        success, message = booking.activate_ride()
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=booking.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error activating booking: {str(e)}", status_code=500)