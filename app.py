import os
import logging
from datetime import datetime, timedelta
import pytz
import jwt
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Set up logging - reduce verbosity for performance
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev-placeholder-key"
app.config['SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY") or "a1taxi-jwt-secret-key"  # JWT secret
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize SocketIO with optimized settings for performance
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    logger=False,          # Disable verbose logging for performance
    engineio_logger=False,
    async_mode='eventlet', # Use eventlet for better WebSocket performance
    ping_timeout=60,       # Increase timeout
    ping_interval=25       # Reduce ping frequency
)

# Initialize WebSocket handlers after socketio is created
from utils.websocket_manager import init_websocket_handlers
init_websocket_handlers(socketio)

# Configure CORS - Allow all origins and headers for development
CORS(app, 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials", "Accept", "Cache-Control", "Pragma"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     origins="*")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "sqlite:///dev.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'admin.login'  # Only for admin panel

# Set timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    """Return current time in IST timezone as naive datetime"""
    # Return naive IST time (without timezone info) since SQLAlchemy strips timezone
    # This ensures stored times match the IST timezone expectation in staleness detection
    return datetime.now(IST).replace(tzinfo=None)

# Import centralized authentication system
from utils.auth_manager import AuthenticationManager, token_required

# JWT Token Creation (uses centralized AuthenticationManager)
def generate_jwt_token(user_data):
    """Generate JWT token with centralized authentication manager"""
    return AuthenticationManager.create_jwt_token(user_data)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import Customer, Driver, Admin
    # Try to load customer first
    user = Customer.query.get(int(user_id))
    if user:
        return user
    # Try driver
    user = Driver.query.get(int(user_id))
    if user:
        return user
    # Try admin
    user = Admin.query.get(int(user_id))
    return user

with app.app_context():
    # Import models to ensure tables are created
    import models
    
    # Import routes
    from routes.customer import customer_bp
    from routes.driver import driver_bp
    from routes.admin import admin_bp
    from routes.mobile import mobile_bp
    from routes.auth import auth_bp
    
    # Initialize background tasks for session management
    from utils.background_tasks import initialize_background_tasks
    initialize_background_tasks()
    
    # Register blueprints
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(driver_bp, url_prefix='/driver')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(mobile_bp, url_prefix='')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Add catch-all login route for backwards compatibility
    @app.route('/login', methods=['POST'])
    def legacy_login():
        """Legacy login endpoint that redirects to driver login for backwards compatibility"""
        from routes.driver import login
        return login()
    
    # Only create tables and initialize data in development
    # In production (Railway), tables should already exist
    is_production = bool(os.environ.get('RAILWAY_ENVIRONMENT')) or os.environ.get('NODE_ENV') == 'production'
    
    if not is_production:
        # Development environment - create tables and default data
        logging.info("Development environment detected - initializing database")
        db.create_all()
        
        # Create default admin user if not exists
        admin = models.Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = models.Admin(username='admin')
            admin.set_password('admin123')  # Now properly hashed
            db.session.add(admin)
            db.session.commit()
            logging.info("Default admin user created: admin/admin123 (password hashed)")
        
        # Initialize default data
        try:
            models.FareConfig.initialize_default_fares()
            models.SpecialFareConfig.initialize_default_special_fares()
            models.Zone.initialize_default_zones()
            models.PromoCode.initialize_default_promo_codes()
        except Exception as e:
            logging.error(f"Error initializing default data: {e}")
    else:
        # Production environment - ensure tables exist and initialize essential data
        logging.info("Production environment detected - ensuring essential data exists")
        # Only create tables if they don't exist (this won't drop existing data)
        db.create_all()
        
        # Ensure essential data exists in production (won't overwrite existing data)
        try:
            models.FareConfig.initialize_default_fares()
            logging.info("Production: Fare configurations initialized")
            models.SpecialFareConfig.initialize_default_special_fares()
            logging.info("Production: Special fare configurations initialized")
            models.Zone.initialize_default_zones()
            logging.info("Production: Zones initialized")
            models.PromoCode.initialize_default_promo_codes()
            logging.info("Production: Promo codes initialized")
        except Exception as e:
            logging.error(f"Error initializing production data: {e}")

# Root route - Login-aware landing page
@app.route('/')
def index():
    from flask_login import current_user
    from flask import redirect, url_for
    
    # Check if user is accessing the admin interface
    if current_user.is_authenticated and hasattr(current_user, 'username'):
        # User is logged in as admin, redirect to dashboard
        return redirect(url_for('admin.dashboard'))
    else:
        # User is not logged in, redirect to admin login
        return redirect(url_for('admin.login'))

# Health check endpoint
@app.route('/health')
def health():
    return {'status': 'healthy', 'timestamp': get_ist_time().isoformat()}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
