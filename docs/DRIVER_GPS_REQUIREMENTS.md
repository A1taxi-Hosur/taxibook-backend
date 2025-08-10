# Driver App GPS Requirements

## Critical Changes Required

### 1. GPS Update Frequency
**REQUIREMENT**: All logged-in drivers must send location updates every 3 seconds regardless of ride status.

**Current Issue**: The backend now filters out drivers with location data older than 30 seconds from:
- Live driver map
- Ride dispatch notifications  
- Driver availability checks

### 2. Implementation Requirements

**GPS Update Endpoint**: `POST /driver/update_current_location`

**Required Payload**:
```json
{
    "latitude": 12.9716,
    "longitude": 77.5946
}
```

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### 3. JavaScript Implementation Example

```javascript
// Start GPS tracking when driver logs in
function startLocationTracking() {
    if (navigator.geolocation) {
        // Update location every 3 seconds (3000ms)
        locationIntervalId = setInterval(() => {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    updateDriverLocation(
                        position.coords.latitude, 
                        position.coords.longitude
                    );
                },
                (error) => {
                    console.error('GPS Error:', error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 1000
                }
            );
        }, 3000); // 3 seconds interval
    }
}

async function updateDriverLocation(latitude, longitude) {
    try {
        const response = await fetch('/driver/update_current_location', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('driver_token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                latitude: latitude,
                longitude: longitude
            })
        });
        
        if (!response.ok) {
            console.error('Failed to update location');
        }
    } catch (error) {
        console.error('Location update error:', error);
    }
}

// Stop tracking when driver logs out
function stopLocationTracking() {
    if (locationIntervalId) {
        clearInterval(locationIntervalId);
        locationIntervalId = null;
    }
}
```

### 4. Backend Changes Made

✅ **30-second timeout rule**: Drivers are removed from live map if no location update for >30 seconds
✅ **Aggressive filtering**: Only drivers with fresh location data receive ride notifications
✅ **Enhanced debugging**: Comprehensive logging for location staleness detection
✅ **Zone-based filtering**: Improved driver matching with location freshness checks

### 5. Testing

After implementing the 3-second GPS updates:

1. **Live Map Test**: Driver should appear on admin live map within 3 seconds of login
2. **Ride Dispatch Test**: Driver should receive ride notifications immediately when rides are booked in their zone
3. **Location Staleness**: If driver stops sending updates, they should disappear from map after 30 seconds

### 6. Battery Optimization Note

The 3-second interval is aggressive but necessary for real-time dispatch. Consider:
- Using background location services
- Implementing battery optimization warnings for users
- Providing option to reduce frequency when not actively seeking rides (future enhancement)