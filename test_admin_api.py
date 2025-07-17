#!/usr/bin/env python3
"""
Test script to verify admin API functionality
"""
import requests
import json

def test_admin_api():
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
    print(f"Login response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Admin login successful")
    else:
        print("❌ Admin login failed")
        print(f"Response: {response.text[:200]}")
        return False
    
    # Step 2: Test dashboard access
    print("\nStep 2: Test dashboard access")
    response = session.get(f"{base_url}/admin/dashboard")
    print(f"Dashboard response status: {response.status_code}")
    
    if response.status_code == 200 and "TaxiBook Admin" in response.text:
        print("✅ Dashboard access successful")
    else:
        print("❌ Dashboard access failed")
        print(f"Response: {response.text[:200]}")
        return False
    
    # Step 3: Test drivers API
    print("\nStep 3: Test drivers API")
    response = session.get(f"{base_url}/admin/api/drivers")
    print(f"API response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"API Response: {json.dumps(data, indent=2)}")
            if data.get('status') == 'success':
                drivers = data.get('data', {}).get('drivers', [])
                print(f"✅ API successful - Found {len(drivers)} drivers")
                
                # Print first driver details
                if drivers:
                    driver = drivers[0]
                    print(f"   Sample driver: {driver['name']} - {driver['availability_status']}")
                    print(f"   Car: {driver['car_type']} - {driver['car_number']}")
                    print(f"   Active rides: {driver['active_rides']}")
                    
                return True
            else:
                print(f"❌ API returned error: {data.get('message')}")
                return False
        except json.JSONDecodeError:
            print("❌ API returned invalid JSON")
            print(f"Response: {response.text[:200]}")
            return False
    else:
        print(f"❌ API request failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return False

if __name__ == "__main__":
    test_admin_api()