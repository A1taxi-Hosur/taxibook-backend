# Customer API Documentation

## Base URL: `http://localhost:5000`

## Customer Authentication

### 1. Login or Register
**Endpoint**: `POST /customer/login_or_register`

**Request**:
```json
{
  "phone": "9876543210",
  "name": "John Doe"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "customer_id": 9,
    "name": "Test Customer",
    "phone": "9876543210",
    "action": "login"
  }
}
```

## Ride Booking Flow

### 2. Get Ride Estimate
**Endpoint**: `POST /customer/ride_estimate`

**Request**:
```json
{
  "pickup_lat": 12.9716,
  "pickup_lng": 77.5946,
  "drop_lat": 12.9352,
  "drop_lng": 77.6245
}
```

**Response**:
```json
{
  "success": true,
  "distance_km": 6.8,
  "estimates": {
    "hatchback": 106.59,
    "sedan": 92.99,
    "suv": 116.59
  }
}
```

### 3. Book Ride
**Endpoint**: `POST /customer/book_ride`

**Request**:
```json
{
  "customer_phone": "9876543210",
  "pickup_address": "Test Pickup",
  "drop_address": "Test Drop",
  "pickup_lat": 12.9716,
  "pickup_lng": 77.5946,
  "drop_lat": 12.9352,
  "drop_lng": 77.6245,
  "ride_type": "sedan",
  "fare_amount": 92.99
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Ride booked. No drivers available for automatic assignment.",
  "data": {
    "ride_id": 38,
    "distance_km": 6.799,
    "pickup_address": "Test Pickup",
    "drop_address": "Test Drop",
    "fare_amount": 92.99,
    "final_fare": 92.99,
    "ride_type": "sedan",
    "ride_category": "regular",
    "status": "new",
    "requires_manual_assignment": true,
    "error_message": "No service zone found for pickup location"
  }
}
```

## Ride Status & Tracking

### 4. Get Ride Status
**Endpoint**: `GET /customer/ride_status?phone=9876543210`

**Response**:
```json
{
  "status": "success",
  "message": "Ride status retrieved",
  "data": {
    "has_active_ride": true,
    "ride_id": 38,
    "status": "new",
    "driver_name": "Driver Name",
    "driver_phone": "9876543210",
    "start_otp": "123456"
  }
}
```

### 5. Get Customer Bookings
**Endpoint**: `GET /customer/bookings?customer_id=9`

**Response**:
```json
{
  "status": "success",
  "data": {
    "customer_id": 9,
    "bookings": [],
    "ongoing": [],
    "history": []
  }
}
```

### 6. Cancel Ride
**Endpoint**: `POST /customer/cancel_ride`

**Request**:
```json
{
  "ride_id": 38,
  "customer_phone": "9876543210"
}
```

## Mobile API Endpoints

### 7. Customer Profile
**Endpoint**: `GET /mobile/customer/profile?phone=9876543210`

### 8. Customer Total Spent
**Endpoint**: `GET /mobile/customer/total_spent?phone=9876543210`

## Important Notes

1. **CORS**: The backend supports CORS for cross-origin requests
2. **Session Management**: Use `credentials: 'include'` in fetch requests
3. **Phone Validation**: Phone numbers must be 10 digits starting with 6-9
4. **Zone Coverage**: Rides outside service zones require manual assignment
5. **Real-time Updates**: Use polling for ride status updates

## Frontend Integration Example

```javascript
// Customer Login
const login = async (phone, name) => {
  const response = await fetch('/customer/login_or_register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ phone, name }),
    credentials: 'include'
  });
  return response.json();
};

// Get Ride Estimate
const getRideEstimate = async (pickupLat, pickupLng, dropLat, dropLng) => {
  const response = await fetch('/customer/ride_estimate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      pickup_lat: pickupLat,
      pickup_lng: pickupLng,
      drop_lat: dropLat,
      drop_lng: dropLng
    })
  });
  return response.json();
};

// Book Ride
const bookRide = async (customerPhone, pickupAddress, dropAddress, pickupLat, pickupLng, dropLat, dropLng, rideType, fareAmount) => {
  const response = await fetch('/customer/book_ride', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      customer_phone: customerPhone,
      pickup_address: pickupAddress,
      drop_address: dropAddress,
      pickup_lat: pickupLat,
      pickup_lng: pickupLng,
      drop_lat: dropLat,
      drop_lng: dropLng,
      ride_type: rideType,
      fare_amount: fareAmount
    }),
    credentials: 'include'
  });
  return response.json();
};
```

## API Status: ✅ FULLY FUNCTIONAL

All customer API endpoints are working correctly and ready for frontend integration.