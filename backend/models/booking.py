"""
Booking model for A1 Taxi Hosur Dev
Handles all ride bookings and their lifecycle
"""

from app import db
from datetime import datetime, timedelta
import json

class Booking(db.Model):
    """Booking model for all ride types"""
    
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ride_category = db.Column(db.String(20), nullable=False)  # regular, rental, outstation, airport
    car_type = db.Column(db.String(20), nullable=False)  # sedan, suv, hatchback
    pickup_address = db.Column(db.Text, nullable=False)
    drop_address = db.Column(db.Text, nullable=True)  # Optional for rentals
    pickup_lat = db.Column(db.Float, nullable=True)
    pickup_lng = db.Column(db.Float, nullable=True)
    drop_lat = db.Column(db.Float, nullable=True)
    drop_lng = db.Column(db.Float, nullable=True)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time, nullable=False)
    assigned_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='new')  # new, assigned, active, completed, cancelled
    final_fare = db.Column(db.Float, nullable=False)
    surge_multiplier = db.Column(db.Float, default=1.0)
    additional_info = db.Column(db.Text, nullable=True)  # JSON string for extra details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(Booking, self).__init__(**kwargs)
    
    @staticmethod
    def create_booking(customer_id, ride_category, car_type, pickup_address, 
                      scheduled_date, scheduled_time, drop_address=None,
                      pickup_lat=None, pickup_lng=None, drop_lat=None, drop_lng=None,
                      additional_info=None):
        """Create a new booking with fare calculation"""
        from config import Config
        from models.fare_matrix import FareMatrix
        from models.zone import Zone
        from utils.geo import calculate_distance, is_point_in_zone
        
        # Validate ride category
        if ride_category not in Config.RIDE_CATEGORIES:
            return False, "Invalid ride category"
        
        # Validate car type
        if car_type not in Config.CAR_TYPES:
            return False, "Invalid car type"
        
        # Airport rides restricted to sedan/suv
        if ride_category == 'airport' and car_type not in Config.AIRPORT_CAR_TYPES:
            return False, "Airport rides are only available for Sedan and SUV"
        
        # Check if pickup is in service zone
        if pickup_lat and pickup_lng:
            zones = Zone.query.all()
            in_service_area = False
            
            for zone in zones:
                if is_point_in_zone(pickup_lat, pickup_lng, zone.center_lat, zone.center_lng, zone.radius_km):
                    in_service_area = True
                    break
            
            if not in_service_area:
                return False, "We are not operating in this area"
        
        # Calculate fare
        fare_matrix = FareMatrix.get_fare(ride_category, car_type)
        if not fare_matrix:
            return False, "Fare not available for this ride type"
        
        # Calculate distance-based fare if drop location provided
        calculated_fare = fare_matrix.base_fare
        
        if drop_lat and drop_lng and pickup_lat and pickup_lng:
            distance_km = calculate_distance(pickup_lat, pickup_lng, drop_lat, drop_lng)
            calculated_fare = fare_matrix.base_fare + (distance_km * fare_matrix.per_km)
        elif fare_matrix.flat_rate:
            calculated_fare = fare_matrix.flat_rate
        
        # Create booking
        booking = Booking(
            customer_id=customer_id,
            ride_category=ride_category,
            car_type=car_type,
            pickup_address=pickup_address,
            drop_address=drop_address,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            drop_lat=drop_lat,
            drop_lng=drop_lng,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            final_fare=calculated_fare,
            additional_info=json.dumps(additional_info) if additional_info else None
        )
        
        try:
            db.session.add(booking)
            db.session.commit()
            return True, booking
        except Exception as e:
            db.session.rollback()
            return False, f"Error creating booking: {str(e)}"
    
    def assign_driver(self, driver_id):
        """Assign driver to booking"""
        if self.status != 'new':
            return False, "Booking cannot be assigned"
        
        # Verify driver exists and is a driver
        from models.user import User
        driver = User.query.filter_by(id=driver_id, role='driver').first()
        if not driver:
            return False, "Driver not found"
        
        self.driver_id = driver_id
        self.status = 'assigned'
        self.assigned_time = datetime.utcnow()
        
        try:
            db.session.commit()
            return True, "Driver assigned successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error assigning driver: {str(e)}"
    
    def activate_ride(self):
        """Activate ride when it's time to start"""
        if self.status != 'assigned':
            return False, "Ride cannot be activated"
        
        # Check if it's within 30 minutes of scheduled time
        scheduled_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        activation_time = scheduled_datetime - timedelta(minutes=30)
        
        if datetime.utcnow() < activation_time:
            return False, "Ride cannot be activated yet"
        
        self.status = 'active'
        
        try:
            db.session.commit()
            return True, "Ride activated successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error activating ride: {str(e)}"
    
    def complete_ride(self):
        """Complete the ride"""
        if self.status != 'active':
            return False, "Ride cannot be completed"
        
        self.status = 'completed'
        
        try:
            db.session.commit()
            return True, "Ride completed successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error completing ride: {str(e)}"
    
    def cancel_ride(self):
        """Cancel the ride"""
        if self.status in ['completed']:
            return False, "Completed rides cannot be cancelled"
        
        self.status = 'cancelled'
        
        try:
            db.session.commit()
            return True, "Ride cancelled successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error cancelling ride: {str(e)}"
    
    def get_additional_info(self):
        """Get additional info as dictionary"""
        if self.additional_info:
            try:
                return json.loads(self.additional_info)
            except:
                return {}
        return {}
    
    def to_dict(self):
        """Convert booking to dictionary"""
        scheduled_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        
        data = {
            'id': self.id,
            'customer_id': self.customer_id,
            'driver_id': self.driver_id,
            'ride_category': self.ride_category,
            'car_type': self.car_type,
            'pickup_address': self.pickup_address,
            'drop_address': self.drop_address,
            'pickup_lat': self.pickup_lat,
            'pickup_lng': self.pickup_lng,
            'drop_lat': self.drop_lat,
            'drop_lng': self.drop_lng,
            'booking_time': self.booking_time.strftime('%d/%m/%Y %H:%M'),
            'scheduled_date': self.scheduled_date.strftime('%d/%m/%Y'),
            'scheduled_time': self.scheduled_time.strftime('%H:%M'),
            'scheduled_datetime': scheduled_datetime.strftime('%d/%m/%Y %H:%M'),
            'assigned_time': self.assigned_time.strftime('%d/%m/%Y %H:%M') if self.assigned_time else None,
            'status': self.status,
            'final_fare': self.final_fare,
            'surge_multiplier': self.surge_multiplier,
            'additional_info': self.get_additional_info(),
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M')
        }
        
        # Add customer details
        if self.customer:
            data['customer'] = {
                'id': self.customer.id,
                'name': self.customer.name,
                'mobile_number': self.customer.mobile_number
            }
        
        # Add driver details
        if self.driver:
            data['driver'] = {
                'id': self.driver.id,
                'name': self.driver.name,
                'mobile_number': self.driver.mobile_number
            }
            
            if self.driver.driver_profile:
                data['driver'].update({
                    'car_type': self.driver.driver_profile.car_type,
                    'car_number': self.driver.driver_profile.car_number,
                    'company_name': self.driver.driver_profile.company_name
                })
        
        return data
    
    def __repr__(self):
        return f'<Booking {self.id} ({self.ride_category} - {self.status})>'