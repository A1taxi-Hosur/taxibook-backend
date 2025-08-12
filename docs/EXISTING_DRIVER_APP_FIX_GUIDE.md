# Fix for Existing Driver Apps - Add Continuous Location Tracking

## Problem Identified
Your existing driver apps can login successfully but drivers disappear from the admin panel after 2-3 minutes because they're not sending continuous location updates and heartbeats.

## What Needs to be Added
Add these 3 missing functionalities to your existing driver apps:

1. **Continuous Location Updates** (every 30-60 seconds)
2. **Heartbeat System** (every 60 seconds) 
3. **Background Service** (keeps tracking active when app is minimized)

---

## Fix 1: Add Location Tracking Service

### For React Native Apps
Add this to your existing app (create new file or add to existing service):

```javascript
// Add to your existing LocationService.js or create new file
class ContinuousLocationTracker {
  constructor() {
    this.locationInterval = null;
    this.heartbeatInterval = null;
    this.isTracking = false;
    this.baseURL = 'YOUR_BACKEND_URL'; // Replace with your backend URL
  }

  // Add this method to your existing login success handler
  startTracking() {
    if (this.isTracking) return;
    
    console.log('🚀 Starting continuous tracking...');
    this.isTracking = true;

    // Send location every 30 seconds
    this.locationInterval = setInterval(() => {
      this.sendLocationUpdate();
    }, 30000);

    // Send heartbeat every 60 seconds  
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, 60000);

    // Send first update immediately
    this.sendLocationUpdate();
  }

  // Add this method to your existing logout handler
  stopTracking() {
    console.log('🛑 Stopping tracking...');
    
    if (this.locationInterval) {
      clearInterval(this.locationInterval);
      this.locationInterval = null;
    }
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    this.isTracking = false;
  }

  // Add this new method
  async sendLocationUpdate() {
    try {
      // Get current location
      navigator.geolocation.getCurrentPosition(async (position) => {
        const { latitude, longitude } = position.coords;
        
        // Get stored JWT token (however you store it in your app)
        const token = await this.getStoredToken(); // Replace with your token retrieval method
        
        // Send to backend
        const response = await fetch(`${this.baseURL}/driver/update_current_location`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
          }),
        });

        const data = await response.json();
        if (data.success) {
          console.log('✅ Location updated');
        } else {
          console.log('❌ Location update failed:', data.message);
        }
      });
    } catch (error) {
      console.log('Location error:', error);
    }
  }

  // Add this new method
  async sendHeartbeat() {
    try {
      const token = await this.getStoredToken(); // Replace with your token retrieval method
      
      const response = await fetch(`${this.baseURL}/driver/heartbeat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      if (data.success) {
        console.log('💓 Heartbeat sent');
      } else {
        console.log('❌ Heartbeat failed:', data.message);
      }
    } catch (error) {
      console.log('Heartbeat error:', error);
    }
  }

  // Replace this with however you get the token in your app
  async getStoredToken() {
    // For React Native:
    // return await AsyncStorage.getItem('driver_token');
    
    // For web apps:
    // return localStorage.getItem('driver_token');
    
    // Replace with your method
    return YOUR_TOKEN_STORAGE_METHOD;
  }
}

// Create instance
const locationTracker = new ContinuousLocationTracker();
export default locationTracker;
```

### For Web Apps
Add this to your existing JavaScript:

```javascript
// Add to your existing app.js or main.js
class WebLocationTracker {
  constructor() {
    this.locationInterval = null;
    this.heartbeatInterval = null;
    this.isTracking = false;
    this.baseURL = 'YOUR_BACKEND_URL'; // Replace with your backend URL
  }

  // Call this after successful login
  startTracking() {
    if (this.isTracking) return;
    
    console.log('🚀 Starting web location tracking...');
    this.isTracking = true;

    // Location updates every 30 seconds
    this.locationInterval = setInterval(() => {
      this.updateLocation();
    }, 30000);

    // Heartbeat every 60 seconds
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, 60000);

    // Send first update
    this.updateLocation();
  }

  // Call this on logout
  stopTracking() {
    console.log('🛑 Stopping web tracking...');
    
    clearInterval(this.locationInterval);
    clearInterval(this.heartbeatInterval);
    this.isTracking = false;
  }

  async updateLocation() {
    if (!navigator.geolocation) {
      console.log('Geolocation not supported');
      return;
    }

    navigator.geolocation.getCurrentPosition(async (position) => {
      try {
        const { latitude, longitude } = position.coords;
        const token = localStorage.getItem('driver_token'); // Adjust based on your storage

        const response = await fetch(`${this.baseURL}/driver/update_current_location`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ latitude, longitude }),
        });

        const data = await response.json();
        console.log(data.success ? '✅ Location sent' : '❌ Location failed');
      } catch (error) {
        console.log('Location error:', error);
      }
    });
  }

  async sendHeartbeat() {
    try {
      const token = localStorage.getItem('driver_token'); // Adjust based on your storage
      
      const response = await fetch(`${this.baseURL}/driver/heartbeat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();
      console.log(data.success ? '💓 Heartbeat OK' : '❌ Heartbeat failed');
    } catch (error) {
      console.log('Heartbeat error:', error);
    }
  }
}

// Create global instance
window.locationTracker = new WebLocationTracker();
```

---

## Fix 2: Integration with Existing Login/Logout

### Modify Your Existing Login Function
Find your current login function and add these lines after successful login:

```javascript
// In your existing login success handler, add:
if (loginResponse.success) {
  // Your existing login code...
  
  // ADD THESE LINES:
  locationTracker.startTracking(); // Start continuous tracking
  console.log('🟢 Driver now online with location tracking');
}
```

### Modify Your Existing Logout Function  
Find your current logout function and add this line:

```javascript
// In your existing logout function, add:
function logout() {
  // ADD THIS LINE FIRST:
  locationTracker.stopTracking(); // Stop tracking before logout
  
  // Your existing logout code...
  console.log('🔴 Driver offline');
}
```

### Modify Your Existing "Go Online" Button
If you have an online/offline toggle, update it:

```javascript
// When driver goes online:
function goOnline() {
  locationTracker.startTracking();
  // Update your UI to show online status
}

// When driver goes offline:
function goOffline() {
  locationTracker.stopTracking();
  // Update your UI to show offline status
}
```

---

## Fix 3: Background Service (React Native Only)

### For React Native Apps
Add background capability to keep location tracking active when app is minimized:

```javascript
// Install background service library first:
// npm install react-native-background-service

// Add to your existing app
import BackgroundService from 'react-native-background-service';

class BackgroundLocationService {
  async startBackgroundService() {
    const options = {
      taskName: 'LocationTracking',
      taskTitle: 'A1 Taxi - Online',
      taskDesc: 'Tracking location for ride requests',
      taskIcon: {
        name: 'ic_launcher',
        type: 'mipmap',
      }
    };

    await BackgroundService.start(options);
    console.log('✅ Background service started');
  }

  async stopBackgroundService() {
    await BackgroundService.stop();
    console.log('✅ Background service stopped');
  }
}

// Use in your login/logout handlers:
const backgroundService = new BackgroundLocationService();

// After login success:
await backgroundService.startBackgroundService();
locationTracker.startTracking();

// Before logout:
locationTracker.stopTracking();
await backgroundService.stopBackgroundService();
```

---

## Fix 4: Permissions (Important!)

### Request Location Permissions Properly

#### For React Native:
```javascript
import { PermissionsAndroid, Platform } from 'react-native';

async function requestLocationPermission() {
  if (Platform.OS === 'android') {
    const granted = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
      {
        title: 'Location Permission',
        message: 'A1 Taxi needs location access to receive ride requests',
        buttonNeutral: 'Ask Me Later',
        buttonNegative: 'Cancel',
        buttonPositive: 'OK',
      },
    );
    return granted === PermissionsAndroid.RESULTS.GRANTED;
  }
  return true;
}

// Call this before starting location tracking:
const hasPermission = await requestLocationPermission();
if (hasPermission) {
  locationTracker.startTracking();
} else {
  alert('Location permission is required');
}
```

#### For Web Apps:
```javascript
// Request permission on first use
navigator.permissions.query({ name: 'geolocation' }).then((result) => {
  if (result.state === 'granted' || result.state === 'prompt') {
    locationTracker.startTracking();
  } else {
    alert('Location permission is required to go online');
  }
});
```

---

## Testing Your Fix

### Test Steps:
1. **Login to your driver app**
2. **Check browser console** (for web) or debug logs (for mobile)
3. **Look for these messages every 30-60 seconds:**
   ```
   ✅ Location sent
   💓 Heartbeat OK
   ```
4. **Check admin panel** - driver should appear on map within 1 minute
5. **Minimize app for 5+ minutes** - driver should stay visible on admin panel

### If Still Not Working:

#### Check Backend URL:
```javascript
// Make sure your baseURL is correct:
this.baseURL = 'https://your-actual-backend-url.replit.app';
// NOT localhost or 127.0.0.1
```

#### Check Token Storage:
```javascript
// Verify token is stored correctly:
console.log('Stored token:', await this.getStoredToken());
// Should start with "eyJhbGciOiJIUzI1NiIs..."
```

#### Check Network Requests:
- Open browser Network tab
- Should see requests to `/driver/update_current_location` every 30 seconds
- Should see requests to `/driver/heartbeat` every 60 seconds

---

## Summary

**What to add to your existing apps:**

1. **Location tracking service** - copy the code above
2. **Start tracking after login** - add one line to login success
3. **Stop tracking on logout** - add one line to logout
4. **Request location permissions** - add permission handling
5. **Background service** (React Native only) - for continuous tracking

**Expected Result:**
- Driver stays visible on admin panel continuously
- Customers can find and book rides with the driver
- Location updates every 30 seconds
- Session maintained with heartbeat every 60 seconds

Your backend is working perfectly - this fix will make your driver apps stay connected and visible for ride requests.