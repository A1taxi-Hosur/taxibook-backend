#!/usr/bin/env python3
"""
Simple test for the enhanced API features
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_admin_login_and_config():
    """Test admin login and special fare configuration"""
    print("Testing admin login and special fare config...")
    
    # Test admin login
    response = requests.post(f'{BASE_URL}/admin/api/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    
    print(f"Admin login status: {response.status_code}")
    
    if response.status_code == 200:
        admin_data = response.json()
        print(f"Admin login successful: {admin_data}")
        cookies = response.cookies
        
        # Test special fare config
        print("\nTesting special fare config...")
        response = requests.get(f'{BASE_URL}/admin/api/special_fare_config', cookies=cookies)
        print(f"Special fare config status: {response.status_code}")
        
        if response.status_code == 200:
            config_data = response.json()
            print(f"Special fare configs: {config_data}")
        else:
            print(f"Special fare config failed: {response.text}")
    else:
        print(f"Admin login failed: {response.text}")

def test_customer_booking():
    """Test customer booking with new features"""
    print("\nTesting customer booking...")
    
    # Register customer
    customer_data = {
        'phone': '9876543210',
        'name': 'Test Customer Enhanced'
    }
    
    response = requests.post(f'{BASE_URL}/customer/login_or_register', json=customer_data)
    print(f"Customer registration status: {response.status_code}")
    
    if response.status_code == 200:
        customer_info = response.json()
        print(f"Customer registered: {customer_info}")
        cookies = response.cookies
        
        # Test airport ride booking
        airport_ride = {
            'customer_phone': '9876543210',
            'pickup_address': 'T.Nagar',
            'drop_address': 'Chennai Airport',
            'pickup_lat': 13.0435,
            'pickup_lng': 80.2339,
            'drop_lat': 12.9941,
            'drop_lng': 80.1709,
            'ride_type': 'sedan',
            'ride_category': 'airport'
        }
        
        response = requests.post(f'{BASE_URL}/customer/book_ride', json=airport_ride, cookies=cookies)
        print(f"Airport ride booking status: {response.status_code}")
        
        if response.status_code == 200:
            ride_info = response.json()
            print(f"Airport ride booked: {ride_info}")
        else:
            print(f"Airport ride booking failed: {response.text}")
    else:
        print(f"Customer registration failed: {response.text}")

def test_driver_zone_status():
    """Test driver zone status"""
    print("\nTesting driver zone status...")
    
    # Create driver first via admin
    admin_response = requests.post(f'{BASE_URL}/admin/api/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    
    if admin_response.status_code == 200:
        admin_cookies = admin_response.cookies
        
        # Create driver
        driver_data = {
            'name': 'Test Driver Zone',
            'phone': '8765432109',
            'car_make': 'Toyota',
            'car_model': 'Innova',
            'car_type': 'sedan',
            'car_number': 'TN01AB1234'
        }
        
        response = requests.post(f'{BASE_URL}/admin/create_driver', json=driver_data, cookies=admin_cookies)
        print(f"Driver creation status: {response.status_code}")
        
        if response.status_code == 200:
            driver_info = response.json()
            print(f"Driver created: {driver_info}")
            
            # Driver login
            driver_login_response = requests.post(f'{BASE_URL}/driver/login', json={
                'username': driver_info['data']['username'],
                'password': driver_info['data']['password']
            })
            
            if driver_login_response.status_code == 200:
                driver_cookies = driver_login_response.cookies
                print("Driver login successful")
                
                # Get zone status
                response = requests.get(f'{BASE_URL}/driver/get_zone_status', 
                                      params={'phone': '8765432109'}, 
                                      cookies=driver_cookies)
                print(f"Zone status: {response.status_code}")
                
                if response.status_code == 200:
                    zone_info = response.json()
                    print(f"Zone status: {zone_info}")
                else:
                    print(f"Zone status failed: {response.text}")
            else:
                print(f"Driver login failed: {driver_login_response.text}")
        else:
            print(f"Driver creation failed: {response.text}")
    else:
        print(f"Admin login failed: {admin_response.text}")

if __name__ == "__main__":
    test_admin_login_and_config()
    test_customer_booking()
    test_driver_zone_status()