#!/usr/bin/env python3
"""
Test script for offline driver assignment functionality
"""
import requests
import json

def test_offline_assignment():
    base_url = "http://localhost:5000"
    
    # Create session to maintain cookies
    session = requests.Session()
    
    # Step 1: Login as admin
    print("Step 1: Admin login")
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    response = session.post(f"{base_url}/admin/login", data=login_data)
    if response.status_code != 200:
        print("❌ Admin login failed")
        return False
    print("✅ Admin login successful")
    
    # Step 2: Create a test ride (outstation)
    print("\nStep 2: Create test ride")
    ride_data = {
        'customer_phone': '9876543210',
        'pickup_address': 'Chennai, Tamil Nadu',
        'drop_address': 'Hosur, Tamil Nadu',
        'ride_type': 'sedan',
        'ride_category': 'outstation',
        'pickup_lat': 13.0827,
        'pickup_lng': 80.2707,
        'drop_lat': 12.7409,
        'drop_lng': 77.8252
    }
    
    response = session.post(f"{base_url}/customer/book_ride", json=ride_data)
    if response.status_code != 200:
        print(f"❌ Failed to create test ride: {response.text}")
        return False
    
    ride_response = response.json()
    if ride_response.get('status') != 'success':
        print(f"❌ Failed to create test ride: {ride_response.get('message')}")
        return False
    
    ride_id = ride_response['data']['ride_id']
    print(f"✅ Test ride created with ID: {ride_id}")
    
    # Step 3: Get available drivers
    print("\nStep 3: Get drivers for assignment")
    response = session.get(f"{base_url}/admin/api/drivers")
    if response.status_code != 200:
        print("❌ Failed to get drivers")
        return False
    
    drivers_response = response.json()
    if drivers_response.get('status') != 'success':
        print(f"❌ Failed to get drivers: {drivers_response.get('message')}")
        return False
    
    drivers = drivers_response['data']['drivers']
    print(f"✅ Found {len(drivers)} drivers")
    
    # Find an offline driver
    offline_driver = None
    online_driver = None
    for driver in drivers:
        if driver['availability_status'] == 'Offline':
            offline_driver = driver
        elif driver['availability_status'] == 'Online':
            online_driver = driver
    
    # Test assignment to offline driver
    if offline_driver:
        print(f"\nStep 4: Test assignment to OFFLINE driver: {offline_driver['name']}")
        
        assignment_data = {
            'ride_id': ride_id,
            'driver_id': offline_driver['id']
        }
        
        response = session.post(f"{base_url}/admin/assign_driver", json=assignment_data)
        if response.status_code == 200:
            assignment_response = response.json()
            if assignment_response.get('status') == 'success':
                print(f"✅ Successfully assigned OFFLINE driver {offline_driver['name']} to ride {ride_id}")
                print(f"   Driver: {assignment_response['data']['driver_name']}")
                print(f"   Status: {assignment_response['data']['status']}")
                return True
            else:
                print(f"❌ Assignment failed: {assignment_response.get('message')}")
                return False
        else:
            print(f"❌ Assignment request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    else:
        print("❌ No offline driver found for testing")
        return False

if __name__ == "__main__":
    test_offline_assignment()