#!/usr/bin/env python3
"""
A1 Taxi Hosur Dev - Production Flask Backend
Main application entry point
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import Config

# Initialize extensions
db = SQLAlchemy()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.customer import customer_bp
    from routes.driver import driver_bp
    from routes.admin import admin_bp
    from routes.booking import booking_bp
    from routes.zone import zone_bp
    from routes.fare import fare_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(driver_bp, url_prefix='/driver')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(booking_bp, url_prefix='/bookings')
    app.register_blueprint(zone_bp, url_prefix='/zones')
    app.register_blueprint(fare_bp, url_prefix='/fare')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Initialize default data
        from models.fare_matrix import FareMatrix
        from models.zone import Zone
        
        # Create default fare matrix if not exists
        if not FareMatrix.query.first():
            FareMatrix.create_default_fares()
            
        # Create default zone if not exists
        if not Zone.query.first():
            default_zone = Zone(
                zone_name="Hosur Central",
                center_lat=12.1264,
                center_lng=77.8267,
                radius_km=5.0
            )
            db.session.add(default_zone)
            db.session.commit()
    
    @app.route('/')
    def index():
        return {
            'message': 'A1 Taxi Hosur Dev API',
            'version': '1.0.0',
            'status': 'running'
        }
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)