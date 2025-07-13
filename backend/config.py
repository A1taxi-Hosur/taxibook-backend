"""
Configuration settings for A1 Taxi Hosur Dev
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a1-taxi-hosur-dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///a1_taxi_hosur.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Application settings
    APP_NAME = "A1 Taxi Hosur Dev"
    APP_VERSION = "1.0.0"
    
    # Indian formatting
    CURRENCY_SYMBOL = "₹"
    DATE_FORMAT = "%d/%m/%Y"
    TIME_FORMAT = "%H:%M"
    DATETIME_FORMAT = "%d/%m/%Y %H:%M"
    
    # Dispatch settings
    INITIAL_DISPATCH_TIMEOUT = 15  # seconds
    DISPATCH_RADIUS_EXPANSION = [7, 10, 15]  # km
    RIDE_ACTIVATION_MINUTES = 30  # minutes before scheduled time
    
    # Zone settings
    OUT_OF_ZONE_RADIUS = 20  # km maximum search radius
    
    # Fare settings
    SURGE_MULTIPLIER_MAX = 3.0
    
    # Mobile number validation
    MOBILE_REGEX = r'^[6-9]\d{9}$'
    
    # Supported ride categories
    RIDE_CATEGORIES = ['regular', 'rental', 'outstation', 'airport']
    
    # Car types
    CAR_TYPES = ['hatchback', 'sedan', 'suv']
    
    # Airport restricted car types
    AIRPORT_CAR_TYPES = ['sedan', 'suv']
    
    # Booking statuses
    BOOKING_STATUSES = ['new', 'assigned', 'active', 'completed', 'cancelled']
    
    # User roles
    USER_ROLES = ['admin', 'customer', 'driver']