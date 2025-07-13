"""
Enhanced Ride Dispatch Engine with Concentric Ring Configuration
Handles polygon zones with customizable ring expansion and extra fare calculation
"""

import logging
from datetime import datetime, timedelta
from models import Zone, Driver, Ride, db, get_ist_time
from utils.distance import haversine_distance, get_polygon_centroid


class EnhancedDispatchEngine:
    """Enhanced dispatch engine with concentric ring logic for polygon zones"""
    
    def __init__(self, ride_id):
        self.ride_id = ride_id
        self.ride = Ride.query.get(ride_id)
        self.dispatch_log = []
        
    def dispatch_ride(self, pickup_lat, pickup_lng):
        """
        Main dispatch method with concentric ring expansion
        
        Args:
            pickup_lat: Pickup location latitude
            pickup_lng: Pickup location longitude
            
        Returns:
            Dict with dispatch result and info
        """
        try:
            # Find the zone containing the pickup location
            pickup_zone = self._find_pickup_zone(pickup_lat, pickup_lng)
            
            if not pickup_zone:
                return {
                    'success': False,
                    'error': 'Out of service area',
                    'message': 'No service zone found for pickup location'
                }
            
            # Update ride with dispatch zone
            self.ride.dispatch_zone_id = pickup_zone.id
            
            # Try concentric ring dispatch within the zone
            result = self._dispatch_with_rings(pickup_zone, pickup_lat, pickup_lng)
            
            if result['success']:
                return result
            
            # If no driver found in zone, try zone expansion
            return self._dispatch_with_zone_expansion(pickup_zone, pickup_lat, pickup_lng)
            
        except Exception as e:
            logging.error(f"Error in enhanced dispatch: {str(e)}")
            return {
                'success': False,
                'error': 'Dispatch system error',
                'message': str(e)
            }
    
    def _find_pickup_zone(self, pickup_lat, pickup_lng):
        """Find the zone containing the pickup location"""
        zones = Zone.query.filter_by(is_active=True).order_by(Zone.priority_order).all()
        
        for zone in zones:
            if zone.is_point_in_zone(pickup_lat, pickup_lng):
                return zone
        
        return None
    
    def _dispatch_with_rings(self, zone, pickup_lat, pickup_lng):
        """Dispatch using concentric rings within the zone"""
        for ring_number in range(1, zone.number_of_rings + 1):
            self.dispatch_log.append(f"Searching Ring {ring_number}")
            
            # Get drivers in this ring
            ring_drivers = zone.get_ring_drivers(ring_number, pickup_lat, pickup_lng)
            
            if ring_drivers:
                # Try to assign to the nearest driver
                driver_info = ring_drivers[0]  # Closest driver
                driver = driver_info['driver']
                
                # Check if driver is available (not already assigned)
                if self._is_driver_available(driver):
                    # Assign ride to driver
                    success = self._assign_ride_to_driver(driver, ring_number, driver_info['distance'])
                    
                    if success:
                        return {
                            'success': True,
                            'driver_assigned': True,
                            'driver_id': driver.id,
                            'ring_number': ring_number,
                            'distance_to_driver': driver_info['distance'],
                            'zone_id': zone.id,
                            'zone_name': zone.zone_name,
                            'dispatch_log': self.dispatch_log
                        }
            
            # Wait before expanding to next ring
            if ring_number < zone.number_of_rings:
                self.dispatch_log.append(f"Ring {ring_number} wait time: {zone.ring_wait_time_seconds}s")
                # In real implementation, this would be handled asynchronously
                # For now, we'll continue immediately for testing
        
        return {
            'success': False,
            'drivers_found_in_zone': False,
            'dispatch_log': self.dispatch_log
        }
    
    def _dispatch_with_zone_expansion(self, pickup_zone, pickup_lat, pickup_lng):
        """Dispatch with zone expansion and extra fare calculation"""
        # Get neighboring zones for expansion
        expansion_zones = Zone.get_next_zones_for_expansion(pickup_zone, pickup_lat, pickup_lng)
        
        if not expansion_zones:
            return {
                'success': False,
                'error': 'No drivers available',
                'message': 'No drivers found in your area or nearby zones'
            }
        
        # Find best driver from expansion zones
        best_driver_info = None
        best_zone = None
        
        for zone_info in expansion_zones[:3]:  # Check top 3 nearest zones
            zone = zone_info['zone']
            
            # Get drivers from this zone
            ring_drivers = zone.get_ring_drivers(1, pickup_lat, pickup_lng)
            
            if ring_drivers:
                driver_info = ring_drivers[0]  # Closest driver
                driver = driver_info['driver']
                
                if self._is_driver_available(driver):
                    best_driver_info = driver_info
                    best_zone = zone
                    break
        
        if not best_driver_info:
            return {
                'success': False,
                'error': 'No drivers available',
                'message': 'No available drivers found in nearby zones'
            }
        
        # Calculate extra fare for zone expansion
        extra_fare = self._calculate_extra_fare(pickup_zone, best_zone)
        
        return {
            'success': True,
            'requires_zone_expansion': True,
            'expansion_zone': best_zone.zone_name,
            'extra_fare': extra_fare,
            'driver_info': {
                'driver_id': best_driver_info['driver'].id,
                'distance': best_driver_info['distance'],
                'zone_id': best_zone.id
            },
            'approval_required': True,
            'message': f"No driver found in your area. An extra fare of ₹{extra_fare} is applicable to bring a driver from {best_zone.zone_name}. Proceed?"
        }
    
    def _calculate_extra_fare(self, pickup_zone, driver_zone):
        """Calculate extra fare based on distance between zones"""
        pickup_centroid = pickup_zone.get_polygon_centroid()
        driver_centroid = driver_zone.get_polygon_centroid()
        
        distance = haversine_distance(
            pickup_centroid['lat'], pickup_centroid['lng'],
            driver_centroid['lat'], driver_centroid['lng']
        )
        
        # Fixed rate of ₹10 per km for zone expansion
        extra_fare = round(distance * 10, 2)
        return max(extra_fare, 25)  # Minimum ₹25 extra fare
    
    def _is_driver_available(self, driver):
        """Check if driver is available for assignment"""
        # Check if driver is online
        if not driver.is_online:
            return False
        
        # Check if driver is already assigned to another ride
        active_ride = Ride.query.filter_by(
            driver_id=driver.id,
            status='assigned'
        ).first()
        
        return active_ride is None
    
    def _assign_ride_to_driver(self, driver, ring_number, distance):
        """Assign ride to driver and update database"""
        try:
            self.ride.driver_id = driver.id
            self.ride.status = 'assigned'
            self.ride.dispatched_ring = ring_number
            self.ride.assigned_time = get_ist_time()
            
            db.session.commit()
            
            self.dispatch_log.append(f"Ride assigned to driver {driver.id} in ring {ring_number}")
            logging.info(f"Ride {self.ride_id} assigned to driver {driver.id} in ring {ring_number}")
            return True
            
        except Exception as e:
            logging.error(f"Error assigning ride to driver: {str(e)}")
            db.session.rollback()
            return False
    
    def approve_zone_expansion(self, driver_id, zone_id, extra_fare):
        """Approve zone expansion and assign driver"""
        try:
            driver = Driver.query.get(driver_id)
            if not driver or not self._is_driver_available(driver):
                return {
                    'success': False,
                    'error': 'Driver no longer available'
                }
            
            # Assign ride to driver
            self.ride.driver_id = driver_id
            self.ride.status = 'assigned'
            self.ride.zone_expansion_approved = True
            self.ride.extra_fare = extra_fare
            self.ride.final_fare = self.ride.fare_amount + extra_fare
            self.ride.assigned_time = get_ist_time()
            
            db.session.commit()
            
            return {
                'success': True,
                'driver_assigned': True,
                'driver_id': driver_id,
                'final_fare': self.ride.final_fare,
                'extra_fare': extra_fare
            }
            
        except Exception as e:
            logging.error(f"Error approving zone expansion: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': 'Failed to approve zone expansion'
            }


def dispatch_ride_with_enhanced_system(ride_id):
    """
    Main entry point for enhanced ride dispatch
    
    Args:
        ride_id: ID of the ride to dispatch
        
    Returns:
        Dict with dispatch result
    """
    engine = EnhancedDispatchEngine(ride_id)
    ride = Ride.query.get(ride_id)
    
    if not ride:
        return {
            'success': False,
            'error': 'Ride not found'
        }
    
    return engine.dispatch_ride(ride.pickup_lat, ride.pickup_lng)


def approve_zone_expansion_for_ride(ride_id, driver_id, zone_id, extra_fare):
    """
    Approve zone expansion for a ride
    
    Args:
        ride_id: ID of the ride
        driver_id: ID of the driver to assign
        zone_id: ID of the expansion zone
        extra_fare: Extra fare amount
        
    Returns:
        Dict with approval result
    """
    engine = EnhancedDispatchEngine(ride_id)
    return engine.approve_zone_expansion(driver_id, zone_id, extra_fare)