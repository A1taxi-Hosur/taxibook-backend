# Enhanced Dispatch System Documentation

## Overview

The TaxiBook backend now features an advanced polygon-based zone management system with concentric ring dispatch logic and dynamic fare expansion. This system provides intelligent driver allocation with automatic zone expansion and customer approval workflows.

## Key Features

### 1. Polygon-Based Zone Management
- **Geometric Zones**: Supports both polygon coordinates and circular zones
- **Ray Casting Algorithm**: Accurate point-in-polygon detection for complex zone shapes
- **Priority-Based Matching**: Zones have priority order for overlapping areas
- **Backward Compatibility**: Maintains support for legacy circular zones

### 2. Concentric Ring Dispatch
- **Multi-Ring System**: 1-5 configurable rings per zone
- **Progressive Expansion**: Searches drivers in expanding rings with delays
- **Distance-Based Sorting**: Closest drivers prioritized within each ring
- **Vehicle Type Filtering**: Matches requested vehicle type (sedan, SUV, hatchback)

### 3. Dynamic Fare Expansion
- **Zone Expansion Logic**: Automatically expands to nearby zones when no drivers found
- **Customer Approval Required**: Zone expansion requires customer consent with extra fare
- **Fare Calculation**: Dynamic extra fare based on distance to expansion zone
- **Fallback Options**: Manual assignment for complex scenarios

### 4. Enhanced Driver Tracking
- **Real-time Zone Assignment**: Automatic zone assignment based on GPS location
- **Out-of-Zone Detection**: Tracks drivers outside service zones
- **Location-Based Filtering**: Efficient driver matching within zones

## Technical Implementation

### Database Schema Enhancements

```sql
-- Enhanced Zone table
ALTER TABLE zone ADD COLUMN polygon_coordinates JSON;
ALTER TABLE zone ADD COLUMN number_of_rings INTEGER DEFAULT 3;
ALTER TABLE zone ADD COLUMN ring_radius_km REAL DEFAULT 2.0;
ALTER TABLE zone ADD COLUMN expansion_delay_sec INTEGER DEFAULT 15;
ALTER TABLE zone ADD COLUMN priority_order INTEGER DEFAULT 1;

-- Enhanced Ride table
ALTER TABLE ride ADD COLUMN dispatch_zone_id INTEGER;
ALTER TABLE ride ADD COLUMN dispatched_ring INTEGER;
ALTER TABLE ride ADD COLUMN zone_expansion_approved BOOLEAN DEFAULT FALSE;
ALTER TABLE ride ADD COLUMN extra_fare REAL;

-- Enhanced Driver table
ALTER TABLE driver ADD COLUMN zone_id INTEGER;
ALTER TABLE driver ADD COLUMN out_of_zone BOOLEAN DEFAULT FALSE;
```

### Zone Model Enhancements

```python
class Zone(db.Model):
    # Polygon support
    polygon_coordinates = db.Column(db.JSON, nullable=True)
    
    # Concentric ring settings
    number_of_rings = db.Column(db.Integer, nullable=False, default=3)
    ring_radius_km = db.Column(db.Float, nullable=False, default=2.0)
    expansion_delay_sec = db.Column(db.Integer, nullable=False, default=15)
    priority_order = db.Column(db.Integer, nullable=False, default=1)
    
    def is_point_in_zone(self, lat, lng):
        """Check if point is inside zone (polygon or circle)"""
        
    def get_drivers_in_ring(self, ring_number, pickup_lat, pickup_lng):
        """Get available drivers within specific ring"""
        
    def get_ring_radius(self, ring_number):
        """Calculate radius for ring number"""
```

### Dispatch Engine Architecture

```python
class RideDispatchEngine:
    def __init__(self, ride_id):
        self.ride_id = ride_id
        self.dispatch_zone = None
        self.current_ring = 1
        self.rejected_drivers = set()
        
    def start_dispatch(self):
        """Main dispatch logic with zone detection"""
        
    def _dispatch_in_rings(self):
        """Search drivers in concentric rings"""
        
    def _expand_to_other_zones(self):
        """Expand search to nearby zones"""
        
    def continue_with_expansion(self, approved_extra_fare):
        """Continue after customer approval"""
```

## API Endpoints

### 1. Enhanced Zone Management

#### Create Zone with Polygon Support
```http
POST /admin/api/zones
Content-Type: application/json

{
    "zone_name": "Downtown Area",
    "center_lat": 13.0827,
    "center_lng": 80.2707,
    "polygon_coordinates": [
        [13.0800, 80.2700],
        [13.0850, 80.2700],
        [13.0850, 80.2750],
        [13.0800, 80.2750]
    ],
    "number_of_rings": 3,
    "ring_radius_km": 2.0,
    "expansion_delay_sec": 15,
    "priority_order": 1,
    "radius_km": 5.0,
    "is_active": true
}
```

### 2. Enhanced Ride Booking

#### Book Ride with Advanced Dispatch
```http
POST /customer/book_ride
Content-Type: application/json

{
    "customer_phone": "9876543210",
    "pickup_address": "T.Nagar",
    "drop_address": "Anna Nagar",
    "pickup_lat": 13.0435,
    "pickup_lng": 80.2339,
    "drop_lat": 13.0850,
    "drop_lng": 80.2101,
    "ride_type": "sedan",
    "ride_category": "regular"
}
```

**Possible Responses:**

1. **Driver Assigned Successfully**
```json
{
    "status": "success",
    "message": "Ride booked and driver assigned successfully",
    "data": {
        "ride_id": 123,
        "status": "assigned",
        "driver_assigned": true,
        "dispatch_info": {
            "ring": 2,
            "distance_to_driver": 1.5
        }
    }
}
```

2. **Zone Expansion Required**
```json
{
    "status": "success",
    "message": "Ride booked. Zone expansion required for driver assignment.",
    "data": {
        "ride_id": 123,
        "status": "new",
        "requires_zone_expansion": true,
        "expansion_info": {
            "extra_fare": 25.0,
            "expansion_zone": "Nearby Zone",
            "expansion_distance": 3.2
        }
    }
}
```

### 3. Zone Expansion Approval

#### Customer Approval for Zone Expansion
```http
POST /customer/approve_zone_expansion
Content-Type: application/json

{
    "ride_id": 123,
    "approved": true,
    "extra_fare": 25.0
}
```

### 4. Driver Location Updates

#### Enhanced Location Update with Zone Assignment
```http
POST /driver/update_current_location
Content-Type: application/json

{
    "phone": "9876543210",
    "latitude": 13.0435,
    "longitude": 80.2339
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Current location updated successfully",
    "data": {
        "driver_id": 456,
        "latitude": 13.0435,
        "longitude": 80.2339,
        "zone": "T.Nagar Zone",
        "out_of_zone": false
    }
}
```

## Configuration Options

### Zone Configuration
- **Number of Rings**: 1-5 rings per zone
- **Ring Radius**: 0.1-10 km per ring
- **Expansion Delay**: 5-60 seconds between rings
- **Priority Order**: 1-100 (lower = higher priority)

### Dispatch Configuration
- **Vehicle Type Matching**: Exact match required
- **Distance Sorting**: Closest drivers first
- **Rejection Tracking**: Prevents reassignment to rejected drivers
- **Fallback Options**: Manual assignment for edge cases

## Integration Examples

### Frontend Implementation

```javascript
// Book ride with dispatch handling
const bookRide = async (rideData) => {
    const response = await fetch('/customer/book_ride', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rideData)
    });
    
    const result = await response.json();
    
    if (result.data.requires_zone_expansion) {
        // Show zone expansion dialog
        const approved = await showZoneExpansionDialog(result.data.expansion_info);
        
        if (approved) {
            // Customer approved - continue with expansion
            const expansionResponse = await fetch('/customer/approve_zone_expansion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ride_id: result.data.ride_id,
                    approved: true,
                    extra_fare: result.data.expansion_info.extra_fare
                })
            });
            
            return await expansionResponse.json();
        }
    }
    
    return result;
};
```

### Mobile App Integration

```dart
// Flutter/Dart example
class DispatchService {
    Future<BookingResult> bookRide(RideRequest request) async {
        final response = await http.post(
            Uri.parse('$baseUrl/customer/book_ride'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(request.toJson())
        );
        
        final result = BookingResult.fromJson(jsonDecode(response.body));
        
        if (result.requiresZoneExpansion) {
            // Show expansion dialog with extra fare
            final approved = await _showExpansionDialog(result.expansionInfo);
            
            if (approved) {
                return await _approveZoneExpansion(
                    result.rideId, 
                    result.expansionInfo.extraFare
                );
            } else {
                return BookingResult.cancelled();
            }
        }
        
        return result;
    }
}
```

## Testing and Validation

### Unit Tests
- Zone polygon detection accuracy
- Ring radius calculations
- Driver filtering logic
- Fare calculation validation

### Integration Tests
- Complete dispatch flow testing
- Zone expansion scenarios
- Customer approval workflows
- Driver assignment validation

### Performance Tests
- Polygon point-in-zone performance
- Database query optimization
- Concurrent dispatch handling
- Memory usage monitoring

## Deployment Considerations

### Database Migration
1. Run schema updates for enhanced fields
2. Initialize default zones with polygon support
3. Update existing circular zones to new format
4. Verify data integrity after migration

### Configuration Updates
1. Set appropriate ring configurations for zones
2. Configure expansion delays based on traffic patterns
3. Set zone priorities for overlapping areas
4. Test dispatch performance with real data

### Monitoring and Logging
- Track dispatch success rates
- Monitor zone expansion frequency
- Log driver assignment patterns
- Alert on dispatch failures

## Future Enhancements

### Advanced Features
- **Time-based Zone Activation**: Dynamic zone boundaries by time
- **Traffic-aware Dispatch**: Integration with traffic data
- **Predictive Driver Allocation**: ML-based driver positioning
- **Multi-modal Transport**: Integration with other transport modes

### Performance Optimizations
- **Spatial Indexing**: Geographic database indexing
- **Caching Layer**: Redis for zone and driver caching
- **Async Processing**: Background dispatch processing
- **Load Balancing**: Distributed dispatch handling

## Version History

- **v2.4 (2025-07-13)**: Enhanced polygon-based zone management system
- **v2.3 (2025-07-13)**: Concentric ring dispatch implementation
- **v2.2 (2025-07-13)**: Dynamic fare expansion with customer approval
- **v2.1 (2025-07-13)**: Zone-based driver tracking and assignment
- **v2.0 (2025-07-13)**: Basic proximity-based dispatch system

## Support and Maintenance

### Common Issues
1. **Polygon Detection Errors**: Verify coordinate format and order
2. **Zone Expansion Failures**: Check zone priority and distance calculations
3. **Driver Assignment Delays**: Review ring configuration and expansion timing
4. **Fare Calculation Discrepancies**: Validate fare config and expansion logic

### Troubleshooting
- Enable debug logging for dispatch events
- Monitor database performance during peak hours
- Verify GPS coordinate accuracy from drivers
- Test zone boundaries with actual location data

This enhanced dispatch system provides a robust foundation for efficient ride allocation with intelligent zone management and customer-friendly expansion options.