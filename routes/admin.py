from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, get_ist_time
from models import Admin, Customer, Driver, Ride, FareConfig, SpecialFareConfig, Zone, PromoCode, Advertisement
from utils.validators import create_error_response, create_success_response, validate_phone, validate_required_fields
import logging
import random
import string
import os
from datetime import datetime
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def generate_driver_username():
    """Generate unique driver username in format DRVAB12CD"""
    while True:
        # Generate 2 random letters + 2 random digits + 2 random letters
        letters1 = ''.join(random.choices(string.ascii_uppercase, k=2))
        digits = ''.join(random.choices(string.digits, k=2))
        letters2 = ''.join(random.choices(string.ascii_uppercase, k=2))
        username = f"DRV{letters1}{digits}{letters2}"
        
        # Check if username already exists
        existing = Driver.query.filter_by(username=username).first()
        if not existing:
            return username

def generate_driver_password(phone):
    """Generate driver password using last 4 digits of phone + @Taxi"""
    return f"{phone[-4:]}@Taxi"

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('admin/login.html')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):  # Now using secure password verification
            login_user(admin)
            logging.info(f"Admin logged in: {admin.username}")
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/api/login', methods=['POST'])
def api_login():
    """Admin API login endpoint for JSON requests"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return create_error_response("Username and password are required")
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            logging.info(f"Admin logged in via API: {admin.username}")
            return create_success_response({
                'admin_id': admin.id,
                'username': admin.username,
                'logged_in': True
            }, "Admin login successful")
        else:
            return create_error_response("Invalid username or password")
    
    except Exception as e:
        logging.error(f"Error in admin API login: {str(e)}")
        return create_error_response("Internal server error")

@admin_bp.route('/logout')
@login_required
def logout():
    """Admin logout"""
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
def landing():
    """Login-aware landing page - redirects based on login status"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    try:
        # Get statistics
        total_customers = Customer.query.count()
        total_drivers = Driver.query.count()
        total_rides = Ride.query.count()
        
        # Get rides by status
        pending_rides = Ride.query.filter_by(status='pending').count()
        active_rides = Ride.query.filter(Ride.status.in_(['accepted', 'arrived', 'started'])).count()
        completed_rides = Ride.query.filter_by(status='completed').count()
        cancelled_rides = Ride.query.filter_by(status='cancelled').count()
        
        # Get recent rides (last 10)
        recent_rides = Ride.query.order_by(Ride.created_at.desc()).limit(10).all()
        
        # Get today's stats
        today = datetime.now().date()
        today_rides = Ride.query.filter(
            db.func.date(Ride.created_at) == today
        ).count()
        
        stats = {
            'total_customers': total_customers,
            'total_drivers': total_drivers,
            'total_rides': total_rides,
            'pending_rides': pending_rides,
            'active_rides': active_rides,
            'completed_rides': completed_rides,
            'cancelled_rides': cancelled_rides,
            'today_rides': today_rides,
            'recent_rides': recent_rides
        }
        
        return render_template('admin/dashboard.html', stats=stats)
        
    except Exception as e:
        logging.error(f"Error in admin dashboard: {str(e)}")
        flash('Error loading dashboard', 'error')
        return render_template('admin/dashboard.html', stats={})

@admin_bp.route('/rides')
@login_required
def rides():
    """Admin rides page"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', 'all')
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Build query
        query = Ride.query
        
        if status_filter != 'all':
            query = query.filter_by(status=status_filter)
        
        # Paginate results
        rides = query.order_by(Ride.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/rides.html', rides=rides, status_filter=status_filter)
        
    except Exception as e:
        logging.error(f"Error in admin rides: {str(e)}")
        flash('Error loading rides', 'error')
        return render_template('admin/rides.html', rides=None, status_filter='all')

@admin_bp.route('/customers')
@login_required
def customers():
    """Admin customers page"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        customers = Customer.query.order_by(Customer.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/customers.html', customers=customers)
        
    except Exception as e:
        logging.error(f"Error in admin customers: {str(e)}")
        flash('Error loading customers', 'error')
        return render_template('admin/customers.html', customers=None)

@admin_bp.route('/drivers')
@login_required
def drivers():
    """Admin drivers page"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        drivers = Driver.query.order_by(Driver.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/drivers.html', drivers=drivers)
        
    except Exception as e:
        logging.error(f"Error in admin drivers: {str(e)}")
        flash('Error loading drivers', 'error')
        return render_template('admin/drivers.html', drivers=None)

@admin_bp.route('/clear_logs', methods=['POST'])
@login_required
def clear_logs():
    """Clear all rides regardless of status"""
    try:
        # Get count of all rides before deletion
        total_rides = Ride.query.count()
        
        # Import related models that might have foreign key constraints
        from models import RideLocation, RideRejection
        
        # Delete related records first to avoid foreign key constraint violations
        RideLocation.query.delete()
        RideRejection.query.delete()
        
        # Now delete all rides
        Ride.query.delete()
        db.session.commit()
        
        logging.info(f"Cleared {total_rides} rides and related records")
        flash(f'Cleared {total_rides} rides successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error clearing logs: {str(e)}")
        flash('Error clearing logs', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/stats')
def api_stats():
    """API endpoint for dashboard stats"""
    try:
        # Get real-time statistics
        from datetime import datetime, timedelta
        from app import get_ist_time
        
        # Calculate today's rides (rides created today in IST)
        today_start = get_ist_time().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        stats = {
            'total_customers': Customer.query.count(),
            'total_drivers': Driver.query.count(),
            'total_rides': Ride.query.count(),
            'today_rides': Ride.query.filter(Ride.created_at >= today_start, Ride.created_at < today_end).count(),
            'pending_rides': Ride.query.filter_by(status='pending').count(),
            'active_rides': Ride.query.filter(Ride.status.in_(['accepted', 'arrived', 'started'])).count(),
            'completed_rides': Ride.query.filter_by(status='completed').count(),
            'cancelled_rides': Ride.query.filter_by(status='cancelled').count(),
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"Error in api_stats: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading stats'}), 500

@admin_bp.route('/api/recent_rides')
def api_recent_rides():
    """API endpoint for recent rides data"""
    try:
        # Get recent rides (last 10)
        recent_rides = Ride.query.order_by(Ride.created_at.desc()).limit(10).all()
        
        rides_data = []
        for ride in recent_rides:
            ride_data = {
                'id': ride.id,
                'customer_name': ride.customer.name if ride.customer else 'Unknown',
                'customer_phone': ride.customer_phone,
                'driver_name': ride.driver.name if ride.driver else None,
                'driver_phone': ride.driver.phone if ride.driver else None,
                'pickup_address': ride.pickup_address,
                'status': ride.status,
                'fare_amount': ride.fare_amount,
                'created_at': ride.created_at.strftime('%Y-%m-%d %H:%M')
            }
            rides_data.append(ride_data)
        
        return jsonify({'rides': rides_data})
        
    except Exception as e:
        logging.error(f"Error in api_recent_rides: {str(e)}")
        return jsonify({'success': False, 'message': 'Error loading recent rides'}), 500

# Removed duplicate api_drivers route - using api_get_drivers instead

@admin_bp.route('/api/rides/<int:ride_id>/cancel', methods=['POST'])
@login_required
def cancel_ride_admin(ride_id):
    """Cancel a ride from admin panel"""
    try:
        ride = Ride.query.get_or_404(ride_id)
        
        if ride.status in ['completed', 'cancelled']:
            return jsonify({'success': False, 'message': 'Ride cannot be cancelled'}), 400
        
        ride.status = 'cancelled'
        ride.cancelled_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Ride {ride_id} cancelled by admin")
        return jsonify({'success': True, 'message': 'Ride cancelled successfully'})
        
    except Exception as e:
        logging.error(f"Error cancelling ride {ride_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error cancelling ride'}), 500

@admin_bp.route('/create_driver', methods=['POST'])
@login_required
def create_driver():
    """Admin API to create a new driver account"""
    try:
        # Support both form data and JSON
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            phone = data.get('phone')
        else:
            name = request.form.get('name')
            phone = request.form.get('phone')
        
        # Basic validation - only name and phone are required
        if not name or not phone:
            return create_error_response("Name and phone are required", 400)
        
        # Validate phone number
        is_valid_phone, phone_or_error = validate_phone(phone)
        if not is_valid_phone:
            return create_error_response(phone_or_error, 400)
        
        # Use the cleaned phone number
        phone = phone_or_error
        
        # Check if driver with this phone already exists
        existing_driver = Driver.query.filter_by(phone=phone).first()
        if existing_driver:
            return create_error_response("Driver with this phone number already exists", 400)
        
        # Generate unique username and password
        username = generate_driver_username()
        password = generate_driver_password(phone)
        password_hash = generate_password_hash(password)
        
        # Validate car year if provided
        car_year = None
        if request.is_json:
            car_year_str = data.get('car_year')
        else:
            car_year_str = request.form.get('car_year')
            
        if car_year_str and str(car_year_str).strip():
            try:
                car_year = int(car_year_str)
                if car_year < 1990 or car_year > 2025:
                    raise ValueError("Invalid car year")
            except (ValueError, TypeError):
                return create_error_response("Invalid car year", 400)
        
        # Create new driver
        if request.is_json:
            new_driver = Driver(
                name=name,
                phone=phone,
                username=username,
                password_hash=password_hash,
                car_make=data.get('car_make') or None,
                car_model=data.get('car_model') or None,
                car_year=car_year,
                license_number=data.get('license_number') or None,
                car_number=data.get('car_number') or None,
                car_type=data.get('car_type') or None,
                aadhaar_url=data.get('aadhaar_url') or None,
                license_url=data.get('license_url') or None,
                rcbook_url=data.get('rcbook_url') or None,
                profile_photo_url=data.get('profile_photo_url') or None,
                is_online=True  # Default to online
            )
        else:
            new_driver = Driver(
                name=name,
                phone=phone,
                username=username,
                password_hash=password_hash,
                car_make=request.form.get('car_make') or None,
                car_model=request.form.get('car_model') or None,
                car_year=car_year,
                license_number=request.form.get('license_number') or None,
                car_number=request.form.get('car_number') or None,
                car_type=request.form.get('car_type') or None,
                aadhaar_url=request.form.get('aadhaar_url') or None,
                license_url=request.form.get('license_url') or None,
                rcbook_url=request.form.get('rcbook_url') or None,
                profile_photo_url=request.form.get('profile_photo_url') or None,
                is_online=True  # Default to online
            )
        
        db.session.add(new_driver)
        db.session.commit()
        
        logging.info(f"Admin created new driver: {new_driver.name} ({username})")
        
        # WARNING: Plain password returned for admin testing only - remove before production
        return create_success_response({
            "driver_id": new_driver.id,
            "name": new_driver.name,
            "phone": new_driver.phone,
            "username": username,
            "password": password  # Plain password for admin testing only
        }, "Driver created successfully")
        
    except ValueError as e:
        logging.error(f"Validation error in create_driver: {str(e)}")
        return create_error_response("Invalid car year provided", 400)
    except Exception as e:
        logging.error(f"Error creating driver: {str(e)}")
        db.session.rollback()
        return create_error_response("Error creating driver account", 500)

@admin_bp.route('/reset_driver_password', methods=['POST'])
@login_required
def reset_driver_password():
    """Admin API to reset driver password"""
    try:
        data = request.get_json()
        
        # Required fields validation
        required_fields = ['username', 'new_password']
        is_valid, error_msg = validate_required_fields(data, required_fields)
        if not is_valid:
            return create_error_response(error_msg, 400)
        
        # Find driver by username
        driver = Driver.query.filter_by(username=data['username']).first()
        if not driver:
            return create_error_response("Driver not found", 404)
        
        # Update password
        new_password_hash = generate_password_hash(data['new_password'])
        driver.password_hash = new_password_hash
        
        db.session.commit()
        
        logging.info(f"Admin reset password for driver: {driver.name} ({driver.username})")
        
        # WARNING: Plain password returned for admin testing only - remove before production
        return jsonify({
            "success": True,
            "message": "Driver password reset successfully",
            "username": driver.username,
            "password": data['new_password']  # Plain password for admin testing only
        })
        
    except Exception as e:
        logging.error(f"Error resetting driver password: {str(e)}")
        db.session.rollback()
        return create_error_response("Error resetting driver password", 500)

@admin_bp.route('/update_driver', methods=['POST'])
@login_required
def update_driver():
    """Admin API to update driver information"""
    try:
        driver_id = request.form.get('driver_id')
        
        if not driver_id:
            return create_error_response('Driver ID is required', 400)
        
        # Find driver
        driver = Driver.query.get(driver_id)
        if not driver:
            return create_error_response('Driver not found', 404)
        
        # Update basic information
        driver.name = request.form.get('name', driver.name)
        driver.is_online = request.form.get('is_online', 'false').lower() == 'true'
        
        # Update vehicle information
        driver.car_make = request.form.get('car_make') or None
        driver.car_model = request.form.get('car_model') or None
        car_year_str = request.form.get('car_year')
        driver.car_year = int(car_year_str) if car_year_str and car_year_str.strip() else None
        driver.car_number = request.form.get('car_number') or None
        driver.car_type = request.form.get('car_type') or None
        
        # Update documents
        driver.license_number = request.form.get('license_number') or None
        driver.profile_photo_url = request.form.get('profile_photo_url') or None
        driver.aadhaar_url = request.form.get('aadhaar_url') or None
        driver.license_url = request.form.get('license_url') or None
        driver.rcbook_url = request.form.get('rcbook_url') or None
        
        db.session.commit()
        
        logging.info(f"Admin updated driver: {driver.name} (ID: {driver.id})")
        
        return create_success_response({
            'driver_id': driver.id,
            'name': driver.name,
            'phone': driver.phone,
            'username': driver.username
        }, f'Driver {driver.name} updated successfully')
        
    except Exception as e:
        logging.error(f"Error updating driver: {str(e)}")
        db.session.rollback()
        return create_error_response('Error updating driver', 500)

@admin_bp.route('/delete_driver', methods=['POST'])
@login_required
def delete_driver():
    """Admin API to delete a driver"""
    try:
        data = request.get_json()
        driver_id = data.get('driver_id')
        
        if not driver_id:
            return create_error_response('Driver ID is required', 400)
        
        # Find driver
        driver = Driver.query.get(driver_id)
        if not driver:
            return create_error_response('Driver not found', 404)
        
        # Check if driver has active rides
        active_rides = Ride.query.filter_by(driver_id=driver_id).filter(
            Ride.status.in_(['accepted', 'arrived', 'started'])
        ).count()
        
        if active_rides > 0:
            return create_error_response(
                'Cannot delete driver with active rides. Please complete or cancel active rides first.',
                400
            )
        
        driver_name = driver.name
        db.session.delete(driver)
        db.session.commit()
        
        logging.info(f"Admin deleted driver: {driver_name} (ID: {driver_id})")
        
        return create_success_response({
            'deleted_driver': driver_name
        }, f'Driver {driver_name} deleted successfully')
        
    except Exception as e:
        logging.error(f"Error deleting driver: {str(e)}")
        db.session.rollback()
        return create_error_response('Error deleting driver', 500)

@admin_bp.route('/api/drivers/<int:driver_id>', methods=['GET'])
@admin_bp.route('/get_driver/<int:driver_id>', methods=['GET'])
def get_driver(driver_id):
    """Admin API to get driver details including plain-text password for testing"""
    try:
        # Find driver
        driver = Driver.query.get(driver_id)
        if not driver:
            return create_error_response('Driver not found', 404)
        
        # Generate current password (since we don't store plain passwords)
        # WARNING: This is for admin testing only - remove before production
        current_password = generate_driver_password(driver.phone)
        
        return jsonify({
            'success': True,
            'driver': {
                'id': driver.id,
                'name': driver.name,
                'phone': driver.phone,
                'username': driver.username,
                'password': current_password,  # Plain password for admin testing only
                'is_online': driver.is_online,
                'car_make': driver.car_make,
                'car_model': driver.car_model,
                'car_year': driver.car_year,
                'car_number': driver.car_number,
                'car_type': driver.car_type,
                'license_number': driver.license_number,
                'profile_photo_url': driver.profile_photo_url,
                'aadhaar_url': driver.aadhaar_url,
                'license_url': driver.license_url,
                'rcbook_url': driver.rcbook_url
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting driver details: {str(e)}")
        return create_error_response('Error retrieving driver details', 500)


@admin_bp.route('/api/rides/<int:ride_id>', methods=['GET'])
@admin_bp.route('/get_ride_details/<int:ride_id>', methods=['GET'])
def get_ride_details(ride_id):
    """API endpoint to get ride details for admin"""
    try:
        ride = Ride.query.get(ride_id)
        if not ride:
            return create_error_response('Ride not found', 404)
        
        # Get related data
        customer = Customer.query.get(ride.customer_id) if ride.customer_id else None
        driver = Driver.query.get(ride.driver_id) if ride.driver_id else None
        
        ride_data = {
            'id': ride.id,
            'customer_name': customer.name if customer else 'Unknown',
            'customer_phone': customer.phone if customer else 'Unknown',
            'driver_name': driver.name if driver else 'Unassigned',
            'driver_phone': driver.phone if driver else 'N/A',
            'pickup_location': ride.pickup_location,
            'pickup_latitude': ride.pickup_latitude,
            'pickup_longitude': ride.pickup_longitude,
            'destination': ride.destination,
            'destination_latitude': ride.destination_latitude,
            'destination_longitude': ride.destination_longitude,
            'ride_type': ride.ride_type,
            'ride_category': ride.ride_category,
            'status': ride.status,
            'fare': float(ride.fare) if ride.fare else 0.0,
            'distance_km': ride.distance_km,
            'created_at': ride.created_at.isoformat() if ride.created_at else None,
            'accepted_at': ride.accepted_at.isoformat() if ride.accepted_at else None,
            'started_at': ride.started_at.isoformat() if ride.started_at else None,
            'completed_at': ride.completed_at.isoformat() if ride.completed_at else None,
            'promo_code': ride.promo_code,
            'promo_discount': float(ride.promo_discount) if ride.promo_discount else 0.0
        }
        
        return jsonify({
            'success': True,
            'ride': ride_data
        })
        
    except Exception as e:
        logging.error(f"Error getting ride details: {str(e)}")
        return create_error_response('Error retrieving ride details', 500)


@admin_bp.route('/fare_config')
@login_required
def fare_config():
    """Fare configuration management page"""
    return render_template('admin/fare_config.html')


@admin_bp.route('/api/fare-config', methods=['GET'])
def api_get_fare_config():
    """API endpoint to get all fare configurations - Public endpoint for mobile app"""
    try:
        fare_configs = FareConfig.query.all()
        
        # Convert to dictionary format expected by mobile app
        config_data = []
        for config in fare_configs:
            config_data.append({
                'id': config.id,
                'ride_type': config.ride_type,
                'base_fare': float(config.base_fare),
                'per_km_rate': float(config.per_km_rate)
            })
        
        return jsonify({
            'success': True,
            'message': 'Fare configurations retrieved successfully',
            'data': config_data
        })
    
    except Exception as e:
        logging.error(f"Error getting fare configurations: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to load fare configurations'
        }), 500


@admin_bp.route('/api/fare-config', methods=['POST'])
def api_update_fare_config():
    """API endpoint to update fare configuration for a specific ride type"""
    # Authentication handled by @login_required decorator
    
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_type', 'base_fare', 'per_km_rate'])
        if not valid:
            return create_error_response(error)
        
        ride_type = data['ride_type'].lower()
        base_fare = float(data['base_fare'])
        per_km_rate = float(data['per_km_rate'])
        
        # Validate values
        if base_fare < 0 or per_km_rate < 0:
            return create_error_response("Base fare and per km rate must be positive")
        
        if ride_type not in ['hatchback', 'sedan', 'suv']:
            return create_error_response("Invalid ride type")
        
        # Find and update the fare configuration
        fare_config = FareConfig.query.filter_by(ride_type=ride_type).first()
        if not fare_config:
            return create_error_response(f"Fare configuration not found for ride type: {ride_type}")
        
        fare_config.base_fare = base_fare
        fare_config.per_km_rate = per_km_rate
        fare_config.updated_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Fare configuration updated for {ride_type}: base=₹{base_fare}, per_km=₹{per_km_rate}")
        return create_success_response(fare_config.to_dict(), f"Fare configuration updated for {ride_type}")
    
    except ValueError:
        return create_error_response("Invalid numeric values for fare amounts")
    except Exception as e:
        logging.error(f"Error updating fare configuration: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to update fare configuration")


@admin_bp.route('/api/fare_config/surge', methods=['POST'])
@login_required
def api_update_surge_multiplier():
    """API endpoint to update global surge multiplier for all ride types"""
    # Authentication handled by @login_required decorator
    
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        surge_multiplier = float(data.get('surge_multiplier', 1.0))
        
        # Validate surge multiplier
        if surge_multiplier < 0.5 or surge_multiplier > 5.0:
            return create_error_response("Surge multiplier must be between 0.5 and 5.0")
        
        # Update all fare configurations with new surge multiplier
        fare_configs = FareConfig.query.all()
        for config in fare_configs:
            config.surge_multiplier = surge_multiplier
            config.updated_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Global surge multiplier updated to {surge_multiplier}x")
        return create_success_response({
            'surge_multiplier': surge_multiplier,
            'updated_configs': len(fare_configs)
        }, f"Global surge multiplier updated to {surge_multiplier}x")
    
    except ValueError:
        return create_error_response("Invalid numeric value for surge multiplier")
    except Exception as e:
        logging.error(f"Error updating surge multiplier: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to update surge multiplier")


@admin_bp.route('/assign_driver', methods=['POST'])
@login_required
def assign_driver():
    """Admin manual assignment of drivers to rides"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_id', 'driver_id'])
        if not valid:
            return create_error_response(error)
        
        ride_id = data['ride_id']
        driver_id = data['driver_id']
        
        # Find ride and driver
        ride = Ride.query.get(ride_id)
        if not ride:
            return create_error_response('Ride not found', 404)
        
        driver = Driver.query.get(driver_id)
        if not driver:
            return create_error_response('Driver not found', 404)
        
        # Check if ride can be assigned
        if ride.status != 'new':
            return create_error_response('Ride cannot be assigned in current status', 400)
        
        # For manual admin assignment, skip availability checks - admin can assign to any driver
        # Generate OTP for ride start confirmation
        import random
        if not ride.start_otp:
            ride.start_otp = str(random.randint(100000, 999999))
        
        # Assign driver to ride
        ride.driver_id = driver_id
        ride.status = 'accepted'  # Change to accepted to match driver workflow
        ride.assigned_time = get_ist_time()
        ride.accepted_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Admin assigned driver {driver.name} to ride {ride_id}")
        
        return create_success_response({
            'ride_id': ride_id,
            'driver_id': driver_id,
            'driver_name': driver.name,
            'status': 'assigned'
        }, f'Driver {driver.name} assigned to ride successfully')
        
    except Exception as e:
        logging.error(f"Error assigning driver: {str(e)}")
        db.session.rollback()
        return create_error_response('Error assigning driver', 500)


@admin_bp.route('/api/special-fares', methods=['GET'])
def api_get_special_fare_config():
    """API endpoint to get all special fare configurations"""
    try:
        configs = SpecialFareConfig.query.all()
        return create_success_response({
            'special_fare_configs': [config.to_dict() for config in configs]
        })
    
    except Exception as e:
        logging.error(f"Error getting special fare configurations: {str(e)}")
        return create_error_response("Failed to get special fare configurations")


@admin_bp.route('/api/special-fares', methods=['POST'])
def api_create_special_fare_config():
    """API endpoint to create or update special fare configuration"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['ride_category', 'ride_type', 'base_fare'])
        if not valid:
            return create_error_response(error)
        
        ride_category = data['ride_category'].lower()
        ride_type = data['ride_type'].lower()
        base_fare = float(data['base_fare'])
        
        # Validate values
        if base_fare < 0:
            return create_error_response("Base fare must be positive")
        
        if ride_category not in ['airport', 'rental', 'outstation']:
            return create_error_response("Invalid ride category")
        
        if ride_type not in ['hatchback', 'sedan', 'suv']:
            return create_error_response("Invalid ride type")
        
        # Airport rides only allow sedan/suv
        if ride_category == 'airport' and ride_type == 'hatchback':
            return create_error_response("Airport rides only allow sedan or suv")
        
        # Find existing configuration or create new one
        config = SpecialFareConfig.query.filter_by(
            ride_category=ride_category,
            ride_type=ride_type
        ).first()
        
        if not config:
            config = SpecialFareConfig(
                ride_category=ride_category,
                ride_type=ride_type
            )
            db.session.add(config)
        
        # Update configuration
        config.base_fare = base_fare
        config.per_km = data.get('per_km') 
        config.hourly = data.get('hourly')
        config.flat_rate = data.get('flat_rate')
        config.is_active = data.get('is_active', True)
        config.updated_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Special fare configuration updated: {ride_category} - {ride_type}")
        return create_success_response(config.to_dict(), f"Special fare configuration updated for {ride_category} - {ride_type}")
        
    except ValueError:
        return create_error_response("Invalid numeric values")
    except Exception as e:
        logging.error(f"Error creating/updating special fare configuration: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to update special fare configuration")


@admin_bp.route('/api/zones', methods=['GET'])
def api_get_zones():
    """API endpoint to get all zones"""
    try:
        zones = Zone.query.all()
        return create_success_response({
            'zones': [zone.to_dict() for zone in zones]
        })
    
    except Exception as e:
        logging.error(f"Error getting zones: {str(e)}")
        return create_error_response("Failed to get zones")


@admin_bp.route('/api/zones', methods=['POST'])
@login_required
def api_create_zone():
    """API endpoint to create a new zone"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        valid, error = validate_required_fields(data, ['zone_name', 'center_lat', 'center_lng'])
        if not valid:
            return create_error_response(error)
        
        zone_name = data['zone_name']
        center_lat = float(data['center_lat'])
        center_lng = float(data['center_lng'])
        
        # Enhanced zone fields
        number_of_rings = int(data.get('number_of_rings', 3))
        ring_radius_km = float(data.get('ring_radius_km', 2.0))
        ring_radius_meters = int(data.get('ring_radius_meters', 1000))
        ring_wait_time_seconds = int(data.get('ring_wait_time_seconds', 15))
        expansion_delay_sec = int(data.get('expansion_delay_sec', 15))
        radius_km = float(data.get('radius_km', 5.0))
        priority_order = int(data.get('priority_order', 1))
        polygon_coordinates = data.get('polygon_coordinates')
        
        # Validate values
        if not (-90 <= center_lat <= 90):
            return create_error_response("Invalid latitude")
        
        if not (-180 <= center_lng <= 180):
            return create_error_response("Invalid longitude")
        
        if radius_km <= 0 or radius_km > 50:
            return create_error_response("Radius must be between 0 and 50 km")
        
        if not (1 <= number_of_rings <= 5):
            return create_error_response("Number of rings must be between 1 and 5")
        
        if ring_radius_km <= 0 or ring_radius_km > 10:
            return create_error_response("Ring radius must be between 0 and 10 km")
        
        if not (5 <= expansion_delay_sec <= 60):
            return create_error_response("Expansion delay must be between 5 and 60 seconds")
        
        if not (100 <= ring_radius_meters <= 5000):
            return create_error_response("Ring radius must be between 100 and 5000 meters")
        
        if not (5 <= ring_wait_time_seconds <= 60):
            return create_error_response("Ring wait time must be between 5 and 60 seconds")
        
        # Check if zone name already exists
        existing_zone = Zone.query.filter_by(zone_name=zone_name).first()
        if existing_zone:
            return create_error_response("Zone with this name already exists")
        
        # Create new zone
        new_zone = Zone(
            zone_name=zone_name,
            center_lat=center_lat,
            center_lng=center_lng,
            polygon_coordinates=polygon_coordinates,
            number_of_rings=number_of_rings,
            ring_radius_km=ring_radius_km,
            ring_radius_meters=ring_radius_meters,
            ring_wait_time_seconds=ring_wait_time_seconds,
            expansion_delay_sec=expansion_delay_sec,
            radius_km=radius_km,
            priority_order=priority_order,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_zone)
        db.session.commit()
        
        logging.info(f"New zone created: {zone_name}")
        return create_success_response(new_zone.to_dict(), f"Zone '{zone_name}' created successfully")
        
    except ValueError:
        return create_error_response("Invalid numeric values")
    except Exception as e:
        logging.error(f"Error creating zone: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to create zone")


@admin_bp.route('/api/bookings', methods=['GET'])
def api_get_all_bookings():
    """API endpoint to get all bookings for admin"""
    try:
        # Get all rides ordered by creation date (newest first)
        rides = Ride.query.order_by(Ride.created_at.desc()).all()
        
        # Convert to dictionaries
        bookings = []
        for ride in rides:
            ride_dict = ride.to_dict()
            # Add customer and driver names for admin view
            if ride.customer:
                ride_dict['customer_name'] = ride.customer.name
            if ride.driver:
                ride_dict['driver_name'] = ride.driver.name
            bookings.append(ride_dict)
        
        return create_success_response({
            'bookings': bookings,
            'total_count': len(bookings)
        })
    
    except Exception as e:
        logging.error(f"Error getting all bookings: {str(e)}")
        return create_error_response("Failed to get bookings")


# New template route handlers for enhanced admin features
@admin_bp.route('/bookings')
@login_required
def bookings():
    """Admin bookings page"""
    return render_template('admin/bookings.html')


@admin_bp.route('/ongoing')
@login_required
def ongoing():
    """Admin ongoing rides page"""
    return render_template('admin/ongoing.html')


@admin_bp.route('/history')
@login_required
def history():
    """Admin history page"""
    return render_template('admin/history.html')


@admin_bp.route('/zones')
@login_required
def zones():
    """Admin zones management page"""
    import os
    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    return render_template('admin/zones.html', google_maps_api_key=google_maps_api_key)


@admin_bp.route('/special_fares')
@login_required
def special_fares():
    """Admin special fares management page"""
    return render_template('admin/special_fares.html')


@admin_bp.route('/live_map')
@login_required
def live_map():
    """Admin live map page"""
    import os
    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    return render_template('admin/live_map.html', google_maps_api_key=google_maps_api_key)


# Additional API endpoints for enhanced features
@admin_bp.route('/api/driver-locations', methods=['GET'])
@admin_bp.route('/api/live_driver_locations', methods=['GET'])
def api_live_driver_locations():
    """API endpoint to get live driver locations - Public endpoint for mobile app"""
    try:
        from datetime import timedelta
        
        # Get current time for staleness check
        current_time = get_ist_time()
        staleness_threshold = timedelta(minutes=15)  # Consider locations older than 15 minutes as stale
        
        # Get all drivers with their current locations
        drivers = Driver.query.all()
        
        driver_locations = []
        for driver in drivers:
            # Check if location is stale (older than 15 minutes)
            is_stale = False
            has_location = bool(driver.current_lat and driver.current_lng)
            
            if driver.location_updated_at and has_location:
                # Convert location_updated_at to IST timezone if it's offset-naive
                if driver.location_updated_at.tzinfo is None:
                    from app import IST
                    location_time = IST.localize(driver.location_updated_at)
                else:
                    location_time = driver.location_updated_at.astimezone(IST)
                
                time_since_update = current_time - location_time
                is_stale = time_since_update > staleness_threshold
            
            # Skip offline drivers with stale or no location data
            if not driver.is_online and (is_stale or not has_location):
                logging.debug(f"Skipping offline driver: {driver.name} (online: {driver.is_online}, has_location: {has_location}, stale: {is_stale})")
                continue
            
            # Include online drivers even without location data (they'll be shown with special status)
            if driver.is_online:
                logging.info(f"Including online driver: {driver.name} (has_location: {has_location})")
            
            driver_data = {
                'id': driver.id,
                'name': driver.name,
                'phone': driver.phone,
                'current_lat': driver.current_lat if has_location else None,
                'current_lng': driver.current_lng if has_location else None,
                'location_updated_at': driver.location_updated_at.isoformat() if driver.location_updated_at else None,
                'is_online': driver.is_online,
                'out_of_zone': driver.out_of_zone,
                'car_type': driver.car_type,
                'car_number': driver.car_number,
                'car_make': driver.car_make,
                'car_model': driver.car_model,
                'car_year': driver.car_year,
                'company_name': 'A1 Taxi',  # Default company name
                'zone': driver.zone.zone_name if driver.zone else None,
                'is_stale': is_stale,
                'has_location': has_location
            }
            driver_locations.append(driver_data)
        
        return create_success_response({
            'drivers': driver_locations,
            'total_count': len(driver_locations)
        })
    
    except Exception as e:
        logging.error(f"Error getting live driver locations: {str(e)}")
        return create_error_response("Failed to get driver locations")


@admin_bp.route('/api/ride_action', methods=['POST'])
@login_required
def api_ride_action():
    """API endpoint for ride actions (complete/cancel)"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        ride_id = data.get('ride_id')
        action = data.get('action')
        
        if not ride_id or not action:
            return create_error_response("Ride ID and action are required")
        
        ride = Ride.query.get(ride_id)
        if not ride:
            return create_error_response("Ride not found")
        
        if action == 'complete':
            ride.status = 'completed'
            ride.completed_at = get_ist_time()
            logging.info(f"Admin completed ride {ride_id}")
        elif action == 'cancel':
            reason = data.get('reason', 'Cancelled by admin')
            ride.status = 'cancelled'
            ride.cancelled_at = get_ist_time()
            # You could add a cancellation reason field to the model
            logging.info(f"Admin cancelled ride {ride_id}: {reason}")
        else:
            return create_error_response("Invalid action")
        
        db.session.commit()
        
        return create_success_response({
            'ride_id': ride_id,
            'action': action,
            'status': ride.status
        }, f"Ride {action}d successfully")
    
    except Exception as e:
        logging.error(f"Error in ride action: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to perform action")


@admin_bp.route('/api/zones/<int:zone_id>', methods=['GET'])
@login_required
def api_get_zone(zone_id):
    """API endpoint to get a specific zone"""
    try:
        zone = Zone.query.get(zone_id)
        if not zone:
            return create_error_response("Zone not found")
        
        return create_success_response(zone.to_dict())
    
    except Exception as e:
        logging.error(f"Error getting zone {zone_id}: {str(e)}")
        return create_error_response("Failed to get zone")


@admin_bp.route('/api/zones/<int:zone_id>', methods=['PUT'])
@login_required
def api_update_zone(zone_id):
    """API endpoint to update a zone"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        zone = Zone.query.get(zone_id)
        if not zone:
            return create_error_response("Zone not found")
        
        # Update zone fields
        zone.zone_name = data.get('zone_name', zone.zone_name)
        zone.center_lat = data.get('center_lat', zone.center_lat)
        zone.center_lng = data.get('center_lng', zone.center_lng)
        zone.polygon_coordinates = data.get('polygon_coordinates', zone.polygon_coordinates)
        zone.number_of_rings = data.get('number_of_rings', zone.number_of_rings)
        zone.ring_radius_km = data.get('ring_radius_km', zone.ring_radius_km)
        zone.ring_radius_meters = data.get('ring_radius_meters', zone.ring_radius_meters)
        zone.ring_wait_time_seconds = data.get('ring_wait_time_seconds', zone.ring_wait_time_seconds)
        zone.expansion_delay_sec = data.get('expansion_delay_sec', zone.expansion_delay_sec)
        zone.priority_order = data.get('priority_order', zone.priority_order)
        zone.radius_km = data.get('radius_km', zone.radius_km)
        zone.is_active = data.get('is_active', zone.is_active)
        zone.updated_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Admin updated zone {zone_id}")
        return create_success_response(zone.to_dict(), "Zone updated successfully")
    
    except Exception as e:
        logging.error(f"Error updating zone {zone_id}: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to update zone")


@admin_bp.route('/api/zones/<int:zone_id>', methods=['DELETE'])
@login_required
def api_delete_zone(zone_id):
    """API endpoint to delete a zone"""
    try:
        zone = Zone.query.get(zone_id)
        if not zone:
            return create_error_response("Zone not found")
        
        zone_name = zone.zone_name
        db.session.delete(zone)
        db.session.commit()
        
        logging.info(f"Admin deleted zone {zone_id}: {zone_name}")
        return create_success_response({
            'zone_id': zone_id,
            'zone_name': zone_name
        }, "Zone deleted successfully")
    
    except Exception as e:
        logging.error(f"Error deleting zone {zone_id}: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to delete zone")


@admin_bp.route('/api/special_fare_config/<int:fare_id>', methods=['PUT'])
@login_required
def api_update_special_fare(fare_id):
    """API endpoint to update a special fare configuration"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        fare = SpecialFareConfig.query.get(fare_id)
        if not fare:
            return create_error_response("Special fare not found")
        
        # Update fare fields
        fare.ride_category = data.get('ride_category', fare.ride_category)
        fare.ride_type = data.get('ride_type', fare.ride_type)
        fare.base_fare = data.get('base_fare', fare.base_fare)
        fare.per_km = data.get('per_km', fare.per_km)
        fare.hourly = data.get('hourly', fare.hourly)
        fare.flat_rate = data.get('flat_rate', fare.flat_rate)
        fare.is_active = data.get('is_active', fare.is_active)
        fare.updated_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Admin updated special fare {fare_id}")
        return create_success_response(fare.to_dict(), "Special fare updated successfully")
    
    except Exception as e:
        logging.error(f"Error updating special fare {fare_id}: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to update special fare")


@admin_bp.route('/api/special_fare_config/<int:fare_id>', methods=['DELETE'])
@login_required
def api_delete_special_fare(fare_id):
    """API endpoint to delete a special fare configuration"""
    try:
        fare = SpecialFareConfig.query.get(fare_id)
        if not fare:
            return create_error_response("Special fare not found")
        
        fare_info = f"{fare.ride_category} {fare.ride_type}"
        db.session.delete(fare)
        db.session.commit()
        
        logging.info(f"Admin deleted special fare {fare_id}: {fare_info}")
        return create_success_response({
            'fare_id': fare_id,
            'fare_info': fare_info
        }, "Special fare deleted successfully")
    
    except Exception as e:
        logging.error(f"Error deleting special fare {fare_id}: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to delete special fare")


@admin_bp.route('/api/drivers', methods=['GET'])
def api_get_drivers():
    """API endpoint to get drivers with filters"""
    try:
        available_only = request.args.get('available', 'false').lower() == 'true'
        
        query = Driver.query
        
        # For manual assignment, show all drivers regardless of availability
        # Admin can assign to any driver
        if available_only:
            query = query.filter_by(is_online=True)
        
        drivers = query.all()
        logging.info(f"Found {len(drivers)} drivers in database")
        
        driver_list = []
        for driver in drivers:
            # Get current active rides count for this driver
            active_rides = Ride.query.filter_by(driver_id=driver.id).filter(
                Ride.status.in_(['accepted', 'arrived', 'started'])
            ).count()
            
            driver_data = {
                'id': driver.id,
                'name': driver.name,
                'phone': driver.phone,
                'car_type': driver.car_type,
                'car_number': driver.car_number,
                'is_online': driver.is_online,
                'zone': driver.zone.zone_name if driver.zone else None,
                'active_rides': active_rides,
                'availability_status': 'Online' if driver.is_online else 'Offline'
            }
            driver_list.append(driver_data)
        
        logging.info(f"Returning {len(driver_list)} drivers to frontend")
        return create_success_response({
            'drivers': driver_list,
            'total_count': len(driver_list)
        })
    
    except Exception as e:
        logging.error(f"Error getting drivers: {str(e)}")
        return create_error_response("Failed to get drivers")


# New Features Implementation
@admin_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Admin change password page"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not old_password or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('admin/change_password.html')
        
        # Verify old password
        if current_user.password_hash != old_password:  # In production, use check_password_hash
            flash('Current password is incorrect', 'error')
            return render_template('admin/change_password.html')
        
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return render_template('admin/change_password.html')
        
        if new_password != confirm_password:
            flash('New password and confirmation do not match', 'error')
            return render_template('admin/change_password.html')
        
        # Update password
        current_user.password_hash = new_password  # In production, use generate_password_hash
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        logging.info(f"Admin {current_user.username} changed password")
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/change_password.html')


@admin_bp.route('/create_admin', methods=['GET', 'POST'])
@login_required
def create_admin():
    """Create new admin page"""
    if request.method == 'POST':
        name = request.form.get('name')
        mobile_number = request.form.get('mobile_number')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate required fields
        if not all([name, mobile_number, username, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('admin/create_admin.html')
        
        # Validate mobile number
        if not validate_phone(mobile_number):
            flash('Invalid mobile number format', 'error')
            return render_template('admin/create_admin.html')
        
        # Validate password length
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('admin/create_admin.html')
        
        # Validate password confirmation
        if password != confirm_password:
            flash('Password and confirmation do not match', 'error')
            return render_template('admin/create_admin.html')
        
        # Check if username already exists
        existing_admin = Admin.query.filter_by(username=username).first()
        if existing_admin:
            flash('Username already exists', 'error')
            return render_template('admin/create_admin.html')
        
        # Check if mobile number already exists
        existing_mobile = Admin.query.filter_by(mobile_number=mobile_number).first()
        if existing_mobile:
            flash('Mobile number already exists', 'error')
            return render_template('admin/create_admin.html')
        
        try:
            # Create new admin
            new_admin = Admin(
                username=username,
                password_hash=password,  # In production, use generate_password_hash
                name=name,
                mobile_number=mobile_number,
                role='admin'
            )
            
            db.session.add(new_admin)
            db.session.commit()
            
            flash(f'Admin {name} created successfully', 'success')
            logging.info(f"New admin created: {username} by {current_user.username}")
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error creating admin', 'error')
            logging.error(f"Error creating admin: {str(e)}")
            return render_template('admin/create_admin.html')
    
    return render_template('admin/create_admin.html')


@admin_bp.route('/api/save_firebase_token', methods=['POST'])
@login_required
def save_firebase_token():
    """Save Firebase FCM token for admin"""
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return create_error_response("Token is required")
        
        token = data['token']
        current_user.firebase_token = token
        db.session.commit()
        
        logging.info(f"Firebase token saved for admin {current_user.username}")
        return create_success_response({'message': 'Token saved successfully'})
        
    except Exception as e:
        logging.error(f"Error saving Firebase token: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to save token")

# ==================== PROMO CODE MANAGEMENT ====================

@admin_bp.route('/api/promo-codes', methods=['GET'])
@admin_bp.route('/api/promo_codes', methods=['GET'])
def api_promo_codes():
    """Get all promo codes for admin"""
    try:
        promo_codes = PromoCode.query.order_by(PromoCode.created_at.desc()).all()
        
        promo_data = []
        for promo in promo_codes:
            try:
                # Manual dict creation to avoid PromoCode.to_dict() issues
                usage_percentage = (promo.current_uses / promo.max_uses * 100) if promo.max_uses > 0 else 0
                
                promo_data.append({
                    'id': promo.id,
                    'code': promo.code,
                    'discount_type': promo.discount_type,
                    'discount_value': float(promo.discount_value),
                    'max_uses': promo.max_uses,
                    'current_uses': promo.current_uses,
                    'active': promo.active,
                    'usage_percentage': round(usage_percentage, 1),
                    'created_at': promo.created_at.isoformat() if promo.created_at else None,
                    'expiry_date': promo.expiry_date.isoformat() if promo.expiry_date else None,
                    'min_fare': float(promo.min_fare) if promo.min_fare else 0.0,
                    'ride_type': promo.ride_type,
                    'ride_category': promo.ride_category
                })
            except Exception as promo_error:
                logging.error(f"Error processing promo {promo.id}: {str(promo_error)}")
                # Add minimal promo data
                promo_data.append({
                    'id': promo.id,
                    'code': promo.code,
                    'discount_type': promo.discount_type,
                    'discount_value': float(promo.discount_value),
                    'max_uses': promo.max_uses,
                    'current_uses': promo.current_uses,
                    'active': promo.active,
                    'usage_percentage': 0.0
                })
        
        return create_success_response(promo_data)
        
    except Exception as e:
        logging.error(f"Error getting promo codes: {str(e)}")
        return create_error_response("Failed to retrieve promo codes")

@admin_bp.route('/api/promo_codes', methods=['POST'])
@login_required
def create_promo_code():
    """Create a new promo code"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Validate required fields
        required_fields = ['code', 'discount_type', 'discount_value', 'max_uses']
        for field in required_fields:
            if field not in data or not data[field]:
                return create_error_response(f"Field '{field}' is required")
        
        # Validate discount type
        if data['discount_type'] not in ['flat', 'percent']:
            return create_error_response("Discount type must be 'flat' or 'percent'")
        
        # Validate discount value
        if data['discount_value'] <= 0:
            return create_error_response("Discount value must be greater than 0")
        
        # Validate max uses
        if data['max_uses'] <= 0:
            return create_error_response("Max uses must be greater than 0")
        
        # Check if code already exists
        code = data['code'].upper().strip()
        existing_promo = PromoCode.query.filter_by(code=code).first()
        if existing_promo:
            return create_error_response("Promo code already exists")
        
        # Parse expiry date if provided
        expiry_date = None
        if data.get('expiry_date'):
            try:
                expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d')
            except ValueError:
                return create_error_response("Invalid expiry date format. Use YYYY-MM-DD")
        
        # Create new promo code
        promo_code = PromoCode(
            code=code,
            discount_type=data['discount_type'],
            discount_value=float(data['discount_value']),
            max_uses=int(data['max_uses']),
            expiry_date=expiry_date,
            min_fare=float(data.get('min_fare', 0)),
            ride_type=data.get('ride_type'),
            ride_category=data.get('ride_category'),
            active=data.get('active', True)
        )
        
        db.session.add(promo_code)
        db.session.commit()
        
        logging.info(f"New promo code created: {code} by admin {current_user.username}")
        return create_success_response(promo_code.to_dict(), "Promo code created successfully")
        
    except Exception as e:
        logging.error(f"Error creating promo code: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to create promo code")

@admin_bp.route('/api/promo_codes/<int:promo_id>', methods=['PUT'])
@login_required
def update_promo_code(promo_id):
    """Update an existing promo code"""
    try:
        promo = PromoCode.query.get(promo_id)
        if not promo:
            return create_error_response("Promo code not found")
        
        data = request.get_json()
        if not data:
            return create_error_response("Invalid JSON data")
        
        # Update fields if provided
        if 'discount_type' in data:
            if data['discount_type'] not in ['flat', 'percent']:
                return create_error_response("Discount type must be 'flat' or 'percent'")
            promo.discount_type = data['discount_type']
        
        if 'discount_value' in data:
            if data['discount_value'] <= 0:
                return create_error_response("Discount value must be greater than 0")
            promo.discount_value = float(data['discount_value'])
        
        if 'max_uses' in data:
            if data['max_uses'] <= 0:
                return create_error_response("Max uses must be greater than 0")
            promo.max_uses = int(data['max_uses'])
        
        if 'expiry_date' in data:
            if data['expiry_date']:
                try:
                    promo.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d')
                except ValueError:
                    return create_error_response("Invalid expiry date format. Use YYYY-MM-DD")
            else:
                promo.expiry_date = None
        
        if 'min_fare' in data:
            promo.min_fare = float(data['min_fare'])
        
        if 'ride_type' in data:
            promo.ride_type = data['ride_type']
        
        if 'ride_category' in data:
            promo.ride_category = data['ride_category']
        
        if 'active' in data:
            promo.active = bool(data['active'])
        
        db.session.commit()
        
        logging.info(f"Promo code updated: {promo.code} by admin {current_user.username}")
        return create_success_response(promo.to_dict(), "Promo code updated successfully")
        
    except Exception as e:
        logging.error(f"Error updating promo code: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to update promo code")

@admin_bp.route('/api/promo_codes/<int:promo_id>', methods=['DELETE'])
@login_required
def delete_promo_code(promo_id):
    """Delete a promo code"""
    try:
        promo = PromoCode.query.get(promo_id)
        if not promo:
            return create_error_response("Promo code not found")
        
        promo_code = promo.code
        db.session.delete(promo)
        db.session.commit()
        
        logging.info(f"Promo code deleted: {promo_code} by admin {current_user.username}")
        return create_success_response({'message': 'Promo code deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting promo code: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to delete promo code")

@admin_bp.route('/promo_codes', methods=['GET'])
@login_required
def promo_codes_page():
    """Promo codes management page"""
    return render_template('admin/promo_codes.html')

# ==================== ADVERTISEMENT MANAGEMENT ====================

@admin_bp.route('/api/advertisements', methods=['GET'])
@login_required
def api_advertisements():
    """Get all advertisements for admin"""
    try:
        ads = Advertisement.query.order_by(Advertisement.display_order, Advertisement.created_at.desc()).all()
        
        ads_data = []
        for ad in ads:
            ad_dict = ad.to_dict()
            # Add calculated fields
            if ad.media_filename:
                ad_dict['media_file_url'] = f"/static/ads/{ad.media_filename}"
            ads_data.append(ad_dict)
        
        return create_success_response(ads_data)
        
    except Exception as e:
        logging.error(f"Error getting advertisements: {str(e)}")
        return create_error_response("Failed to retrieve advertisements")

@admin_bp.route('/api/advertisements', methods=['POST'])
@login_required
def create_advertisement():
    """Create a new advertisement"""
    try:
        # Handle file upload
        if 'media_file' not in request.files:
            return create_error_response("No media file provided")
        
        media_file = request.files['media_file']
        if media_file.filename == '':
            return create_error_response("No file selected")
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
        file_extension = media_file.filename.rsplit('.', 1)[1].lower()
        if file_extension not in allowed_extensions:
            return create_error_response("Invalid file type. Allowed: PNG, JPG, JPEG, GIF, MP4, MOV, AVI")
        
        # Generate unique filename
        import uuid
        unique_filename = f"{uuid.uuid4()}_{media_file.filename}"
        file_path = os.path.join('static/ads', unique_filename)
        
        # Save file
        media_file.save(file_path)
        
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description', '')
        media_type = 'image' if file_extension in {'png', 'jpg', 'jpeg', 'gif'} else 'video'
        
        if not title:
            return create_error_response("Title is required")
        
        # Parse optional fields
        display_duration = int(request.form.get('display_duration', 5))
        display_order = int(request.form.get('display_order', 1))
        target_location = request.form.get('target_location') or None
        target_ride_type = request.form.get('target_ride_type') or None
        target_customer_type = request.form.get('target_customer_type') or None
        
        # Parse dates and times
        start_date = None
        end_date = None
        active_hours_start = None
        active_hours_end = None
        
        if request.form.get('start_date'):
            start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        if request.form.get('end_date'):
            end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        if request.form.get('active_hours_start'):
            active_hours_start = datetime.strptime(request.form.get('active_hours_start'), '%H:%M').time()
        if request.form.get('active_hours_end'):
            active_hours_end = datetime.strptime(request.form.get('active_hours_end'), '%H:%M').time()
        
        # Create advertisement
        ad = Advertisement(
            title=title,
            description=description,
            media_type=media_type,
            media_filename=unique_filename,
            display_duration=display_duration,
            display_order=display_order,
            target_location=target_location,
            target_ride_type=target_ride_type,
            target_customer_type=target_customer_type,
            start_date=start_date,
            end_date=end_date,
            active_hours_start=active_hours_start,
            active_hours_end=active_hours_end,
            is_active=request.form.get('is_active') == 'true',
            created_by=current_user.id
        )
        
        db.session.add(ad)
        db.session.commit()
        
        logging.info(f"New advertisement created: {title} by admin {current_user.username}")
        return create_success_response(ad.to_dict(), "Advertisement created successfully")
        
    except Exception as e:
        logging.error(f"Error creating advertisement: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to create advertisement")

@admin_bp.route('/api/advertisements/<int:ad_id>', methods=['PUT'])
@login_required
def update_advertisement(ad_id):
    """Update an existing advertisement"""
    try:
        ad = Advertisement.query.get(ad_id)
        if not ad:
            return create_error_response("Advertisement not found")
        
        # Handle form data (not JSON for file uploads)
        if request.form.get('title'):
            ad.title = request.form.get('title')
        if request.form.get('description') is not None:
            ad.description = request.form.get('description')
        if request.form.get('display_duration'):
            ad.display_duration = int(request.form.get('display_duration'))
        if request.form.get('display_order'):
            ad.display_order = int(request.form.get('display_order'))
        if request.form.get('target_location') is not None:
            ad.target_location = request.form.get('target_location') or None
        if request.form.get('target_ride_type') is not None:
            ad.target_ride_type = request.form.get('target_ride_type') or None
        if request.form.get('target_customer_type') is not None:
            ad.target_customer_type = request.form.get('target_customer_type') or None
        
        # Handle date and time updates
        if request.form.get('start_date'):
            ad.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        if request.form.get('end_date'):
            ad.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        if request.form.get('active_hours_start'):
            ad.active_hours_start = datetime.strptime(request.form.get('active_hours_start'), '%H:%M').time()
        if request.form.get('active_hours_end'):
            ad.active_hours_end = datetime.strptime(request.form.get('active_hours_end'), '%H:%M').time()
        
        if request.form.get('is_active') is not None:
            ad.is_active = request.form.get('is_active') == 'true'
        
        # Handle new media file upload
        if 'media_file' in request.files and request.files['media_file'].filename != '':
            media_file = request.files['media_file']
            
            # Validate file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
            file_extension = media_file.filename.rsplit('.', 1)[1].lower()
            if file_extension not in allowed_extensions:
                return create_error_response("Invalid file type")
            
            # Delete old file
            old_file_path = os.path.join('static/ads', ad.media_filename)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
            
            # Save new file
            import uuid
            unique_filename = f"{uuid.uuid4()}_{media_file.filename}"
            file_path = os.path.join('static/ads', unique_filename)
            media_file.save(file_path)
            
            ad.media_filename = unique_filename
            ad.media_type = 'image' if file_extension in {'png', 'jpg', 'jpeg', 'gif'} else 'video'
        
        db.session.commit()
        
        logging.info(f"Advertisement updated: {ad.title} by admin {current_user.username}")
        return create_success_response(ad.to_dict(), "Advertisement updated successfully")
        
    except Exception as e:
        logging.error(f"Error updating advertisement: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to update advertisement")

@admin_bp.route('/api/advertisements/<int:ad_id>', methods=['DELETE'])
@login_required
def delete_advertisement(ad_id):
    """Delete an advertisement"""
    try:
        ad = Advertisement.query.get(ad_id)
        if not ad:
            return create_error_response("Advertisement not found")
        
        # Delete media file
        file_path = os.path.join('static/ads', ad.media_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        ad_title = ad.title
        db.session.delete(ad)
        db.session.commit()
        
        logging.info(f"Advertisement deleted: {ad_title} by admin {current_user.username}")
        return create_success_response({'message': 'Advertisement deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting advertisement: {str(e)}")
        db.session.rollback()
        return create_error_response("Failed to delete advertisement")

@admin_bp.route('/api/advertisements/<int:ad_id>/analytics', methods=['POST'])
@login_required
def update_ad_analytics(ad_id):
    """Update advertisement analytics (impressions/clicks)"""
    try:
        ad = Advertisement.query.get(ad_id)
        if not ad:
            return create_error_response("Advertisement not found")
        
        data = request.get_json()
        action = data.get('action')
        
        if action == 'impression':
            ad.increment_impressions()
        elif action == 'click':
            ad.increment_clicks()
        else:
            return create_error_response("Invalid action. Use 'impression' or 'click'")
        
        return create_success_response({
            'impressions': ad.impressions,
            'clicks': ad.clicks
        })
        
    except Exception as e:
        logging.error(f"Error updating advertisement analytics: {str(e)}")
        return create_error_response("Failed to update analytics")

@admin_bp.route('/advertisements', methods=['GET'])
@login_required
def advertisements_page():
    """Advertisements management page"""
    return render_template('admin/advertisements.html')
