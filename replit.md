# A1 Call Taxi - Replit Development Guide

## Overview

A1 Call Taxi is a comprehensive taxi booking platform designed for the Indian market, built with Flask backend and modern mobile applications. The system provides ride booking services with real-time dispatch, driver management, and administrative controls. The platform supports multiple ride categories (regular, rental, airport, outstation) with zone-based driver assignment and concentric ring dispatch logic.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask Application**: Modular blueprint structure with separate route handlers for admin, customer, driver, and mobile endpoints
- **Database**: SQLAlchemy ORM with PostgreSQL for production, supporting timezone-aware operations (Asia/Kolkata)
- **Authentication**: Dual authentication system - JWT tokens for mobile apps (drivers/customers) and Flask-Login sessions for admin panel
- **API Design**: RESTful endpoints with standardized JSON responses following `{success: boolean, message: string, data: object}` format

### Core Models
- **User Management**: Customer, Driver, and Admin models with phone-based authentication and role-based access
- **Ride Management**: Comprehensive ride lifecycle tracking with status transitions, location data, and fare calculations
- **Zone System**: Polygon-based service zones with concentric ring dispatch logic for driver assignment
- **Fare Configuration**: Dynamic pricing system with special rates for different ride categories and promo code support

### Authentication Strategy
- **Mobile Apps**: JWT token-based authentication with 7-day expiration and Bearer token validation
- **Admin Panel**: Traditional session-based authentication using Flask-Login for server-side rendered templates
- **Token Management**: Automatic token refresh and validation with proper error handling for expired tokens
- **Customer API**: Working endpoints at `/customer/*` (not `/api/customer/*`) with proper JWT authentication
- **API Documentation**: Complete customer API documentation created with working examples and field formats

### GPS Tracking Implementation
- **Unified Location Service**: Single GPS implementation serves all location tracking needs across mobile apps
- **Intelligent Frequency**: 30-60 seconds for general availability, 10-15 seconds during active rides
- **Dual Purpose Updates**: Always updates general location (`/driver/update_current_location`), adds ride tracking (`/driver/update_location`) when on active rides
- **Battery Optimized**: Automatic frequency adjustment based on driver state to minimize battery drain
- **Centralized Architecture**: Eliminates duplicate GPS systems, provides consistent behavior across all features

### Dispatch Engine
- **Zone-Based Assignment**: Drivers are automatically assigned to zones based on their GPS location
- **Concentric Ring Logic**: Ride requests expand through configurable rings within zones when no drivers accept
- **Proximity Filtering**: Haversine distance calculation to ensure drivers are within service radius (configurable per zone)
- **Car Type Matching**: Ride requests are filtered by compatible vehicle types (sedan, SUV, hatchback)

### Real-Time Features
- **Driver Location Tracking**: Continuous GPS updates with database persistence and zone reassignment
- **Live Ride Status**: Real-time status updates throughout the ride lifecycle
- **Driver Availability**: Automatic online/offline status management based on login state

### Admin Dashboard
- **Server-Side Rendered**: Bootstrap-based responsive UI with dark theme
- **Comprehensive Management**: Full CRUD operations for drivers, customers, rides, zones, and fare configurations
- **Real-Time Monitoring**: Live dashboard with ride tracking, driver status, and zone visualization
- **Configuration Tools**: Dynamic fare matrix, zone polygon editing, and promotional code management

## External Dependencies

### Google Maps Integration
- **Distance Matrix API**: Route calculation and fare estimation using real road distances
- **Geocoding API**: Address to coordinate conversion and reverse geocoding
- **Places API**: Address autocomplete and location validation
- **Frontend Maps**: JavaScript API for interactive map display and route visualization

### Database Systems
- **Production**: PostgreSQL hosted on Railway with connection pooling and automatic failover
- **Development**: PostgreSQL on Replit with environment-specific configuration
- **Migration Support**: SQLAlchemy migrations with automatic schema updates

### Deployment Infrastructure
- **Railway Production**: Primary hosting platform with automatic deployments and scaling
- **Replit Development**: Development environment with real-time collaboration and testing
- **Environment Management**: Secure configuration handling with environment-specific variables

### Third-Party Services
- **JWT Authentication**: PyJWT library for token generation and validation
- **Password Security**: Werkzeug for secure password hashing and verification
- **CORS Handling**: Flask-CORS for cross-origin request management
- **Timezone Management**: pytz for accurate Indian Standard Time handling

### Mobile App Architecture
- **React Frontend**: Modern web-based driver and customer applications
- **API Communication**: RESTful API consumption with proper error handling and retry logic
- **Real-Time Updates**: Polling-based status updates with configurable intervals
- **Offline Support**: Local storage for critical data and graceful degradation

### Monitoring and Logging
- **Comprehensive Logging**: Structured logging for all critical operations and error tracking
- **Request Debugging**: Detailed request/response logging for API troubleshooting
- **Performance Monitoring**: Database query optimization and response time tracking