from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db, get_ist_time
from models import Admin, Customer, Driver, Ride, FareConfig, SpecialFareConfig, Zone
from utils.validators import create_error_response, create_success_response, validate_phone, validate_required_fields
import logging
import random
import string
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
        if admin and admin.password_hash == password:  # In production, use proper password hashing
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
        if admin and admin.password_hash == password:
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
        
        # Delete all rides
        Ride.query.delete()
        db.session.commit()
        
        logging.info(f"Cleared {total_rides} rides")
        flash(f'Cleared {total_rides} rides successfully', 'success')
        
    except Exception as e:
        logging.error(f"Error clearing logs: {str(e)}")
        flash('Error clearing logs', 'error')
        db.session.rollback()
    
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/stats')
@login_required
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
        return jsonify({'error': 'Error loading stats'}), 500

@admin_bp.route('/api/recent_rides')
@login_required
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
        return jsonify({'error': 'Error loading recent rides'}), 500

@admin_bp.route('/api/drivers')
@login_required
def api_drivers():
    """API endpoint for drivers data"""
    try:
        # Get all drivers
        drivers = Driver.query.order_by(Driver.created_at.desc()).all()
        
        drivers_data = []
        for driver in drivers:
            driver_data = {
                'id': driver.id,
                'name': driver.name,
                'phone': driver.phone,
                'username': driver.username,
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
                'rcbook_url': driver.rcbook_url,
                'total_rides': len(driver.rides),
                'created_at': driver.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            drivers_data.append(driver_data)
        
        return jsonify({'drivers': drivers_data})
        
    except Exception as e:
        logging.error(f"Error in api_drivers: {str(e)}")
        return jsonify({'error': 'Error loading drivers'}), 500

@admin_bp.route('/api/rides/<int:ride_id>/cancel', methods=['POST'])
@login_required
def cancel_ride_admin(ride_id):
    """Cancel a ride from admin panel"""
    try:
        ride = Ride.query.get_or_404(ride_id)
        
        if ride.status in ['completed', 'cancelled']:
            return jsonify({'error': 'Ride cannot be cancelled'}), 400
        
        ride.status = 'cancelled'
        ride.cancelled_at = get_ist_time()
        
        db.session.commit()
        
        logging.info(f"Ride {ride_id} cancelled by admin")
        return jsonify({'message': 'Ride cancelled successfully'})
        
    except Exception as e:
        logging.error(f"Error cancelling ride {ride_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Error cancelling ride'}), 500

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
            "status": "success",
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

@admin_bp.route('/get_driver/<int:driver_id>', methods=['GET'])
@login_required
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
            'data': {
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


@admin_bp.route('/fare_config')
@login_required
def fare_config():
    """Fare configuration management page"""
    return render_template('admin/fare_config.html')


@admin_bp.route('/api/fare_config', methods=['GET'])
@login_required
def api_get_fare_config():
    """API endpoint to get all fare configurations"""
    try:
        fare_configs = FareConfig.query.all()
        return create_success_response({
            'fare_configs': [config.to_dict() for config in fare_configs]
        })
    
    except Exception as e:
        logging.error(f"Error getting fare configurations: {str(e)}")
        return create_error_response("Failed to get fare configurations")


@admin_bp.route('/api/fare_config', methods=['POST'])
@login_required
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
        
        # Check if driver is available
        if not driver.is_online:
            return create_error_response('Driver is not online', 400)
        
        # Check if driver has active rides
        active_rides = Ride.query.filter_by(driver_id=driver_id).filter(
            Ride.status.in_(['assigned', 'active'])
        ).count()
        
        if active_rides > 0:
            return create_error_response('Driver already has active rides', 400)
        
        # Assign driver to ride
        ride.driver_id = driver_id
        ride.status = 'assigned'
        ride.assigned_time = get_ist_time()
        
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


@admin_bp.route('/api/special_fare_config', methods=['GET'])
@login_required
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


@admin_bp.route('/api/special_fare_config', methods=['POST'])
@login_required
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
@login_required
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
        valid, error = validate_required_fields(data, ['zone_name', 'center_lat', 'center_lng', 'radius_km'])
        if not valid:
            return create_error_response(error)
        
        zone_name = data['zone_name']
        center_lat = float(data['center_lat'])
        center_lng = float(data['center_lng'])
        radius_km = float(data['radius_km'])
        
        # Validate values
        if not (-90 <= center_lat <= 90):
            return create_error_response("Invalid latitude")
        
        if not (-180 <= center_lng <= 180):
            return create_error_response("Invalid longitude")
        
        if radius_km <= 0 or radius_km > 50:
            return create_error_response("Radius must be between 0 and 50 km")
        
        # Check if zone name already exists
        existing_zone = Zone.query.filter_by(zone_name=zone_name).first()
        if existing_zone:
            return create_error_response("Zone with this name already exists")
        
        # Create new zone
        new_zone = Zone(
            zone_name=zone_name,
            center_lat=center_lat,
            center_lng=center_lng,
            radius_km=radius_km,
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
@login_required
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
    return render_template('admin/zones.html')


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
@admin_bp.route('/api/live_driver_locations', methods=['GET'])
@login_required
def api_live_driver_locations():
    """API endpoint to get live driver locations"""
    try:
        # Get all drivers with their current locations
        drivers = Driver.query.all()
        
        driver_locations = []
        for driver in drivers:
            driver_data = {
                'id': driver.id,
                'name': driver.name,
                'phone': driver.phone,
                'current_lat': driver.current_lat,
                'current_lng': driver.current_lng,
                'location_updated_at': driver.location_updated_at.isoformat() if driver.location_updated_at else None,
                'is_online': driver.is_online,
                'out_of_zone': driver.out_of_zone,
                'car_type': driver.car_type,
                'car_number': driver.car_number,
                'car_make': driver.car_make,
                'car_model': driver.car_model,
                'car_year': driver.car_year,
                'company_name': 'A1 Taxi',  # Default company name
                'zone': driver.zone.zone_name if driver.zone else None
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
@login_required
def api_get_drivers():
    """API endpoint to get drivers with filters"""
    try:
        available_only = request.args.get('available', 'false').lower() == 'true'
        
        query = Driver.query
        
        if available_only:
            query = query.filter_by(is_online=True)
        
        drivers = query.all()
        
        driver_list = []
        for driver in drivers:
            driver_data = {
                'id': driver.id,
                'name': driver.name,
                'phone': driver.phone,
                'car_type': driver.car_type,
                'car_number': driver.car_number,
                'is_online': driver.is_online,
                'zone': driver.zone.zone_name if driver.zone else None
            }
            driver_list.append(driver_data)
        
        return create_success_response({
            'drivers': driver_list,
            'total_count': len(driver_list)
        })
    
    except Exception as e:
        logging.error(f"Error getting drivers: {str(e)}")
        return create_error_response("Failed to get drivers")
