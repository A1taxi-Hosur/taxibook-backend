# Zone API Documentation

## Base URL: `http://localhost:5000/admin/api`

## Authentication Required
All Zone API endpoints require admin authentication. Use the admin login endpoint first.

### Admin Login
```
POST /admin/api/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

## Zone Management APIs

### 1. Get All Zones
**Endpoint**: `GET /admin/api/zones`

**Response**:
```json
{
  "status": "success",
  "data": {
    "zones": [
      {
        "id": 1,
        "zone_name": "City Center",
        "center_lat": 12.9716,
        "center_lng": 77.5946,
        "polygon_coordinates": [[12.97, 77.59], [12.98, 77.60], [12.96, 77.61]],
        "number_of_rings": 3,
        "ring_radius_km": 2.0,
        "ring_radius_meters": 1000,
        "ring_wait_time_seconds": 15,
        "expansion_delay_sec": 15,
        "priority_order": 1,
        "radius_km": 5.0,
        "is_active": true,
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
      }
    ]
  }
}
```

### 2. Get Specific Zone
**Endpoint**: `GET /admin/api/zones/<zone_id>`

**Response**:
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "zone_name": "City Center",
    "center_lat": 12.9716,
    "center_lng": 77.5946,
    "polygon_coordinates": [[12.97, 77.59], [12.98, 77.60], [12.96, 77.61]],
    "number_of_rings": 3,
    "ring_radius_km": 2.0,
    "ring_radius_meters": 1000,
    "ring_wait_time_seconds": 15,
    "expansion_delay_sec": 15,
    "priority_order": 1,
    "radius_km": 5.0,
    "is_active": true
  }
}
```

### 3. Create New Zone
**Endpoint**: `POST /admin/api/zones`

**Request Body**:
```json
{
  "zone_name": "Airport Zone",
  "center_lat": 12.9716,
  "center_lng": 77.5946,
  "polygon_coordinates": [
    [12.97, 77.59],
    [12.98, 77.60],
    [12.96, 77.61],
    [12.97, 77.59]
  ],
  "number_of_rings": 3,
  "ring_radius_km": 2.0,
  "ring_radius_meters": 1000,
  "ring_wait_time_seconds": 15,
  "expansion_delay_sec": 15,
  "priority_order": 1,
  "radius_km": 5.0,
  "is_active": true
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Zone created successfully",
  "data": {
    "id": 2,
    "zone_name": "Airport Zone",
    "center_lat": 12.9716,
    "center_lng": 77.5946,
    "polygon_coordinates": [[12.97, 77.59], [12.98, 77.60], [12.96, 77.61]],
    "number_of_rings": 3,
    "ring_radius_km": 2.0,
    "ring_radius_meters": 1000,
    "ring_wait_time_seconds": 15,
    "expansion_delay_sec": 15,
    "priority_order": 1,
    "radius_km": 5.0,
    "is_active": true
  }
}
```

### 4. Update Zone
**Endpoint**: `PUT /admin/api/zones/<zone_id>`

**Request Body** (partial updates allowed):
```json
{
  "zone_name": "Updated Zone Name",
  "center_lat": 12.9716,
  "center_lng": 77.5946,
  "polygon_coordinates": [
    [12.97, 77.59],
    [12.98, 77.60],
    [12.96, 77.61]
  ],
  "number_of_rings": 4,
  "ring_radius_meters": 1500,
  "ring_wait_time_seconds": 20,
  "is_active": false
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Zone updated successfully",
  "data": {
    "id": 1,
    "zone_name": "Updated Zone Name",
    "center_lat": 12.9716,
    "center_lng": 77.5946,
    "polygon_coordinates": [[12.97, 77.59], [12.98, 77.60], [12.96, 77.61]],
    "number_of_rings": 4,
    "ring_radius_meters": 1500,
    "ring_wait_time_seconds": 20,
    "is_active": false
  }
}
```

### 5. Delete Zone
**Endpoint**: `DELETE /admin/api/zones/<zone_id>`

**Response**:
```json
{
  "status": "success",
  "message": "Zone deleted successfully"
}
```

## Zone Configuration Parameters

### Required Fields
- **zone_name**: Unique zone name (string, max 100 chars)
- **center_lat**: Zone center latitude (float)
- **center_lng**: Zone center longitude (float)

### Optional Fields
- **polygon_coordinates**: Array of [lat, lng] coordinate pairs for polygon zones
- **number_of_rings**: Number of concentric rings (1-5, default: 3)
- **ring_radius_km**: Radius per ring in kilometers (default: 2.0)
- **ring_radius_meters**: Ring radius in meters (100-5000, default: 1000)
- **ring_wait_time_seconds**: Wait time per ring (5-60, default: 15)
- **expansion_delay_sec**: Delay between expansions (5-60, default: 15)
- **priority_order**: Zone priority for expansion (lower = higher priority, default: 1)
- **radius_km**: Legacy radius support (default: 5.0)
- **is_active**: Zone active status (boolean, default: true)

## Zone Expansion APIs

### 1. Approve Zone Expansion
**Endpoint**: `POST /customer/approve_zone_expansion`

**Request Body**:
```json
{
  "ride_id": 123,
  "customer_phone": "9876543210",
  "approved": true
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Zone expansion approved. Searching for drivers in nearby zones.",
  "data": {
    "ride_id": 123,
    "expansion_approved": true,
    "extra_fare": 45.0,
    "final_fare": 387.99
  }
}
```

## Driver Zone Status APIs

### 1. Get Driver Zone Status
**Endpoint**: `GET /driver/get_zone_status?phone=9876543210`

**Response**:
```json
{
  "status": "success",
  "data": {
    "driver_phone": "9876543210",
    "zone_id": 1,
    "zone_name": "City Center",
    "in_zone": true,
    "out_of_zone": false,
    "current_lat": 12.9716,
    "current_lng": 77.5946,
    "distance_from_zone_center": 0.5
  }
}
```

## Zone Features

### 1. Polygon Support
- **Polygon Zones**: Define zones using coordinate arrays
- **Point-in-Polygon**: Ray casting algorithm for location detection
- **Flexible Boundaries**: Support for complex zone shapes

### 2. Concentric Ring Dispatch
- **Progressive Search**: Search through expanding rings
- **Configurable Rings**: 1-5 rings with custom radius
- **Wait Times**: Configurable wait time per ring
- **Automatic Expansion**: Expand to nearby zones when needed

### 3. Zone Expansion Logic
- **Priority-Based**: Zones sorted by priority and distance
- **Extra Fare Calculation**: ₹10 per km + ₹25 minimum
- **Customer Approval**: Required for zone expansion
- **Dynamic Pricing**: Real-time fare adjustments

### 4. Driver Zone Assignment
- **Automatic Assignment**: Based on GPS location
- **Zone Detection**: Polygon or circular matching
- **Out-of-Zone Tracking**: Monitor drivers outside zones
- **Real-time Updates**: Location-based zone updates

## Integration Examples

### JavaScript Frontend
```javascript
// Get all zones
const getZones = async () => {
  const response = await fetch('/admin/api/zones', {
    method: 'GET',
    credentials: 'include'
  });
  return response.json();
};

// Create new zone
const createZone = async (zoneData) => {
  const response = await fetch('/admin/api/zones', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(zoneData),
    credentials: 'include'
  });
  return response.json();
};

// Update zone
const updateZone = async (zoneId, updateData) => {
  const response = await fetch(`/admin/api/zones/${zoneId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updateData),
    credentials: 'include'
  });
  return response.json();
};
```

### curl Examples
```bash
# Get all zones
curl -X GET "http://localhost:5000/admin/api/zones" \
  -H "Content-Type: application/json" \
  --cookie-jar cookies.txt

# Create zone
curl -X POST "http://localhost:5000/admin/api/zones" \
  -H "Content-Type: application/json" \
  -d '{"zone_name":"Test Zone","center_lat":12.9716,"center_lng":77.5946,"radius_km":5.0}' \
  --cookie cookies.txt

# Update zone
curl -X PUT "http://localhost:5000/admin/api/zones/1" \
  -H "Content-Type: application/json" \
  -d '{"zone_name":"Updated Zone","is_active":false}' \
  --cookie cookies.txt
```

## Error Responses

### Common Error Codes
- **401 Unauthorized**: Admin authentication required
- **404 Not Found**: Zone not found
- **400 Bad Request**: Invalid request data
- **500 Internal Server Error**: Server error

### Error Response Format
```json
{
  "status": "error",
  "message": "Zone not found"
}
```

## Current Active Zones

Based on the logs, I can see zones are being actively used for ride calculations. The system supports:
- Polygon-based zone detection
- Concentric ring dispatch
- Zone expansion with extra fare
- Priority-based zone matching
- Real-time driver assignment

All Zone APIs are fully functional and ready for integration with your customer frontend app.