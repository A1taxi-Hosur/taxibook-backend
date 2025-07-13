"""
Geographic utilities for A1 Taxi Hosur Dev
Distance calculations and zone management
"""

import math

def calculate_distance(lat1, lng1, lat2, lng2):
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    if not all(isinstance(coord, (int, float)) for coord in [lat1, lng1, lat2, lng2]):
        return 0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return c * r

def is_point_in_zone(point_lat, point_lng, zone_lat, zone_lng, radius_km):
    """
    Check if a point is within a circular zone
    Returns True if point is within the zone
    """
    distance = calculate_distance(point_lat, point_lng, zone_lat, zone_lng)
    return distance <= radius_km

def find_nearest_zone(point_lat, point_lng, zones):
    """
    Find the nearest zone to a given point
    Returns (zone, distance) tuple or (None, None) if no zones
    """
    if not zones:
        return None, None
    
    nearest_zone = None
    min_distance = float('inf')
    
    for zone in zones:
        distance = calculate_distance(point_lat, point_lng, zone.center_lat, zone.center_lng)
        if distance < min_distance:
            min_distance = distance
            nearest_zone = zone
    
    return nearest_zone, min_distance

def get_zones_within_radius(point_lat, point_lng, zones, radius_km):
    """
    Get all zones within a specified radius from a point
    Returns list of (zone, distance) tuples
    """
    nearby_zones = []
    
    for zone in zones:
        distance = calculate_distance(point_lat, point_lng, zone.center_lat, zone.center_lng)
        if distance <= radius_km:
            nearby_zones.append((zone, distance))
    
    # Sort by distance
    nearby_zones.sort(key=lambda x: x[1])
    
    return nearby_zones

def validate_coordinates(lat, lng):
    """
    Validate latitude and longitude coordinates
    Returns (is_valid, error_message)
    """
    try:
        lat = float(lat)
        lng = float(lng)
        
        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"
        
        if not (-180 <= lng <= 180):
            return False, "Longitude must be between -180 and 180"
        
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid coordinate format"