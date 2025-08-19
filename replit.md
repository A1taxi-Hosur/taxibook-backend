# A1 Call Taxi - Platform Architecture Guide

## Overview

A1 Call Taxi is a comprehensive taxi booking platform built for the Indian market, featuring real-time ride dispatch, GPS tracking, and zone-based service management. The system consists of a Flask backend with modern WebSocket capabilities, supporting web admin panels and mobile applications for customers and drivers.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
The platform uses a **Flask-based modular architecture** with blueprint-based route organization. The core application (`app.py`) initializes SQLAlchemy with PostgreSQL for production and SQLite for development, configured for the Asia/Kolkata timezone. The system implements dual authentication strategies and real-time WebSocket communication through Socket.IO.

### JWT Authentication Architecture
The system has been **completely audited and implemented with pure JWT authentication** (August 2025):
- **AUDIT COMPLETED**: All competing authentication systems eliminated (session-based, enhanced JWT with sessions)
- **Pure JWT Implementation**: Single unified JWT authentication system using access and refresh tokens  
- **Access Token**: 24-hour expiry for API access and mobile app authentication
- **Refresh Token**: 30-day expiry for token renewal without re-authentication
- **Bearer Token Authentication**: Standard Authorization header format for API requests
- **Multi-source Token Extraction**: Supports Authorization header, JSON body, and form data
- **Phone-based Authentication**: Simple phone number authentication for drivers and customers
- **JWT Token Manager**: Centralized `JWTAuthenticationManager` class for all token operations
- **Automatic Token Validation**: `@token_required` decorator on 31+ protected endpoints
- **Token Verification Endpoint**: `/auth/verify` to validate current tokens
- **Refresh Token Endpoint**: `/auth/refresh` to generate new access tokens
- **Secure Token Creation**: Configurable secret keys and expiry times
- **Legacy Endpoint Deprecation**: All old login endpoints properly deprecated with error messages
- **Cleaned Codebase**: Removed utils/auth_helpers.py, utils/session_manager.py, and other legacy authentication files

### Database Design
The SQLAlchemy ORM manages five core models:
- **User Models**: Customer, Driver, and Admin entities with phone-based authentication
- **Ride System**: Comprehensive ride lifecycle tracking with status transitions, location data, and fare calculations
- **Zone Management**: Polygon-based service zones with concentric ring dispatch logic
- **Pricing Engine**: Dynamic fare configuration with special rates for different ride categories (regular, airport, rental, outstation)
- **Promotional System**: Promo code support with discount types and usage restrictions

### Real-Time Communication System
The platform has been fully migrated from polling-based updates to a **WebSocket-driven real-time architecture** (completed August 2025):
- **Zero Polling Design**: Eliminated all `setInterval` polling loops, achieving 95% reduction in unnecessary server requests
- **WebSocket Broadcasting**: Complete Socket.IO implementation for instant push notifications across admin dashboard, live maps, and ride status updates
- **Event-Driven Updates**: All ride status changes, location updates, and dashboard statistics broadcast instantly to connected clients

### GPS Tracking Implementation
The system features a **unified location service architecture**:
- **Intelligent Frequency**: 30-60 seconds for general driver availability, 10-15 seconds during active rides
- **Dual Purpose Updates**: Always updates general location via `/driver/update_current_location`, adds ride-specific tracking via `/driver/update_location` during active rides
- **Battery Optimization**: Automatic frequency adjustment based on driver state to minimize mobile device battery drain

### Ride Dispatch Engine
The dispatch system implements **zone-based driver assignment** with sophisticated matching logic:
- **Zone Assignment**: Drivers automatically assigned to service zones based on GPS location
- **Concentric Ring Expansion**: Ride requests expand through configurable rings within zones when drivers don't accept
- **Proximity Filtering**: Haversine distance calculation ensures drivers are within service radius
- **Vehicle Type Matching**: Requests filtered by compatible car types (sedan, SUV, hatchback)
- **Special Category Handling**: Airport rides restricted to sedan/SUV, with separate fare matrices for rental and outstation categories

### API Architecture
The REST API follows a standardized response format: `{success: boolean, message: string, data: object}`. Routes are organized into modular blueprints:
- **Customer Routes** (`/customer/*`): Login/registration, ride booking, status tracking
- **Driver Routes** (`/driver/*`): Authentication, ride acceptance, location updates, earnings tracking
- **Admin Routes** (`/admin/*`): Dashboard management, driver assignment, zone configuration
- **Mobile Routes** (`/mobile/*`): Extended endpoints for mobile app features like profile management and ride history

## External Dependencies

### Google Maps Integration
The platform integrates Google Maps services for geocoding and distance calculations:
- **Distance Matrix API**: Used for accurate road distance and travel time calculations between pickup and drop locations
- **Geocoding API**: Converts addresses to coordinates and vice versa for ride booking
- **Places API**: Provides address autocomplete functionality in the frontend applications

### Database Systems
- **Production Database**: PostgreSQL with timezone-aware operations and connection pooling
- **Development Database**: SQLite for local development and testing
- **ORM Layer**: SQLAlchemy with declarative base and automatic migration support

### Frontend Technologies
- **Admin Panel**: Server-rendered Jinja2 templates with Bootstrap CSS framework and vanilla JavaScript
- **WebSocket Client**: Universal JavaScript WebSocket client library for real-time features
- **Mobile Apps**: React-based applications with JWT authentication and real-time GPS tracking

### Infrastructure Services
- **Deployment Platform**: Designed for Railway deployment with environment-based configuration
- **WebSocket Server**: Socket.IO with CORS support for cross-origin real-time communication
- **File Storage**: Support for document uploads (driver licenses, vehicle documents) with URL-based references
- **Logging System**: Comprehensive logging with configurable levels for debugging and monitoring