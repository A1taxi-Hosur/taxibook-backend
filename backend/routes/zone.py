"""
Zone routes for A1 Taxi Hosur Dev
Zone management and geographic operations
"""

from flask import Blueprint, request
from models.zone import Zone
from utils.auth import token_required, create_response
from utils.geo import validate_coordinates

zone_bp = Blueprint('zone', __name__)

@zone_bp.route('/all', methods=['GET'])
@token_required(allowed_roles=['admin', 'driver'])
def get_all_zones():
    """Get all zones"""
    try:
        zones = Zone.query.all()
        
        zones_data = [zone.to_dict() for zone in zones]
        
        return create_response(True, data={'zones': zones_data}, message="Zones retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving zones: {str(e)}", status_code=500)

@zone_bp.route('/active', methods=['GET'])
def get_active_zones():
    """Get active zones (public endpoint)"""
    try:
        zones = Zone.query.filter_by(is_active=True).all()
        
        zones_data = [zone.to_dict() for zone in zones]
        
        return create_response(True, data={'zones': zones_data}, message="Active zones retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving active zones: {str(e)}", status_code=500)

@zone_bp.route('/create', methods=['POST'])
@token_required(allowed_roles=['admin'])
def create_zone():
    """Create a new zone"""
    try:
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        # Validate required fields
        required_fields = ['zone_name', 'center_lat', 'center_lng', 'radius_km']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return create_response(False, message=f"Missing fields: {', '.join(missing_fields)}", status_code=400)
        
        # Validate coordinates
        is_valid, error_message = validate_coordinates(data['center_lat'], data['center_lng'])
        if not is_valid:
            return create_response(False, message=error_message, status_code=400)
        
        # Create zone
        success, result = Zone.create_zone(
            zone_name=data['zone_name'],
            center_lat=float(data['center_lat']),
            center_lng=float(data['center_lng']),
            radius_km=float(data['radius_km'])
        )
        
        if not success:
            return create_response(False, message=result, status_code=400)
        
        zone = result
        
        return create_response(True, data=zone.to_dict(), message="Zone created successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error creating zone: {str(e)}", status_code=500)

@zone_bp.route('/<int:zone_id>', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_zone(zone_id):
    """Get specific zone details"""
    try:
        zone = Zone.query.get(zone_id)
        
        if not zone:
            return create_response(False, message="Zone not found", status_code=404)
        
        return create_response(True, data=zone.to_dict(), message="Zone retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving zone: {str(e)}", status_code=500)

@zone_bp.route('/<int:zone_id>/update', methods=['PUT'])
@token_required(allowed_roles=['admin'])
def update_zone(zone_id):
    """Update zone details"""
    try:
        zone = Zone.query.get(zone_id)
        
        if not zone:
            return create_response(False, message="Zone not found", status_code=404)
        
        data = request.get_json()
        
        if not data:
            return create_response(False, message="No data provided", status_code=400)
        
        # Validate coordinates if provided
        if 'center_lat' in data or 'center_lng' in data:
            lat = data.get('center_lat', zone.center_lat)
            lng = data.get('center_lng', zone.center_lng)
            
            is_valid, error_message = validate_coordinates(lat, lng)
            if not is_valid:
                return create_response(False, message=error_message, status_code=400)
        
        # Update zone
        success, message = zone.update_zone(
            zone_name=data.get('zone_name'),
            center_lat=float(data['center_lat']) if 'center_lat' in data else None,
            center_lng=float(data['center_lng']) if 'center_lng' in data else None,
            radius_km=float(data['radius_km']) if 'radius_km' in data else None
        )
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=zone.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error updating zone: {str(e)}", status_code=500)

@zone_bp.route('/<int:zone_id>/toggle_active', methods=['POST'])
@token_required(allowed_roles=['admin'])
def toggle_zone_active(zone_id):
    """Toggle zone active status"""
    try:
        zone = Zone.query.get(zone_id)
        
        if not zone:
            return create_response(False, message="Zone not found", status_code=404)
        
        success, message = zone.toggle_active()
        
        if not success:
            return create_response(False, message=message, status_code=400)
        
        return create_response(True, data=zone.to_dict(), message=message)
        
    except Exception as e:
        return create_response(False, message=f"Error toggling zone status: {str(e)}", status_code=500)

@zone_bp.route('/<int:zone_id>/drivers', methods=['GET'])
@token_required(allowed_roles=['admin'])
def get_zone_drivers(zone_id):
    """Get drivers in a specific zone"""
    try:
        zone = Zone.query.get(zone_id)
        
        if not zone:
            return create_response(False, message="Zone not found", status_code=404)
        
        available_only = request.args.get('available_only', 'false').lower() == 'true'
        
        drivers = zone.get_drivers_in_zone(available_only=available_only)
        
        drivers_data = []
        for driver in drivers:
            driver_data = driver.to_dict()
            if driver.user:
                driver_data['user'] = driver.user.to_dict()
            drivers_data.append(driver_data)
        
        return create_response(True, data={'drivers': drivers_data}, message="Zone drivers retrieved successfully")
        
    except Exception as e:
        return create_response(False, message=f"Error retrieving zone drivers: {str(e)}", status_code=500)