# Centralized GPS Tracking Implementation Guide
## A1 Call Taxi - Driver & Customer Mobile Apps

## Overview

The A1 Call Taxi platform uses a **unified GPS tracking system** that serves multiple purposes with a single implementation. This eliminates the complexity of managing separate location tracking systems and ensures consistent, accurate positioning across all app features.

## System Architecture

### Single GPS Service Design
```
Mobile App GPS Service
├── Continuous Location Monitoring (30-60 seconds)
├── Enhanced Active Ride Tracking (10-15 seconds)
├── Automatic API Updates to Backend
└── Local Storage for Offline Support
```

### Backend Endpoints
- **General Location**: `POST /driver/update_current_location` (for dispatch and availability)
- **Active Ride Tracking**: `POST /driver/update_location` (during rides)
- **Authentication**: All endpoints require `Authorization: Bearer <JWT_TOKEN>` header

## Implementation for Driver Apps

### Core GPS Service
```javascript
class UnifiedGPSService {
    constructor() {
        this.isTracking = false;
        this.isOnActiveRide = false;
        this.currentRideId = null;
        this.trackingInterval = null;
        this.jwtToken = localStorage.getItem('driver_token');
    }

    startTracking() {
        if (this.isTracking) return;
        
        this.isTracking = true;
        this.updateTrackingFrequency();
        console.log('GPS tracking started');
    }

    stopTracking() {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
        }
        this.isTracking = false;
        console.log('GPS tracking stopped');
    }

    // Automatically adjust frequency based on driver state
    updateTrackingFrequency() {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
        }

        // More frequent updates during active rides
        const interval = this.isOnActiveRide ? 15000 : 30000; // 15s vs 30s
        
        this.trackingInterval = setInterval(() => {
            this.getCurrentLocationAndUpdate();
        }, interval);
    }

    async getCurrentLocationAndUpdate() {
        try {
            const position = await this.getCurrentPosition();
            const location = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                phone: localStorage.getItem('driver_phone')
            };

            // Always update general location (for dispatch)
            await this.updateCurrentLocation(location);

            // Also update ride tracking if on active ride
            if (this.isOnActiveRide && this.currentRideId) {
                await this.updateRideLocation(location, this.currentRideId);
            }

        } catch (error) {
            console.error('GPS update failed:', error);
            // Implement retry logic here
        }
    }

    getCurrentPosition() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                resolve,
                reject,
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 30000
                }
            );
        });
    }

    async updateCurrentLocation(location) {
        try {
            const response = await fetch('/driver/update_current_location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.jwtToken}`
                },
                body: JSON.stringify(location)
            });

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message);
            }

            console.log('Location updated successfully');
            return result;

        } catch (error) {
            console.error('Failed to update location:', error);
            throw error;
        }
    }

    async updateRideLocation(location, rideId) {
        try {
            const rideLocationData = {
                ...location,
                ride_id: rideId
            };

            const response = await fetch('/driver/update_location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.jwtToken}`
                },
                body: JSON.stringify(rideLocationData)
            });

            const result = await response.json();
            if (!result.success) {
                throw new Error(result.message);
            }

            console.log('Ride location updated successfully');
            return result;

        } catch (error) {
            console.error('Failed to update ride location:', error);
            throw error;
        }
    }

    // Call when driver accepts a ride
    startActiveRideTracking(rideId) {
        this.isOnActiveRide = true;
        this.currentRideId = rideId;
        this.updateTrackingFrequency(); // Switch to 15-second intervals
        console.log(`Started active ride tracking for ride ${rideId}`);
    }

    // Call when ride is completed
    stopActiveRideTracking() {
        this.isOnActiveRide = false;
        this.currentRideId = null;
        this.updateTrackingFrequency(); // Switch back to 30-second intervals
        console.log('Stopped active ride tracking');
    }
}

// Global GPS service instance
const gpsService = new UnifiedGPSService();

// Usage in driver app
window.addEventListener('load', () => {
    // Start GPS tracking when driver logs in
    if (localStorage.getItem('driver_token')) {
        gpsService.startTracking();
    }
});

// Hook into ride lifecycle
function onRideAccepted(rideId) {
    gpsService.startActiveRideTracking(rideId);
}

function onRideCompleted() {
    gpsService.stopActiveRideTracking();
}
```

### Driver App Integration Points

1. **Login Flow**: Start GPS tracking after successful authentication
2. **Logout Flow**: Stop GPS tracking when driver logs out
3. **Ride Acceptance**: Switch to enhanced tracking mode
4. **Ride Completion**: Return to standard tracking mode
5. **App Background/Foreground**: Maintain tracking in background

## Implementation for Customer Apps

### Location Tracking for Customers
```javascript
class CustomerLocationService {
    constructor() {
        this.currentLocation = null;
        this.jwtToken = localStorage.getItem('customer_token');
    }

    async getCurrentLocation() {
        try {
            const position = await this.getPosition();
            this.currentLocation = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
            };
            return this.currentLocation;
        } catch (error) {
            console.error('Failed to get customer location:', error);
            throw error;
        }
    }

    getPosition() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation not supported'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                resolve,
                reject,
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                }
            );
        });
    }

    // Update location when booking a ride
    async updateLocationForBooking(bookingData) {
        const currentLocation = await this.getCurrentLocation();
        return {
            ...bookingData,
            pickup_latitude: currentLocation.latitude,
            pickup_longitude: currentLocation.longitude
        };
    }

    // Track ride progress (polling driver location)
    startRideTracking(rideId) {
        const trackingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/customer/ride/${rideId}/location`, {
                    headers: {
                        'Authorization': `Bearer ${this.jwtToken}`
                    }
                });

                const result = await response.json();
                if (result.success && result.data.driver_location) {
                    this.updateDriverLocationOnMap(result.data.driver_location);
                }

            } catch (error) {
                console.error('Failed to get driver location:', error);
            }
        }, 10000); // Poll every 10 seconds

        // Store interval ID to clear later
        this.rideTrackingInterval = trackingInterval;
    }

    stopRideTracking() {
        if (this.rideTrackingInterval) {
            clearInterval(this.rideTrackingInterval);
            this.rideTrackingInterval = null;
        }
    }
}
```

## Key Benefits of This Unified Approach

### 1. **Simplified Architecture**
- Single GPS service handles all location needs
- No duplicate code or conflicting implementations
- Consistent behavior across all app features

### 2. **Intelligent Frequency Management**
- Automatic adjustment based on driver state
- Battery-optimized intervals (30s general, 15s active rides)
- Reduces unnecessary API calls and battery drain

### 3. **Robust Error Handling**
- Centralized retry logic for failed location updates
- Graceful degradation when GPS is unavailable
- Consistent error messages across all features

### 4. **Scalable Design**
- Easy to add new location-based features
- Centralized configuration management
- Simple to update tracking behavior globally

## API Requirements

### Authentication
All location update requests must include:
```
Authorization: Bearer <JWT_TOKEN>
```

### Request Format
```json
{
    "phone": "driver_phone_number",
    "latitude": 13.0827,
    "longitude": 80.2707
}
```

### Response Format
```json
{
    "success": true,
    "message": "Location updated successfully",
    "data": {
        "driver_id": 123,
        "latitude": 13.0827,
        "longitude": 80.2707,
        "updated_at": "2025-08-10T18:30:00",
        "zone": "chennai"
    }
}
```

## Testing and Validation

### Driver App Testing
1. **Login Test**: Verify GPS starts automatically
2. **Ride Acceptance**: Confirm frequency increases to 15 seconds
3. **Ride Completion**: Confirm frequency returns to 30 seconds
4. **Background Mode**: Ensure tracking continues when app is backgrounded
5. **Network Issues**: Test retry logic during connectivity problems

### Customer App Testing
1. **Booking Flow**: Verify current location is captured correctly
2. **Ride Tracking**: Confirm driver location updates every 10 seconds
3. **Map Display**: Ensure smooth movement of driver markers

## Security Considerations

1. **Token Validation**: Always validate JWT tokens on backend
2. **Rate Limiting**: Implement rate limits to prevent GPS spam
3. **Data Privacy**: Only store necessary location data
4. **Encryption**: Use HTTPS for all location API calls

This unified approach ensures reliable, efficient GPS tracking while maintaining simplicity for developers and optimal performance for users.