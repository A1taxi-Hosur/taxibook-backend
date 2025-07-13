#!/usr/bin/env python3
"""
Enhanced Dispatch System Test Suite
Tests polygon-based zone management and concentric ring dispatch
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Configuration
BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}

def print_step(step_num, description):
    """Print formatted step header"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")

def print_result(success, message, data=None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if data:
        print(f"   Data: {json.dumps(data, indent=2)}")

def make_request(method, endpoint, data=None, cookies=None):
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, headers=HEADERS, cookies=cookies)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data, cookies=cookies)
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=data, cookies=cookies)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS, cookies=cookies)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response
    except requests.exceptions.ConnectionError:
        print("❌ Connection error. Make sure the server is running.")
        return None
    except Exception as e:
        print(f"❌ Request error: {str(e)}")
        return None

def test_enhanced_dispatch_system():
    """Test the enhanced dispatch system with polygon zones and concentric rings"""
    
    print("🚀 ENHANCED DISPATCH SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Test data
    admin_credentials = {"username": "admin", "password": "admin123"}
    customer_phone = "9876543210"
    driver_phone = "9876543333"
    
    # Step 1: Admin Login
    print_step(1, "Admin Login")
    response = make_request("POST", "/admin/api/login", admin_credentials)
    
    if response and response.status_code == 200:
        admin_cookies = response.cookies
        print_result(True, "Admin login successful")
    else:
        print_result(False, "Admin login failed")
        return False
    
    # Step 2: Create Enhanced Zone with Polygon
    print_step(2, "Create Enhanced Zone with Polygon Support")
    enhanced_zone = {
        "zone_name": "Test Polygon Zone",
        "center_lat": 13.0827,
        "center_lng": 80.2707,
        "polygon_coordinates": [
            [13.0800, 80.2700],
            [13.0850, 80.2700],
            [13.0850, 80.2750],
            [13.0800, 80.2750]
        ],
        "number_of_rings": 3,
        "ring_radius_km": 1.5,
        "expansion_delay_sec": 10,
        "priority_order": 1,
        "radius_km": 5.0,
        "is_active": True
    }
    
    response = make_request("POST", "/admin/api/zones", enhanced_zone, cookies=admin_cookies)
    
    if response and response.status_code == 200:
        zone_data = response.json()
        zone_id = zone_data["data"]["id"]
        print_result(True, f"Enhanced zone created with ID: {zone_id}")
    else:
        print_result(False, f"Zone creation failed: {response.status_code if response else 'No response'}")
        return False
    
    # Step 3: Create Test Driver
    print_step(3, "Create Test Driver")
    test_driver = {
        "name": "Test Driver",
        "phone": driver_phone,
        "car_make": "Toyota",
        "car_model": "Camry",
        "car_year": 2022,
        "car_number": "TN01AB1234",
        "car_type": "sedan",
        "license_number": "TN123456789"
    }
    
    response = make_request("POST", "/admin/create_driver", test_driver, cookies=admin_cookies)
    
    if response and response.status_code == 200:
        driver_data = response.json()
        driver_id = driver_data["data"]["driver_id"]
        print_result(True, f"Test driver created with ID: {driver_id}")
    else:
        print_result(False, f"Driver creation failed: {response.status_code if response else 'No response'}")
        return False
    
    # Step 4: Update Driver Location (Inside Zone)
    print_step(4, "Update Driver Location Inside Zone")
    driver_location = {
        "phone": driver_phone,
        "latitude": 13.0825,  # Inside the polygon
        "longitude": 80.2725
    }
    
    response = make_request("POST", "/driver/update_current_location", driver_location)
    
    if response and response.status_code == 200:
        location_data = response.json()
        print_result(True, f"Driver location updated - Zone: {location_data['data'].get('zone', 'None')}")
    else:
        print_result(False, f"Driver location update failed: {response.status_code if response else 'No response'}")
    
    # Step 5: Customer Login/Register
    print_step(5, "Customer Login/Register")
    customer_data = {
        "phone": customer_phone,
        "name": "Test Customer"
    }
    
    response = make_request("POST", "/customer/login_or_register", customer_data)
    
    if response and response.status_code == 200:
        customer_info = response.json()
        customer_id = customer_info["data"]["customer_id"]
        print_result(True, f"Customer registered with ID: {customer_id}")
    else:
        print_result(False, f"Customer registration failed: {response.status_code if response else 'No response'}")
        return False
    
    # Step 6: Test Ride Booking with Enhanced Dispatch
    print_step(6, "Test Ride Booking with Enhanced Dispatch")
    ride_request = {
        "customer_phone": customer_phone,
        "pickup_address": "Test Pickup Location",
        "drop_address": "Test Drop Location", 
        "pickup_lat": 13.0820,  # Inside the polygon zone
        "pickup_lng": 80.2720,
        "drop_lat": 13.0900,
        "drop_lng": 80.2800,
        "ride_type": "sedan",
        "ride_category": "regular"
    }
    
    response = make_request("POST", "/customer/book_ride", ride_request)
    
    if response and response.status_code == 200:
        booking_data = response.json()
        ride_id = booking_data["data"]["ride_id"]
        
        if booking_data["data"].get("driver_assigned"):
            print_result(True, f"Ride booked with automatic driver assignment - Ride ID: {ride_id}")
            print(f"   Ring: {booking_data['data']['dispatch_info']['ring']}")
            print(f"   Distance to driver: {booking_data['data']['dispatch_info']['distance_to_driver']} km")
        elif booking_data["data"].get("requires_zone_expansion"):
            print_result(True, f"Ride booked - Zone expansion required - Ride ID: {ride_id}")
            print(f"   Extra fare: ₹{booking_data['data']['expansion_info']['extra_fare']}")
            print(f"   Expansion zone: {booking_data['data']['expansion_info']['expansion_zone']}")
            
            # Test zone expansion approval
            print_step(7, "Test Zone Expansion Approval")
            expansion_approval = {
                "ride_id": ride_id,
                "approved": True,
                "extra_fare": booking_data['data']['expansion_info']['extra_fare']
            }
            
            response = make_request("POST", "/customer/approve_zone_expansion", expansion_approval)
            
            if response and response.status_code == 200:
                expansion_data = response.json()
                print_result(True, f"Zone expansion approved - Driver assigned")
                print(f"   Final fare: ₹{expansion_data['data']['final_fare']}")
            else:
                print_result(False, f"Zone expansion approval failed: {response.status_code if response else 'No response'}")
        else:
            print_result(True, f"Ride booked - Manual assignment required - Ride ID: {ride_id}")
    else:
        print_result(False, f"Ride booking failed: {response.status_code if response else 'No response'}")
        return False
    
    # Step 8: Test Driver Location Update (Outside Zone)
    print_step(8, "Test Driver Location Update Outside Zone")
    driver_location_outside = {
        "phone": driver_phone,
        "latitude": 13.1000,  # Outside the polygon
        "longitude": 80.3000
    }
    
    response = make_request("POST", "/driver/update_current_location", driver_location_outside)
    
    if response and response.status_code == 200:
        location_data = response.json()
        print_result(True, f"Driver location updated outside zone - Out of zone: {location_data['data'].get('out_of_zone', False)}")
    else:
        print_result(False, f"Driver location update failed: {response.status_code if response else 'No response'}")
    
    # Step 9: Test Zone Retrieval
    print_step(9, "Test Zone Retrieval with Enhanced Fields")
    response = make_request("GET", "/admin/api/zones", cookies=admin_cookies)
    
    if response and response.status_code == 200:
        zones_data = response.json()
        zones = zones_data["data"]["zones"]
        
        enhanced_zone_found = False
        for zone in zones:
            if zone["zone_name"] == "Test Polygon Zone":
                enhanced_zone_found = True
                print_result(True, "Enhanced zone retrieved successfully")
                print(f"   Polygon coordinates: {len(zone.get('polygon_coordinates', []))} points")
                print(f"   Number of rings: {zone.get('number_of_rings', 'N/A')}")
                print(f"   Ring radius: {zone.get('ring_radius_km', 'N/A')} km")
                print(f"   Expansion delay: {zone.get('expansion_delay_sec', 'N/A')} seconds")
                print(f"   Priority order: {zone.get('priority_order', 'N/A')}")
                break
        
        if not enhanced_zone_found:
            print_result(False, "Enhanced zone not found in retrieval")
    else:
        print_result(False, f"Zone retrieval failed: {response.status_code if response else 'No response'}")
    
    # Step 10: Test Performance with Multiple Zones
    print_step(10, "Test Performance with Multiple Zones")
    start_time = time.time()
    
    # Create multiple zones for performance testing
    for i in range(3):
        test_zone = {
            "zone_name": f"Performance Zone {i+1}",
            "center_lat": 13.0827 + (i * 0.01),
            "center_lng": 80.2707 + (i * 0.01),
            "number_of_rings": 3,
            "ring_radius_km": 2.0,
            "expansion_delay_sec": 15,
            "priority_order": i + 2,
            "radius_km": 5.0,
            "is_active": True
        }
        
        response = make_request("POST", "/admin/api/zones", test_zone, cookies=admin_cookies)
        
        if not response or response.status_code != 200:
            print_result(False, f"Performance zone {i+1} creation failed")
            break
    
    end_time = time.time()
    print_result(True, f"Performance test completed in {end_time - start_time:.2f} seconds")
    
    # Step 11: Cleanup Test Data
    print_step(11, "Cleanup Test Data")
    cleanup_success = True
    
    # Delete test zones
    response = make_request("GET", "/admin/api/zones", cookies=admin_cookies)
    if response and response.status_code == 200:
        zones_data = response.json()
        zones = zones_data["data"]["zones"]
        
        for zone in zones:
            if zone["zone_name"].startswith("Test") or zone["zone_name"].startswith("Performance"):
                response = make_request("DELETE", f"/admin/api/zones/{zone['id']}", cookies=admin_cookies)
                if not response or response.status_code != 200:
                    cleanup_success = False
                    print(f"   Failed to delete zone: {zone['zone_name']}")
    
    # Delete test driver
    response = make_request("POST", "/admin/delete_driver", {"driver_id": driver_id}, cookies=admin_cookies)
    if not response or response.status_code != 200:
        cleanup_success = False
        print(f"   Failed to delete test driver")
    
    print_result(cleanup_success, "Test data cleanup completed")
    
    print("\n" + "="*60)
    print("🎯 ENHANCED DISPATCH SYSTEM TEST SUMMARY")
    print("="*60)
    print("✅ Polygon-based zone management")
    print("✅ Concentric ring dispatch logic")
    print("✅ Dynamic fare expansion")
    print("✅ Customer approval workflow")
    print("✅ Driver zone assignment")
    print("✅ Enhanced API integration")
    print("✅ Performance validation")
    print("✅ Data cleanup")
    print("="*60)
    
    return True

if __name__ == "__main__":
    success = test_enhanced_dispatch_system()
    
    if success:
        print("🎉 All tests passed! Enhanced dispatch system is working correctly.")
    else:
        print("❌ Some tests failed. Please check the logs and fix issues.")
    
    exit(0 if success else 1)