# A1 Call Taxi - Replit Development Guide

## Overview

A1 Call Taxi is a comprehensive taxi booking platform designed for the Indian market, built with Flask backend and modern mobile applications. The system provides ride booking services with real-time GPS tracking, zone-based driver dispatch, and a complete admin management interface. The platform handles multiple ride categories (regular, airport, rental, outstation) with dynamic fare calculations and serves customers across defined service zones with polygon-based geographic coverage.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Flask Application**: Modular blueprint structure with separate route handlers for admin, customer, driver, and mobile endpoints
- **Database**: SQLAlchemy ORM with PostgreSQL for production, supporting timezone-aware operations (Asia/Kolkata)
- **Authentication**: Dual authentication system - JWT tokens for mobile apps (drivers/customers) and Flask-Login sessions for admin panel
- **API Design**: RESTful endpoints with standardized JSON responses following `{success: boolean, message: string, data: object}` format

### Core Models and Data Architecture
- **User Management**: Customer, Driver, and Admin models with phone-based authentication and role-based access control
- **Ride Management**: Comprehensive ride lifecycle tracking with status transitions (pending → accepted → arrived → started → completed), location data, and fare calculations
- **Zone System**: Polygon-based service zones with concentric ring dispatch logic for intelligent driver assignment
- **Fare Configuration**: Dynamic pricing system with special rates for different ride categories and promotional code support
- **Promo Code System**: Full promotional discount support with flat and percentage-based discounts, usage limits, and expiry dates

### Authentication Strategy
- **Mobile Apps**: JWT token-based authentication with 7-day expiration and Bearer token validation
- **Admin Panel**: Traditional session-based authentication using Flask-Login for server-side rendered templates
- **Token Management**: Automatic token refresh and validation with proper error handling for expired tokens
- **Standardized Auth**: Unified authentication helpers across all customer endpoints with consistent error responses

### Real-Time WebSocket Architecture
- **Zero Polling System**: Complete elimination of polling-based updates, replaced with instant WebSocket push notifications
- **WebSocket Broadcasting**: Socket.IO implementation for real-time ride status updates, driver location tracking, and admin dashboard synchronization
- **Event-Driven Updates**: All ride status changes (accept, arrive, start, complete) broadcast instantly to all connected clients
- **Live Administration**: Real-time admin dashboard with instant statistics updates, live driver map, and ongoing ride monitoring

### GPS Tracking and Location Services
- **Unified Location Service**: Single GPS implementation serving all location tracking needs across mobile applications
- **Intelligent Frequency**: 30-60 seconds for general availability, 3-15 seconds during active rides for optimal battery usage
- **Dual Purpose Updates**: Always updates general location (`/driver/update_current_location`), adds ride tracking (`/driver/update_location`) during active rides
- **Proximity Filtering**: Haversine distance calculation ensuring drivers are within configurable service radius per zone

### Dispatch Engine and Zone Management
- **Zone-Based Assignment**: Automatic driver assignment to service zones based on real-time GPS location
- **Concentric Ring Logic**: Ride requests expand through configurable rings within zones when no drivers accept initially
- **Car Type Matching**: Intelligent vehicle type filtering (sedan, SUV, hatchback) with special restrictions for airport rides
- **Polygon Service Areas**: Geographic service boundaries defined by polygon coordinates with point-in-polygon validation

### Ride Categories and Pricing
- **Multiple Ride Types**: Regular, Airport, Rental, and Outstation rides with category-specific pricing and vehicle requirements
- **Dynamic Fare Calculation**: Special fare configuration system allowing different pricing models per ride category
- **Fare Freezing**: Fare amounts calculated and frozen at booking time to prevent price changes during ride lifecycle
- **Promotional Support**: Complete promo code system with usage tracking, expiry dates, and minimum fare requirements

## External Dependencies

### Google Maps Integration
- **Google Maps JavaScript API**: Frontend address autocomplete and route visualization in web applications
- **Google Maps REST APIs**: Backend geocoding, distance calculation, and address validation services
- **API Key Configuration**: Single API key used across frontend and backend with proper billing setup requirements
- **Distance Matrix API**: Real road distance and travel time calculations for accurate fare computation

### Database Services
- **PostgreSQL**: Primary production database with timezone support and geographic data handling
- **SQLite**: Development database for local testing and rapid prototyping
- **SQLAlchemy ORM**: Database abstraction layer with relationship management and query optimization

### Real-Time Communication
- **Socket.IO**: WebSocket implementation for real-time bidirectional communication between clients and server
- **Flask-SocketIO**: Server-side WebSocket handling integrated with Flask application lifecycle
- **Event Broadcasting**: Instant push notifications for ride updates, location changes, and admin dashboard synchronization

### Authentication and Security
- **PyJWT**: JSON Web Token implementation for mobile app authentication with configurable expiration
- **Flask-Login**: Session-based authentication for admin panel with secure cookie management
- **Werkzeug Security**: Password hashing and verification for driver and admin credentials
- **Flask-CORS**: Cross-origin resource sharing configuration for mobile app API access

### Development and Deployment
- **Railway**: Production hosting platform for backend services with PostgreSQL database provisioning
- **Replit**: Development environment with hot reloading and collaborative features
- **Flask-Migrate**: Database migration management for schema updates and version control
- **Python Logging**: Comprehensive logging system for debugging and monitoring across all application components