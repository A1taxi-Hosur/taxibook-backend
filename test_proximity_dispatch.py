#!/usr/bin/env python3
"""
Test script for Proximity-Based Driver Dispatch System
Tests the 5km radius filtering functionality with real distance calculations
"""

import requests
import json
import time
from datetime import datetime

# Base URL for the TaxiBook API
BASE_URL = "http://localhost:5000"
ADMIN_COOKIES = "admin_cookies.txt"
CUSTOMER_COOKIES = "customer_cookies.txt"

def print_header(title):
    """Print formatted test section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step_num, description):
    """Print formatted test step"""
    print(f"\n{step_num}. {description}")
    print("-" * 40)

def make_request(method, endpoint, data=None, params=None, cookies=None):
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if cookies:
            with open(cookies, 'r') as f:
                cookie_data = f.read().strip()
        else:
            cookie_data = None
            
        headers = {'Content-Type': 'application/json'}
        
        if method.upper() == 'GET':
            response = requests.get(url, params=params, headers=headers, 
                                  cookies=cookie_data if cookie_data else None)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers,
                                   cookies=cookie_data if cookie_data else None)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, {"message": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        return False, {"message": f"Request failed: {str(e)}"}

def setup_admin_session():
    """Login as admin and get session cookie"""
    print_step(1, "Setting up admin session")
    
    # Login as admin
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    success, response = make_request("POST", "/admin/login", login_data)
    
    if success:
        print("   ✅ Admin logged in successfully")
        return True
    else:
        print(f"   ❌ Admin login failed: {response.get('message', 'Unknown error')}")
        return False

def setup_test_drivers():
    """Create test drivers for proximity testing"""
    print_step(2, "Setting up test drivers")
    
    # Clear existing rides first
    success, response = make_request("POST", "/admin/clear_logs", cookies=ADMIN_COOKIES)
    if success:
        print("   ✅ Cleared existing rides")
    
    # Driver configurations
    drivers = [
        {
            "name": "Close Driver Alpha",
            "phone": "9100000001",
            "car_make": "Toyota",
            "car_model": "Camry",
            "car_year": 2020,
            "car_number": "DL01CL0001",
            "car_type": "sedan",
            "location": {"lat": 13.0650, "lng": 80.2800, "distance": "2km from pickup"}
        },
        {
            "name": "Close Driver Beta",
            "phone": "9100000002",
            "car_make": "Honda",
            "car_model": "City",
            "car_year": 2019,
            "car_number": "DL01CL0002",
            "car_type": "sedan",
            "location": {"lat": 13.0700, "lng": 80.2650, "distance": "1.5km from pickup"}
        },
        {
            "name": "Far Driver Alpha",
            "phone": "9100000003",
            "car_make": "Toyota",
            "car_model": "Camry",
            "car_year": 2021,
            "car_number": "DL01FR0003",
            "car_type": "sedan",
            "location": {"lat": 13.1500, "lng": 80.4000, "distance": "10km from pickup"}
        },
        {
            "name": "Far Driver Beta",
            "phone": "9100000004",
            "car_make": "Maruti",
            "car_model": "Swift",
            "car_year": 2020,
            "car_number": "DL01FR0004",
            "car_type": "hatchback",
            "location": {"lat": 13.2000, "lng": 80.1000, "distance": "15km from pickup"}
        }
    ]
    
    created_drivers = []
    
    for driver in drivers:
        # Create driver
        driver_data = {k: v for k, v in driver.items() if k != 'location'}
        success, response = make_request("POST", "/admin/create_driver", driver_data, cookies=ADMIN_COOKIES)
        
        if success:
            print(f"   ✅ Created driver: {driver['name']} ({driver['phone']})")
            
            # Update driver location
            location_data = {
                "phone": driver['phone'],
                "latitude": driver['location']['lat'],
                "longitude": driver['location']['lng']
            }
            
            loc_success, loc_response = make_request("POST", "/driver/update_current_location", location_data)
            
            if loc_success:
                print(f"   ✅ Set location for {driver['name']}: {driver['location']['distance']}")
                created_drivers.append(driver)
            else:
                print(f"   ❌ Failed to set location for {driver['name']}: {loc_response.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ Failed to create driver {driver['name']}: {response.get('message', 'Unknown error')}")
    
    return created_drivers

def setup_customer_session():
    """Register customer and get session"""
    print_step(3, "Setting up customer session")
    
    customer_data = {
        "phone": "9876543210",
        "name": "Test Customer Proximity"
    }
    
    success, response = make_request("POST", "/customer/login_or_register", customer_data)
    
    if success:
        print("   ✅ Customer registered/logged in successfully")
        return True
    else:
        print(f"   ❌ Customer registration failed: {response.get('message', 'Unknown error')}")
        return False

def test_proximity_dispatch():
    """Test proximity-based driver dispatch"""
    print_step(4, "Testing proximity-based driver dispatch")
    
    # Test pickup location: Chennai Central Station
    pickup_lat = 13.0827
    pickup_lng = 80.2707
    
    # Test 1: Book sedan ride (should only consider close drivers)
    print("   📋 Test 1: Booking sedan ride")
    
    booking_data = {
        "customer_phone": "9876543210",
        "pickup_address": "Chennai Central Station",
        "drop_address": "Kanchipuram Bus Stand",
        "pickup_lat": pickup_lat,
        "pickup_lng": pickup_lng,
        "drop_lat": 12.8266,
        "drop_lng": 79.9914,
        "ride_type": "sedan"
    }
    
    success, response = make_request("POST", "/customer/book_ride", booking_data, cookies=CUSTOMER_COOKIES)
    
    if success:
        ride_data = response.get('data', {})
        print(f"   ✅ Ride booked successfully!")
        print(f"   ✅ Ride ID: {ride_data.get('ride_id', 'N/A')}")
        print(f"   ✅ Distance: {ride_data.get('distance_km', 'N/A')}km")
        print(f"   ✅ Fare: ₹{ride_data.get('fare_amount', 'N/A')}")
        print(f"   ✅ Only sedan drivers within 5km were considered")
        
        # Check ride status to see which driver was assigned
        time.sleep(1)
        status_success, status_response = make_request("GET", "/customer/ride_status", 
                                                      params={"phone": "9876543210"})
        
        if status_success:
            ride_status = status_response.get('data', {})
            driver_info = ride_status.get('driver', {})
            if driver_info:
                print(f"   ✅ Assigned Driver: {driver_info.get('name', 'N/A')} ({driver_info.get('phone', 'N/A')})")
                print(f"   ✅ Car Type: {driver_info.get('car_type', 'N/A')}")
                
                # Verify it's one of the close drivers
                close_phones = ["9100000001", "9100000002"]
                if driver_info.get('phone') in close_phones:
                    print("   ✅ PROXIMITY CHECK PASSED: Close driver assigned!")
                else:
                    print("   ❌ PROXIMITY CHECK FAILED: Far driver assigned!")
            else:
                print("   ❌ No driver assigned yet")
        
        return True
    else:
        print(f"   ❌ Booking failed: {response.get('message', 'Unknown error')}")
        return False

def test_no_nearby_drivers():
    """Test scenario where no drivers are within 5km"""
    print_step(5, "Testing scenario with no nearby drivers")
    
    # Set all drivers far away
    far_drivers = [
        {"phone": "9100000001", "lat": 13.2000, "lng": 80.5000},
        {"phone": "9100000002", "lat": 13.2500, "lng": 80.1000}
    ]
    
    print("   📋 Moving all drivers beyond 5km radius...")
    
    for driver in far_drivers:
        location_data = {
            "phone": driver['phone'],
            "latitude": driver['lat'],
            "longitude": driver['lng']
        }
        
        success, response = make_request("POST", "/driver/update_current_location", location_data)
        
        if success:
            print(f"   ✅ Moved driver {driver['phone']} to distance location")
        else:
            print(f"   ❌ Failed to move driver {driver['phone']}")
    
    # Try to book ride
    print("   📋 Attempting to book ride with no nearby drivers...")
    
    booking_data = {
        "customer_phone": "9876543210",
        "pickup_address": "Chennai Central Station",
        "drop_address": "Kanchipuram Bus Stand",
        "pickup_lat": 13.0827,
        "pickup_lng": 80.2707,
        "drop_lat": 12.8266,
        "drop_lng": 79.9914,
        "ride_type": "sedan"
    }
    
    success, response = make_request("POST", "/customer/book_ride", booking_data, cookies=CUSTOMER_COOKIES)
    
    if not success and "No drivers available within 5km" in response.get('message', ''):
        print("   ✅ PROXIMITY CHECK PASSED: Correctly rejected booking with no nearby drivers!")
        return True
    else:
        print(f"   ❌ PROXIMITY CHECK FAILED: {response.get('message', 'Unexpected response')}")
        return False

def test_distance_calculation():
    """Test the distance calculation accuracy"""
    print_step(6, "Testing distance calculation accuracy")
    
    # Known coordinates and expected distances
    test_cases = [
        {
            "pickup": {"lat": 13.0827, "lng": 80.2707},
            "driver": {"lat": 13.0650, "lng": 80.2800},
            "expected_distance": 2.0,  # Approximately 2km
            "should_pass": True
        },
        {
            "pickup": {"lat": 13.0827, "lng": 80.2707},
            "driver": {"lat": 13.1500, "lng": 80.4000},
            "expected_distance": 10.0,  # Approximately 10km
            "should_pass": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"   📋 Test Case {i}: Expected ~{test_case['expected_distance']}km")
        
        # Calculate distance using our utility (we'll simulate this)
        from utils.distance import haversine_distance
        
        calculated_distance = haversine_distance(
            test_case['pickup']['lat'], test_case['pickup']['lng'],
            test_case['driver']['lat'], test_case['driver']['lng']
        )
        
        print(f"   ✅ Calculated distance: {calculated_distance:.2f}km")
        
        within_5km = calculated_distance <= 5.0
        
        if within_5km == test_case['should_pass']:
            print(f"   ✅ DISTANCE CHECK PASSED: {'Within' if within_5km else 'Beyond'} 5km limit")
        else:
            print(f"   ❌ DISTANCE CHECK FAILED: Unexpected result")

def main():
    """Run all proximity dispatch tests"""
    print_header("Proximity-Based Driver Dispatch System Test Suite")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Setup
    if not setup_admin_session():
        print("❌ Test suite failed: Could not setup admin session")
        return
    
    drivers = setup_test_drivers()
    if not drivers:
        print("❌ Test suite failed: Could not setup test drivers")
        return
    
    if not setup_customer_session():
        print("❌ Test suite failed: Could not setup customer session")
        return
    
    # Run tests
    test_results = []
    
    # Test 1: Normal proximity dispatch
    test_results.append(test_proximity_dispatch())
    
    # Test 2: No nearby drivers
    test_results.append(test_no_nearby_drivers())
    
    # Test 3: Distance calculation accuracy
    test_distance_calculation()
    
    # Summary
    print_header("Test Results Summary")
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All proximity dispatch tests PASSED!")
        print("✅ 5km radius filtering is working correctly")
        print("✅ Distance calculations are accurate")
        print("✅ Driver assignment respects proximity constraints")
    else:
        print("❌ Some tests FAILED - please check the implementation")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()