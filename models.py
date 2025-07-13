from app import db, get_ist_time
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func
import logging

class Customer(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=get_ist_time)
    
    # Relationship with rides
    rides = db.relationship('Ride', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Driver(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)  # Auto-generated username
    password_hash = db.Column(db.String(256), nullable=True)  # Hashed password
    is_online = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_ist_time)
    
    # Vehicle details
    car_make = db.Column(db.String(50), nullable=True)
    car_model = db.Column(db.String(50), nullable=True)
    car_year = db.Column(db.Integer, nullable=True)
    car_number = db.Column(db.String(20), nullable=True)
    car_type = db.Column(db.String(30), nullable=True)  # sedan, suv, hatchback, etc.
    
    # License and documents
    license_number = db.Column(db.String(20), nullable=True)
    aadhaar_url = db.Column(db.String(255), nullable=True)
    license_url = db.Column(db.String(255), nullable=True)
    rcbook_url = db.Column(db.String(255), nullable=True)
    profile_photo_url = db.Column(db.String(255), nullable=True)
    
    # Current location for proximity-based dispatch
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    location_updated_at = db.Column(db.DateTime, nullable=True)
    
    # Zone assignment
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True)
    out_of_zone = db.Column(db.Boolean, default=False)
    
    # Relationship with rides
    rides = db.relationship('Ride', backref='driver', lazy=True)
    
    def __repr__(self):
        return f'<Driver {self.name}>'
    
    def update_zone_assignment(self):
        """Update driver's zone assignment based on current location"""
        if self.current_lat is not None and self.current_lng is not None:
            zone = Zone.find_zone_for_location(self.current_lat, self.current_lng)
            if zone:
                self.zone_id = zone.id
                self.out_of_zone = False
            else:
                self.zone_id = None
                self.out_of_zone = True
        else:
            self.zone_id = None
            self.out_of_zone = True

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    name = db.Column(db.String(100), nullable=True)
    mobile_number = db.Column(db.String(10), unique=True, nullable=True)
    role = db.Column(db.String(20), default='admin')  # admin only for now
    firebase_token = db.Column(db.Text, nullable=True)  # FCM token
    created_at = db.Column(db.DateTime, default=get_ist_time)
    
    def __repr__(self):
        return f'<Admin {self.username}>'

class Ride(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Customer information
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer_phone = db.Column(db.String(10), nullable=False)
    
    # Driver information (nullable until assigned)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)
    
    # Ride details
    pickup_address = db.Column(db.Text, nullable=False)
    drop_address = db.Column(db.Text, nullable=False)
    pickup_lat = db.Column(db.Float, nullable=True)
    pickup_lng = db.Column(db.Float, nullable=True)
    drop_lat = db.Column(db.Float, nullable=True)
    drop_lng = db.Column(db.Float, nullable=True)
    
    # Fare and distance
    distance_km = db.Column(db.Float, nullable=True)
    fare_amount = db.Column(db.Float, nullable=False)
    final_fare = db.Column(db.Float, nullable=True)  # Frozen fare at booking time
    extra_fare = db.Column(db.Float, nullable=True)  # Zone expansion fee
    
    # Ride type (vehicle preference)
    ride_type = db.Column(db.String(20), nullable=True)  # hatchback, sedan, suv
    
    # Ride category
    ride_category = db.Column(db.String(20), default='regular')  # regular, airport, rental, outstation
    
    # Status tracking
    status = db.Column(db.String(20), default='new')  # new, assigned, active, completed, cancelled
    
    # Scheduled ride support
    scheduled_date = db.Column(db.Date, nullable=True)
    scheduled_time = db.Column(db.Time, nullable=True)
    
    # Admin assignment
    assigned_time = db.Column(db.DateTime, nullable=True)
    
    # Enhanced dispatch tracking
    dispatch_zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'), nullable=True)  # Initial zone
    dispatched_ring = db.Column(db.Integer, nullable=True)  # Ring number where driver was found
    zone_expansion_approved = db.Column(db.Boolean, default=False)  # Customer approval for expansion
    
    # OTP for ride start confirmation
    start_otp = db.Column(db.String(6), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_ist_time)
    accepted_at = db.Column(db.DateTime, nullable=True)
    arrived_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Ride {self.id} - {self.status}>'
    
    def to_dict(self, include_otp=False):
        """Convert ride to dictionary for API responses"""
        ride_data = {
            'id': self.id,
            'customer_phone': self.customer_phone,
            'customer_name': self.customer.name if self.customer else None,
            'pickup_address': self.pickup_address,
            'drop_address': self.drop_address,
            'pickup_lat': self.pickup_lat,
            'pickup_lng': self.pickup_lng,
            'drop_lat': self.drop_lat,
            'drop_lng': self.drop_lng,
            'distance_km': self.distance_km,
            'fare_amount': self.fare_amount,
            'ride_type': self.ride_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'arrived_at': self.arrived_at.isoformat() if self.arrived_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
        }
        
        # Include OTP for customer responses only when driver is assigned
        if include_otp and self.driver and self.start_otp:
            ride_data['start_otp'] = self.start_otp
        
        # Add driver details only when driver is assigned
        if self.driver:
            ride_data.update({
                'driver_name': self.driver.name,
                'driver_phone': self.driver.phone,
                'car_make': self.driver.car_make,
                'car_model': self.driver.car_model,
                'car_year': self.driver.car_year,
                'car_number': self.driver.car_number,
                'car_type': self.driver.car_type,
                'driver_photo_url': self.driver.profile_photo_url
            })
        else:
            # Set driver fields to None when no driver assigned
            ride_data.update({
                'driver_name': None,
                'driver_phone': None,
                'car_make': None,
                'car_model': None,
                'car_year': None,
                'car_number': None,
                'car_type': None,
                'driver_photo_url': None
            })
        
        return ride_data

class RideRejection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    driver_phone = db.Column(db.String(10), nullable=False)
    rejected_at = db.Column(db.DateTime, default=get_ist_time)
    
    def __repr__(self):
        return f'<RideRejection {self.ride_id} by {self.driver_phone}>'


class RideLocation(db.Model):
    """GPS tracking data for active rides"""
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('ride.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_ist_time, nullable=False)
    is_latest = db.Column(db.Boolean, default=False, nullable=False)  # Index for fast latest location lookup
    
    # Relationships
    ride = db.relationship('Ride', backref='locations', lazy=True)
    
    def __repr__(self):
        return f'<RideLocation {self.ride_id}: {self.latitude}, {self.longitude}>'
    
    def to_dict(self):
        """Convert location to dictionary for API responses"""
        return {
            'id': self.id,
            'ride_id': self.ride_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'timestamp': self.timestamp.isoformat(),
            'is_latest': self.is_latest
        }


class FareConfig(db.Model):
    """
    Fare configuration for different ride types
    Stores base fare, per-km rate, and surge multiplier
    """
    __tablename__ = 'fare_config'
    
    id = db.Column(db.Integer, primary_key=True)
    ride_type = db.Column(db.String(20), nullable=False, unique=True)  # hatchback, sedan, suv
    base_fare = db.Column(db.Float, nullable=False, default=20.0)  # Base fare in ₹
    per_km_rate = db.Column(db.Float, nullable=False, default=8.0)  # Per km rate in ₹
    surge_multiplier = db.Column(db.Float, nullable=False, default=1.0)  # Global surge multiplier
    
    # Metadata
    created_at = db.Column(db.DateTime, default=get_ist_time)
    updated_at = db.Column(db.DateTime, default=get_ist_time, onupdate=get_ist_time)
    
    def __repr__(self):
        return f'<FareConfig {self.ride_type}: ₹{self.base_fare} + ₹{self.per_km_rate}/km>'
    
    def to_dict(self):
        """Convert fare config to dictionary for API responses"""
        return {
            'id': self.id,
            'ride_type': self.ride_type,
            'base_fare': self.base_fare,
            'per_km_rate': self.per_km_rate,
            'surge_multiplier': self.surge_multiplier,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_fare_for_ride_type(ride_type):
        """Get fare configuration for a specific ride type"""
        return FareConfig.query.filter_by(ride_type=ride_type).first()
    
    @staticmethod
    def calculate_fare(ride_type, distance_km):
        """
        Calculate fare based on ride type and distance
        Returns (success, fare_amount, error_message)
        """
        try:
            fare_config = FareConfig.get_fare_for_ride_type(ride_type)
            if not fare_config:
                return False, 0, f"Fare configuration not found for ride type: {ride_type}"
            
            # Calculate base fare
            base_fare = fare_config.base_fare
            distance_fare = distance_km * fare_config.per_km_rate
            subtotal = base_fare + distance_fare
            
            # Apply surge multiplier
            total_fare = subtotal * fare_config.surge_multiplier
            
            return True, round(total_fare, 2), None
            
        except Exception as e:
            return False, 0, f"Error calculating fare: {str(e)}"
    
    @staticmethod
    def initialize_default_fares():
        """Initialize default fare configurations for all ride types"""
        default_fares = [
            {'ride_type': 'hatchback', 'base_fare': 20.0, 'per_km_rate': 8.0, 'surge_multiplier': 1.0},
            {'ride_type': 'sedan', 'base_fare': 25.0, 'per_km_rate': 10.0, 'surge_multiplier': 1.0},
            {'ride_type': 'suv', 'base_fare': 35.0, 'per_km_rate': 12.0, 'surge_multiplier': 1.0}
        ]
        
        for fare_data in default_fares:
            existing_config = FareConfig.query.filter_by(ride_type=fare_data['ride_type']).first()
            if not existing_config:
                config = FareConfig(
                    ride_type=fare_data['ride_type'],
                    base_fare=fare_data['base_fare'],
                    per_km_rate=fare_data['per_km_rate'],
                    surge_multiplier=fare_data['surge_multiplier']
                )
                db.session.add(config)
        
        db.session.commit()


class SpecialFareConfig(db.Model):
    """Special fare configuration for airport, rental, and outstation rides"""
    __tablename__ = 'special_fare_config'
    
    id = db.Column(db.Integer, primary_key=True)
    ride_category = db.Column(db.String(20), nullable=False)  # airport, rental, outstation
    ride_type = db.Column(db.String(20), nullable=False)  # sedan, suv, hatchback
    base_fare = db.Column(db.Float, nullable=False, default=50.0)
    per_km = db.Column(db.Float, nullable=True)  # Per km rate
    hourly = db.Column(db.Float, nullable=True)  # Hourly rate for rentals
    flat_rate = db.Column(db.Float, nullable=True)  # Flat rate for certain routes
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=get_ist_time)
    updated_at = db.Column(db.DateTime, default=get_ist_time, onupdate=get_ist_time)
    
    def __repr__(self):
        return f'<SpecialFareConfig {self.ride_category} - {self.ride_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ride_category': self.ride_category,
            'ride_type': self.ride_type,
            'base_fare': self.base_fare,
            'per_km': self.per_km,
            'hourly': self.hourly,
            'flat_rate': self.flat_rate,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def calculate_special_fare(ride_category, ride_type, distance_km=None, hours=None):
        """Calculate fare for special ride categories"""
        config = SpecialFareConfig.query.filter_by(
            ride_category=ride_category,
            ride_type=ride_type,
            is_active=True
        ).first()
        
        if not config:
            return False, None, f"No fare configuration found for {ride_category} - {ride_type}"
        
        fare_amount = config.base_fare
        
        # Apply flat rate if available
        if config.flat_rate:
            fare_amount = config.flat_rate
        else:
            # Add per-km cost if applicable
            if config.per_km and distance_km:
                fare_amount += (config.per_km * distance_km)
            
            # Add hourly cost if applicable
            if config.hourly and hours:
                fare_amount += (config.hourly * hours)
        
        return True, round(fare_amount, 2), None
    
    @staticmethod
    def initialize_default_special_fares():
        """Initialize default special fare configurations"""
        try:
            existing_configs = SpecialFareConfig.query.all()
            if existing_configs:
                logging.info("Special fare configurations already exist, skipping initialization")
                return
            
            # Default special fare configurations
            default_configs = [
                # Airport rides (sedan/suv only)
                {'ride_category': 'airport', 'ride_type': 'sedan', 'base_fare': 100.0, 'per_km': 15.0, 'is_active': True},
                {'ride_category': 'airport', 'ride_type': 'suv', 'base_fare': 150.0, 'per_km': 18.0, 'is_active': True},
                
                # Rental rides (all types)
                {'ride_category': 'rental', 'ride_type': 'sedan', 'base_fare': 200.0, 'hourly': 100.0, 'is_active': True},
                {'ride_category': 'rental', 'ride_type': 'suv', 'base_fare': 300.0, 'hourly': 150.0, 'is_active': True},
                {'ride_category': 'rental', 'ride_type': 'hatchback', 'base_fare': 150.0, 'hourly': 80.0, 'is_active': True},
                
                # Outstation rides (all types)
                {'ride_category': 'outstation', 'ride_type': 'sedan', 'base_fare': 300.0, 'per_km': 12.0, 'is_active': True},
                {'ride_category': 'outstation', 'ride_type': 'suv', 'base_fare': 400.0, 'per_km': 15.0, 'is_active': True},
                {'ride_category': 'outstation', 'ride_type': 'hatchback', 'base_fare': 250.0, 'per_km': 10.0, 'is_active': True},
            ]
            
            for config_data in default_configs:
                config = SpecialFareConfig(**config_data)
                db.session.add(config)
            
            db.session.commit()
            logging.info("Default special fare configurations initialized")
            
        except Exception as e:
            logging.error(f"Error initializing default special fares: {str(e)}")
            db.session.rollback()


class Zone(db.Model):
    """Enhanced Zone model with polygon support and concentric ring dispatch"""
    __tablename__ = 'zone'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(100), nullable=False, unique=True)
    
    # Polygon support
    polygon_coordinates = db.Column(db.JSON, nullable=True)  # List of [lat, lng] pairs
    
    # Center coordinates (auto-calculated from polygon or manually set)
    center_lat = db.Column(db.Float, nullable=False)
    center_lng = db.Column(db.Float, nullable=False)
    
    # Concentric ring dispatch settings
    number_of_rings = db.Column(db.Integer, nullable=False, default=3)  # 1-5 rings
    ring_radius_km = db.Column(db.Float, nullable=False, default=2.0)  # Radius per ring
    expansion_delay_sec = db.Column(db.Integer, nullable=False, default=15)  # Delay between rings
    
    # Legacy radius support for backward compatibility
    radius_km = db.Column(db.Float, nullable=False, default=5.0)
    
    # Zone priority for expansion logic
    priority_order = db.Column(db.Integer, nullable=False, default=1)  # Lower = higher priority
    
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=get_ist_time)
    updated_at = db.Column(db.DateTime, default=get_ist_time, onupdate=get_ist_time)
    
    # Relationship with drivers
    drivers = db.relationship('Driver', backref='zone', lazy=True)
    
    def __repr__(self):
        return f'<Zone {self.zone_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'polygon_coordinates': self.polygon_coordinates,
            'center_lat': self.center_lat,
            'center_lng': self.center_lng,
            'number_of_rings': self.number_of_rings,
            'ring_radius_km': self.ring_radius_km,
            'expansion_delay_sec': self.expansion_delay_sec,
            'radius_km': self.radius_km,
            'priority_order': self.priority_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_point_in_zone(self, lat, lng):
        """Check if a point is inside the zone (polygon or circle)"""
        if self.polygon_coordinates:
            return self._is_point_in_polygon(lat, lng, self.polygon_coordinates)
        else:
            # Fallback to circular zone
            from utils.distance import haversine_distance
            distance = haversine_distance(lat, lng, self.center_lat, self.center_lng)
            return distance <= self.radius_km
    
    def _is_point_in_polygon(self, lat, lng, polygon):
        """Ray casting algorithm to check if point is inside polygon"""
        x, y = lng, lat
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0][1], polygon[0][0]  # polygon format is [lat, lng]
        
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n][1], polygon[i % n][0]
            
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def get_ring_radius(self, ring_number):
        """Get radius for a specific ring (1-based indexing)"""
        return self.ring_radius_km * ring_number
    
    def get_drivers_in_ring(self, ring_number, pickup_lat, pickup_lng):
        """Get available drivers within a specific ring"""
        from utils.distance import haversine_distance
        
        ring_radius = self.get_ring_radius(ring_number)
        available_drivers = []
        
        for driver in self.drivers:
            if (driver.is_online and 
                driver.current_lat is not None and 
                driver.current_lng is not None):
                
                distance = haversine_distance(
                    pickup_lat, pickup_lng, 
                    driver.current_lat, driver.current_lng
                )
                
                if distance <= ring_radius:
                    available_drivers.append({
                        'driver': driver,
                        'distance': distance
                    })
        
        # Sort by distance
        available_drivers.sort(key=lambda x: x['distance'])
        return available_drivers
    
    @staticmethod
    def find_zone_for_location(lat, lng):
        """Find zone for given coordinates using polygon or circular matching"""
        zones = Zone.query.filter_by(is_active=True).order_by(Zone.priority_order).all()
        
        for zone in zones:
            if zone.is_point_in_zone(lat, lng):
                return zone
        
        return None
    
    @staticmethod
    def get_next_zones_for_expansion(current_zone, pickup_lat, pickup_lng):
        """Get next zones for expansion ordered by priority and distance"""
        from utils.distance import haversine_distance
        
        other_zones = Zone.query.filter(
            Zone.is_active == True,
            Zone.id != current_zone.id
        ).order_by(Zone.priority_order).all()
        
        # Calculate distances and sort
        zone_distances = []
        for zone in other_zones:
            distance = haversine_distance(
                pickup_lat, pickup_lng,
                zone.center_lat, zone.center_lng
            )
            zone_distances.append({
                'zone': zone,
                'distance': distance
            })
        
        # Sort by priority first, then by distance
        zone_distances.sort(key=lambda x: (x['zone'].priority_order, x['distance']))
        return zone_distances
    
    @staticmethod
    def initialize_default_zones():
        """Initialize default zones"""
        try:
            existing_zones = Zone.query.all()
            if existing_zones:
                logging.info("Zones already exist, skipping initialization")
                return
            
            # Default zones for major areas
            default_zones = [
                {'zone_name': 'Chennai Central', 'center_lat': 13.0827, 'center_lng': 80.2707, 'radius_km': 5.0},
                {'zone_name': 'Anna Nagar', 'center_lat': 13.0850, 'center_lng': 80.2101, 'radius_km': 4.0},
                {'zone_name': 'T.Nagar', 'center_lat': 13.0435, 'center_lng': 80.2339, 'radius_km': 3.0},
                {'zone_name': 'Velachery', 'center_lat': 12.9755, 'center_lng': 80.2201, 'radius_km': 4.0},
                {'zone_name': 'Airport', 'center_lat': 12.9941, 'center_lng': 80.1709, 'radius_km': 8.0},
            ]
            
            for zone_data in default_zones:
                zone = Zone(**zone_data)
                db.session.add(zone)
            
            db.session.commit()
            logging.info("Default zones initialized")
            
        except Exception as e:
            logging.error(f"Error initializing default zones: {str(e)}")
            db.session.rollback()
