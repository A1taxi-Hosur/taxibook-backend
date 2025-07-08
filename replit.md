# TaxiBook Backend - System Architecture

## Overview

TaxiBook is a comprehensive taxi booking platform designed for the Indian market. This backend system provides APIs for customer bookings, driver management, and admin operations, along with a complete admin dashboard interface. The system handles the entire ride lifecycle from booking to completion with real-time status tracking.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3) with modular blueprint structure
- **ORM**: SQLAlchemy with Flask-SQLAlchemy integration
- **Database**: SQLite for development, PostgreSQL for production
- **Authentication**: Flask-Login with session-based authentication
- **API Design**: RESTful endpoints with standardized JSON responses
- **Timezone**: All timestamps use Asia/Kolkata timezone

### Frontend Architecture
- **Admin Interface**: Server-side rendered HTML templates with Bootstrap
- **Theme**: Dark theme using Bootstrap agent styling
- **Responsive Design**: Mobile-first approach with Bootstrap grid system
- **JavaScript**: Minimal client-side scripting for interactive features

### Project Structure
```
TaxiBook/
├── app.py                    # Main Flask application setup
├── main.py                   # Application entry point
├── models.py                 # Database models (Customer, Driver, Ride, etc.)
├── routes/                   # API endpoint modules
│   ├── admin.py             # Admin dashboard and driver management
│   ├── customer.py          # Customer booking and ride management
│   ├── driver.py            # Driver authentication and ride handling
│   └── mobile.py            # Mobile app read-only APIs
├── templates/admin/          # Bootstrap-based admin UI templates
├── utils/                    # Utility functions
│   ├── maps.py              # Google Maps API integration
│   └── validators.py        # Input validation and error handling
├── test_*.py                # Automated testing scripts
└── *.md                     # Documentation files
```

## Key Components

### Authentication System
- **Multi-role Authentication**: Separate login flows for customers, drivers, and admins
- **Session Management**: Flask-Login handles user sessions across all user types
- **Phone-based Authentication**: Customers and drivers authenticate using 10-digit Indian mobile numbers
- **Admin Authentication**: Username/password authentication for admin users

### User Management
- **Customer Management**: Registration, login, and profile management
- **Driver Management**: Driver onboarding and account management
- **Admin Management**: Admin user creation and authentication
- **Phone Validation**: Strict validation for Indian mobile numbers (6-9 starting digits)

### Ride Management
- **Booking System**: Customer ride requests with pickup/drop locations
- **Driver Assignment**: Automatic driver assignment based on availability
- **Status Tracking**: Real-time ride status updates through multiple states
- **Fare Calculation**: Database-driven fare configuration with admin-controlled pricing
- **GPS Tracking**: Real-time driver location tracking with optimized database indexing
- **OTP Verification**: Secure ride start confirmation with 6-digit OTP system

### API Integration
- **Google Maps Distance Matrix API**: Calculate distances, routes, and travel times
- **Fare Calculation**: Dynamic pricing based on distance and time
- **Location Services**: Address validation and coordinate handling

## Data Flow

### Customer Journey
1. **Authentication**: Login/register via phone number and name
2. **Booking**: Submit ride request with pickup and drop addresses
3. **Matching**: System finds available drivers and assigns ride
4. **Tracking**: Real-time updates on driver status and location
5. **Completion**: Ride completion with fare calculation and payment

### Driver Journey
1. **Authentication**: Login/register via phone number and name
2. **Availability**: Mark themselves as available for rides
3. **Assignment**: Receive ride assignments from the system
4. **Acceptance**: Accept or decline ride requests
5. **Execution**: Navigate through ride stages (arrive, start, complete)

### Admin Operations
1. **Dashboard**: Overview of system statistics and active rides
2. **User Management**: Monitor and manage customers and drivers
3. **Ride Monitoring**: Track all rides and their statuses
4. **Fare Configuration**: Real-time pricing management with surge control
5. **Analytics**: View system performance and usage metrics

## External Dependencies

### APIs
- **Google Maps Distance Matrix API**: Required for distance calculation and fare estimation
- **Environment Variables**: `GOOGLE_MAPS_API_KEY` must be configured

### Python Packages
- **Flask**: Web framework and routing
- **Flask-SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **Flask-CORS**: Cross-origin resource sharing
- **Werkzeug**: WSGI utilities and security
- **PyTz**: Timezone handling
- **Requests**: HTTP client for API calls

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database with debug mode enabled
- **Production**: PostgreSQL with proper environment variables
- **Session Security**: Configurable session secret key
- **Proxy Support**: ProxyFix middleware for deployment behind proxies

### Database Management
- **Connection Pooling**: Configured with pool recycling and pre-ping
- **Migration Support**: SQLAlchemy model-based schema management
- **Timezone Consistency**: All timestamps in Asia/Kolkata timezone

### Security Considerations
- **Input Validation**: Comprehensive validation for all user inputs
- **Phone Number Sanitization**: Automatic cleanup of international prefixes
- **CORS Configuration**: Proper cross-origin policies for API access
- **Session Management**: Secure session handling with proper logout

## Changelog

```
Changelog:
- July 05, 2025. Initial setup
- July 06, 2025. Added driver online/offline toggle feature (Version 1.1)
- July 06, 2025. Added login-aware landing page with automatic redirects (Version 1.1)
- July 06, 2025. Added comprehensive admin driver management system (Version 1.1)
- July 06, 2025. Enhanced customer API with complete driver details when assigned (Version 1.1)
- July 06, 2025. Added admin password display for testing purposes (Version 1.1)
- July 07, 2025. Implemented driver username/password authentication system (Version 1.2)
- July 07, 2025. Removed old driver login_or_register endpoint to eliminate confusion (Version 1.2)
- July 07, 2025. Added ride rejection tracking system with database table and filtering (Version 1.3)
- July 07, 2025. Implemented complete mobile API endpoints for customer and driver apps (Version 1.4)
- July 07, 2025. Added ride type selection and vehicle-based filtering for customers and drivers (Version 1.5)
- July 07, 2025. Implemented ride estimate endpoint with Google Maps integration and multi-vehicle fare calculation (Version 1.6)
- July 07, 2025. Enhanced ride estimate endpoint with simplified JSON format and strengthened backend-only pricing control (Version 1.6.1)
- July 07, 2025. Implemented comprehensive GPS tracking system with real-time driver location updates, customer location retrieval, and optimized database indexing (Version 1.7)
- July 07, 2025. Implemented OTP-based ride start confirmation system with 6-digit OTP generation, customer OTP retrieval, driver OTP verification, and automatic OTP cleanup for enhanced security (Version 1.8)
- July 08, 2025. Implemented database-driven fare configuration system with admin web interface for real-time pricing management, replacing hardcoded fare calculations with configurable base_fare, per_km_rate, and surge_multiplier settings (Version 1.9)
- July 08, 2025. Resolved authentication issues and completed fare configuration system deployment - admin can now manage all fare settings in real-time with full web interface and API functionality (Version 1.9.1)
- July 08, 2025. Fixed JavaScript error in fare configuration page - resolved data structure mismatch between API response and frontend code, ensuring proper loading of fare configurations (Version 1.9.2)
- July 08, 2025. Enhanced JavaScript error handling in fare configuration page - added null/undefined checks, improved error messages, and robust array validation to prevent forEach errors (Version 1.9.3)
- July 08, 2025. Verified complete database-driven fare system implementation - all APIs (ride estimate, book ride, driver incoming rides) now use FareConfig calculations with no hardcoded values, ensuring admin has full real-time pricing control (Version 1.9.4)
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```