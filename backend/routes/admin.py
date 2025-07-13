"""
Admin routes for A1 Taxi Hosur Dev
Admin dashboard and management functionality
"""

from flask import Blueprint, request
from models.user import User
from models.driver_profile import DriverProfile
from models.booking import Booking
from models.zone import Zone
from models.fare_matrix import FareMatrix
from utils.auth import token_required, get_current_user, create_response
from app import db
from datetime import datetime, date

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_dashboard():
    """Get admin dashboard statistics"""
    try:
        # Get counts
        total_customers = User.query.filter_by(role='customer').count()
        total_drivers = User.query.filter_by(role='driver').count()
        available_drivers = DriverProfile.query.filter_by(is_available=True).count()
        
        # Get booking statistics
        total_bookings = Booking.query.count()
        new_bookings = Booking.query.filter_by(status='new').count()
        assigned_bookings = Booking.query.filter_by(status='assigned').count()
        active_bookings = Booking.query.filter_by(status='active').count()
        completed_bookings = Booking.query.filter_by(status='completed').count()
        
        # Get today's bookings
        today = date.today()
        today_bookings = Booking.query.filter(
            db.func.date(Booking.created_at) == today
        ).count()
        
        # Get revenue (completed bookings)
        total_revenue = db.session.query(
            db.func.sum(Booking.final_fare)
        ).filter_by(status='completed').scalar() or 0
        
        dashboard_data = {
            'users': {
                'total_customers': total_customers,
                'total_drivers': total_drivers,
                'available_drivers': available_drivers
            },
            'bookings': {
                'total': total_bookings,
                'new': new_bookings,
                'assigned': assigned_bookings,
                'active': active_bookings,
                'completed': completed_bookings,
                'today': today_bookings
            },
            'revenue': {
                'total': round(total_revenue, 2),
                'currency': '₹'
            }
        }
        
        return create_response(True, data=dashboard_data, message="Dashboard data retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving dashboard: {str(e)}", status_code=500)

@admin_bp.route('/assign_driver', methods=['POST'])
@token_required(allowed_roles=['admin'])
def assign_driver():
    """Assign driver to a booking"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        booking_id = data.get('booking_id')
        driver_id = data.get('driver_id')
        
        if not booking_id or not driver_id:
            return create_response(False, message="Booking ID and Driver ID are required", status_code=400)
        
        # Get booking
        booking = Booking.query.get(booking_id)
        if not booking:
            return create_response(False, message="Booking not found", status_code=404)
        
        # Assign driver
        success, message = booking.assign_driver(driver_id)
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=booking.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error assigning driver: {str(e)}", status_code=500)

@admin_bp.route('/bookings', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_all_bookings():
    """Get all bookings for admin"""
    try:
        # Get query parameters
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query
        query = Booking.query
        
        if status:
            query = query.filter_by(status=status)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%d/%m/%Y').date()
                query = query.filter(db.func.date(Booking.created_at) >= from_date)
            except ValueError:
                return create_response(False, message="Invalid date_from format. Use DD/MM/YYYY", status_code=400)
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%d/%m/%Y').date()
                query = query.filter(db.func.date(Booking.created_at) <= to_date)
            except ValueError:
                return create_response(False, message="Invalid date_to format. Use DD/MM/YYYY", status_code=400)
        
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

@admin_bp.route('/drivers', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_all_drivers():
    """Get all drivers for admin"""
    try:
        # Get query parameters
        zone_id = request.args.get('zone_id')
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Build query
        query = db.session.query(User, DriverProfile).join(
            DriverProfile, User.id == DriverProfile.user_id
        ).filter(User.role == 'driver')
        
        if zone_id:
            query = query.filter(DriverProfile.zone_id == zone_id)
        
        if available_only:
            query = query.filter(DriverProfile.is_available == True)
        
        # Order by name
        query = query.order_by(User.name)
        
        # Paginate
        drivers = query.paginate(page=page, per_page=per_page, error_out=False)
        
        drivers_data = []
        for user, profile in drivers.items:
            driver_data = user.to_dict()
            driver_data['driver_profile'] = profile.to_dict()
            drivers_data.append(driver_data)
        
        response_data = {
            'drivers': drivers_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': drivers.total,
                'pages': drivers.pages,
                'has_next': drivers.has_next,
                'has_prev': drivers.has_prev
            }
        }
        
        return create_response(True, data=response_data, message="Drivers retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving drivers: {str(e)}", status_code=500)

@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@token_required(allowed_roles=['admin'])
def toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    try:
        user = User.query.get(user_id)
        
        if not user:
            return create_response(False, message="User not found", status_code=404)
        
        # Toggle status
        user.status = 'active' if user.status == 'inactive' else 'inactive'
        
        # If deactivating a driver, make them unavailable
        if user.status == 'inactive' and user.role == 'driver' and user.driver_profile:
            user.driver_profile.is_available = False
        
        db.session.commit()
        
        return create_response(True, data=user.to_dict(), message=f"User status updated to {user.status}")
        
    except Exception as e:
        db.session.rollback()
        return create_response(False, message=f"Error updating user status: {str(e)}", status_code=500)