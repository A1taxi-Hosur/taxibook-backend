"""
Advanced Ride Dispatch Engine with Concentric Ring Logic
Handles zone-based dispatch with automatic expansion and fare calculation
"""

import time
import asyncio
from datetime import datetime, timedelta
from app import db
from models import Ride, Driver, Zone, RideRejection
from utils.distance import haversine_distance
import logging

class RideDispatchEngine:
    """
    Advanced ride dispatch engine with concentric ring logic
    """
    
    def __init__(self, ride_id):
        self.ride_id = ride_id
        self.ride = Ride.query.get(ride_id)
        if not self.ride:
            raise ValueError(f"Ride with ID {ride_id} not found")
        
        self.dispatch_zone = None
        self.current_ring = 1
        self.rejected_drivers = set()
        self.dispatch_log = []
    
    def start_dispatch(self):
        """Start the dispatch process"""
        try:
            # Find initial zone
            self.dispatch_zone = Zone.find_zone_for_location(
                self.ride.pickup_lat, 
                self.ride.pickup_lng
            )
            
            if not self.dispatch_zone:
                return self._no_zone_fallback()
            
            # Update ride with dispatch zone
            self.ride.dispatch_zone_id = self.dispatch_zone.id
            db.session.commit()
            
            # Start concentric ring dispatch
            return self._dispatch_in_rings()
            
        except Exception as e:
            logging.error(f"Error in ride dispatch: {str(e)}")
            return {
                'success': False,
                'message': 'Dispatch system error',
                'error': str(e)
            }
    
    def _dispatch_in_rings(self):
        """Dispatch within concentric rings of the current zone"""
        for ring in range(1, self.dispatch_zone.number_of_rings + 1):
            self.current_ring = ring
            
            # Get drivers in this ring
            drivers_in_ring = self.dispatch_zone.get_drivers_in_ring(
                ring, 
                self.ride.pickup_lat, 
                self.ride.pickup_lng
            )
            
            # Filter out rejected drivers and wrong vehicle type
            available_drivers = [
                d for d in drivers_in_ring 
                if (d['driver'].id not in self.rejected_drivers and
                    d['driver'].car_type == self.ride.ride_type)
            ]
            
            if available_drivers:
                # Try to assign to closest driver
                for driver_info in available_drivers:
                    driver = driver_info['driver']
                    
                    # Check if driver is still available
                    if self._is_driver_available(driver):
                        # Assign ride
                        self.ride.driver_id = driver.id
                        self.ride.dispatched_ring = ring
                        self.ride.status = 'assigned'
                        self.ride.assigned_time = datetime.now()
                        
                        db.session.commit()
                        
                        self._log_dispatch_event(f"Assigned to driver {driver.id} in ring {ring}")
                        
                        return {
                            'success': True,
                            'message': 'Driver assigned successfully',
                            'driver_id': driver.id,
                            'ring': ring,
                            'distance': driver_info['distance']
                        }
            
            # Log ring attempt
            self._log_dispatch_event(f"Ring {ring}: No available drivers")
            
            # Wait for expansion delay (except for last ring)
            if ring < self.dispatch_zone.number_of_rings:
                time.sleep(self.dispatch_zone.expansion_delay_sec)
        
        # No drivers found in any ring - expand to other zones
        return self._expand_to_other_zones()
    
    def _expand_to_other_zones(self):
        """Expand search to other zones with fare calculation"""
        next_zones = Zone.get_next_zones_for_expansion(
            self.dispatch_zone,
            self.ride.pickup_lat,
            self.ride.pickup_lng
        )
        
        if not next_zones:
            return {
                'success': False,
                'message': 'No nearby zones available for expansion',
                'requires_manual_assignment': True
            }
        
        # Calculate extra fare for expansion
        nearest_zone = next_zones[0]
        extra_fare = self._calculate_expansion_fare(nearest_zone)
        
        return {
            'success': False,
            'message': 'Drivers not found nearby',
            'requires_customer_approval': True,
            'extra_fare': extra_fare,
            'expansion_zone': nearest_zone['zone'].zone_name,
            'expansion_distance': nearest_zone['distance']
        }
    
    def _calculate_expansion_fare(self, zone_info):
        """Calculate extra fare for zone expansion"""
        # Get base rate per km from fare config
        from models import FareConfig
        
        fare_config = FareConfig.get_fare_for_ride_type(self.ride.ride_type)
        if not fare_config:
            base_rate = 8.0  # Default rate
        else:
            base_rate = fare_config.per_km_rate
        
        # Calculate extra fare based on distance to new zone center
        distance_km = zone_info['distance']
        extra_fare = base_rate * distance_km
        
        return round(extra_fare, 2)
    
    def continue_with_expansion(self, approved_extra_fare):
        """Continue dispatch after customer approves expansion"""
        try:
            # Update ride with extra fare
            self.ride.extra_fare = approved_extra_fare
            self.ride.zone_expansion_approved = True
            
            # Calculate final fare
            self.ride.final_fare = (self.ride.fare_amount or 0) + approved_extra_fare
            
            db.session.commit()
            
            # Get next zones and try dispatch
            next_zones = Zone.get_next_zones_for_expansion(
                self.dispatch_zone,
                self.ride.pickup_lat,
                self.ride.pickup_lng
            )
            
            for zone_info in next_zones:
                zone = zone_info['zone']
                
                # Try dispatch in this zone
                drivers_in_zone = zone.get_drivers_in_ring(
                    1,  # Start from first ring in new zone
                    self.ride.pickup_lat,
                    self.ride.pickup_lng
                )
                
                # Filter available drivers
                available_drivers = [
                    d for d in drivers_in_zone 
                    if (d['driver'].id not in self.rejected_drivers and
                        d['driver'].car_type == self.ride.ride_type)
                ]
                
                if available_drivers:
                    driver = available_drivers[0]['driver']
                    
                    if self._is_driver_available(driver):
                        # Assign ride
                        self.ride.driver_id = driver.id
                        self.ride.dispatched_ring = 1
                        self.ride.status = 'assigned'
                        self.ride.assigned_time = datetime.now()
                        
                        db.session.commit()
                        
                        self._log_dispatch_event(f"Assigned to driver {driver.id} in expansion zone {zone.zone_name}")
                        
                        return {
                            'success': True,
                            'message': 'Driver assigned after zone expansion',
                            'driver_id': driver.id,
                            'expansion_zone': zone.zone_name,
                            'final_fare': self.ride.final_fare
                        }
            
            return {
                'success': False,
                'message': 'No drivers available even after expansion',
                'requires_manual_assignment': True
            }
            
        except Exception as e:
            logging.error(f"Error in expansion dispatch: {str(e)}")
            return {
                'success': False,
                'message': 'Error in expansion dispatch',
                'error': str(e)
            }
    
    def _is_driver_available(self, driver):
        """Check if driver is available for assignment"""
        return (driver.is_online and 
                driver.current_lat is not None and 
                driver.current_lng is not None and
                not driver.rides.filter_by(status='assigned').first() and
                not driver.rides.filter_by(status='active').first())
    
    def _no_zone_fallback(self):
        """Handle case where pickup location is not in any zone"""
        # Find nearest zone
        all_zones = Zone.query.filter_by(is_active=True).all()
        
        if not all_zones:
            return {
                'success': False,
                'message': 'No zones configured',
                'requires_manual_assignment': True
            }
        
        # Find closest zone
        closest_zone = None
        min_distance = float('inf')
        
        for zone in all_zones:
            distance = haversine_distance(
                self.ride.pickup_lat, self.ride.pickup_lng,
                zone.center_lat, zone.center_lng
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_zone = zone
        
        if closest_zone:
            self.dispatch_zone = closest_zone
            self.ride.dispatch_zone_id = closest_zone.id
            
            # Calculate extra fare for out-of-zone pickup
            from models import FareConfig
            fare_config = FareConfig.get_fare_for_ride_type(self.ride.ride_type)
            base_rate = fare_config.per_km_rate if fare_config else 8.0
            
            extra_fare = base_rate * min_distance
            
            return {
                'success': False,
                'message': 'Pickup location is outside service zones',
                'requires_customer_approval': True,
                'extra_fare': round(extra_fare, 2),
                'expansion_zone': closest_zone.zone_name,
                'expansion_distance': min_distance
            }
        
        return {
            'success': False,
            'message': 'No service zones available',
            'requires_manual_assignment': True
        }
    
    def _log_dispatch_event(self, message):
        """Log dispatch events for debugging"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'ring': self.current_ring,
            'zone': self.dispatch_zone.zone_name if self.dispatch_zone else None
        }
        
        self.dispatch_log.append(log_entry)
        logging.info(f"Dispatch [{self.ride_id}]: {message}")
    
    def add_rejected_driver(self, driver_id):
        """Add driver to rejected list"""
        self.rejected_drivers.add(driver_id)
        
        # Save rejection to database
        rejection = RideRejection(
            ride_id=self.ride_id,
            driver_phone=Driver.query.get(driver_id).phone
        )
        
        db.session.add(rejection)
        db.session.commit()
        
        self._log_dispatch_event(f"Driver {driver_id} rejected - adding to exclusion list")
    
    def get_dispatch_summary(self):
        """Get summary of dispatch attempts"""
        return {
            'ride_id': self.ride_id,
            'dispatch_zone': self.dispatch_zone.zone_name if self.dispatch_zone else None,
            'current_ring': self.current_ring,
            'rejected_drivers': len(self.rejected_drivers),
            'dispatch_log': self.dispatch_log
        }