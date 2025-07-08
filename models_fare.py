"""
Fare Management Models for TaxiBook
Handles fare configuration and calculation settings
"""

from app import db
from datetime import datetime
import pytz

def get_ist_time():
    """Get current time in IST timezone"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist)

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