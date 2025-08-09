# GPS Tracking System Demo

## Overview
The TaxiBook backend now includes a comprehensive GPS tracking system that allows real-time monitoring of driver locations during active rides.

## System Architecture

### Database Schema
```sql
-- RideLocation table for storing GPS coordinates
CREATE TABLE ride_location (
    id INTEGER PRIMARY KEY,
    ride_id INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    timestamp DATETIME NOT NULL,
    is_latest BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (ride_id) REFERENCES ride (id)
);

-- Optimized indexes for fast lookups
CREATE INDEX idx_ride_location_ride_id ON ride_location(ride_id);
CREATE INDEX idx_ride_location_is_latest ON ride_location(is_latest);
CREATE INDEX idx_ride_location_ride_latest ON ride_location(ride_id, is_latest);
CREATE INDEX idx_ride_location_timestamp ON ride_location(timestamp DESC);
```

### Key Features

#### 1. Driver Location Updates
- **Endpoint**: `POST /driver/update_location`
- **Purpose**: Drivers submit GPS coordinates periodically during active rides
- **Data**: ride_id, latitude, longitude, timestamp
- **Validation**: Coordinate range validation, ride status verification
- **Performance**: Latest location flagged for instant retrieval

#### 2. Customer Location Retrieval
- **Endpoint**: `GET /customer/driver_location/{ride_id}`
- **Purpose**: Customers get real-time driver location for their active ride
- **Data**: Current coordinates, timestamp, ride status, pickup/drop locations
- **Performance**: Indexed lookup for sub-millisecond response

#### 3. Location History Preservation
- **Complete Route Storage**: All GPS points stored for completed rides
- **Audit Trail**: Full movement history preserved for analytics
- **Data Integrity**: No location data deleted, only flagged as historical

## API Endpoints

### Driver Location Update
```bash
curl -X POST http://localhost:5000/driver/update_location \
  -H "Content-Type: application/json" \
  -d '{
    "driver_phone": "9876543210",
    "ride_id": 123,
    "latitude": 13.0479374,
    "longitude": 80.1821813
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Location updated successfully",
  "data": {
    "ride_id": 123,
    "latitude": 13.0479374,
    "longitude": 80.1821813,
    "timestamp": "2025-07-07T02:20:30"
  }
}
```

### Customer Location Retrieval
```bash
curl -X GET http://localhost:5000/customer/driver_location/123
```

**Response:**
```json
{
  "ride_id": 123,
  "latitude": 13.0479374,
  "longitude": 80.1821813,
  "timestamp": "2025-07-07T02:20:30",
  "ride_status": "accepted",
  "pickup_lat": 13.0479374,
  "pickup_lng": 80.1821813,
  "drop_lat": 12.8193124,
  "drop_lng": 80.0393459
}
```

## Security & Validation

### Coordinate Validation
- Latitude: -90 to +90 degrees
- Longitude: -180 to +180 degrees
- Type validation for numeric values
- Range checking for realistic coordinates

### Access Control
- Drivers can only update locations for their assigned rides
- Customers can only view locations for their active rides
- Location updates only allowed for active ride statuses

### Data Integrity
- Atomic database operations
- Rollback on errors
- Comprehensive logging
- Error handling for edge cases

## Performance Optimizations

### Database Indexes
- `idx_ride_location_ride_id`: Fast ride-specific queries
- `idx_ride_location_is_latest`: Quick latest location lookup
- `idx_ride_location_ride_latest`: Composite index for optimal performance
- `idx_ride_location_timestamp`: Chronological ordering

### Efficient Updates
- Single latest location per ride marked with `is_latest=true`
- Bulk update previous locations to `is_latest=false`
- Minimized database scans for real-time queries

## Use Cases

### Real-time Tracking
1. Driver starts ride → begins GPS updates
2. Customer opens app → sees live driver location
3. Driver moves → location updates automatically
4. Customer sees movement toward pickup point

### Route Analytics
1. Ride completes → full route preserved
2. Admin can analyze driver efficiency
3. Customer support can review ride path
4. Business intelligence on popular routes

### Emergency Support
1. Customer reports issue → support sees exact location
2. Driver location history available for investigations
3. Audit trail for insurance claims

## Testing

Run the comprehensive GPS tracking test:
```bash
python3 test_gps_tracking.py
```

This test validates:
- Location update functionality
- Customer location retrieval
- Coordinate validation
- Error handling
- Edge case scenarios

## Integration Notes

### Mobile App Integration
- Implement periodic GPS updates (every 15-30 seconds)
- Handle offline scenarios gracefully
- Batch updates when connectivity restored
- Show loading states during location requests

### Customer App Features
- Live map with driver location
- Estimated time to pickup
- Route visualization
- Real-time status updates

### Admin Dashboard
- View all active rides with locations
- Monitor driver movements
- Analyze route efficiency
- Generate location-based reports