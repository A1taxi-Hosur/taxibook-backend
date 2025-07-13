"""
Fare routes for A1 Taxi Hosur Dev
Fare matrix management and pricing
"""

from flask import Blueprint, request
from models.fare_matrix import FareMatrix
from utils.auth import token_required, create_response

fare_bp = Blueprint('fare', __name__)

@fare_bp.route('/matrix', methods=['GET'])
def get_fare_matrix():
    """Get fare matrix (public endpoint)"""
    try:
        ride_category = request.args.get('ride_category')
        car_type = request.args.get('car_type')
        
        if ride_category and car_type:
            # Get specific fare
            fare = FareMatrix.get_fare(ride_category, car_type)
            if not fare:
                return create_response(False, message="Fare not found", status_code=404)
            
            return create_response(True, data=fare.to_dict(), message="Fare retrieved successfully")
        
        # Get all fares
        fares = FareMatrix.query.filter_by(is_active=True).all()
        
        # Group by ride category
        fare_matrix = {}
        for fare in fares:
            if fare.ride_category not in fare_matrix:
                fare_matrix[fare.ride_category] = {}
            fare_matrix[fare.ride_category][fare.car_type] = fare.to_dict()
        
        return create_response(True, data={'fare_matrix': fare_matrix}, message="Fare matrix retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving fare matrix: {str(e)}", status_code=500)

@fare_bp.route('/admin/matrix', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_admin_fare_matrix():
    """Get fare matrix for admin (includes inactive fares)"""
    try:
        fares = FareMatrix.query.all()
        
        # Group by ride category
        fare_matrix = {}
        for fare in fares:
            if fare.ride_category not in fare_matrix:
                fare_matrix[fare.ride_category] = {}
            fare_matrix[fare.ride_category][fare.car_type] = fare.to_dict()
        
        return create_response(True, data={'fare_matrix': fare_matrix}, message="Admin fare matrix retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving admin fare matrix: {str(e)}", status_code=500)

@fare_bp.route('/admin/update', methods=['POST'])
@token_required(allowed_roles=['admin'])
def update_fare():
    """Update fare matrix"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        # Validate required fields
        required_fields = ['ride_category', 'car_type', 'base_fare', 'per_km', 'hourly']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return create_response(False, message=f"Missing fields: {', '.join(missing_fields)}", status_code=400)
        
        # Update fare
        success, message = FareMatrix.update_fare(
            ride_category=data['ride_category'],
            car_type=data['car_type'],
            base_fare=float(data['base_fare']),
            per_km=float(data['per_km']),
            hourly=float(data['hourly']),
            flat_rate=float(data['flat_rate']) if data.get('flat_rate') else None
        )
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        # Get updated fare
        fare = FareMatrix.get_fare(data['ride_category'], data['car_type'])
        
        return create_response(True, data=fare.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error updating fare: {str(e)}", status_code=500)

@fare_bp.route('/admin/<int:fare_id>/toggle_active', methods=['POST'])
@token_required(allowed_roles=['admin'])
def toggle_fare_active(fare_id):
    """Toggle fare active status"""
    try:
        fare = FareMatrix.query.get(fare_id)
        
        if not fare:
            return create_response(False, message="Fare not found", status_code=404)
        
        success, message = fare.toggle_active()
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=fare.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error toggling fare status: {str(e)}", status_code=500)

@fare_bp.route('/estimate', methods=['POST'])
def calculate_fare_estimate():
    """Calculate fare estimate"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        ride_category = data.get('ride_category')
        car_type = data.get('car_type')
        
        if not ride_category or not car_type:
            return create_response(False, message="Ride category and car type are required", status_code=400)
        
        # Get fare matrix
        fare_matrix = FareMatrix.get_fare(ride_category, car_type)
        if not fare_matrix:
            return create_response(False, message="Fare not available for this ride type", status_code=404)
        
        # Calculate fare
        estimated_fare = fare_matrix.base_fare
        
        # Distance-based calculation
        pickup_lat = data.get('pickup_lat')
        pickup_lng = data.get('pickup_lng')
        drop_lat = data.get('drop_lat')
        drop_lng = data.get('drop_lng')
        
        if pickup_lat and pickup_lng and drop_lat and drop_lng:
            from utils.geo import calculate_distance
            distance_km = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
            estimated_fare = fare_matrix.base_fare + (distance_km * fare_matrix.per_km)
        elif fare_matrix.flat_rate:
            estimated_fare = fare_matrix.flat_rate
        
        # Time-based calculation (if provided)
        hours = data.get('hours', 0)
        if hours > 0:
            estimated_fare += (hours * fare_matrix.hourly)
        
        estimate_data = {
            'ride_category': ride_category,
            'car_type': car_type,
            'base_fare': fare_matrix.base_fare,
            'per_km': fare_matrix.per_km,
            'hourly': fare_matrix.hourly,
            'flat_rate': fare_matrix.flat_rate,
            'estimated_fare': round(estimated_fare, 2),
            'currency': '₹'
        }
        
        return create_response(True, data=estimate_data, message="Fare estimate calculated successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error calculating fare estimate: {str(e)}", status_code=500)