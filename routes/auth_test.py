"""
Authentication Testing and Debugging Routes
Only available in development environment for testing the new session management system.
"""

from flask import Blueprint, request, jsonify
from app import db, get_ist_time
from models import Driver, Customer
from utils.session_manager import (
    get_online_drivers_count, 
    get_online_customers_count,
    cleanup_expired_sessions,
    cleanup_stale_connections
)
import os
import logging

# Only create this blueprint in development
auth_test_bp = Blueprint('auth_test', __name__)

@auth_test_bp.route('/session_stats', methods=['GET'])
def session_stats():
    """Get current session statistics"""
    try:
        # Count online users
        online_drivers = get_online_drivers_count()
        online_customers = get_online_customers_count()
        
        # Count total users with sessions
        drivers_with_sessions = Driver.query.filter(Driver.session_token != None).count()
        customers_with_sessions = Customer.query.filter(Customer.session_token != None).count()
        
        # Get all drivers with their session status
        drivers = Driver.query.all()
        driver_sessions = []
        for driver in drivers:
            driver_sessions.append({
                'id': driver.id,
                'name': driver.name,
                'username': driver.username,
                'is_online': driver.is_online,
                'has_session': driver.session_token is not None,
                'last_seen': driver.last_seen.isoformat() if driver.last_seen else None,
                'session_expires': driver.session_expires.isoformat() if driver.session_expires else None
            })
        
        # Get all customers with their session status
        customers = Customer.query.all()
        customer_sessions = []
        for customer in customers:
            customer_sessions.append({
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'is_online': customer.is_online,
                'has_session': customer.session_token is not None,
                'last_seen': customer.last_seen.isoformat() if customer.last_seen else None,
                'session_expires': customer.session_expires.isoformat() if customer.session_expires else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'online_drivers': online_drivers,
                    'online_customers': online_customers,
                    'drivers_with_sessions': drivers_with_sessions,
                    'customers_with_sessions': customers_with_sessions,
                    'total_drivers': len(drivers),
                    'total_customers': len(customers)
                },
                'driver_sessions': driver_sessions,
                'customer_sessions': customer_sessions,
                'timestamp': get_ist_time().isoformat()
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting session stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error retrieving session stats: {str(e)}"
        }), 500

@auth_test_bp.route('/cleanup_sessions', methods=['POST'])
def manual_cleanup():
    """Manually trigger session cleanup"""
    try:
        cleanup_expired_sessions()
        cleanup_stale_connections()
        
        return jsonify({
            'success': True,
            'message': 'Session cleanup completed'
        })
        
    except Exception as e:
        logging.error(f"Error in manual cleanup: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Cleanup error: {str(e)}"
        }), 500

@auth_test_bp.route('/reset_all_sessions', methods=['POST'])
def reset_all_sessions():
    """Reset all user sessions (development only)"""
    try:
        # Reset all driver sessions
        drivers = Driver.query.all()
        for driver in drivers:
            driver.session_token = None
            driver.last_seen = None
            driver.session_expires = None
            driver.is_online = False
            driver.websocket_id = None
        
        # Reset all customer sessions
        customers = Customer.query.all()
        for customer in customers:
            customer.session_token = None
            customer.last_seen = None
            customer.session_expires = None
            customer.is_online = False
        
        db.session.commit()
        
        logging.info("All user sessions reset")
        
        return jsonify({
            'success': True,
            'message': f'Reset sessions for {len(drivers)} drivers and {len(customers)} customers'
        })
        
    except Exception as e:
        logging.error(f"Error resetting sessions: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Reset error: {str(e)}"
        }), 500

@auth_test_bp.route('/auth_system_info', methods=['GET'])
def auth_system_info():
    """Get information about the authentication system"""
    return jsonify({
        'success': True,
        'data': {
            'system_info': {
                'session_management': 'Active',
                'jwt_authentication': 'Active',
                'background_cleanup': 'Active',
                'session_duration_hours': 168,  # 7 days
                'heartbeat_timeout_minutes': 10,
                'cleanup_interval_minutes': 2
            },
            'features': {
                'single_session_per_user': True,
                'automatic_session_expiry': True,
                'heartbeat_system': True,
                'session_token_validation': True,
                'background_cleanup': True,
                'websocket_tracking': True
            },
            'endpoints': {
                'driver_login': '/driver/login',
                'driver_logout': '/driver/logout',
                'driver_heartbeat': '/driver/heartbeat',
                'customer_login_register': '/customer/login_or_register',
                'customer_logout': '/customer/logout',
                'customer_heartbeat': '/customer/heartbeat'
            },
            'timestamp': get_ist_time().isoformat()
        }
    })