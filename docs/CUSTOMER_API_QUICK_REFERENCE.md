# A1 Call Taxi - Customer API Quick Reference

## Authentication Issues Fix

**Problem:** Your customer app is showing "failed to fetch" errors.

**Solution:** The issue is authentication. Here's what you need to fix:

### 1. JWT Token Authentication
All customer API calls (except login/register and fare estimate) need this header:
```
Authorization: Bearer <jwt_token>
```

### 2. Correct API Endpoints

❌ **WRONG:** `/api/customer/login_or_register`  
✅ **CORRECT:** `/customer/login_or_register`

❌ **WRONG:** `/api/customer/book_ride`  
✅ **CORRECT:** `/customer/book_ride`

The API endpoints are:
- `/customer/*` (not `/api/customer/*`)
- `/driver/*` (not `/api/driver/*`)

### 3. Working Authentication Flow

**Step 1: Login/Register (Get Token)**
```bash
curl -X POST http://localhost:5000/customer/login_or_register \
  -H "Content-Type: application/json" \
  -d '{"phone": "9876543210", "name": "John Doe"}'
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "customer": {
    "id": 9,
    "phone": "9876543210",
    "name": "John Doe"
  }
}
```

**Step 2: Use Token for All Other API Calls**
```bash
curl -X GET "http://localhost:5000/customer/ride_status?phone=9876543210" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Essential Customer API Endpoints

### 🔐 Authentication
| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/customer/login_or_register` | POST | ❌ | Login or register customer |

### 🚗 Ride Management
| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/customer/book_ride` | POST | ✅ | Book a new ride |
| `/customer/ride_status?phone=<phone>` | GET | ✅ | Get active ride status |
| `/customer/cancel_ride` | POST | ✅ | Cancel current ride |

### 💰 Pricing & Promos
| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/customer/ride_estimate` | POST | ❌ | Get fare estimates |
| `/customer/validate_promo` | POST | ✅ | Validate promo code |

## Field Formats

### Required Fields for Ride Booking:
```json
{
  "customer_phone": "9876543210",
  "pickup_address": "MG Road, Bengaluru", 
  "drop_address": "Airport Road, Bengaluru",
  "ride_type": "sedan"
}
```

### Optional Fields:
```json
{
  "pickup_lat": 12.9716,
  "pickup_lng": 77.5946,
  "drop_lat": 13.1986,
  "drop_lng": 77.7066,
  "ride_category": "regular",
  "promo_code": "WELCOME50",
  "scheduled_date": "15/08/2025",
  "scheduled_time": "14:30"
}
```

### Ride Types:
- `"hatchback"` - Small cars
- `"sedan"` - Medium cars  
- `"suv"` - Large cars/SUVs

### Ride Categories:
- `"regular"` - Normal city rides (default)
- `"airport"` - Airport transfers
- `"rental"` - Hourly rentals
- `"outstation"` - Inter-city trips

## Common Error Fixes

### ❌ "Failed to fetch"
**Cause:** Missing or incorrect JWT token
**Fix:** Ensure you're including the Authorization header with Bearer token

### ❌ "Customer not found"
**Cause:** Phone number mismatch between login and API calls
**Fix:** Use exact same phone number from login response

### ❌ "You already have an ongoing ride"
**Cause:** Customer has active ride in system
**Fix:** Check ride status first, cancel if needed

### ❌ "Pickup coordinates are required"
**Cause:** Missing pickup_lat/pickup_lng fields
**Fix:** Include GPS coordinates in booking request

## Real-Time Status Flow

**Ride Status Progression:**
1. `"new"` - Just booked, searching for driver
2. `"accepted"` - Driver accepted the ride
3. `"arrived"` - Driver arrived at pickup
4. `"started"` - Trip started (customer in vehicle)
5. `"completed"` - Trip completed
6. `"cancelled"` - Ride cancelled

**Polling Recommendation:** Check ride status every 5-10 seconds during active rides.

## Quick Test Commands

**Login:**
```bash
curl -X POST http://localhost:5000/customer/login_or_register \
  -H "Content-Type: application/json" \
  -d '{"phone": "9876543210", "name": "Test User"}'
```

**Get Fare Estimate:**
```bash
curl -X POST http://localhost:5000/customer/ride_estimate \
  -H "Content-Type: application/json" \
  -d '{"pickup_lat": 12.9716, "pickup_lng": 77.5946, "drop_lat": 13.1986, "drop_lng": 77.7066}'
```

**Book Ride:**
```bash
curl -X POST http://localhost:5000/customer/book_ride \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"customer_phone": "9876543210", "pickup_address": "MG Road", "drop_address": "Airport", "ride_type": "sedan", "pickup_lat": 12.9716, "pickup_lng": 77.5946, "drop_lat": 13.1986, "drop_lng": 77.7066}'
```

## Important Notes

1. **Token Expiry:** JWT tokens expire after 7 days
2. **Phone Format:** Use 10-digit Indian numbers (e.g., "9876543210")
3. **Coordinate Precision:** Use up to 6 decimal places for GPS coordinates
4. **Response Format:** All APIs return `{"success": boolean, "message": string, "data": object}`
5. **Error Handling:** Always check `success` field in response

---

**This resolves the "failed to fetch" authentication issues in your customer app.**