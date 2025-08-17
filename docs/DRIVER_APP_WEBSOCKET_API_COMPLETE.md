# 🚗 A1 Taxi Driver App WebSocket & API Integration Guide

## 📡 **WebSocket Connection & Events**

### **1. WebSocket Connection Setup**

**Driver App Connection:**
```javascript
// Initialize Socket.IO connection
const socket = io('https://your-backend-url.com', {
    transports: ['websocket', 'polling'],
    upgrade: true,
    timeout: 10000,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 2000
});

// Connect as driver with phone number
socket.emit('driver_connect', {
    driver_phone: '9988776655',  // Driver's phone number
    driver_id: 20               // Optional: Driver ID if known
});
```

**Connection Response Events:**
```javascript
// Successfully connected
socket.on('connection_established', (data) => {
    console.log('Connected:', data);
    // Response: {"status": "connected", "driver_id": 20}
});

// Connection error
socket.on('error', (data) => {
    console.log('Error:', data.message);
    // Response: {"message": "Driver identification required"}
});
```

---

### **2. Real-Time GPS Location Updates**

**Send Location Update via WebSocket:**
```javascript
socket.emit('driver_location_update', {
    latitude: 13.0444052,
    longitude: 80.1763357,
    driver_phone: '9988776655',  // Required for identification
    driver_id: 20,              // Optional
    timestamp: new Date().toISOString()  // Optional
});
```

**Location Update Response:**
```javascript
socket.on('location_update_success', (data) => {
    console.log('Location updated:', data);
    /* Response:
    {
        "driver_id": 20,
        "latitude": 13.0444052,
        "longitude": 80.1763357,
        "timestamp": "2025-08-18T01:30:00.000000"
    }
    */
});
```

---

### **3. Ride Request Events (Real-Time)**

**Receive New Ride Requests:**
```javascript
socket.on('new_ride_request', (rideData) => {
    console.log('New ride request:', rideData);
    /* Ride Data Structure:
    {
        "ride_id": 123,
        "customer_name": "John Doe",
        "customer_phone": "9876543210",
        "pickup_address": "123 Main St, Chennai",
        "pickup_lat": 13.0827,
        "pickup_lng": 80.2707,
        "drop_address": "456 Park Ave, Chennai", 
        "drop_lat": 13.0878,
        "drop_lng": 80.2785,
        "fare_amount": 150.0,
        "ride_type": "sedan",
        "distance_km": 8.5,
        "estimated_time": "25 mins",
        "created_at": "2025-08-18T01:30:00",
        "special_requests": "Handle with care"
    }
    */
    
    // Show ride request UI to driver
    showRideRequestDialog(rideData);
});
```

**Ride Status Updates:**
```javascript
socket.on('ride_status_updated', (data) => {
    console.log('Ride status changed:', data);
    /* Status Update Data:
    {
        "ride_id": 123,
        "status": "accepted|arrived|started|completed|cancelled",
        "driver_id": 20,
        "customer_id": 15,
        "driver_name": "Ricco",
        "customer_name": "John Doe",
        "timestamp": "2025-08-18T01:35:00",
        "fare_amount": 150.0
    }
    */
    
    // Update UI based on ride status
    updateRideStatus(data.status, data);
});
```

---

## 🔄 **HTTP API Endpoints**

### **1. Driver Authentication**

**Login:**
```http
POST /driver/login
Content-Type: application/json

{
    "username": "DRVVJ53TA",
    "password": "6655@Taxi"
}
```

**Login Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "driver_id": 20,
        "name": "Ricco",
        "phone": "9988776655",
        "username": "DRVVJ53TA",
        "car_type": "sedan",
        "car_make": "Maruti",
        "car_model": "Ciaz",
        "car_number": "TN29AQ1288",
        "is_online": true,
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_expires": "2025-08-25T01:30:00"
    }
}
```

**Logout:**
```http
POST /driver/logout
Authorization: Bearer <JWT_TOKEN>
```

**Heartbeat (Keep Session Alive):**
```http
POST /driver/heartbeat  
Authorization: Bearer <JWT_TOKEN>
```

---

### **2. Location Updates (HTTP Fallback)**

**Update Current Location:**
```http
POST /driver/update_current_location
Content-Type: application/json

{
    "latitude": 13.0444052,
    "longitude": 80.1763357,
    "driver_phone": "9988776655"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Location updated successfully",
    "data": {
        "driver_id": 20,
        "latitude": 13.0444052,
        "longitude": 80.1763357,
        "is_online": true,
        "zone": "chennai",
        "out_of_zone": false,
        "updated_at": "2025-08-18T01:30:00.000000"
    }
}
```

---

### **3. Ride Management**

**Get Available Rides:**
```http
GET /driver/incoming_rides?driver_phone=9988776655
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
    "success": true,
    "message": "Incoming rides retrieved",
    "data": {
        "rides": [
            {
                "ride_id": 123,
                "customer_name": "John Doe",
                "customer_phone": "9876543210",
                "pickup_address": "123 Main St, Chennai",
                "pickup_lat": 13.0827,
                "pickup_lng": 80.2707,
                "drop_address": "456 Park Ave, Chennai",
                "drop_lat": 13.0878,
                "drop_lng": 80.2785,
                "fare_amount": 150.0,
                "ride_type": "sedan",
                "distance_km": 8.5,
                "distance_to_pickup_km": 2.1,
                "estimated_time": "25 mins",
                "created_at": "2025-08-18T01:30:00"
            }
        ],
        "count": 1
    }
}
```

**Accept Ride:**
```http
POST /driver/accept_ride
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "ride_id": 123
}
```

**Accept Ride Response:**
```json
{
    "success": true,
    "message": "Ride accepted successfully", 
    "data": {
        "ride_id": 123,
        "status": "accepted",
        "customer_name": "John Doe",
        "pickup_address": "123 Main St, Chennai",
        "drop_address": "456 Park Ave, Chennai",
        "fare_amount": 150.0,
        "start_otp": "123456"
    }
}
```

**Reject Ride:**
```http
POST /driver/reject_ride
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "ride_id": 123
}
```

**Mark Arrived:**
```http
POST /driver/arrived
Authorization: Bearer <JWT_TOKEN>
```

**Start Ride (with OTP):**
```http
POST /driver/start_ride
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "ride_id": 123,
    "otp": "123456"
}
```

**Complete Ride:**
```http
POST /driver/complete_ride
Authorization: Bearer <JWT_TOKEN>
```

**Response Format (Standard):**
```json
{
    "success": true,
    "message": "Operation successful",
    "data": {
        "ride_id": 123,
        "status": "completed",
        "fare_amount": 150.0
    }
}
```

---

## ⚠️ **Error Responses**

**Standard Error Format:**
```json
{
    "success": false,
    "message": "Error description",
    "error": "INVALID_TOKEN|DRIVER_NOT_FOUND|RIDE_NOT_AVAILABLE"
}
```

**Common Error Codes:**
- `401`: Authentication required / Invalid token
- `403`: Access denied / Invalid OTP
- `404`: Driver/Ride not found
- `409`: Conflict (already have active ride)
- `422`: Validation error (missing fields)
- `500`: Internal server error

---

## 🔧 **WebSocket Error Events**

```javascript
socket.on('error', (error) => {
    console.log('WebSocket Error:', error);
    /* Common Error Messages:
    - "Driver identification required"  
    - "Driver not found"
    - "Missing latitude or longitude"
    - "Location update failed"
    - "Connection failed"
    */
});

socket.on('disconnect', (reason) => {
    console.log('Disconnected:', reason);
    /* Disconnect Reasons:
    - "io server disconnect" (server initiated)
    - "io client disconnect" (client initiated) 
    - "ping timeout" (connection lost)
    - "transport close" (network issue)
    */
});
```

---

## 🚀 **Complete Driver App Integration Example**

```javascript
class DriverAppWebSocket {
    constructor(serverUrl, driverPhone) {
        this.serverUrl = serverUrl;
        this.driverPhone = driverPhone;
        this.socket = null;
        this.isConnected = false;
    }
    
    connect() {
        this.socket = io(this.serverUrl, {
            transports: ['websocket', 'polling'],
            timeout: 10000,
            reconnection: true,
            reconnectionAttempts: 5
        });
        
        // Connection events
        this.socket.on('connect', () => {
            console.log('✅ Connected to server');
            this.socket.emit('driver_connect', {
                driver_phone: this.driverPhone
            });
        });
        
        this.socket.on('connection_established', (data) => {
            console.log('✅ Driver authenticated:', data);
            this.isConnected = true;
            this.startLocationUpdates();
        });
        
        // Ride events
        this.socket.on('new_ride_request', (ride) => {
            this.handleNewRideRequest(ride);
        });
        
        this.socket.on('ride_status_updated', (data) => {
            this.handleRideStatusUpdate(data);
        });
        
        // Location events
        this.socket.on('location_update_success', (data) => {
            console.log('📍 Location updated:', data);
        });
        
        // Error handling
        this.socket.on('error', (error) => {
            console.error('❌ WebSocket error:', error);
        });
    }
    
    sendLocationUpdate(lat, lng) {
        if (this.isConnected) {
            this.socket.emit('driver_location_update', {
                latitude: lat,
                longitude: lng,
                driver_phone: this.driverPhone,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    startLocationUpdates() {
        // Send location every 30 seconds
        setInterval(() => {
            navigator.geolocation.getCurrentPosition((position) => {
                this.sendLocationUpdate(
                    position.coords.latitude,
                    position.coords.longitude
                );
            });
        }, 30000);
    }
    
    handleNewRideRequest(ride) {
        // Show ride request UI
        console.log('🚗 New ride request:', ride);
        // Display pickup/drop locations, fare, etc.
    }
    
    handleRideStatusUpdate(data) {
        // Update current ride status in UI
        console.log('📊 Ride status:', data.status);
    }
}

// Initialize driver app
const driverApp = new DriverAppWebSocket(
    'https://your-backend.com', 
    '9988776655'
);
driverApp.connect();
```

---

## 🏷️ **WebSocket Event Summary**

### **Outgoing Events (Driver App → Server):**
- `driver_connect` - Initial connection with phone number
- `driver_location_update` - Real-time GPS coordinates

### **Incoming Events (Server → Driver App):**
- `connection_established` - Confirms successful connection
- `new_ride_request` - New ride available for acceptance
- `ride_status_updated` - Status changes for current ride
- `location_update_success` - Confirms GPS update received
- `error` - Error messages and failures

### **HTTP Endpoints Summary:**

#### **Core Driver Operations:**
- `POST /driver/login` - Authenticate with username/password
- `POST /driver/logout` - End session
- `POST /driver/heartbeat` - Keep session alive
- `POST /driver/update_current_location` - HTTP GPS fallback
- `GET /driver/incoming_rides` - Fetch available rides
- `POST /driver/accept_ride` - Accept a ride request
- `POST /driver/reject_ride` - Reject a ride request  
- `POST /driver/arrived` - Mark arrived at pickup
- `POST /driver/start_ride` - Start ride with OTP
- `POST /driver/complete_ride` - Mark ride complete

#### **Extended Mobile App Endpoints:**
- `GET /mobile/driver/profile?username=DRVVJ53TA` - Get driver profile details
- `GET /mobile/driver/history?username=DRVVJ53TA&offset=0&limit=20` - Get ride history
- `GET /mobile/active_drivers_count` - Count of active drivers (public)
- `GET /mobile/driver_locations` - All driver locations for map (public)

---

## 📊 **Additional Mobile API Examples**

### **Driver Profile:**
```http
GET /mobile/driver/profile?username=DRVVJ53TA
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
    "success": true,
    "message": "Driver profile retrieved successfully",
    "data": {
        "id": 20,
        "username": "DRVVJ53TA",
        "name": "Ricco",
        "phone": "9988776655",
        "is_online": true,
        "car_make": "Maruti",
        "car_model": "Ciaz", 
        "car_year": 2003,
        "car_number": "TN29AQ1288",
        "car_type": "sedan",
        "license_number": "TN1234567890",
        "aadhaar_url": "https://example.com/aadhaar.pdf",
        "license_url": "https://example.com/license.pdf",
        "rcbook_url": "https://example.com/rc.pdf",
        "profile_photo_url": "https://example.com/photo.jpg"
    }
}
```

### **Driver History:**
```http
GET /mobile/driver/history?username=DRVVJ53TA&offset=0&limit=10
Authorization: Bearer <JWT_TOKEN>
```

**Response:**
```json
{
    "success": true,
    "message": "Driver history retrieved successfully",
    "data": {
        "rides": [
            {
                "ride_id": 123,
                "customer_name": "John Doe",
                "pickup_address": "123 Main St, Chennai",
                "drop_address": "456 Park Ave, Chennai",
                "fare_amount": 150.0,
                "status": "completed",
                "created_at": "2025-08-18T01:30:00",
                "completed_at": "2025-08-18T02:15:00"
            }
        ],
        "pagination": {
            "offset": 0,
            "limit": 10,
            "total": 45,
            "has_more": true
        }
    }
}
```

### **Active Drivers Count:**
```http
GET /mobile/active_drivers_count
```

**Response:**
```json
{
    "success": true,
    "count": 12,
    "message": "12 active drivers found"
}
```

### **Driver Locations (Map View):**
```http
GET /mobile/driver_locations
```

**Response:**
```json
{
    "success": true,
    "drivers": [
        {
            "id": 20,
            "name": "Ricco",
            "lat": 13.0444052,
            "lng": 80.1763357,
            "is_online": true,
            "car_type": "sedan",
            "car_number": "TN29AQ1288",
            "location_updated_at": "2025-08-18T01:30:00"
        }
    ],
    "count": 1,
    "message": "1 driver locations retrieved"
}
```

This comprehensive guide covers all WebSocket hooks, API formats, and response structures for seamless driver app integration with your A1 Taxi platform!