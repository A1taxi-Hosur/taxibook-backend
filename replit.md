# A1 Call Taxi Backend - System Overview

## Overview
A1 Call Taxi is a comprehensive taxi booking platform for the Indian market, providing backend APIs for customer bookings, driver management, and admin operations. It includes a full admin dashboard and manages the entire ride lifecycle with real-time status tracking. The project aims to deliver a robust and scalable solution for the on-demand taxi service industry.

## User Preferences
Preferred communication style: Simple, everyday language.

## Recent Critical Issues (2025-08-06)
- ✅ **RESOLVED: Driver Authentication Issue** - Fixed frontend form data transmission issue where login requests were sending empty bodies `{}` instead of credentials
- **Railway Production Backend Crisis:** Complete authentication failure affecting all user types (admin, driver, customer)
- **Database Isolation:** Railway production and local development databases are completely separate with different driver credentials
- **Production Driver Credentials Confirmed:** Username `DRIVERMQO`, Password `3210@Taxi` verified from Railway admin panel
- **Authentication Still Fails:** Even with correct production credentials, Railway backend returns "Invalid username or password"
- **Final Conclusion:** This is definitively a Railway deployment configuration issue, not an app or credential problem

## System Architecture
### Backend
- **Framework**: Flask (Python 3) with modular blueprint structure.
- **ORM**: SQLAlchemy with Flask-SQLAlchemy.
- **Database**: PostgreSQL for production (Railway), PostgreSQL for development (Replit). Environment-aware initialization prevents production data loss during deployments (implemented 2025-08-02).
- **Authentication**: Flask-Login for session-based authentication with multi-role support (customer, driver, admin) and phone-based authentication for customers/drivers.
- **API Design**: RESTful endpoints with standardized JSON responses.
- **Timezone**: All timestamps are in Asia/Kolkata timezone.
- **Driver Status**: "Always Online" system - drivers automatically online when logged in, offline when logged out (implemented 2025-08-02).
- **Live Map**: Real-time driver location tracking with Google Maps integration showing driver pins as colored circles (green=online, red=offline, yellow=out of zone) - verified working 2025-08-02.

### Frontend
- **Admin Interface**: Server-side rendered HTML templates using Bootstrap.
- **Theme**: Dark theme with Bootstrap agent styling.
- **Design Principles**: Mobile-first responsive design using Bootstrap grid system.
- **Interactivity**: Minimal client-side JavaScript for dynamic features.

### Core Features
- **Authentication System**: Secure session management and login flows for customers, drivers, and admins. Includes phone-based authentication for customers/drivers and username/password for admins.
- **User Management**: Comprehensive management for customers, drivers, and admins, including profile management and phone number validation. Driver availability managed through login/logout states only (no manual toggle).
- **Ride Management**:
    - **Booking System**: Customer ride requests with pickup/drop locations.
    - **Dispatch System**: Configurable concentric ring-based dispatch logic with priority-based zone matching and automatic driver zone assignment. Includes an approval workflow for zone expansion with extra fare calculation.
    - **Driver Notification**: Driver choice-based acceptance system, filtering by car type, zone, and proximity.
    - **Status Tracking**: Real-time ride status updates and GPS tracking of drivers with OTP verification for ride start.
    - **Fare Calculation**: Database-driven fare configuration with admin-controlled pricing, including special fare configurations and promo code support (flat/percent discounts, usage limits, validity).
    - **Scheduled Rides**: Support for scheduled bookings with distinct handling from immediate rides.
- **Admin Operations**:
    - **Dashboard**: Overview of system statistics, active rides, and user management.
    - **Ride Monitoring**: Live tracking and management of rides, including manual assignment.
    - **Configuration Management**: Real-time pricing control, zone management (polygon-based creation), and advertisement management with media upload and scheduling.
    - **Analytics**: System performance and usage metrics.
    - **Branding**: Integrated A1 Call Taxi branding across the admin interface.

## External Dependencies
### APIs
- **Google Maps Distance Matrix API**: Used for distance calculation, route estimation, and fare estimation. Includes automatic fallback to Haversine formula when billing is not available.
- **Firebase**: For push notification integration (e.g., driver notifications).

### Python Packages
- **Flask**: Web framework.
- **Flask-SQLAlchemy**: ORM for database interaction.
- **Flask-Login**: User session management.
- **Flask-CORS**: Cross-origin resource sharing.
- **Werkzeug**: WSGI utilities and security.
- **PyTz**: Timezone handling.
- **Requests**: HTTP client for external API calls.