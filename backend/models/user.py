"""
User model for A1 Taxi Hosur Dev
Handles customers, drivers, and admin users
"""

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

class User(db.Model):
    """User model for all user types"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # admin, customer, driver
    name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(10), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    driver_profile = db.relationship('DriverProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    customer_bookings = db.relationship('Booking', foreign_keys='Booking.customer_id', backref='customer', lazy='dynamic')
    driver_bookings = db.relationship('Booking', foreign_keys='Booking.driver_id', backref='driver', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def validate_mobile_number(mobile_number):
        """Validate Indian mobile number format"""
        if not mobile_number:
            return False, "Mobile number is required"
        
        # Remove any spaces or special characters
        mobile_number = re.sub(r'[^\d]', '', mobile_number)
        
        # Check length and format
        if len(mobile_number) != 10:
            return False, "Mobile number must be 10 digits"
        
        # Check Indian mobile number pattern
        if not re.match(r'^[6-9]\d{9}$', mobile_number):
            return False, "Invalid Indian mobile number format"
        
        return True, mobile_number
    
    @staticmethod
    def create_user(role, name, mobile_number, password):
        """Create a new user with validation"""
        # Validate mobile number
        is_valid, result = User.validate_mobile_number(mobile_number)
        if not is_valid:
            return False, result
        
        mobile_number = result
        
        # Check if user already exists
        existing_user = User.query.filter_by(mobile_number=mobile_number).first()
        if existing_user:
            return False, "User with this mobile number already exists"
        
        # Validate role
        from config import Config
        if role not in Config.USER_ROLES:
            return False, "Invalid user role"
        
        # Create user
        user = User(
            role=role,
            name=name.strip(),
            mobile_number=mobile_number
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            return True, user
        except Exception as e:
            db.session.rollback()
            return False, f"Error creating user: {str(e)}"
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'role': self.role,
            'name': self.name,
            'mobile_number': self.mobile_number,
            'status': self.status,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'updated_at': self.updated_at.strftime('%d/%m/%Y %H:%M')
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data
    
    def __repr__(self):
        return f'<User {self.name} ({self.role})>'