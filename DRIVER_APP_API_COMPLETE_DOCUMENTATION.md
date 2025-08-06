# **A1 Call Taxi - Driver App API Documentation**

**Base URL:** `https://taxibook-backend-production.up.railway.app/driver`

All API endpoints return standardized JSON responses:

## **📋 Response Format**

### **Success Response**
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### **Error Response**  
```json
{
  "status": "error",
  "message": "Error description"
}
```

---

## **🔐 Authentication APIs**

### **1. Driver Login**
**Endpoint:** `POST /driver/login`

**Request Body:**
```json
{
  "username": "driver123",
  "password": "password123"
}
```

**Success Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "driver_id": 45,
    "name": "John Driver",
    "phone": "9994926574",
    "username": "driver123",
    "is_online": true,
    "car_make": "Maruti",
    "car_model": "Swift Dzire",
    "car_year": 2022,
    "car_number": "TN01AB1234",
    "car_type": "sedan"
  }
}
```

**Notes:**
- Driver is automatically set **online** when logged in
- Requires admin-created account with password hash
- Sets driver online status in database

---

## **🚗 Ride Management APIs**

### **2. Get Available Rides**
**Endpoint:** `GET /driver/incoming_rides`

**Query Parameters:**
```
phone=9994926574&driver_location=lat,lng
```

**Response:**
```json
{
  "status": "success", 
  "message": "Incoming rides retrieved",
  "data": {
    "rides": [
      {
        "id": 123,
        "customer_name": "Rajesh Kumar",
        "customer_phone": "9876543210",
        "pickup_address": "T. Nagar, Chennai",
        "drop_address": "Anna Salai, Chennai", 
        "pickup_lat": 13.0434,
        "pickup_lng": 80.2506,
        "drop_lat": 13.0697,
        "drop_lng": 80.2429,
        "distance_km": 5.2,
        "fare_amount": 120.50,
        "final_fare": 108.45,
        "promo_code": "SAVE10",
        "discount_applied": 12.05,
        "ride_type": "sedan",
        "ride_category": "regular",
        "status": "pending",
        "created_at": "2025-08-06T14:30:00",
        "distance_to_pickup_km": 2.1,
        "driver_name": null,
        "driver_phone": null,
        "car_make": null,
        "car_model": null,
        "car_year": null,
        "car_number": null,
        "car_type": null,
        "driver_photo_url": null
      }
    ],
    "count": 1
  }
}
```

**Ride Filtering Rules:**
- Only shows rides with `status: "pending"`
- Only rides matching driver's `car_type` 
- Excludes rides already rejected by this driver
- Only visible to **online** drivers
- Optional distance calculation if `driver_location` provided

---

### **3. Accept Ride**
**Endpoint:** `POST /driver/accept_ride`

**Request Body:**
```json
{
  "ride_id": 123,
  "driver_phone": "9994926574"
}
```

**Success Response:**
```json
{
  "status": "success",
  "message": "Ride accepted successfully", 
  "data": {
    "ride_id": 123,
    "status": "accepted",
    "customer_name": "Rajesh Kumar",
    "pickup_address": "T. Nagar, Chennai",
    "drop_address": "Anna Salai, Chennai",
    "fare_amount": 120.50
  }
}
```

**Important:**
- Generates 6-digit **OTP** for ride start
- Changes ride status: `pending` → `accepted`  
- Prevents accepting if driver has ongoing ride
- Only available for `status: "pending"` rides

---

### **4. Reject Ride**
**Endpoint:** `POST /driver/reject_ride`

**Request Body:**
```json
{
  "ride_id": 123,
  "driver_phone": "9994926574"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Ride rejected successfully",
  "data": {
    "ride_id": 123,
    "message": "Ride rejected"
  }
}
```

**Notes:**
- Records rejection in `RideRejection` table
- Prevents future offers of same ride to this driver
- Ride remains `pending` for other drivers

---

### **5. Mark Arrived**
**Endpoint:** `POST /driver/arrived`

**Request Body:**
```json
{
  "driver_phone": "9994926574"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Arrival confirmed",
  "data": {
    "ride_id": 123,
    "status": "arrived"
  }
}
```

**Status Flow:** `accepted` → `arrived`

---

### **6. Start Ride (OTP Verification)**
**Endpoint:** `POST /driver/start_ride`

**Request Body:**
```json
{
  "ride_id": 123,
  "otp": "123456"
}
```

**Success Response:**
```json
{
  "status": "success",
  "message": "Ride started successfully",
  "data": {
    "ride_id": 123,
    "status": "started"
  }
}
```

**OTP Verification:**
- Must be exactly 6 digits
- Generated when ride is accepted
- Customer receives OTP
- OTP cleared after successful verification

**Status Flow:** `accepted`/`arrived` → `started`

---

### **7. Complete Ride**
**Endpoint:** `POST /driver/complete_ride`

**Request Body:**
```json
{
  "driver_phone": "9994926574"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Ride completed successfully",
  "data": {
    "ride_id": 123,
    "status": "completed",
    "fare_amount": 120.50
  }
}
```

**Status Flow:** `started` → `completed`

---

### **8. Cancel Ride**
**Endpoint:** `POST /driver/cancel_ride`

**Request Body:**
```json
{
  "driver_phone": "9994926574"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Ride cancelled successfully",
  "data": {
    "ride_id": 123,
    "status": "pending"
  }
}
```

**Cancellation Rules:**
- Only for `accepted` or `arrived` rides
- Cannot cancel `started` rides  
- Resets ride to `pending` for other drivers
- Clears driver assignment and timestamps

---

### **9. Get Current Ride**
**Endpoint:** `GET /driver/current_ride`

**Query Parameters:**
```
phone=9994926574
```

**Response (Active Ride):**
```json
{
  "status": "success",
  "message": "Current ride retrieved", 
  "data": {
    "has_active_ride": true,
    "id": 123,
    "customer_name": "Rajesh Kumar",
    "customer_phone": "9876543210",
    "pickup_address": "T. Nagar, Chennai",
    "drop_address": "Anna Salai, Chennai",
    "pickup_lat": 13.0434,
    "pickup_lng": 80.2506,
    "drop_lat": 13.0697,
    "drop_lng": 80.2429,
    "distance_km": 5.2,
    "fare_amount": 120.50,
    "final_fare": 108.45,
    "status": "started",
    "created_at": "2025-08-06T14:30:00",
    "accepted_at": "2025-08-06T14:35:00",
    "arrived_at": "2025-08-06T14:45:00",
    "started_at": "2025-08-06T14:50:00",
    "driver_name": "John Driver",
    "driver_phone": "9994926574",
    "car_make": "Maruti",
    "car_model": "Swift Dzire",
    "car_year": 2022,
    "car_number": "TN01AB1234",
    "car_type": "sedan",
    "driver_photo_url": null
  }
}
```

**Response (No Active Ride):**
```json
{
  "status": "success",
  "message": "No active ride",
  "data": {
    "has_active_ride": false
  }
}
```

**Active Ride Statuses:** `accepted`, `arrived`, `started`

---

## **📍 Location Tracking APIs**

### **10. Update Ride Location (GPS Tracking)**
**Endpoint:** `POST /driver/update_location`

**Request Body:**
```json
{
  "driver_phone": "9994926574",
  "ride_id": 123,
  "latitude": 13.0434,
  "longitude": 80.2506
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Location updated successfully",
  "data": {
    "ride_id": 123,
    "latitude": 13.0434,
    "longitude": 80.2506,
    "timestamp": "2025-08-06T14:45:30"
  }
}
```

**Usage:**
- Real-time GPS tracking during active rides
- Only for rides with status: `accepted`, `arrived`, `started`
- Stores location in `RideLocation` table
- Marks current location as `is_latest: true`

---

### **11. Update Current Location (Dispatch)**
**Endpoint:** `POST /driver/update_current_location`

**Request Body:**
```json
{
  "phone": "9994926574",
  "latitude": 13.0434,
  "longitude": 80.2506
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Current location updated successfully",
  "data": {
    "driver_id": 45,
    "latitude": 13.0434,
    "longitude": 80.2506,
    "updated_at": "2025-08-06T14:45:30",
    "zone": "Chennai",
    "out_of_zone": false
  }
}
```

**Usage:**
- Updates driver's general location for dispatch
- Automatic zone assignment based on location
- Used for proximity-based ride matching
- Updates `current_lat`, `current_lng` in driver table

---

### **12. Get Zone Status**
**Endpoint:** `GET /driver/get_zone_status`

**Query Parameters:**
```
phone=9994926574
```

**Response:**
```json
{
  "status": "success",
  "message": "Zone status retrieved",
  "data": {
    "driver_id": 45,
    "current_lat": 13.0434,
    "current_lng": 80.2506,
    "zone_id": 1,
    "zone_name": "Chennai",
    "out_of_zone": false,
    "location_updated_at": "2025-08-06T14:45:30"
  }
}
```

---

## **🟢 Status Management APIs**

### **13. Update Status (Always Online)**
**Endpoint:** `POST /driver/status`

**Request Body:**
```json
{
  "mobile": "9994926574"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Driver is always online when logged in",
  "data": {
    "driver_id": 45,
    "name": "John Driver",
    "phone": "9994926574",
    "is_online": true
  }
}
```

**Always Online System:**
- Drivers automatically online when logged in
- No manual toggle available
- Status endpoint returns current state

---

### **14. Get Status**
**Endpoint:** `GET /driver/status`

**Query Parameters:**
```
mobile=9994926574
```

**Response:**
```json
{
  "status": "success",
  "message": "Driver status retrieved",
  "data": {
    "is_online": true,
    "driver_id": 45,
    "name": "John Driver", 
    "phone": "9994926574"
  }
}
```

---

### **15. Logout**
**Endpoint:** `POST /driver/logout`

**Request Body (Optional):**
```json
{
  "phone": "9994926574"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Logout successful"
}
```

**Logout Actions:**
- Sets `is_online: false`
- Clears GPS location data
- Clears zone assignment
- Prevents "ghost driver" appearances
- Ends Flask-Login session

---

## **🔧 API Usage Patterns**

### **Driver App Startup Flow**
```
1. POST /driver/login (username + password)
2. POST /driver/update_current_location (current GPS)
3. GET /driver/current_ride (check ongoing rides)
4. GET /driver/incoming_rides (start polling)
```

### **Ride Lifecycle Flow**
```
pending → accept_ride → accepted
accepted → arrived → arrived  
arrived → start_ride (OTP) → started
started → complete_ride → completed
```

### **Location Tracking Pattern**
```
// For dispatch (general location)
POST /driver/update_current_location

// During active ride (GPS tracking)
POST /driver/update_location
```

### **Polling Requirements**
```
// Check for new rides every 10-15 seconds
GET /driver/incoming_rides?phone=X&driver_location=lat,lng

// Update location every 30 seconds
POST /driver/update_current_location
```

---

## **⚡ Important Notes**

### **Authentication**
- Use session-based authentication after login
- Phone number validates against Indian format
- Username/password required (not phone-based like customers)

### **Ride Filtering**
- Only `pending` rides visible to drivers
- Vehicle type matching enforced (`sedan` drivers see only `sedan` rides)
- Rejected rides never shown again to same driver

### **Location Validation** 
- Latitude: -90 to 90
- Longitude: -180 to 180  
- Coordinates validated on all location APIs

### **Error Handling**
- All APIs return standardized error format
- Phone number validation on all endpoints
- Proper HTTP status codes (403 for invalid OTP)

### **Database Relations**
- Rides link to drivers via `driver_id`
- Location tracking in separate `RideLocation` table
- Rejections stored in `RideRejection` table