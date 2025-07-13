"""
Routes package for A1 Taxi Hosur Dev
"""

from .auth import auth_bp
from .customer import customer_bp
from .driver import driver_bp
from .admin import admin_bp
from .booking import booking_bp
from .zone import zone_bp
from .fare import fare_bp

__all__ = ['auth_bp', 'customer_bp', 'driver_bp', 'admin_bp', 'booking_bp', 'zone_bp', 'fare_bp']