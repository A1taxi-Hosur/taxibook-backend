# A1 Call Taxi - Customer API Documentation

## Base URL
- Development: `http://localhost:5000`
- Production: `https://your-domain.com`

## Authentication System

### JWT Token Authentication
All customer APIs (except login/register) require JWT token authentication.

**Token Format:**
```
Authorization: Bearer <jwt_token>
```

**Token Payload Structure:**
```json
{
  "user_id": 123,
  "username": "9876543210",
  "user_type": "customer",
  "exp": 1693728000
}
```

**Token Expiration:** 7 days

---

## API Endpoints

### 1. Authentication

#### Customer Login/Register
**Endpoint:** `POST /customer/login_or_register`
**Authentication:** None required
**Description:** Login existing customer or register new customer

**Request Body:**
```json
{
  "phone": "9876543210",
  "name": "John Doe"
}
```

**Request Fields:**
- `phone` (string, required): 10-digit Indian mobile number
- `name` (string, required): Customer full name

**Success Response (200):**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "customer": {
    "id": 123,
    "phone": "9876543210",
    "name": "John Doe"
  }
}
```

**Error Response (400):**
```json
{
  "success": false,
  "message": "Invalid phone number format"
}
```

---

### 2. Ride Management

#### Book a Ride
**Endpoint:** `POST /customer/book_ride`
**Authentication:** JWT Token Required
**Description:** Book a new ride

**Request Body:**
```json
{
  "customer_phone": "9876543210",
  "pickup_address": "MG Road, Bengaluru",
  "pickup_lat": 12.9716,
  "pickup_lng": 77.5946,
  "drop_address": "Airport Road, Bengaluru",
  "drop_lat": 13.1986,
  "drop_lng": 77.7066,
  "ride_type": "sedan",
  "ride_category": "regular",
  "promo_code": "WELCOME50"
}
```

**Request Fields:**
- `customer_phone` (string, required): Customer's 10-digit phone number
- `pickup_address` (string, required): Pickup address
- `pickup_lat` (float, optional): Pickup GPS latitude
- `pickup_lng` (float, optional): Pickup GPS longitude
- `drop_address` (string, required): Drop-off address
- `drop_lat` (float, optional): Drop-off GPS latitude
- `drop_lng` (float, optional): Drop-off GPS longitude
- `ride_type` (string, required): "hatchback", "sedan", "suv"
- `ride_category` (string, optional): "regular", "airport", "rental", "outstation" (default: "regular")
- `promo_code` (string, optional): Promo code for discount
- `scheduled_date` (string, optional): Date in DD/MM/YYYY format for scheduled rides
- `scheduled_time` (string, optional): Time in HH:MM format for scheduled rides
- `hours` (integer, optional): Duration in hours for rental rides

**Success Response (200):**
```json
{
  "success": true,
  "message": "Ride booked successfully. Matching drivers have been notified.",
  "data": {
    "ride_id": 456,
    "pickup_address": "MG Road, Bengaluru",
    "drop_address": "Airport Road, Bengaluru",
    "ride_type": "sedan",
    "ride_category": "regular",
    "status": "new",
    "fare_amount": 350.0,
    "distance_km": 15.2,
    "promo_code": "WELCOME50",
    "discount_applied": 50.0,
    "final_fare": 300.0,
    "drivers_notified": true,
    "notification_info": {
      "drivers_count": 3,
      "zone_name": "chennai",
      "message": "3 drivers notified in zone chennai"
    }
  }
}
```

#### Get Active Ride
**Endpoint:** `GET /customer/ride_status?phone=<phone_number>`
**Authentication:** JWT Token Required
**Description:** Get customer's current active ride

**Success Response (200) - With Active Ride:**
```json
{
  "success": true,
  "message": "Ride status retrieved",
  "data": {
    "id": 456,
    "pickup_address": "MG Road, Bengaluru",
    "drop_address": "Airport Road, Bengaluru",
    "ride_type": "sedan",
    "ride_category": "regular",
    "status": "accepted",
    "fare_amount": 300.0,
    "distance_km": 15.2,
    "start_otp": "123456",
    "has_active_ride": true,
    "driver_id": 789,
    "customer_phone": "9876543210",
    "created_at": "2025-08-09T21:30:00.000000"
  }
}
```

**No Active Ride (200):**
```json
{
  "success": true,
  "has_active_ride": false
}
```

#### Cancel Ride
**Endpoint:** `POST /customer/cancel_ride`
**Authentication:** JWT Token Required
**Description:** Cancel current active ride

**Request Body:**
```json
{
  "phone": "9876543210"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Ride cancelled successfully",
  "data": {
    "ride_id": 456,
    "status": "cancelled"
  }
}
```

#### Rate Driver
**Endpoint:** `POST /customer/rate_driver`
**Authentication:** JWT Token Required
**Description:** Rate driver after ride completion

**Request Body:**
```json
{
  "ride_id": 456,
  "rating": 5,
  "review": "Excellent service, very professional driver"
}
```

**Request Fields:**
- `ride_id` (integer, required): Completed ride ID
- `rating` (integer, required): Rating from 1-5
- `review` (string, optional): Text review

**Success Response (200):**
```json
{
  "success": true,
  "message": "Rating submitted successfully"
}
```

---

### 3. Ride History

#### Get Ride History
**Endpoint:** `GET /customer/ride_history`
**Authentication:** JWT Token Required
**Description:** Get paginated ride history

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 10, max: 50)
- `status` (string, optional): Filter by status ("completed", "cancelled")

**Example:** `GET /customer/ride_history?page=1&per_page=10&status=completed`

**Success Response (200):**
```json
{
  "success": true,
  "rides": [
    {
      "id": 456,
      "pickup_location": "MG Road, Bengaluru",
      "destination": "Airport Road, Bengaluru",
      "ride_type": "sedan",
      "ride_category": "regular",
      "status": "completed",
      "fare": 300.0,
      "distance_km": 15.2,
      "driver_name": "Rajesh Kumar",
      "driver_rating": 4.5,
      "customer_rating": 5,
      "promo_discount": 50.0,
      "created_at": "2025-08-09T21:30:00.000000",
      "completed_at": "2025-08-09T22:15:00.000000"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

---

### 4. Location Services

#### Update Customer Location
**Endpoint:** `POST /customer/update_location`
**Authentication:** JWT Token Required
**Description:** Update customer's current GPS location

**Request Body:**
```json
{
  "latitude": 12.9716,
  "longitude": 77.5946
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Location updated successfully"
}
```

#### Get Fare Estimate
**Endpoint:** `POST /customer/ride_estimate`
**Authentication:** None Required
**Description:** Get fare estimate for all ride types based on coordinates

**Request Body:**
```json
{
  "pickup_lat": 12.9716,
  "pickup_lng": 77.5946,
  "drop_lat": 13.1986,
  "drop_lng": 77.7066
}
```

**Success Response (200):**
```json
{
  "success": true,
  "distance_km": 34.83,
  "estimates": {
    "hatchback": {
      "original_fare": 442.91,
      "discount_applied": 0.0,
      "final_fare": 442.91
    },
    "sedan": {
      "original_fare": 373.26,
      "discount_applied": 0.0,
      "final_fare": 373.26
    },
    "suv": {
      "original_fare": 452.91,
      "discount_applied": 0.0,
      "final_fare": 452.91
    }
  }
}
```

---

### 5. Promo Codes

#### Validate Promo Code
**Endpoint:** `POST /customer/validate_promo`
**Authentication:** JWT Token Required
**Description:** Validate and get promo code details

**Request Body:**
```json
{
  "promo_code": "WELCOME50",
  "ride_type": "sedan",
  "ride_category": "regular",
  "fare_amount": 200.0
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Promo code is valid",
  "data": {
    "promo_code": "WELCOME50",
    "discount_type": "flat",
    "discount_value": 50.0,
    "discount_amount": 50.0,
    "original_fare": 200.0,
    "final_fare": 150.0,
    "valid": true
  }
}
```

**Invalid Promo Response (400):**
```json
{
  "success": false,
  "message": "Promo code has expired"
}
```

#### Get Available Promo Codes
**Endpoint:** `GET /customer/promo_codes`
**Authentication:** JWT Token Required
**Description:** Get list of active promo codes

**Success Response (200):**
```json
{
  "success": true,
  "promo_codes": [
    {
      "code": "WELCOME50",
      "discount_type": "flat",
      "discount_value": 50.0,
      "min_fare": 100.0,
      "max_uses": 100,
      "current_uses": 25,
      "ride_type": null,
      "ride_category": null,
      "expiry_date": "2025-09-09T00:00:00.000000"
    }
  ]
}
```

---

### 6. Configuration & Data

#### Get Fare Configuration
**Endpoint:** `GET /customer/fare_config`
**Authentication:** JWT Token Required
**Description:** Get current fare rates

**Success Response (200):**
```json
{
  "success": true,
  "fare_config": [
    {
      "ride_type": "hatchback",
      "base_fare": 25.0,
      "per_km_rate": 12.0,
      "surge_multiplier": 1.0
    },
    {
      "ride_type": "sedan",
      "base_fare": 25.0,
      "per_km_rate": 10.0,
      "surge_multiplier": 1.0
    },
    {
      "ride_type": "suv",
      "base_fare": 35.0,
      "per_km_rate": 12.0,
      "surge_multiplier": 1.0
    }
  ]
}
```

#### Get Service Zones
**Endpoint:** `GET /customer/zones`
**Authentication:** JWT Token Required
**Description:** Get available service zones

**Success Response (200):**
```json
{
  "success": true,
  "zones": [
    {
      "id": 17,
      "zone_name": "chennai",
      "center_lat": 13.098091,
      "center_lng": 80.187873,
      "radius_km": 37.5,
      "is_active": true
    }
  ]
}
```

#### Get Advertisements
**Endpoint:** `GET /customer/advertisements`
**Authentication:** JWT Token Required
**Description:** Get active advertisements for slideshow

**Success Response (200):**
```json
{
  "success": true,
  "advertisements": [
    {
      "id": 1,
      "title": "Special Offer",
      "description": "Get 20% off on your next ride",
      "media_type": "image",
      "media_url": "/static/ads/offer1.jpg",
      "display_duration": 5,
      "display_order": 1
    }
  ]
}
```

---

## Real-Time Events & Notifications

### Ride Status Updates
Monitor ride status changes through polling the `/customer/active_ride` endpoint every 5-10 seconds.

**Ride Status Flow:**
1. `requested` - Ride just booked, searching for driver
2. `accepted` - Driver accepted the ride
3. `arrived` - Driver arrived at pickup location
4. `started` - Trip started (customer in vehicle)
5. `completed` - Trip completed successfully
6. `cancelled` - Ride cancelled by customer or driver

### Push Notifications
Implement push notification handling for:
- Driver assigned to ride
- Driver arrived at pickup
- Trip started
- Trip completed
- Ride cancelled by driver

---

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "message": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE"
}
```

### Common Error Codes
- `INVALID_TOKEN` - JWT token invalid or expired
- `RIDE_NOT_FOUND` - Requested ride doesn't exist
- `NO_DRIVERS_AVAILABLE` - No drivers in the area
- `INVALID_LOCATION` - GPS coordinates outside service area
- `PROMO_EXPIRED` - Promo code has expired
- `RIDE_ALREADY_ACTIVE` - Customer already has an active ride

### HTTP Status Codes
- `200` - Success
- `201` - Created (ride booked)
- `400` - Bad Request (validation error)
- `401` - Unauthorized (invalid/missing token)
- `404` - Not Found
- `500` - Internal Server Error

---

## Data Validation Rules

### Phone Number
- Format: 10-digit Indian mobile number
- Pattern: `^[6-9]\d{9}$`
- Example: `9876543210`

### GPS Coordinates
- Latitude: `-90` to `90`
- Longitude: `-180` to `180`
- Precision: Up to 6 decimal places

### Ride Types
- `hatchback` - Small cars
- `sedan` - Medium cars
- `suv` - Large cars/SUVs

### Ride Categories
- `regular` - Normal city rides
- `airport` - Airport transfers
- `rental` - Hourly rentals
- `outstation` - Inter-city trips

### Rating System
- Scale: 1-5 (integer values only)
- 1 = Very Poor
- 2 = Poor
- 3 = Average
- 4 = Good
- 5 = Excellent

---

## Testing with cURL

### Login/Register
```bash
curl -X POST http://localhost:5000/customer/login_or_register \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "name": "John Doe"
  }'
```

### Book Ride (with token)
```bash
curl -X POST http://localhost:5000/customer/book_ride \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "customer_phone": "9876543210",
    "pickup_address": "MG Road, Bengaluru",
    "pickup_lat": 12.9716,
    "pickup_lng": 77.5946,
    "drop_address": "Airport Road, Bengaluru",
    "drop_lat": 13.1986,
    "drop_lng": 77.7066,
    "ride_type": "sedan",
    "ride_category": "regular"
  }'
```

### Get Active Ride
```bash
curl -X GET "http://localhost:5000/customer/ride_status?phone=9876543210" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Validate Promo Code
```bash
curl -X POST http://localhost:5000/customer/validate_promo \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "promo_code": "WELCOME50",
    "fare_amount": 200,
    "ride_type": "sedan",
    "ride_category": "regular"
  }'
```

### Get Fare Estimate
```bash
curl -X POST http://localhost:5000/customer/ride_estimate \
  -H "Content-Type: application/json" \
  -d '{
    "pickup_lat": 12.9716,
    "pickup_lng": 77.5946,
    "drop_lat": 13.1986,
    "drop_lng": 77.7066
  }'
```

---

## Important Notes

1. **Token Management**: Store JWT token securely and include in all API calls
2. **Location Accuracy**: Use high-accuracy GPS for better driver matching
3. **Error Handling**: Always check `success` field in response
4. **Rate Limiting**: Avoid excessive API calls, respect server resources
5. **Real-Time Updates**: Poll active ride status every 5-10 seconds for live updates
6. **Offline Handling**: Cache essential data for offline scenarios
7. **Security**: Never log or expose JWT tokens in client-side code

---

## Support

For API issues or questions, contact the development team or check the admin dashboard for system status.