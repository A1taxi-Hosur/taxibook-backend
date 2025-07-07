import os
import requests
import logging
from utils.validators import create_error_response

def get_distance_and_fare(pickup_address, drop_address, pickup_lat=None, pickup_lng=None, drop_lat=None, drop_lng=None):
    """
    Calculate distance and fare using Google Maps Distance Matrix API
    Returns: (success, distance_km, fare_amount, error_message)
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logging.error("Google Maps API key not found in environment variables")
        return False, None, None, "Google Maps API configuration error"
    
    try:
        # Use coordinates if available, otherwise use addresses
        if pickup_lat and pickup_lng and drop_lat and drop_lng:
            origins = f"{pickup_lat},{pickup_lng}"
            destinations = f"{drop_lat},{drop_lng}"
        else:
            origins = pickup_address
            destinations = drop_address
        
        # Make API request
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': origins,
            'destinations': destinations,
            'key': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check API response status
        if data.get('status') != 'OK':
            logging.error(f"Google Maps API error: {data.get('status')}")
            return False, None, None, "Could not calculate distance - invalid location"
        
        # Extract distance information
        rows = data.get('rows', [])
        if not rows or not rows[0].get('elements'):
            return False, None, None, "Could not calculate distance - no route found"
        
        element = rows[0]['elements'][0]
        if element.get('status') != 'OK':
            logging.error(f"Google Maps API element error: {element.get('status')}")
            return False, None, None, "Could not calculate distance - no route available"
        
        # Get distance in kilometers
        distance_meters = element['distance']['value']
        distance_km = distance_meters / 1000
        
        # Calculate fare: ₹12 base + ₹11/km
        base_fare = 12
        per_km_rate = 11
        fare_amount = base_fare + (distance_km * per_km_rate)
        fare_amount = round(fare_amount, 2)
        
        logging.info(f"Distance calculated: {distance_km}km, Fare: ₹{fare_amount}")
        return True, distance_km, fare_amount, None
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Google Maps API request failed: {str(e)}")
        return False, None, None, "Could not calculate distance - network error"
    except Exception as e:
        logging.error(f"Unexpected error in distance calculation: {str(e)}")
        return False, None, None, "Could not calculate distance - system error"

def get_distance_to_pickup(driver_location, pickup_address, pickup_lat=None, pickup_lng=None):
    """
    Calculate distance from driver to pickup location
    Returns: (success, distance_km, error_message)
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return False, None, "Google Maps API configuration error"
    
    try:
        # Use coordinates if available, otherwise use address
        if pickup_lat and pickup_lng:
            destinations = f"{pickup_lat},{pickup_lng}"
        else:
            destinations = pickup_address
        
        # Make API request
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': driver_location,
            'destinations': destinations,
            'key': api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Check API response status
        if data.get('status') != 'OK':
            return False, None, "Could not calculate distance to pickup"
        
        # Extract distance information
        rows = data.get('rows', [])
        if not rows or not rows[0].get('elements'):
            return False, None, "Could not calculate distance to pickup"
        
        element = rows[0]['elements'][0]
        if element.get('status') != 'OK':
            return False, None, "Could not calculate distance to pickup"
        
        # Get distance in kilometers
        distance_meters = element['distance']['value']
        distance_km = distance_meters / 1000
        
        return True, distance_km, None
        
    except Exception as e:
        logging.error(f"Error calculating distance to pickup: {str(e)}")
        return False, None, "Could not calculate distance to pickup"
