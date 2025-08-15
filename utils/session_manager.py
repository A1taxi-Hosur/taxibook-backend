"""
Session Management Utilities for A1 Call Taxi
Handles session creation, validation, and cleanup for both drivers and customers.
"""

import secrets
import string
from datetime import datetime, timedelta
from app import db, get_ist_time
from models import Driver, Customer
import logging

# Session configuration - More lenient settings to keep drivers online longer
SESSION_DURATION_HOURS = 24 * 7  # 7 days
HEARTBEAT_TIMEOUT_MINUTES = 30  # Mark offline if no activity for 30 minutes (was 10)

def generate_session_token():
    """Generate a secure random session token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))

def create_driver_session(driver):
    """Create a new session for driver, invalidating any existing sessions"""
    # Invalidate any existing sessions
    invalidate_driver_sessions(driver.id)
    
    # Create new session
    session_token = generate_session_token()
    now = get_ist_time()
    expires = now + timedelta(hours=SESSION_DURATION_HOURS)
    
    driver.session_token = session_token
    driver.last_seen = now
    driver.session_expires = expires
    driver.is_online = True
    
    db.session.commit()
    logging.info(f"Created new session for driver {driver.name} (ID: {driver.id})")
    
    return session_token

def create_customer_session(customer):
    """Create a new session for customer, invalidating any existing sessions"""
    # Invalidate any existing sessions
    invalidate_customer_sessions(customer.id)
    
    # Create new session
    session_token = generate_session_token()
    now = get_ist_time()
    expires = now + timedelta(hours=SESSION_DURATION_HOURS)
    
    customer.session_token = session_token
    customer.last_seen = now
    customer.session_expires = expires
    customer.is_online = True
    
    db.session.commit()
    logging.info(f"Created new session for customer {customer.name} (ID: {customer.id})")
    
    return session_token

def validate_driver_session(session_token):
    """Validate driver session token and return driver if valid"""
    if not session_token:
        return None
    
    driver = Driver.query.filter_by(session_token=session_token).first()
    if not driver:
        return None
    
    # Check if session expired
    now = get_ist_time()
    if not driver.session_expires or now >= driver.session_expires:
        # Session expired, mark offline
        invalidate_driver_sessions(driver.id)
        return None
    
    # Update last seen
    driver.last_seen = now
    db.session.commit()
    
    return driver

def validate_customer_session(session_token):
    """Validate customer session token and return customer if valid"""
    if not session_token:
        return None
    
    customer = Customer.query.filter_by(session_token=session_token).first()
    if not customer:
        return None
    
    # Check if session expired
    now = get_ist_time()
    if not customer.session_expires or now >= customer.session_expires:
        # Session expired, mark offline
        invalidate_customer_sessions(customer.id)
        return None
    
    # Update last seen
    customer.last_seen = now
    db.session.commit()
    
    return customer

def invalidate_driver_sessions(driver_id):
    """Invalidate all sessions for a driver"""
    driver = Driver.query.get(driver_id)
    if driver:
        driver.session_token = None
        driver.last_seen = None
        driver.session_expires = None
        driver.is_online = False
        driver.websocket_id = None
        db.session.commit()
        logging.info(f"Invalidated sessions for driver {driver.name} (ID: {driver_id})")

def invalidate_customer_sessions(customer_id):
    """Invalidate all sessions for a customer"""
    customer = Customer.query.get(customer_id)
    if customer:
        customer.session_token = None
        customer.last_seen = None
        customer.session_expires = None
        customer.is_online = False
        db.session.commit()
        logging.info(f"Invalidated sessions for customer {customer.name} (ID: {customer_id})")

def cleanup_expired_sessions():
    """Background task to cleanup expired sessions"""
    now = get_ist_time()
    
    # Find expired driver sessions
    expired_drivers = Driver.query.filter(
        Driver.session_expires != None,
        Driver.session_expires < now,
        Driver.is_online == True
    ).all()
    
    for driver in expired_drivers:
        invalidate_driver_sessions(driver.id)
    
    # Find expired customer sessions
    expired_customers = Customer.query.filter(
        Customer.session_expires != None,
        Customer.session_expires < now,
        Customer.is_online == True
    ).all()
    
    for customer in expired_customers:
        invalidate_customer_sessions(customer.id)
    
    if expired_drivers or expired_customers:
        logging.info(f"Cleaned up {len(expired_drivers)} expired driver sessions and {len(expired_customers)} expired customer sessions")

def cleanup_stale_connections():
    """Mark users offline if they haven't been seen recently (no heartbeat)"""
    # TEMPORARILY DISABLED FOR TESTING
    return
    now = get_ist_time()
    stale_threshold = now - timedelta(minutes=HEARTBEAT_TIMEOUT_MINUTES)
    
    # Find stale drivers
    stale_drivers = Driver.query.filter(
        Driver.is_online == True,
        Driver.last_seen != None,
        Driver.last_seen < stale_threshold
    ).all()
    
    for driver in stale_drivers:
        driver.is_online = False
        logging.info(f"Marked driver {driver.name} offline due to inactivity")
    
    # Find stale customers
    stale_customers = Customer.query.filter(
        Customer.is_online == True,
        Customer.last_seen != None,
        Customer.last_seen < stale_threshold
    ).all()
    
    for customer in stale_customers:
        customer.is_online = False
        logging.info(f"Marked customer {customer.name} offline due to inactivity")
    
    if stale_drivers or stale_customers:
        db.session.commit()
        logging.info(f"Marked {len(stale_drivers)} drivers and {len(stale_customers)} customers offline due to inactivity")

def update_driver_heartbeat(driver_id):
    """Update driver's last seen timestamp (heartbeat) - More lenient validation"""
    driver = Driver.query.get(driver_id)
    if driver:
        # Update heartbeat even if driver appears offline due to stale connection
        # This helps keep drivers online who have temporary network issues
        driver.last_seen = get_ist_time()
        
        # If driver has a session token, make sure they're marked online
        if driver.session_token:
            driver.is_online = True
            
        db.session.commit()
        logging.debug(f"Updated heartbeat for driver {driver.name} - marked online: {driver.is_online}")
        return True
    return False

def update_customer_heartbeat(customer_id):
    """Update customer's last seen timestamp (heartbeat)"""
    customer = Customer.query.get(customer_id)
    if customer and customer.is_online:
        customer.last_seen = get_ist_time()
        db.session.commit()
        return True
    return False

def get_online_drivers_count():
    """Get count of actually online drivers with valid sessions"""
    now = get_ist_time()
    return Driver.query.filter(
        Driver.is_online == True,
        Driver.session_expires != None,
        Driver.session_expires > now
    ).count()

def get_online_customers_count():
    """Get count of actually online customers with valid sessions"""
    now = get_ist_time()
    return Customer.query.filter(
        Customer.is_online == True,
        Customer.session_expires != None,
        Customer.session_expires > now
    ).count()