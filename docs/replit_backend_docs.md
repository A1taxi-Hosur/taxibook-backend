# TaxiBook Backend API Documentation

## Overview
This document provides comprehensive documentation for the TaxiBook backend API - a complete taxi booking platform for the Indian market. The backend handles customer bookings, driver management, ride lifecycle, and includes an admin dashboard for monitoring.

**🚀 PRODUCTION STATUS: FULLY OPERATIONAL**
- ✅ All APIs tested and working
- ✅ Google Maps integration active with real distance calculation
- ✅ Admin dashboard accessible and functional
- ✅ Database configured with PostgreSQL
- ✅ GPS tracking system implemented with real-time location updates
- ✅ Ready for frontend development

## 🏗️ Architecture
- **Backend**: Flask (Python 3) with SQLAlchemy ORM
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Flask-Login with session management
- **API Integration**: Google Maps Distance Matrix API
- **Frontend**: Admin UI built with Flask templates + Bootstrap
- **Timezone**: All timestamps in Asia/Kolkata timezone

## 📁 Project Structure

```
TaxiBook/
├── 📄 app.py                    # Main Flask application setup, database config
├── 📄 main.py                   # Application entry point (imports app)
├── 📄 models.py                 # SQLAlchemy database models (Customer, Driver, Ride, etc.)
├── 📄 replit.md                 # Project architecture and user preferences
├── 📄 replit_backend_docs.md    # Complete API documentation (this file)
├── 📄 pyproject.toml            # Python dependencies and project config
├── 📄 uv.lock                   # Lock file for dependency versions
├── 
├── 📂 routes/                   # API endpoint modules (Blueprint architecture)
│   ├── 📄 admin.py             # Admin dashboard and driver management APIs
│   ├── 📄 customer.py          # Customer booking and ride management APIs
│   ├── 📄 driver.py            # Driver authentication and ride handling APIs
│   └── 📄 mobile.py            # Mobile app read-only APIs (profiles, history)
│
├── 📂 templates/                # HTML templates for admin dashboard
│   └── 📂 admin/               # Bootstrap-based admin UI templates
│       ├── 📄 dashboard.html   # Main admin dashboard with stats
│       ├── 📄 login.html       # Admin login page
│       ├── 📄 rides.html       # Ride management interface
│       ├── 📄 customers.html   # Customer management interface
│       └── 📄 drivers.html     # Driver management interface
│
├── 📂 utils/                    # Utility functions and helpers
│   ├── 📄 maps.py              # Google Maps API integration for distance/fare calculation
│   └── 📄 validators.py        # Input validation and error handling functions
│
├── 📂 attached_assets/          # User-uploaded files and documentation
├── 📄 GPS_TRACKING_DEMO.md     # GPS tracking implementation guide
├── 📄 BUG_FIXES_LOG.md         # Development bug fixes and solutions
├── 📄 test_admin_drivers.py    # Test script for admin driver management
├── 📄 test_gps_tracking.py     # Test script for GPS tracking system
└── 📄 cookies.txt              # Session storage for testing
```

### Key File Descriptions

**Core Application Files:**
- `app.py`: Flask app initialization, database configuration, session management
- `main.py`: Application entry point for deployment
- `models.py`: All database models with relationships and validation

**API Routes (Blueprint Architecture):**
- `routes/admin.py`: Admin authentication, dashboard, driver CRUD operations
- `routes/customer.py`: Customer auth, ride booking, status tracking, cancellation
- `routes/driver.py`: Driver login, ride acceptance, GPS updates, status management
- `routes/mobile.py`: Read-only APIs for mobile app data (profiles, history, earnings)

**Frontend Templates:**
- `templates/admin/`: Bootstrap-based admin dashboard with dark theme
- All templates use server-side rendering with minimal JavaScript

**Utility Modules:**
- `utils/maps.py`: Google Maps Distance Matrix API integration
- `utils/validators.py`: Input validation, error handling, response formatting

**Testing & Documentation:**
- `test_*.py`: Automated testing scripts for key functionality
- `GPS_TRACKING_DEMO.md`: Implementation guide for real-time location tracking
- `BUG_FIXES_LOG.md`: Development issue tracking and solutions

## 🔗 Base URL
- **API Base URL**: `http://localhost:5000` (development) / `https://d14f67de-8be5-4bba-8cac-e3f54fd01bde-00-3pqh4yrkxjrrd.kirk.replit.dev` (production)
- **Admin Dashboard**: `http://localhost:5000/admin/login` (redirects to login if not authenticated)
- **Health Check**: `http://localhost:5000/health`

## 🔐 Admin Dashboard Access
The admin dashboard is accessible at `/admin/login` with the following default credentials:
- **Username**: `admin`
- **Password**: `admin123`

After login, the dashboard provides:
- Overview statistics and charts
- Real-time ride monitoring
- Customer and driver management
- Ride history and filtering
- System maintenance tools

## 🚗 Ride Type Feature

**New in Version 1.5**: Vehicle-based ride matching system

## 📊 Ride Estimate Feature

**New in Version 1.6**: Pre-booking fare estimation with Google Maps integration

### How It Works
- **Stateless Operation**: No database writes or session requirements
- **Real Distance Calculation**: Uses Google Maps Distance Matrix API for accurate road distances
- **Centralized Pricing Logic**: All fare calculations controlled exclusively by backend
  - Hatchback: ₹12/km
  - Sedan: ₹15/km
  - SUV: ₹18/km
- **Smart Rounding**: All fares rounded to nearest ₹5 using `round(fare/5.0)*5` logic
- **Comprehensive Validation**: Validates coordinate ranges (-90 to 90 for latitude, -180 to 180 for longitude)
- **Error Handling**: Gracefully handles unreachable locations and API failures

### Backend-Only Pricing Control
- **No Client-Side Calculations**: Frontend/mobile apps NEVER calculate fares independently
- **Centralized Rate Management**: All pricing rules adjustable only in backend code
- **Security**: Prevents fare manipulation or client-side pricing inconsistencies
- **Future Flexibility**: Easy to implement dynamic pricing, surge rates, or promotional discounts

### Frontend Integration
- Perfect for showing fare estimates before booking confirmation
- Requires GPS coordinates from device location services
- Displays all three vehicle type options with backend-calculated pricing
- No authentication required - purely utility endpoint
- Frontend should never attempt local fare calculations

### Customer Experience
- Customers must select a vehicle type when booking: **hatchback**, **sedan**, or **suv**
- Ride type selection is mandatory - bookings without `ride_type` will be rejected
- Invalid ride types (like "compact") are automatically rejected with clear error messages

### Driver Experience  
- Drivers only see ride requests that match their vehicle type (`driver.car_type`)
- **Sedan drivers** see only **sedan bookings**
- **Hatchback drivers** see only **hatchback bookings**
- **SUV drivers** see only **SUV bookings**
- Drivers without a specified `car_type` won't see any ride requests

### Business Logic
- Rides are stored in the database with the customer's selected `ride_type`
- The matching system filters rides at the API level using `WHERE ride.ride_type = driver.car_type`
- All existing ride dispatch, acceptance, and completion logic remains unchanged
- Ride rejection tracking continues to work across all vehicle types

## 📱 API Endpoints

### Mobile App Endpoints (Read-Only)

#### Driver Mobile API

**GET /driver/profile**
- **Purpose**: Get driver profile information for mobile app
- **Parameters**: 
  - `username` (required): Driver username
- **Response**: All driver profile fields including vehicle and document details
- **Example**: `GET /driver/profile?username=DRVWR50FN`

**GET /driver/history**
- **Purpose**: Get paginated driver ride history
- **Parameters**:
  - `username` (required): Driver username
  - `offset` (optional): Pagination offset (default: 0)
  - `limit` (optional): Items per page (default: 20, max: 100)
- **Response**: List of completed rides with fare and distance
- **Example**: `GET /driver/history?username=DRVWR50FN&offset=0&limit=20`

**GET /driver/earnings**
- **Purpose**: Get driver earnings summary and daily breakdown
- **Parameters**:
  - `username` (required): Driver username
- **Response**: Total rides, total fare, and daily summary for last 7 days
- **Example**: `GET /driver/earnings?username=DRVWR50FN`

#### Customer Mobile API

**GET /customer/profile**
- **Purpose**: Get customer profile information
- **Parameters**:
  - `phone` (required): Customer phone number
- **Response**: Customer name, phone, and registration date
- **Example**: `GET /customer/profile?phone=9876543210`

**GET /customer/history**
- **Purpose**: Get paginated customer ride history
- **Parameters**:
  - `phone` (required): Customer phone number
  - `offset` (optional): Pagination offset (default: 0)
  - `limit` (optional): Items per page (default: 20, max: 100)
- **Response**: List of all rides with driver details and status
- **Example**: `GET /customer/history?phone=9876543210&offset=0&limit=20`

**GET /customer/total_spent**
- **Purpose**: Get customer spending summary
- **Parameters**:
  - `phone` (required): Customer phone number
- **Response**: Total rides, total spent, and daily breakdown for last 7 days
- **Example**: `GET /customer/total_spent?phone=9876543210`

### Customer API (`/customer/`)

#### 1. Login or Register
- **Endpoint**: `POST /customer/login_or_register`
- **Description**: Authenticate existing customer or register new one
- **📱 Frontend Requirements**: 
  - Must include `credentials: 'include'` in fetch request
  - Must send `Content-Type: application/json` header
  - Phone number must be exactly 10 digits starting with 6-9
- **Request Body**:
```json
{
  "phone": "9876543210",
  "name": "John Doe"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "customer_id": 1,
    "name": "John Doe",
    "phone": "9876543210",
    "action": "login"
  }
}
```

#### 2. Get Ride Estimate
- **Endpoint**: `POST /customer/ride_estimate`
- **Description**: Get fare estimates for all ride types without booking
- **📱 Frontend Notes**: 
  - Use this endpoint to show fare estimates before customer confirms booking
  - Frontend must retrieve lat/lng using device GPS and send coordinates
  - Stateless endpoint - no database writes, no session required
- **Request Body**:
```json
{
  "pickup_lat": 13.0827,
  "pickup_lng": 80.2707,
  "drop_lat": 13.0350,
  "drop_lng": 80.2650
}
```
- **Success Response**:
```json
{
  "hatchback": 125,
  "sedan": 150,
  "suv": 180
}
```
- **Error Response (400)**:
```json
{
  "error": "Missing required fields: pickup_lat, pickup_lng"
}
```
- **Error Response (500)**:
```json
{
  "error": "Could not calculate fare estimate"
}
```

#### 3. Book Ride
- **Endpoint**: `POST /customer/book_ride`
- **Description**: Book a new ride with vehicle type selection
- **📱 Frontend Notes**: 
  - Frontend must retrieve lat/lng using device GPS and send with ride request
  - Show calculated fare to customer **before** final ride confirmation
  - Frontend should draw the pickup→drop route on Google Maps for visual confirmation
- **Request Body**:
```json
{
  "customer_phone": "9876543210",
  "pickup_address": "Connaught Place, New Delhi",
  "drop_address": "India Gate, New Delhi",
  "ride_type": "sedan",
  "pickup_lat": 28.6315,
  "pickup_lng": 77.2167,
  "drop_lat": 28.6129,
  "drop_lng": 77.2295
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Ride booked successfully",
  "data": {
    "ride_id": 1,
    "pickup_address": "Connaught Place, New Delhi",
    "drop_address": "India Gate, New Delhi",
    "distance_km": 3.5,
    "fare_amount": 50.50,
    "status": "pending"
  }
}
```

#### 3. Get Ride Status
- **Endpoint**: `GET /customer/ride_status?phone=9876543210`
- **Description**: Get current ride status for customer with complete driver details when assigned
- **📱 Frontend Note**: Poll this endpoint every 10-15 seconds to get real-time updates. Show "searching for driver..." UI while status is `pending`
- **🚗 Driver Details**: When driver is assigned, response includes complete vehicle and driver information for customer app
- **Response** (with driver assigned):
```json
{
  "status": "success",
  "message": "Ride status retrieved",
  "data": {
    "has_active_ride": true,
    "id": 1,
    "customer_phone": "9876543210",
    "customer_name": "John Doe",
    "driver_name": "Rajesh Kumar",
    "driver_phone": "9876543333",
    "car_make": "Maruti",
    "car_model": "Swift Dzire",
    "car_year": 2021,
    "car_number": "DL 14 CA 1234",
    "car_type": "sedan",
    "driver_photo_url": "https://example.com/profile/123.jpg",
    "pickup_address": "Connaught Place, New Delhi",
    "drop_address": "India Gate, New Delhi",
    "distance_km": 3.5,
    "fare_amount": 50.50,
    "status": "accepted",
    "created_at": "2025-07-05T20:30:00+05:30",
    "accepted_at": "2025-07-05T20:32:00+05:30"
  }
}
```

**Response** (no driver assigned - pending ride):
```json
{
  "status": "success",
  "message": "Ride status retrieved",
  "data": {
    "has_active_ride": true,
    "id": 2,
    "driver_name": null,
    "driver_phone": null,
    "car_make": null,
    "car_model": null,
    "car_year": null,
    "car_number": null,
    "car_type": null,
    "driver_photo_url": null,
    "status": "pending"
  }
}
```

#### 4. Cancel Ride
- **Endpoint**: `POST /customer/cancel_ride`
- **Description**: Cancel current ride (only pending/accepted)
- **Request Body**:
```json
{
  "phone": "9876543210"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Ride cancelled successfully",
  "data": {
    "ride_id": 1,
    "status": "cancelled"
  }
}
```

#### 5. Logout
- **Endpoint**: `POST /customer/logout`
- **Description**: Logout customer session
- **Response**:
```json
{
  "status": "success",
  "message": "Logout successful"
}
```

### Driver API (`/driver/`)

#### 1. Login
- **Endpoint**: `POST /driver/login`
- **Description**: Authenticate driver using username and password
- **📱 Frontend Requirements**: 
  - Must include `credentials: 'include'` in fetch request
  - Must send `Content-Type: application/json` header
  - Username and password are required
- **Request Body**:
```json
{
  "username": "DRVKA14PK",
  "password": "9999@Taxi"
}
```
- **Response (Success)**:
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "driver_id": 7,
    "name": "Debug Driver",
    "phone": "9999999999",
    "username": "DRVKA14PK",
    "is_online": true,
    "car_make": null,
    "car_model": null,
    "car_number": null,
    "car_type": null,
    "car_year": null
  }
}
```
- **Response (Error)**:
```json
{
  "status": "error",
  "message": "Invalid username or password"
}
```

#### 2. Get Incoming Rides
- **Endpoint**: `GET /driver/incoming_rides?phone=9876543211&driver_location=28.6315,77.2167`
- **Description**: Get available rides for driver
- **📱 Frontend Note**: Poll this endpoint every 10-15 seconds to get new ride requests
- **🔄 Ride Dispatch Logic**: Only online drivers (is_online=true) receive ride requests. Offline drivers get empty response.
- **Response**:
```json
{
  "status": "success",
  "message": "Incoming rides retrieved",
  "data": {
    "rides": [
      {
        "id": 1,
        "customer_phone": "9876543210",
        "customer_name": "John Doe",
        "pickup_address": "Connaught Place, New Delhi",
        "drop_address": "India Gate, New Delhi",
        "distance_km": 3.5,
        "fare_amount": 50.50,
        "status": "pending",
        "created_at": "2025-07-05T20:30:00+05:30",
        "distance_to_pickup_km": 2.1
      }
    ],
    "count": 1
  }
}
```

#### 3. Accept Ride
- **Endpoint**: `POST /driver/accept_ride`
- **Description**: Accept a ride (first-come-first-served)
- **Request Body**:
```json
{
  "ride_id": 1,
  "driver_phone": "9876543211"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Ride accepted successfully",
  "data": {
    "ride_id": 1,
    "status": "accepted",
    "customer_name": "John Doe",
    "pickup_address": "Connaught Place, New Delhi",
    "drop_address": "India Gate, New Delhi",
    "fare_amount": 50.50
  }
}
```

#### 4. Mark Arrived
- **Endpoint**: `POST /driver/arrived`
- **Description**: Mark driver as arrived at pickup location
- **Request Body**:
```json
{
  "driver_phone": "9876543211"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Arrival confirmed",
  "data": {
    "ride_id": 1,
    "status": "arrived"
  }
}
```

#### 5. Start Ride
- **Endpoint**: `POST /driver/start_ride`
- **Description**: Start the ride (only after arrived)
- **Request Body**:
```json
{
  "driver_phone": "9876543211"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Ride started successfully",
  "data": {
    "ride_id": 1,
    "status": "started"
  }
}
```

#### 6. Complete Ride
- **Endpoint**: `POST /driver/complete_ride`
- **Description**: Complete the ride
- **Request Body**:
```json
{
  "driver_phone": "9876543211"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Ride completed successfully",
  "data": {
    "ride_id": 1,
    "status": "completed",
    "fare_amount": 50.50
  }
}
```

#### 7. Cancel Ride
- **Endpoint**: `POST /driver/cancel_ride`
- **Description**: Cancel accepted ride (reverts to pending)
- **Request Body**:
```json
{
  "driver_phone": "9876543211"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Ride cancelled successfully",
  "data": {
    "ride_id": 1,
    "status": "pending"
  }
}
```

#### 8. Get Current Ride
- **Endpoint**: `GET /driver/current_ride?phone=9876543211`
- **Description**: Get current active ride for driver
- **📱 Frontend Note**: Poll this endpoint every 10-15 seconds to track ride progress
- **Response**:
```json
{
  "status": "success",
  "message": "Current ride retrieved",
  "data": {
    "has_active_ride": true,
    "id": 1,
    "customer_phone": "9876543210",
    "customer_name": "John Doe",
    "status": "started",
    "pickup_address": "Connaught Place, New Delhi",
    "drop_address": "India Gate, New Delhi",
    "fare_amount": 50.50
  }
}
```

#### 9. Toggle Status (Online/Offline)
- **Endpoint**: `POST /driver/status`
- **Description**: Toggle driver availability for new ride requests
- **📱 Frontend Notes**: 
  - Drivers cannot go offline while having an active ride
  - Status persists in database
  - Use this to control ride dispatch eligibility
- **Request Body**:
```json
{
  "mobile": "9876543211",
  "is_online": true
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Driver status updated to online",
  "data": {
    "driver_id": 1,
    "name": "Test Driver",
    "phone": "9876543211",
    "is_online": true
  }
}
```

#### 10. Get Status
- **Endpoint**: `GET /driver/status?mobile=9876543211`
- **Description**: Get current driver online/offline status
- **📱 Frontend Note**: Use this to sync toggle switch state on driver app load
- **Response**:
```json
{
  "status": "success",
  "message": "Driver status retrieved",
  "data": {
    "is_online": true,
    "driver_id": 1,
    "name": "Test Driver",
    "phone": "9876543211"
  }
}
```

#### 11. Logout
- **Endpoint**: `POST /driver/logout`
- **Description**: Logout driver session
- **Response**:
```json
{
  "status": "success",
  "message": "Logout successful"
}
```

---

## 🔐 Admin Driver Management APIs

### 1. Create Driver Account
- **Endpoint**: `POST /admin/create_driver`
- **Description**: Create a new driver account with complete details (Admin only)
- **Authentication**: Admin login required
- **Request Body**:
```json
{
  "name": "Rajesh Kumar",
  "phone": "9876543333",
  "car_make": "Maruti",
  "car_model": "Swift Dzire", 
  "car_year": 2021,
  "license_number": "DL1420220012345",
  "car_number": "DL 14 CA 1234",
  "car_type": "sedan",
  "aadhaar_url": "https://example.com/aadhaar/123.jpg",
  "license_url": "https://example.com/license/123.jpg",
  "rcbook_url": "https://example.com/rcbook/123.jpg",
  "profile_photo_url": "https://example.com/profile/123.jpg"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Driver created successfully",
  "username": "DRVWR50FN",
  "password": "3333@Taxi"
}
}
```

### 2. Reset Driver Password
- **Endpoint**: `POST /admin/reset_driver_password`
- **Description**: Reset password for existing driver (Admin only)
- **Authentication**: Admin login required
- **Request Body**:
```json
{
  "username": "DRVWR50FN",
  "new_password": "NewSecure@123"
}
```
- **Response**:
```json
{
  "status": "success",
  "message": "Driver password reset successfully",
  "username": "DRVWR50FN",
  "password": "NewSecure@123"
}
```

### 3. Get Driver Details (with Password)
- **Endpoint**: `GET /admin/get_driver/{driver_id}`
- **Description**: Retrieve complete driver details including plain-text password for admin testing
- **Authentication**: Admin login required
- **Response**:
```json
{
  "success": true,
  "data": {
    "id": 5,
    "name": "Rajesh Kumar", 
    "phone": "9876543333",
    "username": "DRVWR50FN",
    "password": "3333@Taxi",
    "is_online": true,
    "car_make": "Maruti",
    "car_model": "Swift Dzire",
    "car_year": 2021,
    "car_number": "DL 14 CA 1234",
    "car_type": "sedan",
    "license_number": "DL1420220012345",
    "profile_photo_url": "https://example.com/profile/123.jpg",
    "aadhaar_url": "https://example.com/aadhaar/123.jpg",
    "license_url": "https://example.com/license/123.jpg",
    "rcbook_url": "https://example.com/rcbook/123.jpg"
  }
}
```

### Key Features:
- **Auto-generated Usernames**: Format DRVAB12CD (DRV + 2 letters + 2 digits + 2 letters)
- **Auto-generated Passwords**: Last 4 digits of phone + "@Taxi" (e.g., "3333@Taxi")
- **Secure Password Storage**: All passwords hashed using Werkzeug
- **Comprehensive Validation**: Phone numbers, required fields, duplicate checking
- **Enhanced Driver Model**: Includes vehicle details, license info, and document URLs

### ⚠️ Password Testing Features
**FOR ADMIN TESTING ONLY - REMOVE BEFORE PRODUCTION**
- All driver management APIs return plain-text passwords in responses
- Admin edit modal displays current password in plain text
- GET /admin/get_driver endpoint provides password for admin testing
- Passwords are NOT stored in plain text in database (generated on-demand)
- **CRITICAL**: Remove these features before production deployment

## 🎯 Frontend Implementation Guide

### Customer App Requirements

#### 1. Login/Register Screen
- **Fields**: Phone (10-digit), Name
- **Validation**: Phone must start with 6-9
- **API**: POST `/customer/login_or_register`
- **Success**: Navigate to booking screen

#### 2. Ride Booking Screen
- **Fields**: Pickup Address, Drop Address, Location coordinates (optional)
- **Validation**: Both addresses required
- **API**: POST `/customer/book_ride`
- **Success**: Navigate to ride tracking screen

#### 3. Ride Tracking Screen
- **Display**: Ride status, driver info (when assigned), fare, addresses
- **Polling**: GET `/customer/ride_status` every 10-15 seconds
- **Actions**: Cancel ride button (only for pending/accepted status)
- **States**: pending → accepted → arrived → started → completed

#### 4. Ride History Screen (Optional)
- **Display**: Past rides with status and fare
- **Note**: Backend does not provide history API - frontend must track locally

### Driver App Requirements

#### 1. Login/Register Screen
- **Fields**: Phone (10-digit), Name
- **Validation**: Phone must start with 6-9
- **API**: POST `/driver/login_or_register`
- **Success**: Navigate to rides screen

#### 2. Available Rides Screen
- **Display**: List of pending rides with customer details, pickup/drop addresses
- **Polling**: GET `/driver/incoming_rides` every 10-15 seconds
- **Actions**: Accept ride button
- **Location**: Send driver's current location for distance calculation

#### 3. Active Ride Screen
- **Display**: Current ride details, customer info, addresses
- **Actions**: 
  - "Arrived" button (when accepted)
  - "Start Ride" button (when arrived)
  - "Complete Ride" button (when started)
  - "Cancel Ride" button (when accepted/arrived)
- **Polling**: GET `/driver/current_ride` for updates

### Admin Dashboard (Already Implemented)

#### 1. Login Screen (`/admin/login`)
- **Credentials**: admin / admin123
- **Features**: Session-based authentication

#### 2. Dashboard (`/admin/dashboard`)
- **Stats**: Total customers, drivers, rides
- **Charts**: Ride status breakdown
- **Recent**: Last 10 rides table
- **Auto-refresh**: Every 30 seconds (improved with better error handling)
- **Clear Logs**: Button to delete ALL rides regardless of status

#### 3. Rides Management (`/admin/rides`)
- **Filters**: All, Pending, Accepted, Completed, Cancelled
- **Actions**: Cancel ride button
- **Pagination**: 20 rides per page
- **Details**: Full ride information

#### 4. Users Management (`/admin/customers`, `/admin/drivers`)
- **Display**: User info, ride counts, activity
- **Pagination**: 20 users per page

## 🔒 Authentication & Session Management

### Session Handling
- **Type**: Server-side sessions using Flask-Login
- **Storage**: Session cookies
- **Timeout**: Default Flask session timeout
- **Security**: CSRF protection enabled
- **📱 Frontend Requirement**: All API calls must be sent with `credentials: 'include'` for session continuity

### API Security
- **CORS**: Enabled with credentials support
- **Validation**: Input validation on all endpoints
- **Phone Format**: Automatic +91 prefix removal
- **Error Handling**: Standardized error responses

## 📊 Data Models

### Customer
- **ID**: Auto-increment primary key
- **Name**: String, required
- **Phone**: 10-digit string, unique
- **Created At**: Timestamp with IST timezone

### Driver
- **ID**: Auto-increment primary key
- **Name**: String, required
- **Phone**: 10-digit string, unique
- **Username**: Auto-generated unique string (DRVAB12CD format)
- **Password Hash**: Securely hashed password using Werkzeug
- **Is Online**: Boolean, default=True (tracks driver availability for new rides)
- **Created At**: Timestamp with IST timezone

**Vehicle Details:**
- **Car Make**: String (e.g., Maruti, Honda)
- **Car Model**: String (e.g., Swift Dzire, City)
- **Car Year**: Integer
- **Car Number**: String (e.g., DL 14 CA 1234)
- **Car Type**: String (sedan, suv, hatchback, etc.)

**License and Documents:**
- **License Number**: String
- **Aadhaar URL**: String (URL to Aadhaar card image)
- **License URL**: String (URL to driving license image)
- **RC Book URL**: String (URL to vehicle registration certificate)
- **Profile Photo URL**: String (URL to driver's profile photo)

### Ride
- **ID**: Auto-increment primary key
- **Customer**: Foreign key to Customer
- **Driver**: Foreign key to Driver (nullable)
- **Addresses**: Pickup and drop addresses (text)
- **Coordinates**: Pickup and drop lat/lng (optional)
- **Distance**: Distance in kilometers
- **Fare**: Calculated fare amount
- **Status**: pending → accepted → arrived → started → completed/cancelled
- **Timestamps**: Created, accepted, arrived, started, completed, cancelled

### Admin
- **ID**: Auto-increment primary key
- **Username**: String, unique
- **Password**: String (plain text - should be hashed in production)
- **Created At**: Timestamp with IST timezone

## 🗺️ Google Maps Integration (✅ ACTIVE)

### Distance Matrix API
- **Status**: ✅ **FULLY CONFIGURED AND WORKING**
- **Purpose**: Calculate real road distance and travel time between pickup and drop locations
- **API Key**: Configured in environment variables
- **Testing**: Verified with real Delhi locations (Connaught Place to India Gate: 5.03km)
- **Fallback**: Error handling for API failures
- **Usage**: Both address-based and coordinate-based lookups are supported
- **Real Example**: Connaught Place → India Gate = 5.03km actual road distance

### Fare Calculation
- **Status**: ✅ **ACTIVE WITH REAL DATA**
- **Base Fare**: ₹12
- **Per KM Rate**: ₹11
- **Formula**: `fare = ₹12 + (₹11 × distance_km)`
- **Example**: 5.03km ride = ₹12 + (₹11 × 5.03) = ₹67.33
- **Rounding**: Final fare is rounded to 2 decimal places

## 🛰️ GPS Tracking System (✅ ACTIVE)

### Real-time Location Tracking
- **Status**: ✅ **FULLY IMPLEMENTED AND OPERATIONAL**
- **Purpose**: Track driver location in real-time during active rides
- **Database**: Optimized RideLocation table with performance indexes
- **Security**: Coordinate validation and ride status verification

### Driver Location Updates
- **Endpoint**: `POST /driver/update_location`
- **Frequency**: Every 15-30 seconds (recommended)
- **Validation**: Latitude (-90 to +90), Longitude (-180 to +180)
- **Active Rides Only**: Updates only allowed for accepted/arrived/started rides
- **Latest Flag**: Automatically marks newest location as `is_latest=true`

### Customer Location Retrieval
- **Endpoint**: `GET /customer/driver_location/{ride_id}`
- **Performance**: Sub-millisecond response with optimized indexes
- **Data**: Current driver coordinates, timestamp, ride status, pickup/drop locations
- **Real-time**: Shows live driver movement toward pickup point

### Database Schema
```sql
-- Optimized for fast lookups and historical preservation
CREATE TABLE ride_location (
    id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timestamp DATETIME NOT NULL,
    is_latest BOOLEAN NOT NULL DEFAULT false
);

-- Performance indexes
CREATE INDEX idx_ride_location_ride_latest ON ride_location(ride_id, is_latest);
CREATE INDEX idx_ride_location_timestamp ON ride_location(timestamp DESC);
```

### Location History Preservation
- **Complete Routes**: All GPS points preserved for completed rides
- **Analytics Ready**: Historical data available for route analysis
- **Audit Trail**: Full movement history for support and investigations
- **Performance**: Latest location indexed for instant customer queries

### Integration Examples
**Driver Update:**
```bash
curl -X POST /driver/update_location -d '{
  "driver_phone": "9876543210",
  "ride_id": 123,
  "latitude": 28.6139,
  "longitude": 77.2090
}'
```

**Customer Retrieval:**
```bash
curl /customer/driver_location/123
# Returns: {latitude, longitude, timestamp, ride_status, pickup/drop coords}
```

## 🚨 Error Handling

### API Errors
- **Format**: Standardized JSON error responses
- **Status Codes**: 400 (Bad Request), 500 (Internal Server Error)
- **Messages**: Clear, user-friendly error messages

### Standard Error Format
```json
{
  "status": "error",
  "message": "Clear description here",
  "data": null
}
```

### Common Errors
- **Invalid Phone**: "Invalid phone number format"
- **Missing Fields**: "Missing required fields: pickup_address, drop_address"
- **Ongoing Ride**: "You already have an ongoing ride"
- **Ride Not Found**: "Ride not available or already accepted"
- **Maps API**: "Could not calculate distance"
- **Already Has Active Ride**: "Customer already has an active ride"
- **Missing Pickup Address**: "Pickup address is required"
- **Missing Drop Address**: "Drop address is required"

## 📱 Frontend Connection Guidelines

### HTTP Requests
- **Base URL**: Use environment-specific base URL
- **Headers**: `Content-Type: application/json`
- **Credentials**: Include `credentials: 'include'` for session cookies (REQUIRED)
- **Method**: Use appropriate HTTP methods (GET, POST)

### Polling Strategy
- **Customer `/customer/ride_status`**: Poll every 10-15 seconds
- **Driver `/driver/incoming_rides`**: Poll every 10-15 seconds
- **Driver `/driver/current_ride`**: Poll every 10-15 seconds
- **Error Handling**: Continue polling on errors, show user-friendly messages
- **UI States**: Show "searching for driver..." while status is `pending`

### State Management
- **Sessions**: Handle session expiration gracefully
- **Offline**: Show appropriate messages when backend is unreachable
- **Loading**: Show loading states during API calls

### Frontend Responsibilities
- **Route Mapping**: Frontend should draw the pickup→drop route on Google Maps
- **Fare Display**: Show calculated fare to customer **before** final ride confirmation
- **Location Services**: Frontend must retrieve lat/lng using device GPS and send with ride request
- **Ride History**: Since there is no ride history API, frontend should store ride history locally if needed
- **Session Management**: All requests must include `credentials: 'include'` to maintain Flask-Login sessions

## ❌ Backend Limitations

### Features NOT Supported
- **OTP/SMS Verification**: No SMS/OTP system implemented
- **Payment or Billing APIs**: No payment gateway integration
- **Push Notifications**: No real-time notifications
- **Real-time Driver Location**: No WebSocket or real-time location tracking via WebSockets
- **Ratings/Reviews**: No rating system for rides or drivers
- **Profile Edit/Update Endpoints**: No user profile update endpoints
- **Ride History API**: No endpoint for historical rides

### Frontend Must Handle
- **Local Storage**: Store user preferences and temporary data
- **Location Services**: Handle GPS and location permissions
- **UI/UX**: Complete user interface design and interactions
- **Offline Mode**: Handle network connectivity issues
- **Input Validation**: Client-side validation in addition to server-side
- **Error Recovery**: Retry logic and error recovery strategies
- **Ride History**: Store ride history locally if needed (no backend API available)

## 🔧 Troubleshooting Common Issues

### Driver App Login Problems
**Issue**: Driver app cannot login successfully
**✅ Backend Status**: Driver login endpoint is fully functional and tested
**Common Causes**:
1. **Missing credentials**: Frontend must include `credentials: 'include'` in fetch request
2. **Wrong Content-Type**: Must send `Content-Type: application/json` header
3. **Invalid phone format**: Phone must be exactly 10 digits starting with 6-9
4. **Missing session handling**: All subsequent requests must include `credentials: 'include'`

**Correct Implementation**:
```javascript
fetch('/driver/login_or_register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',  // CRITICAL: Required for sessions
  body: JSON.stringify({
    phone: '9876543211',    // 10 digits starting with 6-9
    name: 'Driver Name'
  })
})
```

### Admin Dashboard Stats Errors
**Issue**: "Error refreshing stats" in console
**✅ Fix Applied**: Enhanced error handling and element existence checks
**Status**: Fixed in current version

### Clear Logs Function
**Issue**: Clear logs only cleared some rides
**✅ Fix Applied**: Now deletes ALL rides regardless of status
**Status**: Fixed - shows exact count of cleared rides

## 🔧 Setup & Configuration

### Environment Variables
- **DATABASE_URL**: PostgreSQL connection string (automatically configured)
- **GOOGLE_MAPS_API_KEY**: Google Maps API key for distance calculation (✅ CONFIGURED)
- **SESSION_SECRET**: Secret key for session encryption (automatically configured)

### Installation
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables
3. Run application: `python main.py` or `gunicorn main:app`

### Database
- **Development**: SQLite (automatic)
- **Production**: PostgreSQL (via DATABASE_URL)
- **Auto-migration**: Tables created automatically on startup

---

## 📝 Changelog

### Version 1.0 (July 5, 2025)
- ✅ Complete customer API implementation
- ✅ Complete driver API implementation  
- ✅ Admin dashboard with full UI
- ✅ Google Maps integration (FULLY CONFIGURED AND TESTED)
- ✅ Session-based authentication
- ✅ Phone number validation for Indian numbers
- ✅ Ride lifecycle management
- ✅ Error handling and logging
- ✅ Dark theme admin interface
- ✅ Responsive design
- ✅ Database models and relationships
- ✅ Asia/Kolkata timezone support
- ✅ Real distance calculation with Google Maps API
- ✅ Production-ready deployment on Replit
- ✅ Clear logs functionality (deletes ALL rides regardless of status)
- ✅ Enhanced admin dashboard with improved stats refresh
- ✅ Driver login endpoint fully tested and working

### Version 1.1 (July 6, 2025)
- ✅ **NEW: Driver Online/Offline Toggle**
  - Added `is_online` field to Driver model (default: true)
  - POST `/driver/status` endpoint to toggle availability  
  - GET `/driver/status` endpoint to check current status
  - Ride dispatch integration: Only online drivers receive ride requests
  - Protection: Drivers cannot go offline while having active rides
  - Status persists in database across sessions

- ✅ **NEW: Login-Aware Landing Page**
  - Root route `/` now automatically redirects based on authentication status
  - Authenticated admins redirect to `/admin/dashboard`
  - Non-authenticated users redirect to `/admin/login`
  - Improved user experience with seamless navigation
  - Server-side session management using Flask-Login

- ✅ **NEW: Admin Driver Management System**
  - Complete admin-side driver account creation and management
  - POST `/admin/create_driver` endpoint with comprehensive driver details
  - POST `/admin/reset_driver_password` endpoint for password management
  - Auto-generated usernames (DRVAB12CD format) and passwords
  - Enhanced Driver model with vehicle and document information
  - Secure password hashing using Werkzeug

- ✅ **NEW: Enhanced Customer Ride API with Driver Details**
  - Customer ride status API now includes complete driver information when assigned
  - Driver details: name, phone, car make/model/year, car number, car type, photo URL
  - Proper null handling for pending rides (no driver assigned)
  - Real-time driver information for improved customer experience
