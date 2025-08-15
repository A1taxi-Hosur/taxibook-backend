from flask import Blueprint, request, jsonify
from app import db, get_ist_time, generate_jwt_token
from utils.auth_manager import token_required
from models import Customer, Ride, RideLocation, FareConfig, Driver, SpecialFareConfig, Zone, Advertisement, PromoCode
from utils.validators import validate_phone, validate_required_fields, validate_ride_type, create_error_response, create_success_response
from utils.maps import get_distance_and_fare
from utils.distance import haversine_distance, filter_drivers_by_proximity
from utils.ride_dispatch_engine import RideDispatchEngine
from utils.auth_helpers import standardized_auth_response, handle_auth_error
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
            # Login existing customer - create session and generate JWT token using centralized auth manager
            from utils.auth_manager import AuthenticationManager
            session_token = AuthenticationManager.create_customer_session(customer)
            
            token_data = {
                'user_id': customer.id,
                'username': customer.phone,
                'user_type': 'customer',
                'session_token': session_token
            }
            token = generate_jwt_token(token_data)
            logging.info(f"Customer logged in: {customer.name} ({customer.phone})")
            return jsonify({
                'success': True,
                'token': token,
                'customer': {
                    'id': customer.id,
                    'phone': customer.phone,
                    'name': customer.name
                }
            })
        else:
            # Register new customer - create session and generate JWT token
            customer = Customer(name=name, phone=phone)
            db.session.add(customer)
            db.session.commit()
            
            from utils.auth_manager import AuthenticationManager
            session_token = AuthenticationManager.create_customer_session(customer)
            
            token_data = {
                'user_id': customer.id,
                'username': customer.phone,
                'user_type': 'customer',
                'session_token': session_token
            }
            token = generate_jwt_token(token_data)
            logging.info(f"New customer registered: {customer.name} ({customer.phone})")
            return jsonify({
                'success': True,
                'token': token,
                'customer': {
                    'id': customer.id,
                    'phone': customer.phone,
                    'name': customer.name
                }
            })
            
    except Exception as e:
        logging.error(f"Error in customer login/register: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@customer_bp.route('/book_ride', methods=['POST'])
@token_required
def book_ride(current_user):
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
        
        # Apply promo code if provided
        promo_code_str = data.get('promo_code', '').strip().upper()
        discount_applied = 0.0
        
        if promo_code_str:
            from models import PromoCode
            promo = PromoCode.query.filter_by(code=promo_code_str).first()
            if promo:
                is_valid, validation_message = promo.is_valid(ride_type, ride_category, fare_amount)
                if is_valid:
                    discount_applied = promo.calculate_discount(fare_amount)
                    fare_amount = max(0, fare_amount - discount_applied)
                    # Increment usage counter
                    promo.current_uses += 1
                    logging.info(f"Applied promo {promo.code}: discount ₹{discount_applied:.2f}")
                else:
                    logging.info(f"Invalid promo code {promo_code_str}: {validation_message}")
                    return create_error_response(validation_message)
            else:
                logging.info(f"Promo code {promo_code_str} not found")
                return create_error_response("Invalid promo code")
        
        # Check if we have pickup coordinates for proximity dispatch
        if pickup_lat is None or pickup_lng is None:
            return create_error_response("Pickup coordinates are required for ride booking")
        
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
        
        # Generate OTP for ride start
        import random
        start_otp = str(random.randint(100000, 999999))
        
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
            promo_code=promo_code_str if promo_code_str else None,
            discount_applied=discount_applied,
            ride_type=ride_type,
            ride_category=ride_category,
            scheduled_date=scheduled_date_obj,
            scheduled_time=scheduled_time_obj,
            start_otp=start_otp,
            status='new'
        )
        
        db.session.add(ride)
        db.session.commit()
        
        # Check if it's a special ride category that requires admin assignment
        if ride_category != 'regular':
            # All non-regular rides (airport, rental, outstation) require admin assignment
            if scheduled_date_obj and scheduled_time_obj:
                logging.info(f"Scheduled {ride_category} ride – skipping auto dispatch for ride {ride.id}")
                message = f"Scheduled {ride_category} ride booked successfully."
                response_data = {
                    "ride_id": ride.id,
                    "pickup_address": pickup_address,
                    "drop_address": drop_address,
                    "distance_km": distance_km,
                    "fare_amount": fare_amount,
                    "ride_type": ride_type,
                    "ride_category": ride_category,
                    "final_fare": fare_amount,
                    "promo_code": promo_code_str if promo_code_str else None,
                    "discount_applied": discount_applied,
                    "scheduled": True,
                    "scheduled_date": scheduled_date,
                    "scheduled_time": scheduled_time,
                    "status": "new"
                }
            else:
                logging.info(f"Immediate {ride_category} ride – skipping auto dispatch for ride {ride.id}")
                message = f"{ride_category.title()} ride booked successfully. Admin will assign driver."
                response_data = {
                    "ride_id": ride.id,
                    "pickup_address": pickup_address,
                    "drop_address": drop_address,
                    "distance_km": distance_km,
                    "fare_amount": fare_amount,
                    "ride_type": ride_type,
                    "ride_category": ride_category,
                    "final_fare": fare_amount,
                    "promo_code": promo_code_str if promo_code_str else None,
                    "discount_applied": discount_applied,
                    "scheduled": False,
                    "requires_admin_assignment": True,
                    "status": "new"
                }
            
            return create_success_response(response_data, message)
        
        # For regular rides only, notify matching drivers in zone
        if ride_category == 'regular' and not scheduled_date_obj and not scheduled_time_obj:
            try:
                # Find matching drivers in pickup zone
                from utils.driver_notification_system import notify_matching_drivers_in_zone
                notification_result = notify_matching_drivers_in_zone(ride.id, pickup_lat, pickup_lng, ride_type)
                
                if notification_result.get('success'):
                    # Drivers notified successfully - status should now be 'pending'
                    db.session.refresh(ride)  # Refresh to get updated status
                    logging.info(f"Matching drivers notified for ride {ride.id}, status: {ride.status}")
                    return create_success_response({
                        'ride_id': ride.id,
                        'pickup_address': pickup_address,
                        'drop_address': drop_address,
                        'distance_km': distance_km,
                        'fare_amount': fare_amount,
                        'ride_type': ride_type,
                        'ride_category': ride_category,
                        'final_fare': fare_amount,
                        'promo_code': promo_code_str if promo_code_str else None,
                        'discount_applied': discount_applied,
                        'status': ride.status,  # Show updated status (should be 'pending')
                        'drivers_notified': True,
                        'notification_info': {
                            'drivers_count': notification_result.get('drivers_count'),
                            'zone_name': notification_result.get('zone_name'),
                            'message': notification_result.get('message')
                        }
                    }, "Ride booked successfully. Matching drivers have been notified.")
                
                else:
                    # No matching drivers found in zone - but status should be 'pending'
                    db.session.refresh(ride)  # Refresh to get updated status from notification system
                    logging.info(f"No matching drivers found in zone for ride {ride.id}, status updated to: {ride.status}")
                    return create_success_response({
                        'ride_id': ride.id,
                        'pickup_address': pickup_address,
                        'drop_address': drop_address,
                        'distance_km': distance_km,
                        'fare_amount': fare_amount,
                        'ride_type': ride_type,
                        'ride_category': ride_category,
                        'final_fare': fare_amount,
                        'promo_code': promo_code_str if promo_code_str else None,
                        'discount_applied': discount_applied,
                        'status': ride.status,  # Show updated status ('pending' even when no drivers found)
                        'drivers_notified': False,
                        'error_message': notification_result.get('message', 'No matching drivers available in zone')
                    }, "Ride booked. No matching drivers available in your area.")
                
            except Exception as notification_error:
                logging.error(f"Driver notification error for ride {ride.id}: {str(notification_error)}")
                # Continue with ride booking even if notification fails
                return create_success_response({
                    'ride_id': ride.id,
                    'pickup_address': pickup_address,
                    'drop_address': drop_address,
                    'distance_km': distance_km,
                    'fare_amount': fare_amount,
                    'ride_type': ride_type,
                    'ride_category': ride_category,
                    'final_fare': fare_amount,
                    'promo_code': promo_code_str if promo_code_str else None,
                    'discount_applied': discount_applied,
                    'status': 'new',
                    'requires_manual_assignment': True
                }, "Ride booked. Dispatch system error - manual assignment required.")
        
        else:
            # Scheduled ride - no immediate dispatch
            logging.info(f"Scheduled ride booked: {ride.id} for customer {customer.name} - {ride_type}")
            return create_success_response({
                'ride_id': ride.id,
                'pickup_address': pickup_address,
                'drop_address': drop_address,
                'distance_km': distance_km,
                'fare_amount': fare_amount,
                'ride_type': ride_type,
                'ride_category': ride_category,
                'final_fare': fare_amount,
                'promo_code': promo_code_str if promo_code_str else None,
                'discount_applied': discount_applied,
                'status': 'new',
                'scheduled': True,
                'scheduled_date': scheduled_date,
                'scheduled_time': scheduled_time
            }, "Scheduled ride booked successfully")
        
    except Exception as e:
        logging.error(f"Error in book_ride: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@customer_bp.route('/validate_promo', methods=['POST'])
@token_required
def validate_promo(current_user):
    """Validate promo code for given ride parameters"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['promo_code', 'fare_amount'])
        if not valid:
            return create_error_response(error)
        
        promo_code_str = data['promo_code'].strip().upper()
        fare_amount = data['fare_amount']
        ride_type = data.get('ride_type')
        ride_category = data.get('ride_category', 'regular')
        
        # Validate fare amount
        if fare_amount <= 0:
            return create_error_response("Invalid fare amount")
        
        # Find promo code
        from models import PromoCode
        promo = PromoCode.query.filter_by(code=promo_code_str).first()
        if not promo:
            return create_error_response("Invalid promo code")
        
        # Validate promo code
        is_valid, validation_message = promo.is_valid(ride_type, ride_category, fare_amount)
        if not is_valid:
            return create_error_response(validation_message)
        
        # Calculate discount
        discount_amount = promo.calculate_discount(fare_amount)
        final_fare = max(0, fare_amount - discount_amount)
        
        return create_success_response({
            'promo_code': promo_code_str,
            'discount_type': promo.discount_type,
            'discount_value': promo.discount_value,
            'discount_amount': discount_amount,
            'original_fare': fare_amount,
            'final_fare': final_fare,
            'valid': True
        }, "Promo code is valid")
        
    except Exception as e:
        logging.error(f"Error in validate_promo: {str(e)}")
        return create_error_response("Internal server error")

@customer_bp.route('/approve_zone_expansion', methods=['POST'])
@token_required
def approve_zone_expansion(current_user):
    """Customer approval for zone expansion with extra fare"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_id', 'approved'])
        if not valid:
            return create_error_response(error)
        
        ride_id = data['ride_id']
        approved = data['approved']
        
        # Find the ride
        ride = Ride.query.filter_by(id=ride_id).first()
        if not ride:
            return create_error_response("Ride not found")
        
        if approved:
            # Customer approved expansion - continue with enhanced dispatch
            try:
                driver_id = data.get('driver_id')
                zone_id = data.get('zone_id')
                extra_fare = data.get('extra_fare', 0)
                
                if not driver_id or not zone_id:
                    return create_error_response("Driver ID and Zone ID are required for zone expansion")
                
                from utils.enhanced_dispatch_engine import approve_zone_expansion_for_ride
                result = approve_zone_expansion_for_ride(ride_id, driver_id, zone_id, extra_fare)
                
                if result.get('success'):
                    return create_success_response({
                        'ride_id': ride_id,
                        'status': 'assigned',
                        'driver_assigned': True,
                        'driver_id': result.get('driver_id'),
                        'final_fare': result.get('final_fare'),
                        'extra_fare': result.get('extra_fare')
                    }, "Zone expansion approved and driver assigned")
                
                else:
                    return create_error_response(result.get('error', 'Failed to approve zone expansion'))
                
            except Exception as dispatch_error:
                logging.error(f"Zone expansion dispatch error: {str(dispatch_error)}")
                return create_error_response("Failed to assign driver after zone expansion")
        
        else:
            # Customer declined expansion - cancel ride
            ride.status = 'cancelled'
            ride.cancelled_at = get_ist_time()
            db.session.commit()
            
            return create_success_response({
                'ride_id': ride_id,
                'status': 'cancelled'
            }, "Zone expansion declined. Ride cancelled.")
        
    except Exception as e:
        logging.error(f"Error in approve_zone_expansion: {str(e)}")
        db.session.rollback()
        return create_error_response("Internal server error")

@customer_bp.route('/ride_status', methods=['GET'])
@token_required
def ride_status(current_user):
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
@token_required
def cancel_ride(current_user):
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
            return jsonify({'success': False, 'message': f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        pickup_lat = data['pickup_lat']
        pickup_lng = data['pickup_lng']
        drop_lat = data['drop_lat']
        drop_lng = data['drop_lng']
        
        # Validate coordinate ranges
        if not (-90 <= pickup_lat <= 90) or not (-90 <= drop_lat <= 90):
            return jsonify({'success': False, 'message': 'Invalid latitude values'}), 400
        if not (-180 <= pickup_lng <= 180) or not (-180 <= drop_lng <= 180):
            return jsonify({'success': False, 'message': 'Invalid longitude values'}), 400
        
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
        
        # Check if promo code is provided
        promo_code_str = data.get('promo_code', '').strip().upper()
        promo_discount_info = None
        
        promo = None
        if promo_code_str:
            from models import PromoCode
            promo = PromoCode.query.filter_by(code=promo_code_str).first()
            if promo:
                promo_discount_info = {
                    'promo_code': promo_code_str,
                    'discount_type': promo.discount_type,
                    'discount_value': promo.discount_value,
                    'min_fare': promo.min_fare,
                    'valid_ride_types': promo.ride_type,
                    'valid_ride_categories': promo.ride_category
                }
        
        for ride_type in ride_types:
            # Calculate fare using database configuration
            fare_success, fare_amount, fare_error = FareConfig.calculate_fare(ride_type, distance_km)
            if fare_success:
                original_fare = round(fare_amount, 2)
                final_fare = original_fare
                discount_applied = 0.0
                
                # Apply promo code if provided and valid
                if promo_discount_info and promo:
                    ride_category = data.get('ride_category', 'regular')
                    is_valid, validation_message = promo.is_valid(ride_type, ride_category, fare_amount)
                    if is_valid:
                        discount_applied = promo.calculate_discount(fare_amount)
                        final_fare = max(0, fare_amount - discount_applied)
                
                estimates[ride_type] = {
                    'original_fare': original_fare,
                    'final_fare': round(final_fare, 2),
                    'discount_applied': round(discount_applied, 2)
                }
            else:
                # Fallback if fare calculation fails
                estimates[ride_type] = {
                    'original_fare': 0,
                    'final_fare': 0,
                    'discount_applied': 0
                }
                logging.error(f"Fare calculation failed for {ride_type}: {fare_error}")
        
        logging.info(f"Fare estimates calculated for {distance_km:.2f}km: {estimates}")
        
        # Return response with promo code information
        response_data = {
            'success': True,
            'distance_km': round(distance_km, 2),
            'estimates': estimates
        }
        
        if promo_discount_info:
            response_data['promo_code_info'] = promo_discount_info
        
        return jsonify(response_data)
        
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
            return jsonify({'success': False, 'message': 'Ride not found'}), 404
        
        # Only allow location tracking for active rides
        if ride.status not in ['accepted', 'arrived', 'started']:
            return jsonify({'success': False, 'message': 'Location tracking only available for active rides'}), 400
        
        # Get latest location for this ride
        latest_location = RideLocation.query.filter_by(
            ride_id=ride_id,
            is_latest=True
        ).first()
        
        if not latest_location:
            return jsonify({'success': False, 'message': 'No location data available'}), 404
        
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
        return jsonify({'success': False, 'message': 'Error retrieving location'}), 500


@customer_bp.route('/bookings/<int:customer_id>', methods=['GET'])
@token_required
def get_customer_bookings(current_user, customer_id):
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
@token_required
def customer_logout(current_user_data):
    """Customer logout - invalidates session and JWT token"""
    try:
        from utils.session_manager import invalidate_customer_sessions
        
        # Get customer
        customer = Customer.query.get(current_user_data['user_id'])
        if not customer:
            return create_error_response("Customer not found")
        
        # Invalidate all sessions for this customer
        invalidate_customer_sessions(customer.id)
        
        logging.info(f"Customer logged out: {customer.name} ({customer.phone})")
        
        return create_success_response({}, "Logged out successfully")
    except Exception as e:
        logging.error(f"Error in logout: {str(e)}")
        return create_error_response("Internal server error")

@customer_bp.route('/heartbeat', methods=['POST'])
@token_required
def heartbeat(current_user_data):
    """Customer heartbeat to keep session alive"""
    try:
        from utils.session_manager import update_customer_heartbeat
        
        # Update heartbeat
        success = update_customer_heartbeat(current_user_data['user_id'])
        
        if not success:
            return create_error_response("Customer not found or session invalid")
        
        return create_success_response({
            'timestamp': get_ist_time().isoformat(),
            'status': 'active'
        }, "Heartbeat updated")
        
    except Exception as e:
        logging.error(f"Error in customer heartbeat: {str(e)}")
        return create_error_response("Internal server error")


# ==================== ADVERTISEMENT API ====================

@customer_bp.route('/advertisements', methods=['GET'])
def get_advertisements():
    """Get active advertisements for slideshow display"""
    try:
        # Get optional filters from query parameters
        location = request.args.get('location')
        ride_type = request.args.get('ride_type')
        customer_type = request.args.get('customer_type')
        
        # Get active advertisements using the model method
        ads = Advertisement.get_active_ads_for_slideshow(
            location=location,
            ride_type=ride_type,
            customer_type=customer_type
        )
        
        # Convert to dictionary format with media URLs
        ads_data = []
        for ad in ads:
            ad_dict = ad.to_dict()
            # Add full media URL for customer app
            if ad.media_filename:
                ad_dict['media_url'] = f"/static/ads/{ad.media_filename}"
            ads_data.append(ad_dict)
        
        # Calculate total slideshow duration
        total_duration = sum(ad.display_duration for ad in ads)
        
        return create_success_response({
            'advertisements': ads_data,
            'total_ads': len(ads_data),
            'total_duration_seconds': total_duration,
            'slideshow_config': {
                'auto_advance': True,
                'loop': True,
                'show_controls': False
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting advertisements: {str(e)}")
        return create_error_response("Failed to retrieve advertisements")

@customer_bp.route('/advertisements/<int:ad_id>/impression', methods=['POST'])
def record_ad_impression(ad_id):
    """Record an advertisement impression (view)"""
    try:
        ad = Advertisement.query.get(ad_id)
        if not ad:
            return create_error_response("Advertisement not found")
        
        ad.increment_impressions()
        
        return create_success_response({
            'ad_id': ad_id,
            'impressions': ad.impressions,
            'message': 'Impression recorded'
        })
        
    except Exception as e:
        logging.error(f"Error recording advertisement impression: {str(e)}")
        return create_error_response("Failed to record impression")

@customer_bp.route('/advertisements/<int:ad_id>/click', methods=['POST'])
def record_ad_click(ad_id):
    """Record an advertisement click"""
    try:
        ad = Advertisement.query.get(ad_id)
        if not ad:
            return create_error_response("Advertisement not found")
        
        ad.increment_clicks()
        
        return create_success_response({
            'ad_id': ad_id,
            'clicks': ad.clicks,
            'impressions': ad.impressions,
            'ctr': round((ad.clicks / ad.impressions * 100), 2) if ad.impressions > 0 else 0,
            'message': 'Click recorded'
        })
        
    except Exception as e:
        logging.error(f"Error recording advertisement click: {str(e)}")
        return create_error_response("Failed to record click")


# ==================== PROMO CODE API ====================

@customer_bp.route('/promo_codes/available', methods=['GET'])
def get_available_promo_codes():
    """Get list of available promo codes for customer app display"""
    try:
        # Get optional filters from query parameters
        ride_type = request.args.get('ride_type')
        ride_category = request.args.get('ride_category')
        min_fare = request.args.get('min_fare', type=float)
        
        # Get active promo codes
        query = PromoCode.query.filter_by(active=True)
        
        # Filter by expiry date
        current_time = get_ist_time()
        query = query.filter(
            (PromoCode.expiry_date.is_(None)) | 
            (PromoCode.expiry_date > current_time)
        )
        
        # Filter by usage limits
        query = query.filter(PromoCode.current_uses < PromoCode.max_uses)
        
        # Apply filters if provided
        if ride_type:
            query = query.filter(
                (PromoCode.ride_type == ride_type) | 
                (PromoCode.ride_type.is_(None))
            )
        
        if ride_category:
            query = query.filter(
                (PromoCode.ride_category == ride_category) | 
                (PromoCode.ride_category.is_(None))
            )
        
        if min_fare:
            query = query.filter(PromoCode.min_fare <= min_fare)
        
        # Order by best discount first (flat discounts first, then percentage)
        promo_codes = query.order_by(
            PromoCode.discount_type.desc(),  # 'percent' comes before 'flat' alphabetically, so desc() puts flat first
            PromoCode.discount_value.desc()
        ).all()
        
        # Convert to customer-friendly format
        available_promos = []
        for promo in promo_codes:
            promo_data = {
                'code': promo.code,
                'discount_type': promo.discount_type,
                'discount_value': promo.discount_value,
                'min_fare': promo.min_fare,
                'expiry_date': promo.expiry_date.isoformat() if promo.expiry_date else None,
                'ride_type': promo.ride_type,
                'ride_category': promo.ride_category,
                'usage_remaining': promo.max_uses - promo.current_uses,
                'max_uses': promo.max_uses,
                'is_limited': promo.max_uses > 0,
                'display_text': format_promo_display_text(promo),
                'savings_text': format_savings_text(promo, min_fare),
                'terms': format_promo_terms(promo)
            }
            available_promos.append(promo_data)
        
        return create_success_response({
            'promo_codes': available_promos,
            'total_available': len(available_promos),
            'filters_applied': {
                'ride_type': ride_type,
                'ride_category': ride_category,
                'min_fare': min_fare
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting available promo codes: {str(e)}")
        return create_error_response("Failed to retrieve promo codes")

def format_promo_display_text(promo):
    """Format promo code for display in customer app"""
    if promo.discount_type == 'flat':
        return f"₹{int(promo.discount_value)} OFF"
    else:
        return f"{int(promo.discount_value)}% OFF"

def format_savings_text(promo, estimated_fare=None):
    """Calculate and format potential savings text"""
    if not estimated_fare or estimated_fare < promo.min_fare:
        if promo.discount_type == 'flat':
            return f"Save ₹{int(promo.discount_value)} on rides above ₹{int(promo.min_fare)}"
        else:
            return f"Save {int(promo.discount_value)}% on rides above ₹{int(promo.min_fare)}"
    
    # Calculate actual savings for the estimated fare
    if promo.discount_type == 'flat':
        savings = promo.discount_value
        return f"You'll save ₹{int(savings)} on this ride"
    else:
        savings = estimated_fare * (promo.discount_value / 100)
        return f"You'll save ₹{int(savings)} ({int(promo.discount_value)}% off)"

def format_promo_terms(promo):
    """Format terms and conditions for promo code"""
    terms = []
    
    if promo.min_fare > 0:
        terms.append(f"Minimum fare: ₹{int(promo.min_fare)}")
    
    if promo.ride_type:
        terms.append(f"Valid for: {promo.ride_type.title()} rides only")
    
    if promo.ride_category:
        terms.append(f"Category: {promo.ride_category.title()} rides")
    
    if promo.expiry_date:
        expiry_str = promo.expiry_date.strftime("%d %b %Y")
        terms.append(f"Valid till: {expiry_str}")
    
    usage_remaining = promo.max_uses - promo.current_uses
    if promo.max_uses > 0:
        terms.append(f"Uses remaining: {usage_remaining}")
    
    return terms
