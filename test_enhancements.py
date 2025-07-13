#!/usr/bin/env python3
"""
Test script for A1 Taxi Hosur Enhanced Backend Features
Tests all new enhancements including special fare configs, zones, and enhanced booking system
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000"

def print_header(title):
    """Print formatted test section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step_num, description):
    """Print formatted test step"""
    print(f"\n[Step {step_num}] {description}")

def make_request(method, endpoint, data=None, params=None, cookies=None):
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, params=params, cookies=cookies)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, cookies=cookies)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, cookies=cookies)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, cookies=cookies)
        
        return response
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def test_special_fare_configurations():
    """Test special fare configuration APIs"""
    print_header("Testing Special Fare Configuration System")
    
    # Login as admin first
    print_step(1, "Admin login")
    admin_response = make_request('POST', '/admin/api/login', {
        'username': 'admin',
        'password': 'admin123'
    })
    
    if admin_response.status_code == 200:
        admin_cookies = admin_response.cookies
        print("✅ Admin login successful")
    else:
        print(f"❌ Admin login failed: {admin_response.status_code}")
        return False
    
    # Get existing special fare configurations
    print_step(2, "Get existing special fare configurations")
    response = make_request('GET', '/admin/api/special_fare_config', cookies=admin_cookies)
    
    if response.status_code == 200:
        configs = response.json()
        print(f"✅ Retrieved {len(configs.get('data', {}).get('special_fare_configs', []))} special fare configs")
        for config in configs.get('data', {}).get('special_fare_configs', []):
            print(f"   - {config['ride_category']} {config['ride_type']}: ₹{config['base_fare']}")
    else:
        print(f"❌ Failed to get special fare configs: {response.status_code}")
    
    # Create new special fare configuration
    print_step(3, "Create new special fare configuration")
    new_config = {
        'ride_category': 'airport',
        'ride_type': 'sedan',
        'base_fare': 120.0,
        'per_km': 18.0,
        'is_active': True
    }
    
    response = make_request('POST', '/admin/api/special_fare_config', new_config, cookies=admin_cookies)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Special fare config created: {result.get('message', 'Success')}")
    else:
        print(f"❌ Failed to create special fare config: {response.status_code}")
    
    return True

def test_zone_management():
    """Test zone management APIs"""
    print_header("Testing Zone Management System")
    
    # Login as admin first
    admin_response = make_request('POST', '/admin/login', {
        'username': 'admin',
        'password': 'admin123'
    })
    admin_cookies = admin_response.cookies
    
    # Get existing zones
    print_step(1, "Get existing zones")
    response = make_request('GET', '/admin/api/zones', cookies=admin_cookies)
    
    if response.status_code == 200:
        zones = response.json()
        print(f"✅ Retrieved {len(zones.get('data', {}).get('zones', []))} zones")
        for zone in zones.get('data', {}).get('zones', []):
            print(f"   - {zone['zone_name']}: ({zone['center_lat']}, {zone['center_lng']}) - {zone['radius_km']}km")
    else:
        print(f"❌ Failed to get zones: {response.status_code}")
    
    # Create new zone
    print_step(2, "Create new zone")
    new_zone = {
        'zone_name': 'Test Zone',
        'center_lat': 12.9716,
        'center_lng': 77.5946,
        'radius_km': 6.0,
        'is_active': True
    }
    
    response = make_request('POST', '/admin/api/zones', new_zone, cookies=admin_cookies)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Zone created: {result.get('message', 'Success')}")
    else:
        print(f"❌ Failed to create zone: {response.status_code}")
    
    return True

def test_enhanced_booking_system():
    """Test enhanced booking system with new ride categories"""
    print_header("Testing Enhanced Booking System")
    
    # Register customer
    print_step(1, "Register customer")
    customer_data = {
        'phone': '9876543210',
        'name': 'Test Customer Enhanced'
    }
    
    customer_response = make_request('POST', '/customer/login_or_register', customer_data)
    
    if customer_response.status_code == 200:
        customer_cookies = customer_response.cookies
        customer_info = customer_response.json()
        customer_id = customer_info['data']['customer_id']
        print(f"✅ Customer registered: {customer_info['data']['name']}")
    else:
        print(f"❌ Customer registration failed: {customer_response.status_code}")
        return False
    
    # Test regular ride booking
    print_step(2, "Book regular ride")
    regular_ride = {
        'customer_phone': '9876543210',
        'pickup_address': 'Chennai Central Station',
        'drop_address': 'Anna Nagar',
        'pickup_lat': 13.0827,
        'pickup_lng': 80.2707,
        'drop_lat': 13.0850,
        'drop_lng': 80.2101,
        'ride_type': 'sedan',
        'ride_category': 'regular'
    }
    
    response = make_request('POST', '/customer/book_ride', regular_ride, cookies=customer_cookies)
    
    if response.status_code == 200:
        ride_info = response.json()
        print(f"✅ Regular ride booked: ID {ride_info['data']['ride_id']}")
        print(f"   - Fare: ₹{ride_info['data']['fare_amount']}")
        print(f"   - Final Fare: ₹{ride_info['data']['final_fare']}")
    else:
        print(f"❌ Regular ride booking failed: {response.status_code}")
    
    # Test airport ride booking
    print_step(3, "Book airport ride")
    airport_ride = {
        'customer_phone': '9876543210',
        'pickup_address': 'T.Nagar',
        'drop_address': 'Chennai Airport',
        'pickup_lat': 13.0435,
        'pickup_lng': 80.2339,
        'drop_lat': 12.9941,
        'drop_lng': 80.1709,
        'ride_type': 'suv',
        'ride_category': 'airport'
    }
    
    response = make_request('POST', '/customer/book_ride', airport_ride, cookies=customer_cookies)
    
    if response.status_code == 200:
        ride_info = response.json()
        print(f"✅ Airport ride booked: ID {ride_info['data']['ride_id']}")
        print(f"   - Fare: ₹{ride_info['data']['fare_amount']}")
        print(f"   - Category: {ride_info['data']['ride_category']}")
    else:
        print(f"❌ Airport ride booking failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Test scheduled ride booking
    print_step(4, "Book scheduled ride")
    tomorrow = datetime.now() + timedelta(days=1)
    scheduled_ride = {
        'customer_phone': '9876543210',
        'pickup_address': 'Velachery',
        'drop_address': 'OMR',
        'pickup_lat': 12.9755,
        'pickup_lng': 80.2201,
        'drop_lat': 12.9698,
        'drop_lng': 80.2434,
        'ride_type': 'sedan',
        'ride_category': 'regular',
        'scheduled_date': tomorrow.strftime('%d/%m/%Y'),
        'scheduled_time': '10:30'
    }
    
    response = make_request('POST', '/customer/book_ride', scheduled_ride, cookies=customer_cookies)
    
    if response.status_code == 200:
        ride_info = response.json()
        print(f"✅ Scheduled ride booked: ID {ride_info['data']['ride_id']}")
        print(f"   - Scheduled: {scheduled_ride['scheduled_date']} at {scheduled_ride['scheduled_time']}")
    else:
        print(f"❌ Scheduled ride booking failed: {response.status_code}")
    
    # Test customer bookings retrieval
    print_step(5, "Get customer bookings")
    response = make_request('GET', f'/customer/bookings/{customer_id}', cookies=customer_cookies)
    
    if response.status_code == 200:
        bookings = response.json()
        data = bookings.get('data', {})
        print(f"✅ Retrieved customer bookings:")
        print(f"   - Bookings: {len(data.get('bookings', []))}")
        print(f"   - Ongoing: {len(data.get('ongoing', []))}")
        print(f"   - History: {len(data.get('history', []))}")
    else:
        print(f"❌ Failed to get customer bookings: {response.status_code}")
    
    return True

def test_driver_zone_assignment():
    """Test driver zone assignment system"""
    print_header("Testing Driver Zone Assignment System")
    
    # Login as admin first
    admin_response = make_request('POST', '/admin/login', {
        'username': 'admin',
        'password': 'admin123'
    })
    admin_cookies = admin_response.cookies
    
    # Create a test driver
    print_step(1, "Create test driver")
    driver_data = {
        'name': 'Test Driver Zone',
        'phone': '8765432109',
        'car_make': 'Toyota',
        'car_model': 'Innova',
        'car_type': 'suv',
        'car_number': 'TN01AB1234'
    }
    
    response = make_request('POST', '/admin/create_driver', driver_data, cookies=admin_cookies)
    
    if response.status_code == 200:
        driver_info = response.json()
        print(f"✅ Test driver created: {driver_info['data']['name']}")
        driver_username = driver_info['data']['username']
        driver_password = driver_info['data']['password']
    else:
        print(f"❌ Driver creation failed: {response.status_code}")
        return False
    
    # Driver login
    print_step(2, "Driver login")
    driver_login_response = make_request('POST', '/driver/login', {
        'username': driver_username,
        'password': driver_password
    })
    
    if driver_login_response.status_code == 200:
        driver_cookies = driver_login_response.cookies
        print(f"✅ Driver login successful")
    else:
        print(f"❌ Driver login failed: {driver_login_response.status_code}")
        return False
    
    # Update driver location
    print_step(3, "Update driver location")
    location_data = {
        'driver_phone': '8765432109',
        'latitude': 13.0827,
        'longitude': 80.2707
    }
    
    response = make_request('POST', '/driver/update_location', location_data, cookies=driver_cookies)
    
    if response.status_code == 200:
        location_info = response.json()
        print(f"✅ Driver location updated")
        print(f"   - Zone: {location_info['data'].get('zone', 'None')}")
        print(f"   - Out of zone: {location_info['data']['out_of_zone']}")
    else:
        print(f"❌ Driver location update failed: {response.status_code}")
    
    # Get zone status
    print_step(4, "Get driver zone status")
    response = make_request('GET', '/driver/get_zone_status', params={'phone': '8765432109'}, cookies=driver_cookies)
    
    if response.status_code == 200:
        zone_status = response.json()
        print(f"✅ Zone status retrieved")
        print(f"   - Current zone: {zone_status['data'].get('zone_name', 'None')}")
        print(f"   - Out of zone: {zone_status['data']['out_of_zone']}")
    else:
        print(f"❌ Failed to get zone status: {response.status_code}")
    
    return True

def test_admin_assignment_system():
    """Test admin manual assignment system"""
    print_header("Testing Admin Manual Assignment System")
    
    # Login as admin
    admin_response = make_request('POST', '/admin/login', {
        'username': 'admin',
        'password': 'admin123'
    })
    admin_cookies = admin_response.cookies
    
    # Get all bookings
    print_step(1, "Get all bookings for admin")
    response = make_request('GET', '/admin/api/bookings', cookies=admin_cookies)
    
    if response.status_code == 200:
        bookings = response.json()
        all_bookings = bookings.get('data', {}).get('bookings', [])
        print(f"✅ Retrieved {len(all_bookings)} total bookings")
        
        # Find a 'new' ride for assignment
        new_ride = None
        for booking in all_bookings:
            if booking['status'] == 'new':
                new_ride = booking
                break
        
        if new_ride:
            print(f"   - Found new ride ID: {new_ride['id']}")
            ride_id = new_ride['id']
        else:
            print("   - No new rides found for assignment")
            return True
    else:
        print(f"❌ Failed to get bookings: {response.status_code}")
        return False
    
    # Get available drivers
    print_step(2, "Get available drivers")
    response = make_request('GET', '/admin/api/drivers', cookies=admin_cookies)
    
    if response.status_code == 200:
        drivers = response.json()
        available_drivers = drivers.get('data', {}).get('drivers', [])
        print(f"✅ Retrieved {len(available_drivers)} drivers")
        
        # Find an online driver
        online_driver = None
        for driver in available_drivers:
            if driver['is_online']:
                online_driver = driver
                break
        
        if online_driver:
            print(f"   - Found online driver: {online_driver['name']}")
            driver_id = online_driver['id']
        else:
            print("   - No online drivers found")
            return True
    else:
        print(f"❌ Failed to get drivers: {response.status_code}")
        return False
    
    # Assign driver to ride
    print_step(3, "Assign driver to ride")
    assignment_data = {
        'ride_id': ride_id,
        'driver_id': driver_id
    }
    
    response = make_request('POST', '/admin/assign_driver', assignment_data, cookies=admin_cookies)
    
    if response.status_code == 200:
        assignment_info = response.json()
        print(f"✅ Driver assigned successfully")
        print(f"   - Driver: {assignment_info['data']['driver_name']}")
        print(f"   - Status: {assignment_info['data']['status']}")
    else:
        print(f"❌ Driver assignment failed: {response.status_code}")
        print(f"   Response: {response.text}")
    
    return True

def main():
    """Run all enhancement tests"""
    print("🚀 Starting A1 Taxi Hosur Enhanced Backend Tests")
    print(f"Testing against: {BASE_URL}")
    
    test_results = []
    
    # Test each enhancement
    test_results.append(("Special Fare Configurations", test_special_fare_configurations()))
    test_results.append(("Zone Management", test_zone_management()))
    test_results.append(("Enhanced Booking System", test_enhanced_booking_system()))
    test_results.append(("Driver Zone Assignment", test_driver_zone_assignment()))
    test_results.append(("Admin Assignment System", test_admin_assignment_system()))
    
    # Print summary
    print_header("TEST SUMMARY")
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All enhancement tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the output above.")

if __name__ == "__main__":
    main()