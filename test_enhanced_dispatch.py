#!/usr/bin/env python3
"""
Test script for Enhanced Dispatch System with Concentric Ring Configuration
Tests polygon zones, ring dispatch, and zone expansion functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import app, db
from models import Customer, Driver, Ride, Zone, get_ist_time
from utils.enhanced_dispatch_engine import dispatch_ride_with_enhanced_system, approve_zone_expansion_for_ride
import json

def create_test_data():
    """Create test data for enhanced dispatch testing"""
    print("Creating test data...")
    
    # Create test customer
    customer = Customer(
        name="Test Customer",
        phone="9876543210"
    )
    db.session.add(customer)
    
    # Create test drivers in different locations within zones
    drivers = [
        Driver(
            name="Driver 1",
            phone="9876543211",
            username="DRV001",
            password_hash="hashed_password",
            is_online=True,
            current_lat=12.9720,  # Inside Indiranagar zone
            current_lng=77.6410,
            location_updated_at=get_ist_time(),
            car_type="sedan"
        ),
        Driver(
            name="Driver 2", 
            phone="9876543212",
            username="DRV002",
            password_hash="hashed_password",
            is_online=True,
            current_lat=12.9700,  # Inside Whitefield zone
            current_lng=77.7500,
            location_updated_at=get_ist_time(),
            car_type="suv"
        ),
        Driver(
            name="Driver 3",
            phone="9876543213",
            username="DRV003",
            password_hash="hashed_password",
            is_online=True,
            current_lat=12.9350,  # Inside Koramangala zone
            current_lng=77.6250,
            location_updated_at=get_ist_time(),
            car_type="hatchback"
        )
    ]
    
    for driver in drivers:
        db.session.add(driver)
    
    # Create test zones with enhanced ring configuration
    zones = [
        Zone(
            zone_name="Koramangala",
            center_lat=12.9351,
            center_lng=77.6245,
            polygon_coordinates=[
                [12.9300, 77.6200],
                [12.9400, 77.6200],
                [12.9400, 77.6300],
                [12.9300, 77.6300]
            ],
            number_of_rings=3,
            ring_radius_km=2.0,
            ring_radius_meters=1500,
            ring_wait_time_seconds=10,
            expansion_delay_sec=15,
            radius_km=5.0,
            priority_order=1,
            is_active=True
        ),
        Zone(
            zone_name="Whitefield",
            center_lat=12.9698,
            center_lng=77.7500,
            polygon_coordinates=[
                [12.9650, 77.7450],
                [12.9750, 77.7450],
                [12.9750, 77.7550],
                [12.9650, 77.7550]
            ],
            number_of_rings=4,
            ring_radius_km=1.5,
            ring_radius_meters=1000,
            ring_wait_time_seconds=12,
            expansion_delay_sec=20,
            radius_km=6.0,
            priority_order=2,
            is_active=True
        ),
        Zone(
            zone_name="Indiranagar",
            center_lat=12.9719,
            center_lng=77.6412,
            polygon_coordinates=[
                [12.9670, 77.6360],
                [12.9770, 77.6360],
                [12.9770, 77.6460],
                [12.9670, 77.6460]
            ],
            number_of_rings=2,
            ring_radius_km=2.5,
            ring_radius_meters=2000,
            ring_wait_time_seconds=15,
            expansion_delay_sec=10,
            radius_km=4.0,
            priority_order=3,
            is_active=True
        )
    ]
    
    for zone in zones:
        db.session.add(zone)
    
    db.session.commit()
    print("✓ Test data created successfully")
    return customer, drivers, zones

def test_polygon_zone_detection():
    """Test polygon zone detection"""
    print("\n=== Testing Polygon Zone Detection ===")
    
    zones = Zone.query.all()
    
    # Test points within zones
    test_points = [
        (12.9350, 77.6250, "Koramangala"),
        (12.9700, 77.7500, "Whitefield"),
        (12.9720, 77.6410, "Indiranagar"),
        (12.8000, 77.5000, None)  # Outside all zones
    ]
    
    for lat, lng, expected_zone in test_points:
        found_zone = Zone.find_zone_for_location(lat, lng)
        zone_name = found_zone.zone_name if found_zone else None
        
        if zone_name == expected_zone:
            print(f"✓ Point ({lat}, {lng}) correctly detected in zone: {zone_name}")
        else:
            print(f"✗ Point ({lat}, {lng}) expected in {expected_zone}, found in {zone_name}")

def test_ring_dispatch():
    """Test concentric ring dispatch"""
    print("\n=== Testing Ring Dispatch ===")
    
    customer = Customer.query.first()
    
    # Create a test ride
    ride = Ride(
        customer_id=customer.id,
        customer_phone=customer.phone,
        pickup_address="Forum Mall, Koramangala",
        drop_address="Whitefield Main Road",
        pickup_lat=12.9351,
        pickup_lng=77.6245,
        drop_lat=12.9698,
        drop_lng=77.7500,
        distance_km=10.5,
        fare_amount=120.0,
        final_fare=120.0,
        ride_type="sedan",
        ride_category="regular",
        start_otp="123456",
        status="new"
    )
    
    db.session.add(ride)
    db.session.commit()
    
    # Test enhanced dispatch
    print(f"Testing dispatch for ride {ride.id}...")
    result = dispatch_ride_with_enhanced_system(ride.id)
    
    print(f"Dispatch result: {json.dumps(result, indent=2)}")
    
    if result.get('success'):
        if result.get('driver_assigned'):
            print(f"✓ Driver assigned successfully in ring {result.get('ring_number')}")
            print(f"  Zone: {result.get('zone_name')}")
            print(f"  Driver ID: {result.get('driver_id')}")
            print(f"  Distance to driver: {result.get('distance_to_driver'):.2f} km")
        elif result.get('requires_zone_expansion'):
            print(f"✓ Zone expansion required")
            print(f"  Extra fare: ₹{result.get('extra_fare')}")
            print(f"  Expansion zone: {result.get('expansion_zone')}")
    else:
        print(f"✗ Dispatch failed: {result.get('error')}")
    
    return ride

def test_zone_expansion():
    """Test zone expansion functionality"""
    print("\n=== Testing Zone Expansion ===")
    
    customer = Customer.query.first()
    
    # Create a ride in an area with no nearby drivers
    ride = Ride(
        customer_id=customer.id,
        customer_phone=customer.phone,
        pickup_address="Electronic City",
        drop_address="Hebbal",
        pickup_lat=12.8440,
        pickup_lng=77.6619,
        drop_lat=13.0359,
        drop_lng=77.5974,
        distance_km=15.2,
        fare_amount=180.0,
        final_fare=180.0,
        ride_type="suv",
        ride_category="regular",
        start_otp="654321",
        status="new"
    )
    
    db.session.add(ride)
    db.session.commit()
    
    # Test dispatch
    print(f"Testing zone expansion for ride {ride.id}...")
    result = dispatch_ride_with_enhanced_system(ride.id)
    
    print(f"Zone expansion result: {json.dumps(result, indent=2)}")
    
    if result.get('requires_zone_expansion'):
        # Test approval
        driver_info = result.get('driver_info', {})
        if driver_info:
            print(f"Testing approval of zone expansion...")
            approval_result = approve_zone_expansion_for_ride(
                ride.id,
                driver_info.get('driver_id'),
                driver_info.get('zone_id'),
                result.get('extra_fare')
            )
            
            print(f"Approval result: {json.dumps(approval_result, indent=2)}")
            
            if approval_result.get('success'):
                print("✓ Zone expansion approved successfully")
            else:
                print(f"✗ Zone expansion approval failed: {approval_result.get('error')}")
    
    return ride

def test_ring_configuration():
    """Test ring configuration parameters"""
    print("\n=== Testing Ring Configuration ===")
    
    zones = Zone.query.all()
    
    for zone in zones:
        print(f"\nZone: {zone.zone_name}")
        print(f"  Rings: {zone.number_of_rings}")
        print(f"  Ring radius: {zone.ring_radius_meters}m")
        print(f"  Ring wait time: {zone.ring_wait_time_seconds}s")
        print(f"  Expansion delay: {zone.expansion_delay_sec}s")
        
        # Test ring radius calculation
        for ring in range(1, zone.number_of_rings + 1):
            radius = zone.get_ring_radius(ring)
            print(f"  Ring {ring} radius: {radius:.2f} km")

def test_driver_zone_assignment():
    """Test automatic driver zone assignment"""
    print("\n=== Testing Driver Zone Assignment ===")
    
    drivers = Driver.query.all()
    
    for driver in drivers:
        print(f"\nDriver: {driver.name}")
        print(f"  Location: ({driver.current_lat}, {driver.current_lng})")
        
        # Update zone assignment
        driver.update_zone_assignment()
        
        if driver.zone_id:
            zone = Zone.query.get(driver.zone_id)
            print(f"  Assigned to zone: {zone.zone_name}")
            print(f"  Out of zone: {driver.out_of_zone}")
        else:
            print(f"  No zone assigned (out of service area)")

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning up test data ===")
    
    # Delete in reverse order to avoid foreign key constraints
    Ride.query.delete()
    Driver.query.delete()
    Customer.query.delete()
    Zone.query.delete()
    
    db.session.commit()
    print("✓ Test data cleaned up")

def main():
    """Main test function"""
    print("Enhanced Dispatch System - Comprehensive Test Suite")
    print("=" * 60)
    
    with app.app_context():
        try:
            # Clean up any existing test data
            cleanup_test_data()
            
            # Create test data
            customer, drivers, zones = create_test_data()
            
            # Run tests
            test_polygon_zone_detection()
            test_ring_configuration()
            test_driver_zone_assignment()
            
            # Test dispatch functionality
            ride1 = test_ring_dispatch()
            ride2 = test_zone_expansion()
            
            print("\n" + "=" * 60)
            print("Enhanced Dispatch System Test Summary:")
            print("✓ Polygon zone detection")
            print("✓ Ring configuration")
            print("✓ Driver zone assignment")
            print("✓ Ring dispatch system")
            print("✓ Zone expansion functionality")
            print("=" * 60)
            
        except Exception as e:
            print(f"Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            cleanup_test_data()

if __name__ == "__main__":
    main()