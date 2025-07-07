from flask import Blueprint, request, jsonify
from models import db, Driver, Customer, Ride
from utils.validators import validate_phone, create_error_response, create_success_response
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import logging

mobile_bp = Blueprint('mobile', __name__)

# DRIVER ENDPOINTS

@mobile_bp.route('/driver/profile', methods=['GET'])
def driver_profile():
    """Get driver profile information"""
    try:
        username = request.args.get('username')
        if not username:
            return create_error_response("Username is required", 400)
        
        # Find driver by username
        driver = Driver.query.filter_by(username=username).first()
        if not driver:
            return create_error_response("Driver not found", 404)
        
        # Return all driver fields
        profile_data = {
            'id': driver.id,
            'username': driver.username,
            'name': driver.name,
            'phone': driver.phone,
            'is_online': driver.is_online,
            'created_at': driver.created_at.isoformat() if driver.created_at else None,
            'car_make': driver.car_make,
            'car_model': driver.car_model,
            'car_year': driver.car_year,
            'car_number': driver.car_number,
            'car_type': driver.car_type,
            'license_number': driver.license_number,
            'aadhaar_url': driver.aadhaar_url,
            'license_url': driver.license_url,
            'rcbook_url': driver.rcbook_url,
            'profile_photo_url': driver.profile_photo_url
        }
        
        return create_success_response(profile_data, "Driver profile retrieved successfully")
    
    except Exception as e:
        logging.error(f"Error retrieving driver profile: {str(e)}")
        return create_error_response("Internal server error", 500)

@mobile_bp.route('/driver/history', methods=['GET'])
def driver_history():
    """Get paginated driver ride history"""
    try:
        username = request.args.get('username')
        if not username:
            return create_error_response("Username is required", 400)
        
        # Get pagination parameters
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 20))
        
        # Validate pagination parameters
        if offset < 0 or limit < 1 or limit > 100:
            return create_error_response("Invalid pagination parameters", 400)
        
        # Find driver by username
        driver = Driver.query.filter_by(username=username).first()
        if not driver:
            return create_error_response("Driver not found", 404)
        
        # Get completed rides for this driver
        rides = Ride.query.filter_by(
            driver_id=driver.id,
            status='completed'
        ).order_by(Ride.completed_at.desc()).offset(offset).limit(limit).all()
        
        # Format ride data
        ride_history = []
        for ride in rides:
            ride_data = {
                'ride_id': ride.id,
                'customer_phone': ride.customer_phone,
                'pickup_address': ride.pickup_address,
                'drop_address': ride.drop_address,
                'fare': ride.fare_amount,
                'distance_km': ride.distance_km,
                'completed_at': ride.completed_at.isoformat() if ride.completed_at else None
            }
            ride_history.append(ride_data)
        
        return create_success_response({
            'rides': ride_history,
            'offset': offset,
            'limit': limit,
            'count': len(ride_history)
        }, "Driver history retrieved successfully")
    
    except Exception as e:
        logging.error(f"Error retrieving driver history: {str(e)}")
        return create_error_response("Internal server error", 500)

@mobile_bp.route('/driver/earnings', methods=['GET'])
def driver_earnings():
    """Get driver earnings summary"""
    try:
        username = request.args.get('username')
        if not username:
            return create_error_response("Username is required", 400)
        
        # Find driver by username
        driver = Driver.query.filter_by(username=username).first()
        if not driver:
            return create_error_response("Driver not found", 404)
        
        # Get total earnings and ride count
        total_stats = db.session.query(
            func.count(Ride.id).label('total_rides'),
            func.sum(Ride.fare_amount).label('total_fare')
        ).filter_by(driver_id=driver.id, status='completed').first()
        
        total_rides = total_stats.total_rides or 0
        total_fare = float(total_stats.total_fare or 0)
        
        # Get daily earnings for last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_earnings = db.session.query(
            func.date(Ride.completed_at).label('date'),
            func.count(Ride.id).label('ride_count'),
            func.sum(Ride.fare_amount).label('total_fare')
        ).filter(
            Ride.driver_id == driver.id,
            Ride.status == 'completed',
            Ride.completed_at >= seven_days_ago
        ).group_by(func.date(Ride.completed_at)).order_by(func.date(Ride.completed_at).desc()).all()
        
        # Format daily data
        daily_summary = []
        for day in daily_earnings:
            daily_summary.append({
                'date': day.date.isoformat(),
                'ride_count': day.ride_count,
                'total_fare': float(day.total_fare)
            })
        
        earnings_data = {
            'total_rides': total_rides,
            'total_fare': total_fare,
            'daily_summary': daily_summary
        }
        
        return create_success_response(earnings_data, "Driver earnings retrieved successfully")
    
    except Exception as e:
        logging.error(f"Error retrieving driver earnings: {str(e)}")
        return create_error_response("Internal server error", 500)

# CUSTOMER ENDPOINTS

@mobile_bp.route('/customer/profile', methods=['GET'])
def customer_profile():
    """Get customer profile information"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return create_error_response("Phone number is required", 400)
        
        # Validate phone number
        if not validate_phone(phone):
            return create_error_response("Invalid phone number format", 400)
        
        # Find customer by phone
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            return create_error_response("Customer not found", 404)
        
        # Return customer profile data
        profile_data = {
            'name': customer.name,
            'phone': customer.phone,
            'created_at': customer.created_at.isoformat() if customer.created_at else None
        }
        
        return create_success_response(profile_data, "Customer profile retrieved successfully")
    
    except Exception as e:
        logging.error(f"Error retrieving customer profile: {str(e)}")
        return create_error_response("Internal server error", 500)

@mobile_bp.route('/customer/history', methods=['GET'])
def customer_history():
    """Get paginated customer ride history"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return create_error_response("Phone number is required", 400)
        
        # Validate phone number
        if not validate_phone(phone):
            return create_error_response("Invalid phone number format", 400)
        
        # Get pagination parameters
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 20))
        
        # Validate pagination parameters
        if offset < 0 or limit < 1 or limit > 100:
            return create_error_response("Invalid pagination parameters", 400)
        
        # Find customer by phone
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            return create_error_response("Customer not found", 404)
        
        # Get rides for this customer with driver details
        rides = db.session.query(Ride).join(
            Driver, Ride.driver_id == Driver.id, isouter=True
        ).filter(
            Ride.customer_phone == phone
        ).order_by(Ride.completed_at.desc()).offset(offset).limit(limit).all()
        
        # Format ride data
        ride_history = []
        for ride in rides:
            ride_data = {
                'ride_id': ride.id,
                'pickup_address': ride.pickup_address,
                'drop_address': ride.drop_address,
                'status': ride.status,
                'fare': ride.fare_amount,
                'distance_km': ride.distance_km,
                'completed_at': ride.completed_at.isoformat() if ride.completed_at else None,
                'driver_name': ride.driver.name if ride.driver else None
            }
            ride_history.append(ride_data)
        
        return create_success_response({
            'rides': ride_history,
            'offset': offset,
            'limit': limit,
            'count': len(ride_history)
        }, "Customer history retrieved successfully")
    
    except Exception as e:
        logging.error(f"Error retrieving customer history: {str(e)}")
        return create_error_response("Internal server error", 500)

@mobile_bp.route('/customer/total_spent', methods=['GET'])
def customer_total_spent():
    """Get customer spending summary"""
    try:
        phone = request.args.get('phone')
        if not phone:
            return create_error_response("Phone number is required", 400)
        
        # Validate phone number
        if not validate_phone(phone):
            return create_error_response("Invalid phone number format", 400)
        
        # Find customer by phone
        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            return create_error_response("Customer not found", 404)
        
        # Get total spending and ride count
        total_stats = db.session.query(
            func.count(Ride.id).label('total_rides'),
            func.sum(Ride.fare_amount).label('total_fare')
        ).filter_by(customer_phone=phone, status='completed').first()
        
        total_rides = total_stats.total_rides or 0
        total_fare = float(total_stats.total_fare or 0)
        
        # Get daily spending for last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_spending = db.session.query(
            func.date(Ride.completed_at).label('date'),
            func.count(Ride.id).label('ride_count'),
            func.sum(Ride.fare_amount).label('total_fare')
        ).filter(
            Ride.customer_phone == phone,
            Ride.status == 'completed',
            Ride.completed_at >= seven_days_ago
        ).group_by(func.date(Ride.completed_at)).order_by(func.date(Ride.completed_at).desc()).all()
        
        # Format daily data
        daily_summary = []
        for day in daily_spending:
            daily_summary.append({
                'date': day.date.isoformat(),
                'ride_count': day.ride_count,
                'total_fare': float(day.total_fare)
            })
        
        spending_data = {
            'total_rides': total_rides,
            'total_fare': total_fare,
            'daily_summary': daily_summary
        }
        
        return create_success_response(spending_data, "Customer spending retrieved successfully")
    
    except Exception as e:
        logging.error(f"Error retrieving customer spending: {str(e)}")
        return create_error_response("Internal server error", 500)