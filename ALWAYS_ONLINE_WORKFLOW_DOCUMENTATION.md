# Always Online Driver System - Complete Workflow Documentation

## Overview
The A1 Call Taxi driver system has been updated to use an "Always Online" approach, eliminating manual online/offline status toggles and simplifying the driver experience.

## Core Concept
**Drivers are automatically online when logged in and offline when logged out**

### Previous System (Deprecated)
- Driver logs in → Still offline
- Driver manually toggles online → Receives rides
- Driver manually toggles offline → No rides
- Driver logs out → Session ends

### New System (Current)
- Driver logs in → **Automatically online** → Receives rides immediately
- Driver logs out → **Automatically offline** → No rides
- **No manual toggle needed**

---

## API Changes & Workflow

### 1. Login Process

**Endpoint**: `POST /driver/login`

**Request Format**:
```json
{
    "username": "DRVVJ53TA",
    "password": "driver123"
}
```

**Response Format**:
```json
{
    "status": "success",
    "message": "Login successful",
    "data": {
        "driver_id": 20,
        "name": "Ricco",
        "phone": "9988776655",
        "username": "DRVVJ53TA",
        "is_online": true,  // ← ALWAYS TRUE after login
        "car_make": "Maruti",
        "car_model": "Ciaz",
        "car_year": 2003,
        "car_number": "TN29AQ1288",
        "car_type": "sedan"
    }
}
```

**Backend Behavior**:
```python
# Automatically sets driver online upon successful login
driver.is_online = True
db.session.commit()
```

---

### 2. Incoming Rides (Simplified)

**Endpoint**: `GET /driver/incoming_rides?phone=9988776655`

**Previous Behavior**:
- Check if driver is online
- If offline: Return "Driver is offline. No rides available."
- If online: Return available rides

**New Behavior**:
- **No online check needed** - all logged-in drivers receive rides
- Always returns available rides matching driver's vehicle type and zone

**Response Format**:
```json
{
    "status": "success",
    "message": "Incoming rides retrieved",
    "data": {
        "rides": [
            {
                "id": 123,
                "pickup_address": "Chennai Central",
                "drop_address": "Anna Nagar",
                "fare_amount": 250.00,
                "ride_type": "sedan",
                "distance_km": 12.5,
                "created_at": "2025-08-02T16:00:00"
            }
        ],
        "count": 1
    }
}
```

---

### 3. Status Endpoints (Modified)

#### Get Status
**Endpoint**: `GET /driver/status?mobile=9988776655`

**Response**:
```json
{
    "status": "success",
    "message": "Driver status retrieved",
    "data": {
        "is_online": true,  // ← ALWAYS TRUE for logged-in drivers
        "driver_id": 20,
        "name": "Ricco",
        "phone": "9988776655"
    }
}
```

#### Update Status (Deprecated but Compatible)
**Endpoint**: `POST /driver/status`

**Request**:
```json
{
    "mobile": "9988776655",
    "is_online": true  // ← Ignored in new system
}
```

**Response**:
```json
{
    "status": "success",
    "message": "Driver is always online when logged in",
    "data": {
        "driver_id": 20,
        "name": "Ricco",
        "phone": "9988776655",
        "is_online": true  // ← Always returns true
    }
}
```

---

### 4. Logout Process

**Endpoint**: `POST /driver/logout`

**Request Format**:
```json
{
    "phone": "9988776655"  // ← Required for setting offline
}
```

**Response Format**:
```json
{
    "status": "success",
    "message": "Logout successful"
}
```

**Backend Behavior**:
```python
# Automatically sets driver offline upon logout
driver.is_online = False
db.session.commit()
logout_user()  # End session
```

---

## Complete Driver Workflow

### Mobile App Flow

```
1. App Launch
   ↓
2. Login Screen
   ↓
3. Enter Username/Password → POST /driver/login
   ↓
4. Success → Driver automatically online
   ↓
5. Dashboard Screen (No online/offline toggle)
   ↓
6. Poll for rides → GET /driver/incoming_rides
   ↓
7. Receive rides immediately (no status check)
   ↓
8. Accept/Reject rides → Normal flow continues
   ↓
9. Logout → POST /driver/logout (with phone)
   ↓
10. Driver automatically offline → No more rides
```

### Removed UI Elements
- Online/Offline toggle switch
- Status indicator (online/offline badge)
- Manual status update buttons
- Status-related notifications

---

## Field Formats & Validation

### Required Fields for Login
```json
{
    "username": "string (required, non-empty)",
    "password": "string (required, non-empty)"
}
```

### Required Fields for Logout  
```json
{
    "phone": "string (10-digit Indian mobile, starts with 6-9)"
}
```

### Phone Number Validation
- **Format**: 10 digits exactly
- **Pattern**: Must start with 6, 7, 8, or 9
- **Examples**: `9988776655`, `8765432109`
- **Invalid**: `1234567890`, `555-123-4567`

---

## Database Schema Changes

### Driver Table
```sql
-- is_online field behavior:
-- true: Driver logged in (available for rides)
-- false: Driver logged out (unavailable for rides)

-- Default state: All drivers set to online initially
UPDATE driver SET is_online = true;
```

### Ride Assignment Logic
```sql
-- Previous query (with online check):
SELECT * FROM ride 
WHERE status = 'pending' 
  AND driver_id IS NULL 
  AND ride_type = :driver_car_type
  AND driver.is_online = true;  -- ← REMOVED

-- New query (no online check):
SELECT * FROM ride 
WHERE status = 'pending' 
  AND driver_id IS NULL 
  AND ride_type = :driver_car_type;
-- All logged-in drivers automatically receive matching rides
```

---

## Migration Guide for Existing Apps

### Frontend Changes Required

#### Remove These Components:
```javascript
// Remove online/offline toggle
<Switch 
  value={isOnline} 
  onValueChange={toggleOnlineStatus}  // ← DELETE
/>

// Remove status update calls
const toggleOnlineStatus = async () => {  // ← DELETE FUNCTION
  await fetch('/driver/status', {
    method: 'POST',
    body: JSON.stringify({
      mobile: phone,
      is_online: !isOnline
    })
  });
};
```

#### Update These Components:
```javascript
// Logout function - add phone parameter
const logout = async () => {
  await fetch('/driver/logout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone: driverPhone  // ← ADD THIS
    })
  });
};

// Remove online status checks
const checkRides = async () => {
  // OLD: if (!isOnline) return;  ← REMOVE THIS CHECK
  
  const response = await fetch(`/driver/incoming_rides?phone=${phone}`);
  // Rides will come automatically for logged-in drivers
};
```

---

## Error Handling

### Login Errors
```json
{
    "status": "error",
    "message": "Invalid username or password"
}
```

### Phone Validation Errors
```json
{
    "status": "error", 
    "message": "Invalid phone number format. Must be a 10-digit Indian mobile number starting with 6-9"
}
```

### General Errors
```json
{
    "status": "error",
    "message": "Internal server error"
}
```

---

## Benefits of Always Online System

### For Drivers
- **Simplified Experience**: No confusing online/offline buttons
- **Immediate Availability**: Rides start coming right after login
- **No Missed Rides**: Can't accidentally be offline while logged in
- **Clear States**: Logged in = Available, Logged out = Unavailable

### For Dispatch System
- **Reliable Availability**: All logged-in drivers are genuinely available
- **Simplified Logic**: No complex status checks in ride assignment
- **Better Coverage**: Maximum driver pool always available
- **Reduced Errors**: Eliminates status-related bugs

### For Development
- **Simpler Code**: Fewer conditional checks
- **Better Testing**: Predictable driver states
- **Easier Integration**: Mobile apps don't need status management
- **Reduced Support**: Fewer status-related user issues

---

## Testing the System

### Test Login & Auto-Online
```bash
curl -X POST "http://localhost:5000/driver/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"DRVVJ53TA","password":"driver123"}'
# Should return is_online: true
```

### Test Rides (No Status Check)
```bash
curl "http://localhost:5000/driver/incoming_rides?phone=9988776655"
# Should return rides without checking online status
```

### Test Logout & Auto-Offline
```bash
curl -X POST "http://localhost:5000/driver/logout" \
  -H "Content-Type: application/json" \
  -d '{"phone":"9988776655"}'
# Driver should be set offline in database
```

---

This new system eliminates complexity while ensuring drivers are always available when they intend to be working.