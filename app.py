import os
import logging
from datetime import datetime
import pytz
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev-placeholder-key"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure CORS
CORS(app, supports_credentials=True)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL") or "sqlite:///dev.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'admin.login'

# Set timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_time():
    return datetime.now(IST)

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
    
    # Register blueprints
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(driver_bp, url_prefix='/driver')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(mobile_bp, url_prefix='')
    
    # Create all tables
    db.create_all()
    
    # Create default admin user if not exists
    admin = models.Admin.query.filter_by(username='admin').first()
    if not admin:
        admin = models.Admin(
            username='admin',
            password_hash='admin123'  # In production, this should be hashed
        )
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin user created: admin/admin123")

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
