# A1 Call Taxi - Complete Customer App API Documentation

## Base URL
```
http://localhost:5000/customer
```

## API Response Format
All APIs return responses in this standardized format:

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Success message"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message"
}
```

---

## 🔐 Authentication APIs

### 1. Login/Register Customer
**Endpoint:** `POST /customer/login_or_register`

**Description:** Handles both login and registration for customers using phone number.

**Request Body:**
```json
{
  "phone": "9876543210",
  "name": "John Doe"
}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "customer_id": 123,
    "name": "John Doe",
    "phone": "9876543210",
    "action": "login" // or "register"
  },
  "message": "Login successful"
}
```

### 2. Logout Customer
**Endpoint:** `POST /customer/logout`

**Request Body:** Empty
```json
{}
```

**Success Response:**
```json
{
  "success": true,
  "data": {},
  "message": "Logout successful"
}
```

---

## 🚗 Ride Booking APIs

### 3. Get Fare Estimate
**Endpoint:** `POST /customer/ride_estimate`

**Description:** Calculate fare estimates for all vehicle types based on pickup/drop coordinates.

**Request Body:**
```json
{
  "pickup_lat": 12.7400,
  "pickup_lng": 77.8253,
  "drop_lat": 12.7500,
  "drop_lng": 77.8353,
  "promo_code": "SAVE20", // Optional
  "ride_category": "regular" // Optional: regular, airport, rental, outstation
}
```

**Success Response:**
```json
{
  "success": true,
  "distance_km": 5.25,
  "estimates": {
    "hatchback": {
      "original_fare": 120.00,
      "final_fare": 100.00,
      "discount_applied": 20.00
    },
    "sedan": {
      "original_fare": 150.00,
      "final_fare": 130.00,
      "discount_applied": 20.00
    },
    "suv": {
      "original_fare": 180.00,
      "final_fare": 160.00,
      "discount_applied": 20.00
    }
  },
  "promo_code_info": {
    "promo_code": "SAVE20",
    "discount_type": "flat",
    "discount_value": 20,
    "min_fare": 100,
    "valid_ride_types": null,
    "valid_ride_categories": null
  }
}
```

### 4. Book a Ride
**Endpoint:** `POST /customer/book_ride`

**Description:** Book a new ride with all details.

**Request Body:**
```json
{
  "customer_phone": "9876543210",
  "pickup_address": "MG Road, Hosur",
  "drop_address": "Bus Stand, Hosur",
  "pickup_lat": 12.7400,
  "pickup_lng": 77.8253,
  "drop_lat": 12.7500,
  "drop_lng": 77.8353,
  "ride_type": "hatchback", // hatchback, sedan, suv
  "ride_category": "regular", // regular, airport, rental, outstation
  "promo_code": "SAVE20", // Optional
  "scheduled_date": "25/12/2024", // Optional (DD/MM/YYYY)
  "scheduled_time": "14:30", // Optional (HH:MM)
  "hours": 4 // Optional (for rental rides only)
}
```

**Success Response - Regular Ride (Immediate):**
```json
{
  "success": true,
  "data": {
    "ride_id": 456,
    "pickup_address": "MG Road, Hosur",
    "drop_address": "Bus Stand, Hosur",
    "distance_km": 5.25,
    "fare_amount": 120.00,
    "ride_type": "hatchback",
    "ride_category": "regular",
    "final_fare": 100.00,
    "promo_code": "SAVE20",
    "discount_applied": 20.00,
    "status": "new",
    "drivers_notified": true,
    "notification_info": {
      "drivers_count": 3,
      "zone_name": "Hosur Central",
      "message": "Drivers in zone notified"
    }
  },
  "message": "Ride booked successfully. Matching drivers have been notified."
}
```

**Success Response - Special Ride (Airport/Rental/Outstation):**
```json
{
  "success": true,
  "data": {
    "ride_id": 457,
    "pickup_address": "MG Road, Hosur",
    "drop_address": "Kempegowda Airport, Bangalore",
    "distance_km": 45.8,
    "fare_amount": 1500.00,
    "ride_type": "sedan",
    "ride_category": "airport",
    "final_fare": 1500.00,
    "promo_code": null,
    "discount_applied": 0.00,
    "scheduled": false,
    "requires_admin_assignment": true,
    "status": "new"
  },
  "message": "Airport ride booked successfully. Admin will assign driver."
}
```

**Success Response - Scheduled Ride:**
```json
{
  "success": true,
  "data": {
    "ride_id": 458,
    "pickup_address": "MG Road, Hosur",
    "drop_address": "Bus Stand, Hosur",
    "distance_km": 5.25,
    "fare_amount": 120.00,
    "ride_type": "hatchback",
    "ride_category": "regular",
    "final_fare": 120.00,
    "promo_code": null,
    "discount_applied": 0.00,
    "scheduled": true,
    "scheduled_date": "25/12/2024",
    "scheduled_time": "14:30",
    "status": "new"
  },
  "message": "Scheduled ride booked successfully."
}
```

---

## 📱 Ride Management APIs

### 5. Get Ride Status
**Endpoint:** `GET /customer/ride_status?phone=9876543210`

**Description:** Get current active ride status for customer.

**Query Parameters:**
- `phone` (required): Customer phone number

**Success Response - Active Ride:**
```json
{
  "success": true,
  "data": {
    "has_active_ride": true,
    "id": 456,
    "customer_phone": "9876543210",
    "pickup_address": "MG Road, Hosur",
    "drop_address": "Bus Stand, Hosur",
    "pickup_lat": 12.7400,
    "pickup_lng": 77.8253,
    "drop_lat": 12.7500,
    "drop_lng": 77.8353,
    "distance_km": 5.25,
    "fare_amount": 120.00,
    "final_fare": 100.00,
    "ride_type": "hatchback",
    "ride_category": "regular",
    "status": "accepted", // new, assigned, accepted, arrived, started, completed, cancelled
    "driver_id": 789,
    "driver_name": "Ravi Kumar",
    "driver_phone": "9876543211",
    "driver_vehicle": "KA 01 AB 1234",
    "start_otp": "123456",
    "created_at": "2024-12-25T14:30:00",
    "accepted_at": "2024-12-25T14:32:00",
    "arrived_at": null,
    "started_at": null,
    "completed_at": null
  },
  "message": "Ride status retrieved"
}
```

**Success Response - No Active Ride:**
```json
{
  "success": true,
  "data": {
    "has_active_ride": false
  },
  "message": "No active ride"
}
```

### 6. Cancel Ride
**Endpoint:** `POST /customer/cancel_ride`

**Description:** Cancel current active ride.

**Request Body:**
```json
{
  "phone": "9876543210"
}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "ride_id": 456,
    "status": "cancelled"
  },
  "message": "Ride cancelled successfully"
}
```

### 7. Get Driver Location (Live Tracking)
**Endpoint:** `GET /customer/driver_location/{ride_id}`

**Description:** Get real-time driver location during active ride.

**Success Response:**
```json
{
  "ride_id": 456,
  "latitude": 12.7420,
  "longitude": 77.8270,
  "timestamp": "2024-12-25T14:35:00",
  "ride_status": "started",
  "pickup_lat": 12.7400,
  "pickup_lng": 77.8253,
  "drop_lat": 12.7500,
  "drop_lng": 77.8353
}
```

### 8. Approve Zone Expansion
**Endpoint:** `POST /customer/approve_zone_expansion`

**Description:** Customer approval for ride dispatch outside their zone with extra fare.

**Request Body:**
```json
{
  "ride_id": 456,
  "approved": true,
  "driver_id": 789,
  "zone_id": 2,
  "extra_fare": 50.00
}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "ride_id": 456,
    "status": "assigned",
    "driver_assigned": true,
    "driver_id": 789,
    "final_fare": 170.00,
    "extra_fare": 50.00
  },
  "message": "Zone expansion approved and driver assigned"
}
```

---

## 🎟️ Promo Code APIs

### 9. Validate Promo Code
**Endpoint:** `POST /customer/validate_promo`

**Description:** Validate promo code before booking.

**Request Body:**
```json
{
  "promo_code": "SAVE20",
  "fare_amount": 120.00,
  "ride_type": "hatchback", // Optional
  "ride_category": "regular" // Optional
}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "promo_code": "SAVE20",
    "discount_type": "flat",
    "discount_value": 20,
    "discount_amount": 20.00,
    "original_fare": 120.00,
    "final_fare": 100.00,
    "valid": true
  },
  "message": "Promo code is valid"
}
```

### 10. Get Available Promo Codes
**Endpoint:** `GET /customer/promo_codes/available`

**Description:** Get list of available promo codes for display.

**Query Parameters (Optional):**
- `ride_type`: Filter by ride type (hatchback, sedan, suv)
- `ride_category`: Filter by ride category (regular, airport, rental, outstation)
- `min_fare`: Filter by minimum fare amount

**Example:** `GET /customer/promo_codes/available?ride_type=sedan&min_fare=100`

**Success Response:**
```json
{
  "success": true,
  "data": {
    "promo_codes": [
      {
        "code": "SAVE20",
        "discount_type": "flat",
        "discount_value": 20,
        "min_fare": 100,
        "expiry_date": "2024-12-31T23:59:59",
        "ride_type": null,
        "ride_category": null,
        "usage_remaining": 45,
        "max_uses": 100,
        "is_limited": true,
        "display_text": "₹20 OFF",
        "savings_text": "Save ₹20 on rides above ₹100",
        "terms": [
          "Minimum fare: ₹100",
          "Valid till: 31 Dec 2024",
          "Uses remaining: 45"
        ]
      },
      {
        "code": "FIRST15",
        "discount_type": "percent",
        "discount_value": 15,
        "min_fare": 50,
        "expiry_date": null,
        "ride_type": null,
        "ride_category": "regular",
        "usage_remaining": 8,
        "max_uses": 10,
        "is_limited": true,
        "display_text": "15% OFF",
        "savings_text": "Save 15% on rides above ₹50",
        "terms": [
          "Minimum fare: ₹50",
          "Category: Regular rides",
          "Uses remaining: 8"
        ]
      }
    ],
    "total_available": 2,
    "filters_applied": {
      "ride_type": "sedan",
      "ride_category": null,
      "min_fare": 100
    }
  },
  "message": "Available promo codes retrieved"
}
```

---

## 📚 Booking History APIs

### 11. Get Customer Bookings
**Endpoint:** `GET /customer/bookings/{customer_id}`

**Description:** Get categorized ride history for customer.

**Success Response:**
```json
{
  "success": true,
  "data": {
    "customer_id": 123,
    "bookings": [
      {
        "id": 460,
        "pickup_address": "Station Road, Hosur",
        "drop_address": "SIPCOT, Hosur",
        "fare_amount": 80.00,
        "ride_type": "hatchback",
        "status": "assigned",
        "created_at": "2024-12-25T15:00:00"
      }
    ],
    "ongoing": [
      {
        "id": 459,
        "pickup_address": "Bus Stand, Hosur",
        "drop_address": "Railway Station, Hosur",
        "fare_amount": 60.00,
        "ride_type": "hatchback",
        "status": "started",
        "driver_name": "Suresh",
        "driver_phone": "9876543212",
        "started_at": "2024-12-25T14:45:00"
      }
    ],
    "history": [
      {
        "id": 458,
        "pickup_address": "MG Road, Hosur",
        "drop_address": "Bus Stand, Hosur",
        "fare_amount": 120.00,
        "final_fare": 100.00,
        "ride_type": "hatchback",
        "status": "completed",
        "driver_name": "Ravi Kumar",
        "completed_at": "2024-12-24T16:30:00"
      }
    ]
  },
  "message": "Customer bookings retrieved"
}
```

---

## 📢 Advertisement APIs

### 12. Get Advertisements
**Endpoint:** `GET /customer/advertisements`

**Description:** Get active advertisements for slideshow display.

**Query Parameters (Optional):**
- `location`: Filter by target location
- `ride_type`: Filter by target ride type
- `customer_type`: Filter by customer type (new, regular)

**Example:** `GET /customer/advertisements?ride_type=sedan&location=Hosur`

**Success Response:**
```json
{
  "success": true,
  "data": {
    "advertisements": [
      {
        "id": 1,
        "title": "Welcome to A1 Call Taxi",
        "content": "Reliable rides across Hosur",
        "media_type": "image",
        "media_url": "/static/ads/welcome_banner.jpg",
        "display_duration": 5,
        "display_order": 1,
        "target_location": null,
        "target_ride_type": null,
        "target_customer_type": "new",
        "click_url": null,
        "is_active": true,
        "impressions": 1250,
        "clicks": 45
      },
      {
        "id": 2,
        "title": "Airport Rides Available",
        "content": "Book your airport transfer now",
        "media_type": "image",
        "media_url": "/static/ads/airport_promo.jpg",
        "display_duration": 7,
        "display_order": 2,
        "target_location": "Hosur",
        "target_ride_type": "sedan",
        "target_customer_type": null,
        "click_url": "https://example.com/airport-booking",
        "is_active": true,
        "impressions": 890,
        "clicks": 23
      }
    ],
    "total_ads": 2,
    "total_duration_seconds": 12,
    "slideshow_config": {
      "auto_advance": true,
      "loop": true,
      "show_controls": false
    }
  },
  "message": "Advertisements retrieved successfully"
}
```

### 13. Record Advertisement Impression
**Endpoint:** `POST /customer/advertisements/{ad_id}/impression`

**Description:** Track when an advertisement is viewed.

**Request Body:** Empty
```json
{}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "ad_id": 1,
    "impressions": 1251,
    "message": "Impression recorded"
  },
  "message": "Impression recorded successfully"
}
```

### 14. Record Advertisement Click
**Endpoint:** `POST /customer/advertisements/{ad_id}/click`

**Description:** Track when an advertisement is clicked.

**Request Body:** Empty
```json
{}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "ad_id": 1,
    "clicks": 46,
    "impressions": 1251,
    "ctr": 3.68,
    "message": "Click recorded"
  },
  "message": "Click recorded successfully"
}
```

---

## 🚨 Error Handling

### Common Error Responses

**Invalid Phone Number:**
```json
{
  "success": false,
  "error": "Invalid phone number format. Please use 10-digit Indian mobile number."
}
```

**Customer Not Found:**
```json
{
  "success": false,
  "error": "Customer not found. Please login first."
}
```

**Invalid Ride Type:**
```json
{
  "success": false,
  "error": "Invalid ride type. Must be: hatchback, sedan, or suv"
}
```

**Invalid Coordinates:**
```json
{
  "success": false,
  "error": "Invalid latitude values"
}
```

**Ongoing Ride Exists:**
```json
{
  "success": false,
  "error": "You already have an ongoing ride"
}
```

**Invalid Promo Code:**
```json
{
  "success": false,
  "error": "Invalid promo code"
}
```

**No Cancellable Ride:**
```json
{
  "success": false,
  "error": "No cancellable ride found"
}
```

---

## 📋 API Status Summary

| API Endpoint | Status | Description |
|-------------|---------|-------------|
| `/login_or_register` | ✅ READY | Customer authentication |
| `/logout` | ✅ READY | Customer logout |
| `/ride_estimate` | ✅ READY | Fare calculation |
| `/book_ride` | ✅ READY | Ride booking |
| `/ride_status` | ✅ READY | Active ride status |
| `/cancel_ride` | ✅ READY | Cancel active ride |
| `/driver_location/{ride_id}` | ✅ READY | Live driver tracking |
| `/approve_zone_expansion` | ✅ READY | Zone expansion approval |
| `/validate_promo` | ✅ READY | Promo code validation |
| `/promo_codes/available` | ✅ READY | Available promo codes |
| `/bookings/{customer_id}` | ✅ READY | Booking history |
| `/advertisements` | ✅ READY | Advertisement slideshow |
| `/advertisements/{ad_id}/impression` | ✅ READY | Ad impression tracking |
| `/advertisements/{ad_id}/click` | ✅ READY | Ad click tracking |

---

## 🔧 Integration Notes

### Authentication Flow
1. Use `/login_or_register` for customer authentication
2. Store `customer_id` locally for future API calls
3. Use `/logout` when customer logs out

### Ride Booking Flow
1. Get fare estimate using `/ride_estimate`
2. Show estimates to customer with promo code option
3. Use `/validate_promo` if customer enters promo code
4. Book ride using `/book_ride`
5. Poll `/ride_status` for updates
6. Use `/driver_location/{ride_id}` for live tracking during active rides

### Error Handling
- Always check `success` field in response
- Display `error` message to user for failed requests
- Implement retry logic for network failures

### Data Validation
- Validate phone numbers: 10-digit Indian mobile format
- Validate coordinates: latitude (-90 to 90), longitude (-180 to 180)
- Validate ride types: hatchback, sedan, suv
- Validate ride categories: regular, airport, rental, outstation

### Performance Tips
- Cache available promo codes for 5-10 minutes
- Batch advertisement impression/click tracking
- Use websockets or polling for real-time ride status updates
- Preload advertisement media for smooth slideshow experience

---

## 🧪 Testing

All APIs are fully functional and tested. Use the base URL `http://localhost:5000/customer` for all endpoints.

For production deployment, replace the base URL with your production domain.

**API Status: ✅ FULLY FUNCTIONAL - Ready for Customer App Integration**