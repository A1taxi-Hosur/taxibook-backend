"""
Fare Matrix model for A1 Taxi Hosur Dev
Admin-controlled fare structure for different ride types
"""

from app import db
from datetime import datetime

class FareMatrix(db.Model):
    """Fare matrix for different ride categories and car types"""
    
    __tablename__ = 'fare_matrix'
    
    id = db.Column(db.Integer, primary_key=True)
    ride_category = db.Column(db.String(20), nullable=False)  # regular, rental, outstation, airport
    car_type = db.Column(db.String(20), nullable=False)  # sedan, suv, hatchback
    base_fare = db.Column(db.Float, nullable=False)
    per_km = db.Column(db.Float, nullable=False, default=0.0)
    hourly = db.Column(db.Float, nullable=False, default=0.0)
    flat_rate = db.Column(db.Float, nullable=True)  # For fixed price rides
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint for ride_category and car_type combination
    __table_args__ = (
        db.UniqueConstraint('ride_category', 'car_type', name='unique_fare_category_car'),
    )
    
    def __init__(self, **kwargs):
        super(FareMatrix, self).__init__(**kwargs)
    
    @staticmethod
    def get_fare(ride_category, car_type):
        """Get fare for specific ride category and car type"""
        return FareMatrix.query.filter_by(
            ride_category=ride_category,
            car_type=car_type,
            is_active=True
        ).first()
    
    @staticmethod
    def create_default_fares():
        """Create default fare matrix"""
        default_fares = [
            # Regular rides
            {'ride_category': 'regular', 'car_type': 'hatchback', 'base_fare': 50.0, 'per_km': 8.0, 'hourly': 0.0},
            {'ride_category': 'regular', 'car_type': 'sedan', 'base_fare': 80.0, 'per_km': 12.0, 'hourly': 0.0},
            {'ride_category': 'regular', 'car_type': 'suv', 'base_fare': 120.0, 'per_km': 15.0, 'hourly': 0.0},
            
            # Rental rides (hourly)
            {'ride_category': 'rental', 'car_type': 'hatchback', 'base_fare': 100.0, 'per_km': 5.0, 'hourly': 80.0},
            {'ride_category': 'rental', 'car_type': 'sedan', 'base_fare': 150.0, 'per_km': 8.0, 'hourly': 120.0},
            {'ride_category': 'rental', 'car_type': 'suv', 'base_fare': 200.0, 'per_km': 10.0, 'hourly': 150.0},
            
            # Outstation rides
            {'ride_category': 'outstation', 'car_type': 'hatchback', 'base_fare': 200.0, 'per_km': 12.0, 'hourly': 0.0},
            {'ride_category': 'outstation', 'car_type': 'sedan', 'base_fare': 300.0, 'per_km': 15.0, 'hourly': 0.0},
            {'ride_category': 'outstation', 'car_type': 'suv', 'base_fare': 400.0, 'per_km': 18.0, 'hourly': 0.0},
            
            # Airport rides (flat rate)
            {'ride_category': 'airport', 'car_type': 'sedan', 'base_fare': 500.0, 'per_km': 0.0, 'hourly': 0.0, 'flat_rate': 500.0},
            {'ride_category': 'airport', 'car_type': 'suv', 'base_fare': 700.0, 'per_km': 0.0, 'hourly': 0.0, 'flat_rate': 700.0},
        ]
        
        try:
            for fare_data in default_fares:
                existing = FareMatrix.query.filter_by(
                    ride_category=fare_data['ride_category'],
                    car_type=fare_data['car_type']
                ).first()
                
                if not existing:
                    fare = FareMatrix(**fare_data)
                    db.session.add(fare)
            
            db.session.commit()
            return True, "Default fares created successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error creating default fares: {str(e)}"
    
    @staticmethod
    def update_fare(ride_category, car_type, base_fare, per_km, hourly, flat_rate=None):
        """Update fare for specific ride category and car type"""
        fare = FareMatrix.query.filter_by(
            ride_category=ride_category,
            car_type=car_type
        ).first()
        
        if not fare:
            # Create new fare if doesn't exist
            fare = FareMatrix(
                ride_category=ride_category,
                car_type=car_type,
                base_fare=base_fare,
                per_km=per_km,
                hourly=hourly,
                flat_rate=flat_rate
            )
            db.session.add(fare)
        else:
            # Update existing fare
            fare.base_fare = base_fare
            fare.per_km = per_km
            fare.hourly = hourly
            fare.flat_rate = flat_rate
            fare.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            return True, "Fare updated successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating fare: {str(e)}"
    
    def toggle_active(self):
        """Toggle fare active status"""
        self.is_active = not self.is_active
        
        try:
            db.session.commit()
            status = "activated" if self.is_active else "deactivated"
            return True, f"Fare {status} successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating fare status: {str(e)}"
    
    def to_dict(self):
        """Convert fare matrix to dictionary"""
        return {
            'id': self.id,
            'ride_category': self.ride_category,
            'car_type': self.car_type,
            'base_fare': self.base_fare,
            'per_km': self.per_km,
            'hourly': self.hourly,
            'flat_rate': self.flat_rate,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M')
        }
    
    def __repr__(self):
        return f'<FareMatrix {self.ride_category} {self.car_type}>'