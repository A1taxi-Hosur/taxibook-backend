from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, get_ist_time
from models import Customer, Ride, RideLocation, FareConfig, Driver, SpecialFareConfig, Zone
from utils.validators import validate_phone, validate_required_fields, validate_ride_type, create_error_response, create_success_response
from utils.maps import get_distance_and_fare
from utils.distance import haversine_distance, filter_drivers_by_proximity
import logging
from datetime import datetime, date, time

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/login_or_register', methods=['POST'])
def login_or_register():
    """Customer login or registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['phone', 'name'])
        if not valid:
            return create_error_response(error)
        
        # Validate phone number
        valid, phone_or_error = validate_phone(data['phone'])
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        name = data['name'].strip()
        
        if not name:
            return create_error_response("Name cannot be empty")
        
        # Check if customer exists
        customer = Customer.query.filter_by(phone=phone).first()
        
        if customer:
            # Login existing customer
            login_user(customer)
            logging.info(f"Customer logged in: {customer.name} ({customer.phone})")
            return create_success_response({
                'customer_id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'action': 'login'
            }, "Login successful")
        else:
            # Register new customer
            customer = Customer(name=name, phone=phone)
            db.session.add(customer)
            db.session.commit()
            
            login_user(customer)
            logging.info(f"New customer registered: {customer.name} ({customer.phone})")
            return create_success_response({
                'customer_id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'action': 'register'
            }, "Registration successful")
            
    except Exception as e:
        logging.error(f"Error in customer login/register: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@customer_bp.route('/book_ride', methods=['POST'])
def book_ride():
    """Book a new ride"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['customer_phone', 'pickup_address', 'drop_address', 'ride_type'])
        if not valid:
            return create_error_response(error)
        
        # Validate phone number
        valid, phone_or_error = validate_phone(data['customer_phone'])
        if not valid:
            return create_error_response(phone_or_error)
        
        # Validate ride type
        valid, ride_type_or_error = validate_ride_type(data['ride_type'])
        if not valid:
            return create_error_response(ride_type_or_error)
        
        phone = phone_or_error
        ride_type = ride_type_or_error
        pickup_address = data['pickup_address'].strip()
        drop_address = data['drop_address'].strip()
        
        if not pickup_address or not drop_address:
            return create_error_response("Pickup and drop addresses cannot be empty")
        
        # Find customer
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            return create_error_response("Customer not found. Please login first.")
        
        # Check if customer has any ongoing ride
        ongoing_ride = Ride.query.filter_by(
            customer_id=customer.id
        ).filter(
            Ride.status.in_(['pending', 'accepted', 'arrived', 'started'])
        ).first()
        
        if ongoing_ride:
            return create_error_response("You already have an ongoing ride")
        
        # Get optional coordinates
        pickup_lat = data.get('pickup_lat')
        pickup_lng = data.get('pickup_lng')
        drop_lat = data.get('drop_lat')
        drop_lng = data.get('drop_lng')
        
        # Calculate distance using Google Maps API (for distance only)
        success, distance_km, _, error_msg = get_distance_and_fare(
            pickup_address, drop_address, pickup_lat, pickup_lng, drop_lat, drop_lng
        )
        
        if not success:
            return create_error_response(error_msg)
        
        # Get optional ride category and schedule details
        ride_category = data.get('ride_category', 'regular').lower()
        scheduled_date = data.get('scheduled_date')
        scheduled_time = data.get('scheduled_time')
        hours = data.get('hours')  # For rental rides
        
        # Validate ride category
        if ride_category not in ['regular', 'airport', 'rental', 'outstation']:
            return create_error_response("Invalid ride category")
        
        # Validate vehicle type for airport rides
        if ride_category == 'airport' and ride_type == 'hatchback':
            return create_error_response("Airport rides only allow sedan or suv")
        
        # Calculate fare based on ride category
        if ride_category == 'regular':
            # Regular ride using standard fare config
            fare_success, fare_amount, fare_error = FareConfig.calculate_fare(ride_type, distance_km)
            if not fare_success:
                return create_error_response(fare_error)
        else:
            # Special ride using special fare config
            fare_success, fare_amount, fare_error = SpecialFareConfig.calculate_special_fare(
                ride_category, ride_type, distance_km, hours
            )
            if not fare_success:
                return create_error_response(fare_error)
        
        # Check if we have pickup coordinates for proximity dispatch
        if pickup_lat is None or pickup_lng is None:
            return create_error_response("Pickup coordinates are required for ride booking")
        
        # For regular rides, find eligible drivers within 5km radius
        if ride_category == 'regular':
            online_drivers = Driver.query.filter_by(is_online=True, car_type=ride_type).all()
            eligible_drivers = filter_drivers_by_proximity(
                online_drivers, pickup_lat, pickup_lng, max_distance_km=5.0
            )
            
            # Check if any drivers are available within range
            if not eligible_drivers:
                return create_error_response("No drivers available within 5km of pickup location")
        
        # Parse scheduled datetime if provided
        scheduled_date_obj = None
        scheduled_time_obj = None
        if scheduled_date and scheduled_time:
            try:
                # Parse date (DD/MM/YYYY format)
                day, month, year = scheduled_date.split('/')
                scheduled_date_obj = date(int(year), int(month), int(day))
                
                # Parse time (HH:MM format)
                hour, minute = scheduled_time.split(':')
                scheduled_time_obj = time(int(hour), int(minute))
                
            except ValueError:
                return create_error_response("Invalid date/time format. Use DD/MM/YYYY for date and HH:MM for time")
        
        # Create new ride
        ride = Ride(
            customer_id=customer.id,
            customer_phone=phone,
            pickup_address=pickup_address,
            drop_address=drop_address,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            drop_lat=drop_lat,
            drop_lng=drop_lng,
            distance_km=distance_km,
            fare_amount=fare_amount,
            final_fare=fare_amount,  # Freeze fare at booking time
            ride_type=ride_type,
            ride_category=ride_category,
            scheduled_date=scheduled_date_obj,
            scheduled_time=scheduled_time_obj,
            status='new'
        )
        
        db.session.add(ride)
        db.session.commit()
        
        logging.info(f"Ride booked: {ride.id} for customer {customer.name} - {ride_type}")
        return create_success_response({
            'ride_id': ride.id,
            'pickup_address': pickup_address,
            'drop_address': drop_address,
            'distance_km': distance_km,
            'fare_amount': fare_amount,
            'ride_type': ride_type,
            'ride_category': ride_category,
            'final_fare': fare_amount,
            'status': 'new'
        }, "Ride booked successfully")
        
    except Exception as e:
        logging.error(f"Error in book_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@customer_bp.route('/ride_status', methods=['GET'])
def ride_status():
    """Get current ride status for customer"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return create_error_response("Phone number is required")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find customer
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            return create_success_response({'has_active_ride': False}, "No active ride")
        
        # Get active ride
        active_ride = Ride.query.filter_by(
            customer_id=customer.id
        ).filter(
            Ride.status.in_(['pending', 'accepted', 'arrived', 'started'])
        ).first()
        
        if not active_ride:
            return create_success_response({'has_active_ride': False}, "No active ride")
        
        # Return ride details with OTP for customer
        ride_data = active_ride.to_dict(include_otp=True)
        ride_data['has_active_ride'] = True
        
        return create_success_response(ride_data, "Ride status retrieved")
        
    except Exception as e:
        logging.error(f"Error in ride_status: {str(e)}")
        return create_success_response({'has_active_ride': False}, "Error retrieving ride status")

@customer_bp.route('/cancel_ride', methods=['POST'])
def cancel_ride():
    """Cancel current ride"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        phone = data.get('phone')
        if not phone:
            return create_error_response("Phone number is required")
        
        # Validate phone number
        valid, phone_or_error = validate_phone(phone)
        if not valid:
            return create_error_response(phone_or_error)
        
        phone = phone_or_error
        
        # Find customer
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            return create_error_response("Customer not found")
        
        # Find active ride
        active_ride = Ride.query.filter_by(
            customer_id=customer.id
        ).filter(
            Ride.status.in_(['pending', 'accepted'])
        ).first()
        
        if not active_ride:
            return create_error_response("No cancellable ride found")
        
        # Cancel the ride
        active_ride.status = 'cancelled'
        active_ride.cancelled_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Ride cancelled: {active_ride.id} by customer {customer.name}")
        return create_success_response({
            'ride_id': active_ride.id,
            'status': 'cancelled'
        }, "Ride cancelled successfully")
        
    except Exception as e:
        logging.error(f"Error in cancel_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@customer_bp.route('/ride_estimate', methods=['POST'])
def ride_estimate():
    """Get fare estimates for all ride types based on pickup and drop coordinates"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("No data provided", 400)
        
        # Validate required coordinates
        required_fields = ['pickup_lat', 'pickup_lng', 'drop_lat', 'drop_lng']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        pickup_lat = data['pickup_lat']
        pickup_lng = data['pickup_lng']
        drop_lat = data['drop_lat']
        drop_lng = data['drop_lng']
        
        # Validate coordinate ranges
        if not (-90 <= pickup_lat <= 90) or not (-90 <= drop_lat <= 90):
            return jsonify({'error': 'Invalid latitude values'}), 400
        if not (-180 <= pickup_lng <= 180) or not (-180 <= drop_lng <= 180):
            return jsonify({'error': 'Invalid longitude values'}), 400
        
        # Use Google Maps to calculate actual road distance
        # We'll use coordinates as both address and coordinates for the distance calculation
        pickup_address = f"{pickup_lat},{pickup_lng}"
        drop_address = f"{drop_lat},{drop_lng}"
        
        success, distance_km, _, error_message = get_distance_and_fare(
            pickup_address, drop_address, 
            pickup_lat, pickup_lng, 
            drop_lat, drop_lng
        )
        
        if not success:
            logging.error(f"Distance calculation failed: {error_message}")
            return jsonify({
                'error': 'Could not calculate fare estimate'
            }), 500
        
        # Calculate fare estimates using database configuration
        # CENTRALIZED PRICING LOGIC - BACKEND ONLY
        # ========================================
        # ALL fare calculations MUST happen on backend to ensure:
        # 1. Security: Prevents client-side fare manipulation
        # 2. Consistency: Single source of truth for pricing
        # 3. Flexibility: Easy to implement dynamic pricing, surge rates, discounts
        # 4. Auditability: All pricing decisions logged and traceable
        #
        # NEVER allow frontend/mobile apps to calculate fares independently
        # Frontend should only display backend-provided pricing
        
        estimates = {}
        ride_types = ['hatchback', 'sedan', 'suv']
        
        for ride_type in ride_types:
            # Calculate fare using database configuration
            fare_success, fare_amount, fare_error = FareConfig.calculate_fare(ride_type, distance_km)
            if fare_success:
                estimates[ride_type] = round(fare_amount, 2)
            else:
                # Fallback if fare calculation fails
                estimates[ride_type] = 0
                logging.error(f"Fare calculation failed for {ride_type}: {fare_error}")
        
        logging.info(f"Fare estimates calculated for {distance_km:.2f}km: {estimates}")
        
        # Return response in the exact format specified
        return jsonify({
            'success': True,
            'distance_km': round(distance_km, 2),
            'estimates': estimates
        })
        
    except Exception as e:
        logging.error(f"Error in ride_estimate: {str(e)}")
        return jsonify({
            'error': 'Could not calculate fare estimate'
        }), 500

@customer_bp.route('/driver_location/<int:ride_id>', methods=['GET'])
def get_driver_location(ride_id):
    """Get latest driver location for a specific ride"""
    try:
        # Validate that the ride exists
        ride = Ride.query.get(ride_id)
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404
        
        # Only allow location tracking for active rides
        if ride.status not in ['accepted', 'arrived', 'started']:
            return jsonify({'error': 'Location tracking only available for active rides'}), 400
        
        # Get latest location for this ride
        latest_location = RideLocation.query.filter_by(
            ride_id=ride_id,
            is_latest=True
        ).first()
        
        if not latest_location:
            return jsonify({'error': 'No location data available'}), 404
        
        # Return location data
        return jsonify({
            'ride_id': ride_id,
            'latitude': latest_location.latitude,
            'longitude': latest_location.longitude,
            'timestamp': latest_location.timestamp.isoformat(),
            'ride_status': ride.status,
            'pickup_lat': ride.pickup_lat,
            'pickup_lng': ride.pickup_lng,
            'drop_lat': ride.drop_lat,
            'drop_lng': ride.drop_lng
        })
        
    except Exception as e:
        logging.error(f"Error getting driver location: {str(e)}")
        return jsonify({'error': 'Error retrieving location'}), 500


@customer_bp.route('/bookings/<int:customer_id>', methods=['GET'])
def get_customer_bookings(customer_id):
    """Get bookings for a specific customer categorized by status"""
    try:
        # Find customer
        customer = Customer.query.get(customer_id)
        if not customer:
            return create_error_response("Customer not found", 404)
        
        # Get all customer rides
        rides = Ride.query.filter_by(customer_id=customer_id).order_by(Ride.created_at.desc()).all()
        
        # Categorize rides based on status
        bookings = []
        ongoing = []
        history = []
        
        for ride in rides:
            ride_data = ride.to_dict()
            
            # Tab categorization based on status
            if ride.status in ['new', 'assigned']:
                bookings.append(ride_data)
            elif ride.status == 'active':
                ongoing.append(ride_data)
            elif ride.status == 'completed':
                history.append(ride_data)
        
        return create_success_response({
            'customer_id': customer_id,
            'bookings': bookings,      # new + assigned
            'ongoing': ongoing,        # active
            'history': history         # completed
        })
    
    except Exception as e:
        logging.error(f"Error getting customer bookings: {str(e)}")
        return create_error_response("Error retrieving bookings")


@customer_bp.route('/logout', methods=['POST'])
def logout():
    """Logout customer"""
    try:
        logout_user()
        return create_success_response(message="Logout successful")
    except Exception as e:
        logging.error(f"Error in logout: {str(e)}")
        return create_error_response("Internal server error")
