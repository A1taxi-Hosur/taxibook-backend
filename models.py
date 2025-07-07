from app import db, get_ist_time
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import func

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
    
    # Relationship with rides
    rides = db.relationship('Ride', backref='driver', lazy=True)
    
    def __repr__(self):
        return f'<Driver {self.name}>'

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
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
    
    # Ride type (vehicle preference)
    ride_type = db.Column(db.String(20), nullable=True)  # hatchback, sedan, suv
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, accepted, arrived, started, completed, cancelled
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_ist_time)
    accepted_at = db.Column(db.DateTime, nullable=True)
    arrived_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Ride {self.id} - {self.status}>'
    
    def to_dict(self):
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
