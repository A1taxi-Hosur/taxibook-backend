"""
Driver Profile model for A1 Taxi Hosur Dev
Extended driver information and location tracking
"""

from app import db
from datetime import datetime

class DriverProfile(db.Model):
    """Driver profile with vehicle and location information"""
    
    __tablename__ = 'driver_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    car_type = db.Column(db.String(20), nullable=False)  # sedan, suv, hatchback
    car_number = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(100), nullable=True)
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=True)
    is_available = db.Column(db.Boolean, default=False)
    last_location_update = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    zone = db.relationship('Zone', backref='drivers')
    
    def __init__(self, **kwargs):
        super(DriverProfile, self).__init__(**kwargs)
    
    def update_location(self, lat, lng):
        """Update driver's current location"""
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            return False, "Invalid coordinates"
        
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return False, "Coordinates out of range"
        
        self.current_lat = lat
        self.current_lng = lng
        self.last_location_update = datetime.utcnow()
        
        # Update zone assignment
        self.assign_zone()
        
        try:
            db.session.commit()
            return True, "Location updated successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating location: {str(e)}"
    
    def assign_zone(self):
        """Assign driver to appropriate zone based on location"""
        if not self.current_lat or not self.current_lng:
            self.zone_id = None
            return
        
        from models.zone import Zone
        from utils.geo import calculate_distance
        
        # Find all zones
        zones = Zone.query.all()
        
        # Find the closest zone that contains the driver
        closest_zone = None
        min_distance = float('inf')
        
        for zone in zones:
            distance = calculate_distance(
                self.current_lat, self.current_lng,
                zone.center_lat, zone.center_lng
            )
            
            if distance <= zone.radius_km and distance < min_distance:
                closest_zone = zone
                min_distance = distance
        
        self.zone_id = closest_zone.id if closest_zone else None
        
        # If no zone assigned, mark as unavailable
        if not self.zone_id:
            self.is_available = False
    
    def toggle_availability(self):
        """Toggle driver availability"""
        if not self.zone_id:
            return False, "Driver must be in a service zone to go online"
        
        self.is_available = not self.is_available
        
        try:
            db.session.commit()
            status = "online" if self.is_available else "offline"
            return True, f"Driver is now {status}"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating availability: {str(e)}"
    
    @staticmethod
    def create_profile(user_id, car_type, car_number, license_number, company_name=None):
        """Create a new driver profile"""
        from config import Config
        
        # Validate car type
        if car_type not in Config.CAR_TYPES:
            return False, "Invalid car type"
        
        # Check if profile already exists
        existing_profile = DriverProfile.query.filter_by(user_id=user_id).first()
        if existing_profile:
            return False, "Driver profile already exists"
        
        # Create profile
        profile = DriverProfile(
            user_id=user_id,
            car_type=car_type,
            car_number=car_number.upper(),
            license_number=license_number.upper(),
            company_name=company_name
        )
        
        try:
            db.session.add(profile)
            db.session.commit()
            return True, profile
        except Exception as e:
            db.session.rollback()
            return False, f"Error creating profile: {str(e)}"
    
    def to_dict(self):
        """Convert driver profile to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'car_type': self.car_type,
            'car_number': self.car_number,
            'license_number': self.license_number,
            'company_name': self.company_name,
            'current_lat': self.current_lat,
            'current_lng': self.current_lng,
            'zone_id': self.zone_id,
            'zone_name': self.zone.zone_name if self.zone else None,
            'is_available': self.is_available,
            'last_location_update': self.last_location_update.strftime('%d/%m/%Y %H:%M') if self.last_location_update else None,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M')
        }
    
    def __repr__(self):
        return f'<DriverProfile {self.car_number} ({self.car_type})>'