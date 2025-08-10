# Additional admin API endpoints for history and analytics

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db, get_ist_time
from models import Ride, Customer, Driver
from utils.validators import create_error_response, create_success_response
import logging
from datetime import datetime, timedelta

# This will be imported into the main admin blueprint

def setup_history_routes(admin_bp):
    """Setup history and analytics routes for admin panel"""
    
    @admin_bp.route('/api/history', methods=['GET'])
    @login_required
    def api_get_ride_history():
        """API endpoint to get ride history with filters"""
        try:
            # Get filter parameters
            status_filter = request.args.get('status', 'all')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            customer_phone = request.args.get('customer_phone')
            driver_id = request.args.get('driver_id')
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            
            # Build query
            query = Ride.query
            
            # Apply filters
            if status_filter != 'all':
                query = query.filter_by(status=status_filter)
            
            if customer_phone:
                query = query.filter(Ride.customer_phone.like(f'%{customer_phone}%'))
            
            if driver_id:
                query = query.filter_by(driver_id=driver_id)
            
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, '%Y-%m-%d')
                    query = query.filter(Ride.created_at >= from_date)
                except ValueError:
                    logging.warning(f"Invalid date_from format: {date_from}")
            
            if date_to:
                try:
                    to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                    query = query.filter(Ride.created_at <= to_date)
                except ValueError:
                    logging.warning(f"Invalid date_to format: {date_to}")
            
            # Order by newest first and paginate
            paginated_rides = query.order_by(Ride.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # Convert to dictionaries
            history_data = []
            for ride in paginated_rides.items:
                try:
                    ride_dict = {
                        'id': ride.id,
                        'customer_phone': ride.customer_phone or '',
                        'pickup_address': ride.pickup_address or '',
                        'drop_address': ride.drop_address or '',
                        'status': ride.status or 'new',
                        'ride_type': ride.ride_type or 'sedan',
                        'ride_category': ride.ride_category or 'regular',
                        'fare_amount': float(ride.fare_amount) if ride.fare_amount else 0.0,
                        'final_fare': float(ride.final_fare) if ride.final_fare else 0.0,
                        'distance_km': float(ride.distance_km) if ride.distance_km else 0.0,
                        'created_at': ride.created_at.isoformat() if ride.created_at else None,
                        'accepted_at': ride.accepted_at.isoformat() if ride.accepted_at else None,
                        'completed_at': ride.completed_at.isoformat() if ride.completed_at else None,
                        'cancelled_at': ride.cancelled_at.isoformat() if ride.cancelled_at else None,
                        'customer_name': ride.customer.name if ride.customer else 'Unknown',
                        'driver_name': ride.driver.name if ride.driver else 'Not Assigned'
                    }
                    history_data.append(ride_dict)
                except Exception as ride_error:
                    logging.error(f"Error processing ride {ride.id} in history: {str(ride_error)}")
            
            # Calculate statistics
            total_rides = query.count()
            completed_rides = query.filter_by(status='completed').count()
            cancelled_rides = query.filter_by(status='cancelled').count()
            pending_rides = query.filter(Ride.status.in_(['new', 'pending', 'accepted', 'arrived', 'started'])).count()
            
            logging.info(f"Retrieved {len(history_data)} rides for history page")
            
            return create_success_response({
                'rides': history_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': paginated_rides.total,
                    'pages': paginated_rides.pages,
                    'has_next': paginated_rides.has_next,
                    'has_prev': paginated_rides.has_prev
                },
                'statistics': {
                    'total_rides': total_rides,
                    'completed_rides': completed_rides,
                    'cancelled_rides': cancelled_rides,
                    'pending_rides': pending_rides
                }
            })
        
        except Exception as e:
            logging.error(f"Error getting ride history: {str(e)}")
            return create_error_response("Failed to retrieve ride history")
    
    @admin_bp.route('/api/analytics/summary', methods=['GET'])
    @login_required
    def api_analytics_summary():
        """API endpoint to get analytics summary for dashboard"""
        try:
            # Get date range (default to last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Basic counts
            total_customers = Customer.query.count()
            total_drivers = Driver.query.count()
            active_drivers = Driver.query.filter_by(is_online=True).count()
            
            # Ride statistics
            total_rides = Ride.query.count()
            completed_rides = Ride.query.filter_by(status='completed').count()
            ongoing_rides = Ride.query.filter(Ride.status.in_(['accepted', 'arrived', 'started'])).count()
            pending_rides = Ride.query.filter(Ride.status.in_(['new', 'pending'])).count()
            
            # Recent rides (last 30 days)
            recent_rides = Ride.query.filter(
                Ride.created_at >= start_date
            ).count()
            
            # Revenue calculation (completed rides only)
            revenue_query = db.session.query(db.func.sum(Ride.final_fare)).filter(
                Ride.status == 'completed',
                Ride.final_fare.isnot(None)
            ).scalar()
            total_revenue = float(revenue_query) if revenue_query else 0.0
            
            return create_success_response({
                'customers': {
                    'total': total_customers,
                    'new_this_month': Customer.query.filter(Customer.created_at >= start_date).count()
                },
                'drivers': {
                    'total': total_drivers,
                    'active': active_drivers,
                    'offline': total_drivers - active_drivers
                },
                'rides': {
                    'total': total_rides,
                    'completed': completed_rides,
                    'ongoing': ongoing_rides,
                    'pending': pending_rides,
                    'recent': recent_rides
                },
                'revenue': {
                    'total': total_revenue,
                    'currency': 'INR'
                }
            })
        
        except Exception as e:
            logging.error(f"Error getting analytics summary: {str(e)}")
            return create_error_response("Failed to retrieve analytics summary")