from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, get_ist_time
from models import Driver, Ride, RideRejection, RideLocation
from utils.validators import validate_phone, validate_required_fields, create_error_response, create_success_response
from utils.maps import get_distance_to_pickup
from werkzeug.security import check_password_hash
import logging

driver_bp = Blueprint('driver', __name__)

@driver_bp.route('/login', methods=['POST'])
def login():
    """Driver login with username and password"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['username', 'password'])
        if not valid:
            return create_error_response(error)
        
        username = data['username'].strip()
        password = data['password']
        
        if not username or not password:
            return create_error_response("Username and password cannot be empty")
        
        # Find driver by username
        driver = Driver.query.filter_by(username=username).first()
        
        if not driver:
            return create_error_response("Invalid username or password")
        
        # Check if driver has password hash (was created by admin)
        if not driver.password_hash:
            return create_error_response("Account not properly setup. Contact admin.")
        
        # Verify password
        if not check_password_hash(driver.password_hash, password):
            return create_error_response("Invalid username or password")
        
        # Login successful
        login_user(driver)
        logging.info(f"Driver logged in: {driver.name} ({driver.username})")
        
        return create_success_response({
            'driver_id': driver.id,
            'name': driver.name,
            'phone': driver.phone,
            'username': driver.username,
            'is_online': driver.is_online,
            'car_make': driver.car_make,
            'car_model': driver.car_model,
            'car_year': driver.car_year,
            'car_number': driver.car_number,
            'car_type': driver.car_type
        }, "Login successful")
        
    except Exception as e:
        logging.error(f"Error in driver login: {str(e)}")
        return create_error_response("Internal server error")



@driver_bp.route('/incoming_rides', methods=['GET'])
def incoming_rides():
    """Get available rides for driver"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return create_error_response("Phone number is required")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found. Please login first.")
        
        # Check if driver is online
        if not driver.is_online:
            return create_success_response({
                'rides': [],
                'count': 0
            }, "Driver is offline. No rides available.")
        
        # Get available rides (pending status, not assigned to any driver, not rejected by this driver, matching vehicle type)
        # First get ride IDs rejected by this driver
        rejected_ride_ids = db.session.query(RideRejection.ride_id).filter_by(driver_phone=phone)
        
        # Query for available rides excluding rejected ones and matching vehicle type
        available_rides = Ride.query.filter(
            Ride.status == 'pending',
            Ride.driver_id.is_(None),
            ~Ride.id.in_(rejected_ride_ids),
            Ride.ride_type == driver.car_type  # Only show rides matching driver's vehicle type
        ).order_by(Ride.created_at.desc()).all()
        
        # Convert to list of dictionaries
        rides_data = []
        for ride in available_rides:
            ride_dict = ride.to_dict()
            
            # Add distance to pickup if driver location is provided
            driver_location = request.args.get('driver_location')
            if driver_location:
                success, distance_km, error_msg = get_distance_to_pickup(
                    driver_location, ride.pickup_address, ride.pickup_lat, ride.pickup_lng
                )
                if success:
                    ride_dict['distance_to_pickup_km'] = distance_km
                else:
                    ride_dict['distance_to_pickup_km'] = None
            
            rides_data.append(ride_dict)
        
        return create_success_response({
            'rides': rides_data,
            'count': len(rides_data)
        }, "Incoming rides retrieved")
        
    except Exception as e:
        logging.error(f"Error in incoming_rides: {str(e)}")
        return create_success_response({'rides': [], 'count': 0}, "Error retrieving rides")

@driver_bp.route('/accept_ride', methods=['POST'])
def accept_ride():
    """Accept a ride"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_id', 'driver_phone'])
        if not valid:
            return create_error_response(error)
        
        ride_id = data['ride_id']
        driver_phone = data['driver_phone']
        
        # Validate phone number
        valid, phone_or_error = validate_phone(driver_phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found")
        
        # Check if driver has any ongoing ride
        ongoing_ride = Ride.query.filter_by(
            driver_id=driver.id
        ).filter(
            Ride.status.in_(['accepted', 'arrived', 'started'])
        ).first()
        
        if ongoing_ride:
            return create_error_response("You already have an ongoing ride")
        
        # Find the ride and check if it's still available
        ride = Ride.query.filter_by(id=ride_id, status='pending', driver_id=None).first()
        if not ride:
            return create_error_response("Ride not available or already accepted")
        
        # Generate OTP for ride start confirmation
        import random
        ride.start_otp = str(random.randint(100000, 999999))
        
        # Assign ride to driver
        ride.driver_id = driver.id
        ride.status = 'accepted'
        ride.accepted_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Ride accepted: {ride.id} by driver {driver.name}")
        return create_success_response({
            'ride_id': ride.id,
            'status': 'accepted',
            'customer_name': ride.customer.name,
            'pickup_address': ride.pickup_address,
            'drop_address': ride.drop_address,
            'fare_amount': ride.fare_amount
        }, "Ride accepted successfully")
        
    except Exception as e:
        logging.error(f"Error in accept_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@driver_bp.route('/reject_ride', methods=['POST'])
def reject_ride():
    """Reject a ride"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_id', 'driver_phone'])
        if not valid:
            return create_error_response(error)
        
        ride_id = data['ride_id']
        driver_phone = data['driver_phone']
        
        # Validate phone number
        valid, phone_or_error = validate_phone(driver_phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Check if ride exists and is pending
        ride = Ride.query.filter_by(id=ride_id, status='pending').first()
        if not ride:
            return create_error_response("Ride not found or no longer available")
        
        # Check if driver has already rejected this ride
        existing_rejection = RideRejection.query.filter_by(
            ride_id=ride_id, 
            driver_phone=phone
        ).first()
        if existing_rejection:
            return create_error_response("Ride already rejected by this driver")
        
        # Create rejection record
        rejection = RideRejection(
            ride_id=ride_id,
            driver_phone=phone,
            rejected_at=get_ist_time()
        )
        db.session.add(rejection)
        db.session.commit()
        
        logging.info(f"Driver {phone} rejected ride {ride_id}")
        
        return create_success_response({
            'ride_id': ride_id,
            'message': 'Ride rejected'
        }, "Ride rejected successfully")
        
    except Exception as e:
        logging.error(f"Error in reject_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@driver_bp.route('/arrived', methods=['POST'])
def arrived():
    """Mark driver as arrived at pickup location"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        driver_phone = data.get('driver_phone')
        if not driver_phone:
            return create_error_response("Driver phone is required")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(driver_phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found")
        
        # Find accepted ride
        ride = Ride.query.filter_by(
            driver_id=driver.id,
            status='accepted'
        ).first()
        
        if not ride:
            return create_error_response("No accepted ride found")
        
        # Mark as arrived
        ride.status = 'arrived'
        ride.arrived_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Driver arrived: {driver.name} for ride {ride.id}")
        return create_success_response({
            'ride_id': ride.id,
            'status': 'arrived'
        }, "Arrival confirmed")
        
    except Exception as e:
        logging.error(f"Error in arrived: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@driver_bp.route('/start_ride', methods=['POST'])
def start_ride():
    """Start the ride with OTP verification"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_id', 'otp'])
        if not valid:
            return create_error_response(error)
        
        ride_id = data['ride_id']
        submitted_otp = data['otp'].strip()
        
        # Validate OTP format (6 digits)
        if not submitted_otp.isdigit() or len(submitted_otp) != 6:
            return create_error_response("OTP must be exactly 6 digits")
        
        # Find the ride
        ride = Ride.query.filter_by(id=ride_id).first()
        if not ride:
            return create_error_response("Ride not found")
        
        # Validate ride state
        if ride.status not in ['accepted', 'arrived']:
            return create_error_response("Ride cannot be started from current status")
        
        if ride.status == 'started':
            return create_error_response("Ride is already started")
        
        if ride.status in ['completed', 'cancelled']:
            return create_error_response("Ride is already completed or cancelled")
        
        # Verify driver is assigned to this ride
        if not ride.driver_id:
            return create_error_response("No driver assigned to this ride")
        
        # Check if current user is the assigned driver (for session-based auth)
        if hasattr(current_user, 'id') and current_user.is_authenticated:
            if current_user.id != ride.driver_id:
                return create_error_response("You are not authorized to start this ride")
        
        # Verify OTP
        if not ride.start_otp:
            return create_error_response("No OTP generated for this ride")
        
        if ride.start_otp != submitted_otp:
            logging.warning(f"Invalid OTP attempt for ride {ride_id}: expected {ride.start_otp}, got {submitted_otp}")
            return create_error_response("Invalid OTP", 403)
        
        # Start the ride
        ride.status = 'started'
        ride.started_at = get_ist_time()
        # Clear OTP after successful verification (optional security measure)
        ride.start_otp = None
        
        db.session.commit()
        
        logging.info(f"Ride started: {ride.id} by driver {ride.driver.name} with OTP verification")
        return create_success_response({
            'ride_id': ride.id,
            'status': 'started'
        }, "Ride started successfully")
        
    except Exception as e:
        logging.error(f"Error in start_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@driver_bp.route('/complete_ride', methods=['POST'])
def complete_ride():
    """Complete the ride"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        driver_phone = data.get('driver_phone')
        if not driver_phone:
            return create_error_response("Driver phone is required")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(driver_phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found")
        
        # Find started ride
        ride = Ride.query.filter_by(
            driver_id=driver.id,
            status='started'
        ).first()
        
        if not ride:
            return create_error_response("No started ride found")
        
        # Complete the ride
        ride.status = 'completed'
        ride.completed_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Ride completed: {ride.id} by driver {driver.name}")
        return create_success_response({
            'ride_id': ride.id,
            'status': 'completed',
            'fare_amount': ride.fare_amount
        }, "Ride completed successfully")
        
    except Exception as e:
        logging.error(f"Error in complete_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@driver_bp.route('/cancel_ride', methods=['POST'])
def cancel_ride():
    """Cancel accepted ride"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        driver_phone = data.get('driver_phone')
        if not driver_phone:
            return create_error_response("Driver phone is required")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(driver_phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found")
        
        # Find cancellable ride
        ride = Ride.query.filter_by(
            driver_id=driver.id
        ).filter(
            Ride.status.in_(['accepted', 'arrived'])
        ).first()
        
        if not ride:
            return create_error_response("No cancellable ride found")
        
        # Cancel and reset ride
        ride.status = 'pending'
        ride.driver_id = None
        ride.accepted_at = None
        ride.arrived_at = None
        
        db.session.commit()
        
        logging.info(f"Ride cancelled: {ride.id} by driver {driver.name}")
        return create_success_response({
            'ride_id': ride.id,
            'status': 'pending'
        }, "Ride cancelled successfully")
        
    except Exception as e:
        logging.error(f"Error in cancel_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@driver_bp.route('/current_ride', methods=['GET'])
def current_ride():
    """Get current ride for driver"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return create_error_response("Phone number is required")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_success_response({'has_active_ride': False}, "No active ride")
        
        # Get active ride
        active_ride = Ride.query.filter_by(
            driver_id=driver.id
        ).filter(
            Ride.status.in_(['accepted', 'arrived', 'started'])
        ).first()
        
        if not active_ride:
            return create_success_response({'has_active_ride': False}, "No active ride")
        
        # Return ride details
        ride_data = active_ride.to_dict()
        ride_data['has_active_ride'] = True
        
        return create_success_response(ride_data, "Current ride retrieved")
        
    except Exception as e:
        logging.error(f"Error in current_ride: {str(e)}")
        return create_success_response({'has_active_ride': False}, "Error retrieving ride")

@driver_bp.route('/logout', methods=['POST'])
def logout():
    """Logout driver"""
    try:
        logout_user()
        return create_success_response(message="Logout successful")
    except Exception as e:
        logging.error(f"Error in logout: {str(e)}")
        return create_error_response("Internal server error")

@driver_bp.route('/status', methods=['POST'])
def update_status():
    """Toggle driver availability (online/offline)"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['mobile', 'is_online'])
        if not valid:
            return create_error_response(error)
        
        # Validate phone number
        valid, phone_or_error = validate_phone(data['mobile'])
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        is_online = data['is_online']
        
        if not isinstance(is_online, bool):
            return create_error_response("is_online must be a boolean value")
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found")
        
        # Check if driver has active ride when trying to go offline
        if not is_online:
            active_ride = Ride.query.filter_by(
                driver_id=driver.id
            ).filter(
                Ride.status.in_(['accepted', 'arrived', 'started'])
            ).first()
            
            if active_ride:
                return create_error_response("Cannot go offline while having an active ride")
        
        # Update driver status
        driver.is_online = is_online
        db.session.commit()
        
        status_text = "online" if is_online else "offline"
        logging.info(f"Driver {driver.name} ({driver.phone}) went {status_text}")
        
        return create_success_response({
            'driver_id': driver.id,
            'name': driver.name,
            'phone': driver.phone,
            'is_online': driver.is_online
        }, f"Driver status updated to {status_text}")
        
    except Exception as e:
        logging.error(f"Error in update_status: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@driver_bp.route('/status', methods=['GET'])
def get_status():
    """Get current driver status (online/offline)"""
    try:
        mobile = request.args.get('mobile')
        if not mobile:
            return create_error_response("Mobile number is required")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(mobile)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found")
        
        return create_success_response({
            'is_online': driver.is_online,
            'driver_id': driver.id,
            'name': driver.name,
            'phone': driver.phone
        }, "Driver status retrieved")
        
    except Exception as e:
        logging.error(f"Error in get_status: {str(e)}")
        return create_error_response("Internal server error")


@driver_bp.route('/update_location', methods=['POST'])
def update_location():
    """Update driver's GPS location for active ride"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        required_fields = ['driver_phone', 'ride_id', 'latitude', 'longitude']
        valid, error = validate_required_fields(data, required_fields)
        if not valid:
            return create_error_response(error)
        
        # Validate phone number
        valid, phone_or_error = validate_phone(data['driver_phone'])
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        ride_id = data['ride_id']
        
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return create_error_response("Invalid latitude or longitude format")
        
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            return create_error_response("Invalid latitude. Must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            return create_error_response("Invalid longitude. Must be between -180 and 180")
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found")
        
        # Verify ride exists and belongs to this driver
        ride = Ride.query.filter_by(id=ride_id, driver_id=driver.id).first()
        if not ride:
            return create_error_response("Ride not found or not assigned to you")
        
        # Only allow location updates for active rides
        if ride.status not in ['accepted', 'arrived', 'started']:
            return create_error_response("Can only update location for active rides")
        
        # Mark all previous locations as not latest for this ride
        RideLocation.query.filter_by(ride_id=ride_id).update({'is_latest': False})
        
        # Create new location entry
        new_location = RideLocation(
            ride_id=ride_id,
            latitude=latitude,
            longitude=longitude,
            is_latest=True
        )
        
        db.session.add(new_location)
        db.session.commit()
        
        logging.info(f"GPS location updated for ride {ride_id}: {latitude}, {longitude}")
        
        return create_success_response({
            'ride_id': ride_id,
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': new_location.timestamp.isoformat()
        }, "Location updated successfully")
    
    except Exception as e:
        logging.error(f"Error updating location: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")
