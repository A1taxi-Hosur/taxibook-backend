from flask import Blueprint, request, jsonify
from app import db, get_ist_time, generate_jwt_token
from utils.auth_manager import token_required
from models import Driver, Ride, RideRejection, RideLocation, Zone
from utils.validators import validate_phone, validate_required_fields, create_error_response, create_success_response
from utils.maps import get_distance_to_pickup
from werkzeug.security import check_password_hash
import logging

driver_bp = Blueprint('driver', __name__)

@driver_bp.route('/test', methods=['POST', 'GET'])
def test_endpoint():
    """Test endpoint to debug request data"""
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "message": "Test endpoint is working",
            "method": "GET"
        })
    
    try:
        # Log everything about the request
        logging.info(f"=== REQUEST DEBUG ===")
        logging.info(f"Content-Type: {request.content_type}")
        logging.info(f"Method: {request.method}")
        logging.info(f"Headers: {dict(request.headers)}")
        
        if request.is_json:
            data = request.get_json()
            logging.info(f"JSON Data: {data}")
        else:
            form_data = request.form.to_dict()
            logging.info(f"Form Data: {form_data}")
            data = form_data
            
        raw_data = request.get_data(as_text=True)
        logging.info(f"Raw Body: {raw_data}")
        logging.info(f"=== END DEBUG ===")
        
        return jsonify({
            "success": True,
            "message": "Test successful",
            "received_data": data,
            "content_type": request.content_type,
            "raw_body_length": len(raw_data)
        })
        
    except Exception as e:
        logging.error(f"Test endpoint error: {str(e)}")
        return jsonify({
            "success": False, 
            "message": str(e)
        }), 400

@driver_bp.route('/login', methods=['POST'])
@driver_bp.route('/', methods=['POST'])  # Also handle requests to /driver/ (root driver route)
def login():
    """Driver login with username and password"""
    try:
        # Enhanced data parsing to handle Content-Type issues
        data = None
        raw_body = request.get_data(as_text=True)
        
        # Try to parse JSON from raw body if request.get_json() fails
        if request.content_type == 'application/json' or raw_body.startswith('{'):
            try:
                import json
                data = json.loads(raw_body) if raw_body else {}
            except:
                data = request.get_json() or {}
        else:
            data = request.form.to_dict()
        
        # Enhanced debugging
        raw_body = request.get_data(as_text=True)
        logging.info(f"=== LOGIN DEBUG ===")
        logging.info(f"Content-Type: {request.content_type}")
        logging.info(f"Raw body: {raw_body}")
        logging.info(f"Raw body length: {len(raw_body)}")
        logging.info(f"Parsed data: {data}")
        logging.info(f"Request headers: {dict(request.headers)}")
        logging.info(f"=== END DEBUG ===")
        
        if not data:
            logging.warning("Empty login data received - form data might not be transmitted properly")
            return create_error_response("Missing login data - check if frontend is sending data properly")
        
        if not data.get('username') or not data.get('password'):
            logging.warning(f"Incomplete login data - username: {bool(data.get('username'))}, password: {bool(data.get('password'))}")
            return create_error_response("Username and password are required")
        
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
        
        # Login successful - create session and set driver online using centralized auth manager
        from utils.auth_manager import AuthenticationManager
        session_token = AuthenticationManager.create_driver_session(driver)
        
        # Generate JWT token for mobile app authentication using centralized system
        token_data = {
            'user_id': driver.id,
            'username': driver.username,
            'user_type': 'driver',
            'session_token': session_token
        }
        token = generate_jwt_token(token_data)
        
        logging.info(f"Driver logged in: {driver.name} ({driver.username}) - automatically set online, JWT token generated")
        
        return jsonify({
            'success': True,
            'token': token,
            'driver': {
                'id': str(driver.id),           # Mobile apps expect string
                'driver_id': str(driver.id),    # Use numeric ID as driver_id
                'name': driver.name,
                'phone': driver.phone,
                'username': driver.username,    # Include username for reference
                'car_type': driver.car_type,
                'status': 'online',
                'zone_id': driver.zone_id,
                'car_make': driver.car_make,
                'car_model': driver.car_model,
                'car_year': driver.car_year,
                'car_number': driver.car_number,
                'email': f"{driver.username}@driver.local"  # Mock email for mobile apps
            }
        })
        
    except Exception as e:
        logging.error(f"Error in driver login: {str(e)}")
        return create_error_response("Internal server error")

@driver_bp.route('/logout', methods=['POST'])
@token_required
def driver_logout(current_user_data):
    """Driver logout - invalidates session and JWT token"""
    try:
        from utils.auth_manager import AuthenticationManager
        
        # Get driver
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        # Invalidate all sessions for this driver using centralized auth manager
        AuthenticationManager.invalidate_driver_sessions(driver.id)
        
        logging.info(f"Driver logged out: {driver.name} ({driver.username})")
        
        return create_success_response({}, "Logged out successfully")
        
    except Exception as e:
        logging.error(f"Error in driver logout: {str(e)}")
        return create_error_response("Internal server error")

@driver_bp.route('/heartbeat', methods=['POST'])
@token_required
def heartbeat(current_user_data):
    """Driver heartbeat to keep session alive"""
    try:
        from utils.session_manager import update_driver_heartbeat
        
        # Update heartbeat
        success = update_driver_heartbeat(current_user_data['user_id'])
        
        if not success:
            return create_error_response("Driver not found or session invalid")
        
        return jsonify({
            'success': True,
            'message': "Session valid",
            'data': {
                'driver_id': str(current_user_data['user_id']),
                'session_expires': get_ist_time().isoformat(),
                'status': 'active'
            }
        })
        
    except Exception as e:
        logging.error(f"Error in driver heartbeat: {str(e)}")
        return create_error_response("Internal server error")



@driver_bp.route('/incoming_rides', methods=['GET'])
# @token_required  # TEMPORARILY DISABLED FOR TESTING
def incoming_rides(current_user_data=None):
    """Get available rides for driver (JWT protected)"""
    try:
        # For testing without JWT tokens, get driver by phone
        driver_phone = request.args.get('driver_phone')
        if current_user_data:
            # Use JWT token data if available
            driver = Driver.query.get(current_user_data['user_id'])
        elif driver_phone:
            # Fallback to phone parameter for testing
            driver = Driver.query.filter_by(phone=driver_phone).first()
        else:
            return create_error_response("Driver identification required")
        
        if not driver:
            return create_error_response("Driver not found")
        
        # Check if driver is actually online (logged in)
        # Only online drivers should receive ride requests
        if not driver.is_online:
            return create_success_response({
                'rides': [],
                'count': 0
            }, "Driver is offline - no rides available")
        
        # Get available rides (pending status, not assigned to any driver, not rejected by this driver, matching vehicle type)
        # First get ride IDs rejected by this driver
        rejected_ride_ids = db.session.query(RideRejection.ride_id).filter_by(driver_phone=driver.phone)
        
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
@token_required
def accept_ride(current_user_data):
    """Accept a ride (JWT protected)"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_id'])
        if not valid:
            return create_error_response(error)
        
        ride_id = data['ride_id']
        
        # Get driver from JWT token
        driver = Driver.query.get(current_user_data['user_id'])
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
        
        # Broadcast ride status update via WebSocket
        try:
            from utils.websocket_manager import broadcast_ride_status_update
            ride_data = {
                'ride_id': ride.id,
                'status': 'accepted',
                'driver_id': driver.id,
                'customer_id': ride.customer_id,
                'driver_name': driver.name,
                'customer_name': ride.customer.name,
                'pickup_address': ride.pickup_address,
                'drop_address': ride.drop_address
            }
            broadcast_ride_status_update(ride_data)
        except Exception as e:
            logging.warning(f"Failed to broadcast ride accepted via WebSocket: {str(e)}")
        
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
@token_required
def reject_ride(current_user_data):
    """Reject a ride (JWT protected)"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_id'])
        if not valid:
            return create_error_response(error)
        
        ride_id = data['ride_id']
        
        # Get driver from JWT token
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        # Check if ride exists and is pending
        ride = Ride.query.filter_by(id=ride_id, status='pending').first()
        if not ride:
            return create_error_response("Ride not found or no longer available")
        
        # Check if driver has already rejected this ride
        existing_rejection = RideRejection.query.filter_by(
            ride_id=ride_id, 
            driver_phone=driver.phone
        ).first()
        if existing_rejection:
            return create_error_response("Ride already rejected by this driver")
        
        # Create rejection record
        rejection = RideRejection(
            ride_id=ride_id,
            driver_phone=driver.phone,
            rejected_at=get_ist_time()
        )
        db.session.add(rejection)
        db.session.commit()
        
        logging.info(f"Driver {driver.phone} rejected ride {ride_id}")
        
        return create_success_response({
            'ride_id': ride_id,
            'message': 'Ride rejected'
        }, "Ride rejected successfully")
        
    except Exception as e:
        logging.error(f"Error in reject_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@driver_bp.route('/arrived', methods=['POST'])
@token_required
def arrived(current_user_data):
    """Mark driver as arrived at pickup location (JWT protected)"""
    try:
        # Get driver from JWT token
        driver = Driver.query.get(current_user_data['user_id'])
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
        
        # Broadcast ride status update via WebSocket
        try:
            from utils.websocket_manager import broadcast_ride_status_update
            ride_data = {
                'ride_id': ride.id,
                'status': 'arrived',
                'driver_id': driver.id,
                'customer_id': ride.customer_id,
                'driver_name': driver.name,
                'customer_name': ride.customer.name
            }
            broadcast_ride_status_update(ride_data)
        except Exception as e:
            logging.warning(f"Failed to broadcast ride arrived via WebSocket: {str(e)}")
        
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
@token_required
def start_ride(current_user_data):
    """Start the ride with OTP verification (JWT protected)"""
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
        
        # Verify JWT user is the assigned driver
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
            
        if driver.id != ride.driver_id:
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
        
        # Broadcast ride status update via WebSocket
        try:
            from utils.websocket_manager import broadcast_ride_status_update
            ride_data = {
                'ride_id': ride.id,
                'status': 'started',
                'driver_id': driver.id,
                'customer_id': ride.customer_id,
                'driver_name': driver.name,
                'customer_name': ride.customer.name
            }
            broadcast_ride_status_update(ride_data)
        except Exception as e:
            logging.warning(f"Failed to broadcast ride started via WebSocket: {str(e)}")
        
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
@token_required
def complete_ride(current_user_data):
    """Complete the ride (JWT protected)"""
    try:
        # Get driver from JWT token
        driver = Driver.query.get(current_user_data['user_id'])
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
        
        # Broadcast ride status update via WebSocket
        try:
            from utils.websocket_manager import broadcast_ride_status_update
            ride_data = {
                'ride_id': ride.id,
                'status': 'completed',
                'driver_id': driver.id,
                'customer_id': ride.customer_id,
                'driver_name': driver.name,
                'customer_name': ride.customer.name,
                'fare_amount': ride.fare_amount
            }
            broadcast_ride_status_update(ride_data)
        except Exception as e:
            logging.warning(f"Failed to broadcast ride completed via WebSocket: {str(e)}")
        
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
@token_required
def cancel_ride(current_user_data):
    """Cancel accepted ride (JWT protected)"""
    try:
        # Get driver from JWT token
        driver = Driver.query.get(current_user_data['user_id'])
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
@token_required
def current_ride(current_user_data):
    """Get current ride for driver (JWT protected)"""
    try:
        # Get driver from JWT token
        driver = Driver.query.get(current_user_data['user_id'])
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
@token_required
def logout(current_user_data):
    """Logout driver, set offline, and clear location data (JWT protected)"""
    try:
        # Get driver from JWT token
        driver = Driver.query.get(current_user_data['user_id'])
        if driver:
            # Set driver offline
            driver.is_online = False
            
            # Clear location data to prevent ghost driver appearance
            driver.current_lat = None
            driver.current_lng = None
            driver.location_updated_at = None
            driver.zone_id = None
            driver.out_of_zone = False
            
            db.session.commit()
            logging.info(f"Driver {driver.name} ({driver.phone}) logged out, set offline, and location cleared")
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        })
    except Exception as e:
        logging.error(f"Error in logout: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': 'Internal server error'
        }), 500

@driver_bp.route('/status', methods=['POST'])
def update_status():
    """Always online approach - drivers are online when logged in"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(data.get('mobile', ''))
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find driver
        driver = Driver.query.filter_by(phone=phone).first()
        if not driver:
            return create_error_response("Driver not found")
        
        # In the "always online" system, drivers are automatically online when logged in
        # This endpoint now just returns the current status without changing it
        return create_success_response({
            'driver_id': driver.id,
            'name': driver.name,
            'phone': driver.phone,
            'is_online': True  # Always online when logged in
        }, "Driver is always online when logged in")
        
    except Exception as e:
        logging.error(f"Error in update_status: {str(e)}")
        return create_error_response("Internal server error")

@driver_bp.route('/status', methods=['GET'])
def get_status():
    """Get current driver status - always online when logged in"""
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
            'is_online': True,  # Always online in the new system
            'driver_id': driver.id,
            'name': driver.name,
            'phone': driver.phone
        }, "Driver status retrieved")
        
    except Exception as e:
        logging.error(f"Error in get_status: {str(e)}")
        return create_error_response("Internal server error")


@driver_bp.route('/update_location', methods=['POST'])
@driver_bp.route('/update_current_location', methods=['POST'])  # Keep both for backward compatibility
def update_location(current_user_data=None):
    """Unified location update endpoint - handles both driver availability and ride tracking (JWT protected)"""
    try:
        logging.info(f"=== LOCATION UPDATE REQUEST ===")
        logging.info(f"User data from JWT: {current_user_data}")
        logging.info(f"Request headers: {dict(request.headers)}")
        logging.info(f"Content-Type: {request.content_type}")
        
        data = request.get_json()
        logging.info(f"Received location data: {data}")
        
        if not data:
            logging.error("No JSON data provided in location update request")
            return create_error_response("No data provided")
        
        # Parse coordinates from multiple possible formats
        latitude = longitude = None
        if 'latitude' in data and 'longitude' in data:
            lat_field, lng_field = 'latitude', 'longitude'
        elif 'current_lat' in data and 'current_lng' in data:
            lat_field, lng_field = 'current_lat', 'current_lng'
        else:
            logging.error(f"Missing latitude/longitude fields in data: {data}")
            return create_error_response("Missing latitude and longitude fields")
        
        try:
            latitude = float(data[lat_field])
            longitude = float(data[lng_field])
        except (ValueError, TypeError):
            logging.error(f"Invalid coordinate format: {data.get(lat_field)}, {data.get(lng_field)}")
            return create_error_response("Invalid latitude or longitude format")
        
        # Validate coordinates
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return create_error_response("Invalid latitude or longitude values")
        
        # Get driver from JWT token or phone parameter for testing
        if current_user_data:
            driver = Driver.query.get(current_user_data['user_id'])
        else:
            # Fallback for testing without JWT
            driver_phone = data.get('driver_phone') or request.args.get('driver_phone') 
            if driver_phone:
                driver = Driver.query.filter_by(phone=driver_phone).first()
            else:
                return create_error_response("Driver identification required")
        
        if not driver:
            return create_error_response("Driver not found")
        
        # ALWAYS update driver's current location for availability tracking
        driver.current_lat = latitude
        driver.current_lng = longitude
        driver.location_updated_at = get_ist_time()
        
        # Mark driver online and update heartbeat
        if driver.session_token:
            driver.is_online = True
            driver.last_seen = get_ist_time()
            logging.debug(f"Location update auto-marking driver {driver.name} as online")
        
        # If ride_id is provided, also update ride-specific tracking
        ride_updated = False
        if 'ride_id' in data and data['ride_id']:
            ride_id = data['ride_id']
            ride = Ride.query.filter_by(id=ride_id, driver_id=driver.id).first()
            
            if ride and ride.status in ['accepted', 'arrived', 'started']:
                # Mark previous locations as not latest
                RideLocation.query.filter_by(ride_id=ride_id).update({'is_latest': False})
                
                # Create new ride location entry
                new_location = RideLocation(
                    ride_id=ride_id,
                    latitude=latitude,
                    longitude=longitude,
                    is_latest=True
                )
                db.session.add(new_location)
                ride_updated = True
                logging.info(f"Also updated ride tracking for ride {ride_id}")
        
        # Update zone assignment based on new location
        old_zone = driver.zone.zone_name if driver.zone else None
        driver.update_zone_assignment()
        new_zone = driver.zone.zone_name if driver.zone else None
        
        db.session.commit()
        
        logging.info(f"=== DRIVER LOCATION UPDATE ===")
        logging.info(f"Driver: {driver.name} ({driver.phone})")
        logging.info(f"Location: ({latitude}, {longitude})")
        logging.info(f"Zone change: {old_zone} -> {new_zone}")
        logging.info(f"Out of zone: {driver.out_of_zone}")
        logging.info(f"Car type: {driver.car_type}")
        logging.info(f"Online status: {driver.is_online}")
        
        # Broadcast location update via WebSocket
        try:
            from utils.websocket_manager import broadcast_driver_location_update
            location_data = {
                'driver_id': driver.id,
                'name': driver.name,
                'latitude': latitude,
                'longitude': longitude,
                'timestamp': get_ist_time().isoformat(),
                'is_online': driver.is_online,
                'car_type': driver.car_type,
                'zone': driver.zone.zone_name if driver.zone else None,
                'out_of_zone': driver.out_of_zone
            }
            broadcast_driver_location_update(location_data)
            logging.debug(f"Broadcasted WebSocket location update for driver {driver.id}")
        except Exception as e:
            logging.warning(f"Failed to broadcast location update via WebSocket: {str(e)}")
        
        response_data = {
            'driver_id': driver.id,
            'latitude': latitude,
            'longitude': longitude,
            'updated_at': driver.location_updated_at.isoformat(),
            'zone': driver.zone.zone_name if driver.zone else None,
            'out_of_zone': driver.out_of_zone,
            'is_online': driver.is_online
        }
        
        if ride_updated:
            response_data['ride_tracking_updated'] = True
            
        return create_success_response(response_data, "Location updated successfully")
        
    except Exception as e:
        logging.error(f"Error updating driver current location: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")


@driver_bp.route('/get_zone_status', methods=['GET'])
@token_required
def get_zone_status(current_user_data):
    """Get driver's current zone status (JWT protected)"""
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
            return create_error_response("Driver not found")
        
        zone_info = {
            'driver_id': driver.id,
            'current_lat': driver.current_lat,
            'current_lng': driver.current_lng,
            'zone_id': driver.zone_id,
            'zone_name': driver.zone.zone_name if driver.zone else None,
            'out_of_zone': driver.out_of_zone,
            'location_updated_at': driver.location_updated_at.isoformat() if driver.location_updated_at else None
        }
        
        return create_success_response(zone_info, "Zone status retrieved")
        
    except Exception as e:
        logging.error(f"Error getting zone status: {str(e)}")
        return create_error_response("Error retrieving zone status")
