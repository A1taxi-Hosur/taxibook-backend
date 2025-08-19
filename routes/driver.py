from flask import Blueprint, request, jsonify
from app import db, get_ist_time
from utils.auth_manager import token_required, JWTAuthenticationManager
from models import Driver, Ride, RideRejection, RideLocation, Zone
from utils.validators import validate_phone, validate_required_fields, create_error_response, create_success_response
from utils.maps import get_distance_to_pickup
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
    """DEPRECATED: Use /auth/login instead for JWT authentication"""
    return create_error_response("This endpoint is deprecated. Please use /auth/login for JWT authentication.")

@driver_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user_data):
    """Driver logout (JWT protected)"""
    try:
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        # Mark driver as offline
        driver.is_online = False
        db.session.commit()
        
        logging.info(f"Driver logged out: {driver.name} ({driver.phone})")
        
        return create_success_response({
            'driver_id': str(driver.id),
            'status': 'offline'
        }, "Logged out successfully")
        
    except Exception as e:
        logging.error(f"Error in driver logout: {str(e)}")
        return create_error_response("Internal server error")

@driver_bp.route('/heartbeat', methods=['POST'])
@token_required
def heartbeat(current_user_data):
    """Driver heartbeat to maintain session (JWT protected)"""
    try:
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        # Update last seen
        driver.last_seen = get_ist_time()
        db.session.commit()
        
        return create_success_response({
            'driver_id': str(current_user_data['user_id']),
            'status': 'active',
            'last_seen': driver.last_seen.isoformat()
        }, "Heartbeat updated")
        
    except Exception as e:
        logging.error(f"Error in driver heartbeat: {str(e)}")
        return create_error_response("Internal server error")

@driver_bp.route('/incoming_rides', methods=['GET'])
@token_required
def incoming_rides(current_user_data):
    """Get available rides for driver (JWT protected)"""
    try:
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        # Check if driver is online
        if not driver.is_online:
            return create_success_response({
                'rides': [],
                'count': 0
            }, "Driver is offline - no rides available")
        
        # Get available rides (pending status, not assigned, not rejected by this driver, matching vehicle type)
        rejected_ride_ids = db.session.query(RideRejection.ride_id).filter_by(driver_phone=driver.phone)
        
        available_rides = Ride.query.filter(
            Ride.status == 'pending',
            Ride.driver_id.is_(None),
            ~Ride.id.in_(rejected_ride_ids),
            Ride.ride_type == driver.car_type
        ).order_by(Ride.created_at.desc()).all()
        
        # Convert to list of dictionaries
        rides_data = []
        for ride in available_rides:
            ride_dict = ride.to_dict()
            
            # Add distance to pickup if driver location is available
            if driver.current_lat and driver.current_lng:
                from utils.distance import haversine_distance
                distance_km = haversine_distance(
                    driver.current_lat, driver.current_lng,
                    ride.pickup_lat or 0, ride.pickup_lng or 0
                )
                ride_dict['distance_to_pickup_km'] = distance_km
            
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
        if not data or 'ride_id' not in data:
            return create_error_response("Ride ID is required")
        
        ride_id = data['ride_id']
        driver = Driver.query.get(current_user_data['user_id'])
        
        if not driver:
            return create_error_response("Driver not found")
        
        # Check if driver is online
        if not driver.is_online:
            return create_error_response("Driver must be online to accept rides")
        
        # Find the ride
        ride = Ride.query.get(ride_id)
        if not ride:
            return create_error_response("Ride not found")
        
        if ride.status != 'pending':
            return create_error_response("Ride is no longer available")
        
        if ride.driver_id:
            return create_error_response("Ride already assigned to another driver")
        
        # Check if driver has already rejected this ride
        rejection = RideRejection.query.filter_by(
            ride_id=ride_id,
            driver_phone=driver.phone
        ).first()
        
        if rejection:
            return create_error_response("You have already rejected this ride")
        
        # Assign ride to driver
        ride.driver_id = driver.id
        ride.status = 'accepted'
        ride.accepted_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Ride {ride_id} accepted by driver {driver.name} ({driver.phone})")
        
        # Broadcast ride update via WebSocket
        from utils.websocket_manager import broadcast_ride_update
        broadcast_ride_update(ride)
        
        return create_success_response({
            'ride_id': ride_id,
            'status': 'accepted',
            'ride': ride.to_dict()
        }, "Ride accepted successfully")
        
    except Exception as e:
        logging.error(f"Error in accept_ride: {str(e)}")
        return create_error_response("Error accepting ride")

@driver_bp.route('/reject_ride', methods=['POST'])
@token_required
def reject_ride(current_user_data):
    """Reject a ride (JWT protected)"""
    try:
        data = request.get_json()
        if not data or 'ride_id' not in data:
            return create_error_response("Ride ID is required")
        
        ride_id = data['ride_id']
        driver = Driver.query.get(current_user_data['user_id'])
        
        if not driver:
            return create_error_response("Driver not found")
        
        # Check if already rejected
        existing_rejection = RideRejection.query.filter_by(
            ride_id=ride_id,
            driver_phone=driver.phone
        ).first()
        
        if not existing_rejection:
            # Add rejection record
            rejection = RideRejection(
                ride_id=ride_id,
                driver_phone=driver.phone,
                rejected_at=get_ist_time()
            )
            db.session.add(rejection)
            db.session.commit()
        
        logging.info(f"Ride {ride_id} rejected by driver {driver.name} ({driver.phone})")
        
        return create_success_response({
            'ride_id': ride_id,
            'status': 'rejected'
        }, "Ride rejected successfully")
        
    except Exception as e:
        logging.error(f"Error in reject_ride: {str(e)}")
        return create_error_response("Error rejecting ride")

@driver_bp.route('/update_current_location', methods=['POST'])
@token_required
def update_current_location(current_user_data):
    """Update driver's current location (JWT protected)"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        required_fields = ['latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return create_error_response(f"{field} is required")
        
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return create_error_response("Invalid latitude or longitude")
        
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        logging.info(f"=== LOCATION UPDATE REQUEST ===")
        logging.info(f"Received location data: {data}")
        
        # Update driver location (RAW GPS DATA - NO MODIFICATIONS)
        old_zone = driver.zone_id
        driver.current_lat = latitude  # Store exact GPS coordinates
        driver.current_lng = longitude  # Store exact GPS coordinates
        driver.location_updated_at = get_ist_time()
        driver.last_seen = get_ist_time()
        
        # Update zone assignment based on location
        driver.update_zone_assignment()
        
        # Get zone name for response
        zone_name = driver.zone.name if driver.zone_id and driver.zone else 'unknown'
        
        db.session.commit()
        
        logging.info(f"=== DRIVER LOCATION UPDATE ===")
        logging.info(f"Driver: {driver.name} ({driver.phone})")
        logging.info(f"Location: ({latitude}, {longitude})")  # Log raw coordinates
        logging.info(f"Zone change: {Zone.query.get(old_zone).name if old_zone else 'none'} -> {zone_name}")
        logging.info(f"Out of zone: {driver.out_of_zone}")
        logging.info(f"Car type: {driver.car_type}")
        logging.info(f"Online status: {driver.is_online}")
        
        # Broadcast location update via WebSocket
        from utils.websocket_manager import broadcast_driver_location_update
        broadcast_driver_location_update(driver)
        
        return create_success_response({
            'driver_id': driver.id,
            'latitude': latitude,  # Return exact coordinates
            'longitude': longitude,  # Return exact coordinates
            'zone': zone_name,
            'out_of_zone': driver.out_of_zone,
            'is_online': driver.is_online,
            'updated_at': driver.location_updated_at.isoformat()
        }, "Location updated successfully")
        
    except Exception as e:
        logging.error(f"Error updating driver location: {str(e)}")
        return create_error_response("Failed to update location")

@driver_bp.route('/update_location', methods=['POST'])
@token_required
def update_location(current_user_data):
    """Update driver location during active ride (JWT protected)"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        # Validate required fields
        required_fields = ['ride_id', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return create_error_response(f"{field} is required")
        
        try:
            ride_id = int(data['ride_id'])
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return create_error_response("Invalid ride_id, latitude, or longitude")
        
        # Find the ride
        ride = Ride.query.get(ride_id)
        if not ride:
            return create_error_response("Ride not found")
        
        if ride.driver_id != driver.id:
            return create_error_response("This ride is not assigned to you")
        
        # Update driver's general location
        driver.current_lat = latitude
        driver.current_lng = longitude
        driver.location_updated_at = get_ist_time()
        driver.last_seen = get_ist_time()
        driver.update_zone_assignment()
        
        # Create ride-specific location record
        ride_location = RideLocation(
            ride_id=ride_id,
            latitude=latitude,
            longitude=longitude,
            recorded_at=get_ist_time()
        )
        db.session.add(ride_location)
        db.session.commit()
        
        logging.info(f"Driver {driver.name} location updated during ride {ride_id}: ({latitude}, {longitude})")
        
        # Broadcast location update
        from utils.websocket_manager import broadcast_driver_location_update
        broadcast_driver_location_update(driver, ride_id)
        
        return create_success_response({
            'driver_id': driver.id,
            'ride_id': ride_id,
            'latitude': latitude,
            'longitude': longitude,
            'updated_at': driver.location_updated_at.isoformat()
        }, "Location updated successfully")
        
    except Exception as e:
        logging.error(f"Error updating driver location for ride: {str(e)}")
        return create_error_response("Failed to update location")

@driver_bp.route('/current_ride', methods=['GET'])
@token_required
def current_ride(current_user_data):
    """Get driver's current active ride (JWT protected)"""
    try:
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        # Find active ride
        active_ride = Ride.query.filter_by(driver_id=driver.id).filter(
            Ride.status.in_(['accepted', 'arrived', 'started'])
        ).first()
        
        if not active_ride:
            return create_success_response({
                'has_active_ride': False,
                'ride': None
            }, "No active ride")
        
        return create_success_response({
            'has_active_ride': True,
            'ride': active_ride.to_dict()
        }, "Active ride retrieved")
        
    except Exception as e:
        logging.error(f"Error getting current ride: {str(e)}")
        return create_error_response("Error retrieving current ride")

@driver_bp.route('/update_ride_status', methods=['POST'])
@token_required
def update_ride_status(current_user_data):
    """Update ride status (arrived, started, completed) (JWT protected)"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        driver = Driver.query.get(current_user_data['user_id'])
        if not driver:
            return create_error_response("Driver not found")
        
        required_fields = ['ride_id', 'status']
        for field in required_fields:
            if field not in data:
                return create_error_response(f"{field} is required")
        
        ride_id = data['ride_id']
        new_status = data['status']
        
        # Validate status
        valid_statuses = ['arrived', 'started', 'completed']
        if new_status not in valid_statuses:
            return create_error_response(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Find the ride
        ride = Ride.query.get(ride_id)
        if not ride:
            return create_error_response("Ride not found")
        
        if ride.driver_id != driver.id:
            return create_error_response("This ride is not assigned to you")
        
        # Update ride status with timestamp
        ride.status = new_status
        
        if new_status == 'arrived':
            ride.arrived_at = get_ist_time()
        elif new_status == 'started':
            ride.started_at = get_ist_time()
        elif new_status == 'completed':
            ride.completed_at = get_ist_time()
            # Optional: Calculate final fare if provided
            if 'final_fare' in data:
                try:
                    ride.final_fare = float(data['final_fare'])
                except (ValueError, TypeError):
                    pass  # Keep estimated fare if final_fare is invalid
        
        db.session.commit()
        
        logging.info(f"Ride {ride_id} status updated to '{new_status}' by driver {driver.name}")
        
        # Broadcast ride update
        from utils.websocket_manager import broadcast_ride_update
        broadcast_ride_update(ride)
        
        return create_success_response({
            'ride_id': ride_id,
            'status': new_status,
            'ride': ride.to_dict()
        }, f"Ride status updated to {new_status}")
        
    except Exception as e:
        logging.error(f"Error updating ride status: {str(e)}")
        return create_error_response("Error updating ride status")