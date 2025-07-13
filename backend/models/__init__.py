"""
Models package for A1 Taxi Hosur Dev
"""

from app import db

# Import all models to ensure they're registered
from .user import User
from .driver_profile import DriverProfile
from .booking import Booking
from .fare_matrix import FareMatrix
from .zone import Zone

__all__ = ['User', 'DriverProfile', 'Booking', 'FareMatrix', 'Zone', 'db']