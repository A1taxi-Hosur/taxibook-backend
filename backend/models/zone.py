"""
Zone model for A1 Taxi Hosur Dev
Service area management for driver dispatch
"""

from app import db
from datetime import datetime

class Zone(db.Model):
    """Service zones for geographic coverage"""
    
    __tablename__ = 'zones'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(100), unique=True, nullable=False)
    center_lat = db.Column(db.Float, nullable=False)
    center_lng = db.Column(db.Float, nullable=False)
    radius_km = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Zone, self).__init__(**kwargs)
    
    @staticmethod
    def create_zone(zone_name, center_lat, center_lng, radius_km):
        """Create a new service zone"""
        # Validate coordinates
        if not (-90 <= center_lat <= 90) or not (-180 <= center_lng <= 180):
            return False, "Invalid coordinates"
        
        if radius_km <= 0:
            return False, "Radius must be positive"
        
        # Check if zone name already exists
        existing_zone = Zone.query.filter_by(zone_name=zone_name).first()
        if existing_zone:
            return False, "Zone name already exists"
        
        zone = Zone(
            zone_name=zone_name,
            center_lat=center_lat,
            center_lng=center_lng,
            radius_km=radius_km
        )
        
        try:
            db.session.add(zone)
            db.session.commit()
            return True, zone
        except Exception as e:
            db.session.rollback()
            return False, f"Error creating zone: {str(e)}"
    
    def update_zone(self, zone_name=None, center_lat=None, center_lng=None, radius_km=None):
        """Update zone details"""
        if zone_name:
            # Check if new name conflicts with existing zone
            existing_zone = Zone.query.filter(
                Zone.zone_name == zone_name,
                Zone.id != self.id
            ).first()
            if existing_zone:
                return False, "Zone name already exists"
            self.zone_name = zone_name
        
        if center_lat is not None:
            if not (-90 <= center_lat <= 90):
                return False, "Invalid latitude"
            self.center_lat = center_lat
        
        if center_lng is not None:
            if not (-180 <= center_lng <= 180):
                return False, "Invalid longitude"
            self.center_lng = center_lng
        
        if radius_km is not None:
            if radius_km <= 0:
                return False, "Radius must be positive"
            self.radius_km = radius_km
        
        try:
            db.session.commit()
            return True, "Zone updated successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating zone: {str(e)}"
    
    def toggle_active(self):
        """Toggle zone active status"""
        self.is_active = not self.is_active
        
        # If deactivating zone, make all drivers in this zone unavailable
        if not self.is_active:
            for driver in self.drivers:
                driver.is_available = False
        
        try:
            db.session.commit()
            status = "activated" if self.is_active else "deactivated"
            return True, f"Zone {status} successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating zone status: {str(e)}"
    
    def get_drivers_in_zone(self, available_only=False):
        """Get all drivers in this zone"""
        from models.driver_profile import DriverProfile
        
        query = DriverProfile.query.filter_by(zone_id=self.id)
        
        if available_only:
            query = query.filter_by(is_available=True)
        
        return query.all()
    
    def to_dict(self):
        """Convert zone to dictionary"""
        return {
            'id': self.id,
            'zone_name': self.zone_name,
            'center_lat': self.center_lat,
            'center_lng': self.center_lng,
            'radius_km': self.radius_km,
            'is_active': self.is_active,
            'driver_count': len(self.drivers),
            'available_drivers': len([d for d in self.drivers if d.is_available]),
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M')
        }
    
    def __repr__(self):
        return f'<Zone {self.zone_name}>'