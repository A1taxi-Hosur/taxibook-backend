"""
Distance calculation utilities for TaxiBook
Provides Haversine formula for calculating distances between coordinates
"""
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point (in decimal degrees)
        lat2, lon2: Latitude and longitude of second point (in decimal degrees)
    
    Returns:
        Distance in kilometers
    """
    # Earth radius in kilometers
    R = 6371
    
    # Convert decimal degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_phi / 2)**2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Distance in kilometers
    distance = R * c
    return distance

def filter_drivers_by_proximity(drivers, pickup_lat, pickup_lng, max_distance_km=5.0):
    """
    Filter drivers by proximity to pickup location
    
    Args:
        drivers: List of Driver objects
        pickup_lat: Pickup latitude
        pickup_lng: Pickup longitude
        max_distance_km: Maximum distance in kilometers (default: 5.0)
    
    Returns:
        List of (driver, distance) tuples for drivers within range
    """
    eligible_drivers = []
    
    for driver in drivers:
        # Skip drivers without current location
        if driver.current_lat is None or driver.current_lng is None:
            continue
            
        # Calculate distance from driver to pickup
        distance = haversine_distance(
            pickup_lat, pickup_lng,
            driver.current_lat, driver.current_lng
        )
        
        # Include drivers within the specified range
        if distance <= max_distance_km:
            eligible_drivers.append((driver, distance))
    
    # Sort by distance (closest first)
    eligible_drivers.sort(key=lambda x: x[1])
    
    return eligible_drivers