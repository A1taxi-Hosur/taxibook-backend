"""
Driver Notification System for TaxiBook
Handles notifying matching drivers in zones about new rides
"""

import logging
from models import Driver, Zone, Ride, db
from utils.distance import haversine_distance
from app import get_ist_time

def notify_matching_drivers_in_zone(ride_id, pickup_lat, pickup_lng, ride_type):
    """
    Notify matching drivers in the pickup zone about a new ride
    
    Args:
        ride_id: ID of the ride
        pickup_lat: Pickup latitude
        pickup_lng: Pickup longitude
        ride_type: Type of ride (sedan, suv, hatchback)
    
    Returns:
        Dict with notification result
    """
    try:
        # Find the zone for pickup location
        pickup_zone = Zone.find_zone_for_location(pickup_lat, pickup_lng)
        
        if not pickup_zone:
            logging.warning(f"No zone found for pickup location ({pickup_lat}, {pickup_lng})")
            return {
                'success': False,
                'message': 'No service zone found for pickup location',
                'drivers_count': 0
            }
        
        # Find matching drivers in the zone - use case insensitive matching for car type
        # Only include drivers with recent location data (within 30 seconds)
        from datetime import timedelta, datetime
        # Use UTC time to match database timestamps (which are in UTC)
        current_time = datetime.utcnow()
        staleness_threshold = timedelta(seconds=120)  # More realistic threshold for driver locations
        
        all_zone_drivers = Driver.query.filter(
            Driver.zone_id == pickup_zone.id,
            Driver.is_online == True,
            Driver.car_type.ilike(f'%{ride_type}%'),  # Case-insensitive partial match
            Driver.current_lat.isnot(None),
            Driver.current_lng.isnot(None),
            Driver.location_updated_at.isnot(None)
        ).all()
        
        # Filter out drivers with stale location data
        matching_drivers = []
        for driver in all_zone_drivers:
            time_since_update = current_time - driver.location_updated_at
            if time_since_update <= staleness_threshold:
                matching_drivers.append(driver)
            else:
                logging.debug(f"Excluding driver {driver.name}: location is {time_since_update.total_seconds():.0f}s old")
        
        # Debug logging
        all_debug_drivers = Driver.query.filter(Driver.zone_id == pickup_zone.id).all()
        logging.info(f"=== DRIVER NOTIFICATION DEBUG ===")
        logging.info(f"Zone: {pickup_zone.zone_name} (ID: {pickup_zone.id})")
        logging.info(f"Looking for ride_type: {ride_type}")
        logging.info(f"Total drivers in zone: {len(all_debug_drivers)}")
        logging.info(f"Drivers with fresh location (<30s): {len(matching_drivers)}")
        
        for driver in all_debug_drivers:
            has_location = bool(driver.current_lat and driver.current_lng)
            location_age = "N/A"
            if driver.location_updated_at and has_location:
                age_seconds = (current_time - driver.location_updated_at).total_seconds()
                location_age = f"{age_seconds:.0f}s ago"
                
            logging.info(f"Driver: {driver.name} - Online: {driver.is_online}, Car: {driver.car_type}, Location: {location_age}")
        
        logging.info(f"Final matching drivers (fresh locations): {len(matching_drivers)}")
        
        if not matching_drivers:
            logging.info(f"No matching {ride_type} drivers found in zone {pickup_zone.zone_name}")
            # Still mark as pending even when no drivers available in zone
            ride = Ride.query.get(ride_id)
            if ride:
                ride.status = 'pending'  # Customer waits for drivers to come online in zone
                db.session.commit()
                logging.info(f"Ride {ride_id} marked as pending - no drivers in zone yet")
            
            return {
                'success': False,
                'message': f'No {ride_type} drivers available in {pickup_zone.zone_name} zone',
                'drivers_count': 0,
                'zone_name': pickup_zone.zone_name
            }
        
        # ALL drivers in the zone with matching car type get notified (no proximity limit)
        notified_drivers = []
        for driver in matching_drivers:
            distance = haversine_distance(
                pickup_lat, pickup_lng,
                driver.current_lat, driver.current_lng
            )
            
            logging.info(f"Notifying driver {driver.name} ({driver.phone}) about ride {ride_id} - Distance: {distance:.2f}km")
            notified_drivers.append({
                'driver_id': driver.id,
                'driver_name': driver.name,
                'driver_phone': driver.phone,
                'distance_km': round(distance, 2),
                'car_type': driver.car_type,
                'car_number': driver.car_number
            })
        
        # Sort by distance (closest first)
        notified_drivers.sort(key=lambda x: x['distance_km'])
        
        # Update ride status to indicate drivers have been notified
        ride = Ride.query.get(ride_id)
        if ride:
            ride.status = 'pending'  # Changed from 'new' to 'pending' to indicate drivers notified
            db.session.commit()
        
        logging.info(f"Successfully notified {len(notified_drivers)} drivers about ride {ride_id}")
        
        return {
            'success': True,
            'message': f'Notified {len(notified_drivers)} matching drivers',
            'drivers_count': len(notified_drivers),
            'zone_name': pickup_zone.zone_name,
            'notified_drivers': notified_drivers
        }
        
    except Exception as e:
        logging.error(f"Error in driver notification system: {str(e)}")
        return {
            'success': False,
            'message': 'Notification system error',
            'error': str(e),
            'drivers_count': 0
        }

def get_notified_drivers_for_ride(ride_id):
    """
    Get the list of drivers who were notified about a ride
    This function can be used to track which drivers received notifications
    """
    try:
        ride = Ride.query.get(ride_id)
        if not ride:
            return []
        
        # For now, we'll return the current matching drivers
        # In a real system, you might store this in a separate table
        if ride.pickup_lat and ride.pickup_lng:
            result = notify_matching_drivers_in_zone(
                ride_id, ride.pickup_lat, ride.pickup_lng, ride.ride_type
            )
            return result.get('notified_drivers', [])
        
        return []
        
    except Exception as e:
        logging.error(f"Error getting notified drivers for ride {ride_id}: {str(e)}")
        return []