# A1 Taxi Complete API Documentation

## Authentication System

### Driver/Customer APIs
- **Type**: JWT Token-based (stateless)
- **Header**: `Authorization: Bearer <token>`
- **Token Expiry**: 7 days
- **Current Status**: TEMPORARILY BYPASSED FOR TESTING

### Admin Panel
- **Type**: Flask-Login sessions (cookie-based)
- **Login Required**: Yes for all admin routes

---

## Driver APIs

### Authentication

#### POST `/driver/login`
**Purpose**: Driver login with username/password
```json
Request:
{
  "username": "DRVTEST123",
  "password": "password123"
}

Response:
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "driver": {
    "id": 25,
    "name": "Test Driver",
    "phone": "9876543210",
    "car_type": "suv",
    "status": "online",
    "zone_id": 1,
    "car_make": "Mahindra",
    "car_model": "XUV300",
    "car_year": 2022,
    "car_number": "TN09AB1234"
  }
}
```

#### POST `/driver/logout` 🔒
**Purpose**: Logout driver and set offline
```json
Response:
{
  "success": true,
  "message": "Driver logged out successfully"
}
```

### Ride Management

#### GET `/driver/incoming_rides` 🔒
**Purpose**: Get available rides for driver
```json
Response:
{
  "success": true,
  "count": 2,
  "rides": [
    {
      "id": 101,
      "customer_name": "John Doe",
      "customer_phone": "9994926574",
      "pickup_address": "T. Nagar, Chennai",
      "drop_address": "Marina Beach, Chennai",
      "pickup_lat": 13.0418,
      "pickup_lng": 80.2341,
      "drop_lat": 13.0499,
      "drop_lng": 80.2824,
      "distance_km": 6.574,
      "fare_amount": 103.89,
      "final_fare": 103.89,
      "ride_type": "sedan",
      "ride_category": "regular",
      "status": "pending",
      "created_at": "2025-08-03T22:43:01.421830"
    }
  ]
}
```

#### GET `/driver/current_ride` 🔒
**Purpose**: Get driver's current active ride
```json
Response:
{
  "success": true,
  "has_active_ride": true,
  "id": 68,
  "customer_name": "Test User Chennai",
  "customer_phone": "9994926574",
  "pickup_address": "T. Nagar, Chennai",
  "drop_address": "Marina Beach, Chennai",
  "pickup_lat": 13.0418,
  "pickup_lng": 80.2341,
  "drop_lat": 13.0499,
  "drop_lng": 80.2824,
  "distance_km": 6.574,
  "fare_amount": 103.89,
  "final_fare": 103.89,
  "ride_type": "hatchback",
  "ride_category": "regular",
  "status": "accepted",
  "driver_name": "Test Driver SUV",
  "driver_phone": "9876543210",
  "car_make": "Mahindra",
  "car_model": "XUV300",
  "car_type": "suv",
  "car_year": 2022,
  "car_number": "TN09AB1234",
  "accepted_at": "2025-08-04T06:02:37.512926",
  "created_at": "2025-08-03T22:43:01.421830"
}
```

#### POST `/driver/accept_ride` 🔒
**Purpose**: Accept a pending ride
```json
Request:
{
  "ride_id": 101
}

Response:
{
  "success": true,
  "message": "Ride accepted successfully",
  "ride_id": 101,
  "status": "accepted",
  "start_otp": "123456"
}
```

#### POST `/driver/reject_ride` 🔒
**Purpose**: Reject a pending ride
```json
Request:
{
  "ride_id": 101
}

Response:
{
  "success": true,
  "message": "Ride rejected successfully"
}
```

#### POST `/driver/arrived` 🔒
**Purpose**: Mark driver as arrived at pickup location
```json
Request:
{
  "ride_id": 101
}

Response:
{
  "success": true,
  "message": "Arrival confirmed",
  "ride_id": 101,
  "status": "arrived"
}
```

#### POST `/driver/start_ride` 🔒
**Purpose**: Start ride with OTP verification
```json
Request:
{
  "ride_id": 101,
  "otp": "123456"
}

Response:
{
  "success": true,
  "message": "Ride started successfully",
  "ride_id": 101,
  "status": "started"
}
```

#### POST `/driver/complete_ride` 🔒
**Purpose**: Complete the ride
```json
Request:
{
  "ride_id": 101
}

Response:
{
  "success": true,
  "message": "Ride completed successfully",
  "ride_id": 101,
  "status": "completed",
  "final_fare": 103.89
}
```

#### POST `/driver/cancel_ride` 🔒
**Purpose**: Cancel accepted ride
```json
Request:
{
  "ride_id": 101,
  "reason": "Customer not found"
}

Response:
{
  "success": true,
  "message": "Ride cancelled successfully"
}
```

### Location Services

#### POST `/driver/update_location` 🔒
**Purpose**: Update driver's GPS location during active ride
```json
Request:
{
  "latitude": 13.0418,
  "longitude": 80.2341
}

Response:
{
  "success": true,
  "message": "Location updated successfully"
}
```

#### POST `/driver/update_current_location` 🔒
**Purpose**: Update driver's current location for proximity dispatch
```json
Request:
{
  "latitude": 13.0418,
  "longitude": 80.2341
}

Response:
{
  "success": true,
  "message": "Current location updated",
  "zone_assigned": true,
  "zone_name": "T. Nagar Zone"
}
```

#### GET `/driver/zone_status` 🔒
**Purpose**: Get driver's current zone status
```json
Response:
{
  "success": true,
  "zone_id": 1,
  "zone_name": "T. Nagar Zone",
  "out_of_zone": false,
  "current_lat": 13.0418,
  "current_lng": 80.2341
}
```

---

## Customer APIs

### Authentication

#### POST `/customer/login_or_register`
**Purpose**: Customer login or registration with phone number
```json
Request:
{
  "phone": "9994926574",
  "name": "John Doe"
}

Response:
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "customer": {
    "id": 15,
    "phone": "9994926574",
    "name": "John Doe"
  }
}
```

### Ride Management

#### POST `/customer/book_ride`
**Purpose**: Book a new ride
```json
Request:
{
  "customer_phone": "9994926574",
  "pickup_address": "T. Nagar, Chennai",
  "drop_address": "Marina Beach, Chennai",
  "pickup_lat": 13.0418,
  "pickup_lng": 80.2341,
  "drop_lat": 13.0499,
  "drop_lng": 80.2824,
  "ride_type": "sedan",
  "ride_category": "regular",
  "promo_code": "SAVE20"
}

Response:
{
  "success": true,
  "ride": {
    "id": 102,
    "status": "pending",
    "fare_amount": 103.89,
    "final_fare": 83.11,
    "discount_applied": 20.78,
    "estimated_time": "10-15 minutes"
  },
  "message": "Ride booked successfully"
}
```

#### GET `/customer/fare_estimate`
**Purpose**: Get fare estimate for a route
```json
Request Parameters:
?pickup_address=T. Nagar, Chennai&drop_address=Marina Beach&pickup_lat=13.0418&pickup_lng=80.2341&drop_lat=13.0499&drop_lng=80.2824&promo_code=SAVE20

Response:
{
  "success": true,
  "distance_km": 6.57,
  "estimates": {
    "hatchback": {
      "original_fare": 89.84,
      "final_fare": 69.06,
      "discount_applied": 20.78
    },
    "sedan": {
      "original_fare": 103.89,
      "final_fare": 83.11,
      "discount_applied": 20.78
    },
    "suv": {
      "original_fare": 113.84,
      "final_fare": 93.06,
      "discount_applied": 20.78
    }
  },
  "promo_code_info": {
    "promo_code": "SAVE20",
    "discount_type": "flat",
    "discount_value": 20.0
  }
}
```

#### GET `/customer/ride_status`
**Purpose**: Get current ride status
```json
Request Parameters:
?customer_phone=9994926574

Response:
{
  "success": true,
  "has_active_ride": true,
  "ride": {
    "id": 68,
    "status": "accepted",
    "driver_name": "Test Driver SUV",
    "driver_phone": "9876543210",
    "car_make": "Mahindra",
    "car_model": "XUV300",
    "car_number": "TN09AB1234",
    "pickup_address": "T. Nagar, Chennai",
    "drop_address": "Marina Beach, Chennai",
    "fare_amount": 103.89,
    "start_otp": "123456"
  }
}
```

---

## Error Responses

All APIs return consistent error format:
```json
{
  "success": false,
  "message": "Error description"
}
```

Common HTTP Status Codes:
- `200`: Success
- `400`: Bad Request (validation errors)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `500`: Internal Server Error

---

## Location Tracking

### Driver Location Updates
- **Frequency**: Every 10-30 seconds during active rides
- **Accuracy**: GPS coordinates with 6 decimal precision
- **Zone Assignment**: Automatic based on current location

### Customer Tracking
- **Real-time Updates**: Driver location visible to customer during ride
- **ETA Calculation**: Based on current traffic and distance

---

## Notes

🔒 = Requires JWT Authentication (currently bypassed for testing)

**Current Testing State**: JWT authentication is temporarily disabled. All protected endpoints can be accessed without tokens for debugging driver app issues.

**Production Ready**: When JWT is re-enabled, all endpoints will require proper authentication headers.