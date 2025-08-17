# 📱 A1 Taxi Customer App WebSocket & API Integration Guide

## 📡 **WebSocket Connection & Real-Time Events**

### **1. Customer WebSocket Connection Setup**

**Customer App Connection:**
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

// Connect as customer with customer ID (after login)
socket.emit('customer_connect', {
    customer_id: 15,
    customer_phone: '9876543210'  // Optional: Customer's phone number
});
```

**Connection Response Events:**
```javascript
// Successfully connected
socket.on('connection_established', (data) => {
    console.log('Connected:', data);
    // Response: {"status": "connected", "customer_id": 15}
});

// Connection error
socket.on('error', (data) => {
    console.log('Error:', data.message);
    // Response: {"message": "Customer identification required"}
});
```

---

### **2. Real-Time Ride Status Updates**

**Receive Ride Status Updates:**
```javascript
socket.on('ride_status_updated', (rideData) => {
    console.log('Ride status changed:', rideData);
    /* Ride Status Update Structure:
    {
        "ride_id": 123,
        "status": "pending|accepted|arrived|started|completed|cancelled",
        "driver_id": 20,
        "customer_id": 15,
        "driver_name": "Ricco",
        "customer_name": "John Doe",
        "pickup_address": "123 Main St, Chennai",
        "drop_address": "456 Park Ave, Chennai",
        "fare_amount": 150.0,
        "driver_phone": "9988776655",
        "driver_car_number": "TN29AQ1288",
        "driver_car_type": "sedan",
        "start_otp": "123456",  // Only when status is 'accepted'
        "timestamp": "2025-08-18T01:35:00"
    }
    */
    
    // Update UI based on ride status
    updateRideStatus(rideData.status, rideData);
    
    // Handle specific status changes
    switch(rideData.status) {
        case 'accepted':
            showDriverDetails(rideData);
            displayStartOTP(rideData.start_otp);
            break;
        case 'arrived':
            showDriverArrivedNotification();
            break;
        case 'started':
            startRideTracking(rideData.ride_id);
            break;
        case 'completed':
            showPaymentSummary(rideData.fare_amount);
            break;
        case 'cancelled':
            showRideCancelledMessage();
            break;
    }
});
```

---

## 🔄 **HTTP API Endpoints**

### **1. Customer Authentication**

**Login/Register (Combined):**
```http
POST /customer/login_or_register
Content-Type: application/json

{
    "phone": "9876543210",
    "name": "John Doe"
}
```

**Login/Register Response:**
```json
{
    "success": true,
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "customer": {
        "id": 15,
        "phone": "9876543210",
        "name": "John Doe"
    }
}
```

**Logout:**
```http
POST /customer/logout
Authorization: Bearer <JWT_TOKEN>
```

**Heartbeat (Keep Session Alive):**
```http
POST /customer/heartbeat
Authorization: Bearer <JWT_TOKEN>
```

---

### **2. Ride Booking & Management**

**Get Fare Estimate:**
```http
POST /customer/ride_estimate
Content-Type: application/json

{
    "pickup_lat": 13.0444052,
    "pickup_lng": 80.1763357,
    "drop_lat": 13.0878234,
    "drop_lng": 80.2785456,
    "promo_code": "DISCOUNT10"  // Optional
}
```

**Fare Estimate Response:**
```json
{
    "success": true,
    "distance_km": 8.5,
    "estimated_time": "25 mins",
    "estimates": {
        "hatchback": {
            "fare": 120.0,
            "vehicle_type": "hatchback",
            "available": true
        },
        "sedan": {
            "fare": 150.0,
            "vehicle_type": "sedan", 
            "available": true
        },
        "suv": {
            "fare": 200.0,
            "vehicle_type": "suv",
            "available": true
        }
    },
    "promo_code_info": {
        "code": "DISCOUNT10",
        "discount_type": "percentage",
        "discount_value": 10,
        "applicable": true,
        "savings": 15.0
    }
}
```

**Book Ride:**
```http
POST /customer/book_ride
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "customer_phone": "9876543210",
    "pickup_address": "123 Main St, Chennai",
    "pickup_lat": 13.0444052,
    "pickup_lng": 80.1763357,
    "drop_address": "456 Park Ave, Chennai",
    "drop_lat": 13.0878234,
    "drop_lng": 80.2785456,
    "ride_type": "sedan",
    "ride_category": "regular",
    "promo_code": "DISCOUNT10",
    "special_requests": "Handle with care",
    "scheduled_date": "2025-08-18",
    "scheduled_time": "14:30"
}
```

**Book Ride Response:**
```json
{
    "success": true,
    "message": "Ride booked successfully",
    "data": {
        "ride_id": 123,
        "status": "pending",
        "pickup_address": "123 Main St, Chennai",
        "drop_address": "456 Park Ave, Chennai",
        "fare_amount": 135.0,  // After promo discount
        "original_fare": 150.0,
        "discount_applied": 15.0,
        "ride_type": "sedan",
        "distance_km": 8.5,
        "estimated_time": "25 mins",
        "promo_code_used": "DISCOUNT10"
    }
}
```

**Get Current Ride Status:**
```http
GET /customer/ride_status?phone=9876543210
Authorization: Bearer <JWT_TOKEN>
```

**Ride Status Response:**
```json
{
    "success": true,
    "message": "Ride status retrieved",
    "data": {
        "has_active_ride": true,
        "ride_id": 123,
        "status": "accepted",
        "customer_id": 15,
        "customer_name": "John Doe",
        "driver_id": 20,
        "driver_name": "Ricco",
        "driver_phone": "9988776655",
        "pickup_address": "123 Main St, Chennai",
        "drop_address": "456 Park Ave, Chennai",
        "fare_amount": 135.0,
        "start_otp": "123456",
        "created_at": "2025-08-18T01:30:00",
        "accepted_at": "2025-08-18T01:32:00"
    }
}
```

**Cancel Ride:**
```http
POST /customer/cancel_ride
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json

{
    "phone": "9876543210"
}
```

---

### **3. Real-Time Driver Tracking**

**Get Driver Location:**
```http
GET /customer/driver_location/123
```

**Driver Location Response:**
```json
{
    "ride_id": 123,
    "latitude": 13.0444052,
    "longitude": 80.1763357,
    "timestamp": "2025-08-18T01:35:00",
    "ride_status": "started",
    "pickup_lat": 13.0444052,
    "pickup_lng": 80.1763357,
    "drop_lat": 13.0878234,
    "drop_lng": 80.2785456
}
```

---

### **4. Customer Profile & History**

**Get Customer Bookings:**
```http
GET /customer/bookings/15
Authorization: Bearer <JWT_TOKEN>
```

**Bookings Response:**
```json
{
    "success": true,
    "data": {
        "customer_id": 15,
        "bookings": [
            {
                "ride_id": 125,
                "status": "pending",
                "pickup_address": "Home",
                "drop_address": "Office",
                "fare_amount": 120.0,
                "created_at": "2025-08-18T09:00:00"
            }
        ],
        "ongoing": [
            {
                "ride_id": 123,
                "status": "started", 
                "driver_name": "Ricco",
                "pickup_address": "Office",
                "drop_address": "Mall",
                "fare_amount": 150.0
            }
        ],
        "history": [
            {
                "ride_id": 122,
                "status": "completed",
                "pickup_address": "Mall",
                "drop_address": "Home", 
                "fare_amount": 100.0,
                "completed_at": "2025-08-17T20:30:00"
            }
        ]
    }
}
```

---

### **5. Additional Features**

**Get Advertisements:**
```http
GET /customer/advertisements?location=chennai&ride_type=sedan
```

**Advertisements Response:**
```json
{
    "success": true,
    "data": {
        "advertisements": [
            {
                "id": 1,
                "title": "Summer Special - 20% Off",
                "description": "Book rides in summer and save 20%",
                "media_url": "/static/ads/summer_offer.jpg",
                "display_duration": 5,
                "is_active": true
            }
        ],
        "total_ads": 1,
        "total_duration_seconds": 5,
        "slideshow_config": {
            "auto_advance": true,
            "loop": true,
            "show_controls": false
        }
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
    "error": "INVALID_TOKEN|CUSTOMER_NOT_FOUND|ONGOING_RIDE_EXISTS"
}
```

**Common Error Scenarios:**
- `401`: Authentication required / Invalid token
- `400`: Missing required fields / Invalid data
- `409`: Customer already has ongoing ride
- `404`: Customer/Ride not found
- `500`: Internal server error / Google Maps API issues

---

## 🔧 **WebSocket Error Events**

```javascript
socket.on('error', (error) => {
    console.log('WebSocket Error:', error);
    /* Common Error Messages:
    - "Customer identification required"  
    - "Customer not found"
    - "Authentication required"
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
    
    // Attempt reconnection for customer apps
    setTimeout(() => {
        socket.connect();
    }, 2000);
});
```

---

## 🚀 **Complete Customer App Integration Example**

```javascript
class CustomerAppWebSocket {
    constructor(serverUrl, customerId, customerPhone) {
        this.serverUrl = serverUrl;
        this.customerId = customerId;
        this.customerPhone = customerPhone;
        this.socket = null;
        this.isConnected = false;
        this.currentRide = null;
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
            this.socket.emit('customer_connect', {
                customer_id: this.customerId,
                customer_phone: this.customerPhone
            });
        });
        
        this.socket.on('connection_established', (data) => {
            console.log('✅ Customer authenticated:', data);
            this.isConnected = true;
            this.checkCurrentRideStatus();
        });
        
        // Ride status events
        this.socket.on('ride_status_updated', (rideData) => {
            this.handleRideStatusUpdate(rideData);
        });
        
        // Error handling
        this.socket.on('error', (error) => {
            console.error('❌ WebSocket error:', error);
            this.showErrorMessage(error.message);
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('🔌 Disconnected:', reason);
            this.isConnected = false;
        });
    }
    
    handleRideStatusUpdate(rideData) {
        this.currentRide = rideData;
        
        console.log('🚗 Ride status update:', rideData.status);
        
        // Update UI based on status
        switch(rideData.status) {
            case 'pending':
                this.showSearchingForDriver();
                break;
            case 'accepted':
                this.showDriverAssigned(rideData);
                this.displayOTP(rideData.start_otp);
                break;
            case 'arrived':
                this.showDriverArrived();
                this.enableStartRideNotification();
                break;
            case 'started':
                this.showRideInProgress();
                this.startLocationTracking(rideData.ride_id);
                break;
            case 'completed':
                this.showRideCompleted(rideData.fare_amount);
                this.showRatingDialog();
                break;
            case 'cancelled':
                this.showRideCancelled();
                this.resetRideState();
                break;
        }
    }
    
    async bookRide(rideDetails) {
        try {
            const response = await fetch('/customer/book_ride', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify(rideDetails)
            });
            
            const result = await response.json();
            
            if (result.success) {
                console.log('✅ Ride booked:', result.data);
                this.showRideBooked(result.data);
                return result.data;
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('❌ Booking failed:', error);
            this.showErrorMessage(error.message);
            throw error;
        }
    }
    
    async getFareEstimate(pickupCoords, dropCoords, promoCode = null) {
        try {
            const requestData = {
                pickup_lat: pickupCoords.lat,
                pickup_lng: pickupCoords.lng,
                drop_lat: dropCoords.lat,
                drop_lng: dropCoords.lng
            };
            
            if (promoCode) {
                requestData.promo_code = promoCode;
            }
            
            const response = await fetch('/customer/ride_estimate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            return await response.json();
        } catch (error) {
            console.error('❌ Fare estimate failed:', error);
            throw error;
        }
    }
    
    async trackDriverLocation(rideId) {
        try {
            const response = await fetch(`/customer/driver_location/${rideId}`);
            const locationData = await response.json();
            
            if (locationData.latitude && locationData.longitude) {
                this.updateDriverMarkerOnMap(locationData);
                return locationData;
            }
        } catch (error) {
            console.error('❌ Driver tracking failed:', error);
        }
    }
    
    startLocationTracking(rideId) {
        // Track driver location every 10 seconds during active ride
        this.locationTrackingInterval = setInterval(() => {
            this.trackDriverLocation(rideId);
        }, 10000);
    }
    
    // UI Helper Methods
    showSearchingForDriver() {
        console.log('🔍 Searching for driver...');
        // Update UI to show searching animation
    }
    
    showDriverAssigned(rideData) {
        console.log('👨‍✈️ Driver assigned:', rideData.driver_name);
        // Show driver details card with photo, name, car details
    }
    
    displayOTP(otp) {
        console.log('🔐 Start OTP:', otp);
        // Display OTP prominently for driver verification
    }
    
    showDriverArrived() {
        console.log('📍 Driver has arrived!');
        // Show arrival notification and prepare for ride start
    }
    
    showRideInProgress() {
        console.log('🚗 Ride started!');
        // Switch to ride tracking view with map
    }
    
    showRideCompleted(fareAmount) {
        console.log('✅ Ride completed! Fare:', fareAmount);
        // Show payment summary and rating interface
    }
    
    showRideCancelled() {
        console.log('❌ Ride cancelled');
        // Return to booking interface
    }
}

// Initialize customer app
const customerApp = new CustomerAppWebSocket(
    'https://your-backend.com', 
    15,  // customer ID
    '9876543210'  // customer phone
);

// Login first, then connect
async function loginAndConnect() {
    const loginResponse = await fetch('/customer/login_or_register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            phone: '9876543210',
            name: 'John Doe'
        })
    });
    
    const loginData = await loginResponse.json();
    if (loginData.success) {
        customerApp.authToken = loginData.token;
        customerApp.connect();
    }
}

loginAndConnect();
```

---

## 🏷️ **API Endpoint Summary**

### **Core Customer Operations:**
- `POST /customer/login_or_register` - Login/register with phone & name
- `POST /customer/logout` - End session
- `POST /customer/heartbeat` - Keep session alive
- `POST /customer/ride_estimate` - Get fare estimates for all vehicle types
- `POST /customer/book_ride` - Book a new ride with full details
- `GET /customer/ride_status?phone=X` - Get current ride status
- `POST /customer/cancel_ride` - Cancel pending/accepted rides
- `GET /customer/driver_location/{ride_id}` - Track driver in real-time
- `GET /customer/bookings/{customer_id}` - Get ride history categorized by status
- `GET /customer/advertisements` - Get promotional content for display

### **WebSocket Events:**
- **Outgoing**: `customer_connect` - Initial connection with customer ID
- **Incoming**: `ride_status_updated` - Real-time ride status changes
- **Incoming**: `connection_established` - Connection confirmation
- **Incoming**: `error` - Error messages and failures

### **Key Features:**
- **Real-time ride tracking** with WebSocket updates
- **Comprehensive fare estimation** with promo code support  
- **Driver location tracking** during active rides
- **OTP-based ride verification** for security
- **Categorized ride history** (bookings/ongoing/history)
- **Advertisement display** with slideshow configuration
- **Session management** with heartbeat and logout

This comprehensive guide covers all WebSocket hooks, API formats, and response structures for seamless customer app integration with your A1 Taxi platform!