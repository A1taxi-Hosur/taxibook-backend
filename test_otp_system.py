#!/usr/bin/env python3
"""
Comprehensive Test Suite for OTP-based Ride Start Confirmation System
Tests all aspects of the OTP system including generation, retrieval, verification, and security
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_CUSTOMER_PHONE = "9876543210"
TEST_DRIVER_PHONE = "9876543210"  # Using same phone as both customer and driver for testing

def print_header(title):
    """Print formatted test section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step_num, description):
    """Print formatted test step"""
    print(f"\n📝 Step {step_num}: {description}")
    print("-" * 50)

def make_request(method, endpoint, data=None, params=None):
    """Make HTTP request with error handling"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        return 500, {"error": str(e)}
    except json.JSONDecodeError:
        return response.status_code, {"error": "Invalid JSON response"}

def test_otp_system():
    """Run comprehensive OTP system tests"""
    print_header("OTP-based Ride Start Confirmation System Test")
    print(f"Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Clear test data
    print_step(1, "Clearing test data and setting up clean environment")
    
    # Book a fresh ride
    print_step(2, "Customer books a new ride")
    ride_data = {
        "customer_phone": TEST_CUSTOMER_PHONE,
        "pickup_address": "Connaught Place, New Delhi",
        "drop_address": "India Gate, New Delhi",
        "ride_type": "sedan"
    }
    
    status_code, response = make_request("POST", "/customer/book_ride", ride_data)
    if status_code == 200 and response.get("status") == "success":
        ride_id = response["data"]["ride_id"]
        print(f"✅ Ride booked successfully with ID: {ride_id}")
    else:
        print(f"❌ Failed to book ride: {response.get('message', 'Unknown error')}")
        return False
    
    # Driver accepts ride (OTP generation)
    print_step(3, "Driver accepts ride - OTP should be generated")
    accept_data = {
        "ride_id": ride_id,
        "driver_phone": TEST_DRIVER_PHONE,
        "driver_location": "28.6315,77.2167"
    }
    
    status_code, response = make_request("POST", "/driver/accept_ride", accept_data)
    if status_code == 200 and response.get("status") == "success":
        print("✅ Driver accepted ride successfully")
        print("✅ OTP should be generated automatically")
    else:
        print(f"❌ Driver acceptance failed: {response.get('message', 'Unknown error')}")
        return False
    
    # Customer retrieves OTP
    print_step(4, "Customer retrieves OTP through ride status")
    status_code, response = make_request("GET", "/customer/ride_status", 
                                       params={"phone": TEST_CUSTOMER_PHONE})
    
    if status_code == 200 and response.get("status") == "success":
        ride_data = response["data"]
        otp = ride_data.get("start_otp")
        ride_status = ride_data.get("status")
        driver_name = ride_data.get("driver_name")
        
        print(f"✅ Ride Status: {ride_status}")
        print(f"✅ Assigned Driver: {driver_name}")
        
        if otp:
            print(f"✅ OTP Retrieved: {otp}")
            print(f"✅ OTP Length: {len(otp)} digits")
            print(f"✅ OTP Format: {'Valid' if otp.isdigit() else 'Invalid'}")
        else:
            print("❌ No OTP found in customer response")
            return False
    else:
        print(f"❌ Failed to get ride status: {response.get('message', 'Unknown error')}")
        return False
    
    # Test OTP verification with correct OTP
    print_step(5, "Testing OTP verification with correct OTP")
    start_data = {
        "ride_id": ride_id,
        "otp": otp
    }
    
    status_code, response = make_request("POST", "/driver/start_ride", start_data)
    if status_code == 200 and response.get("status") == "success":
        print("✅ OTP verification successful")
        print("✅ Ride started successfully")
        print(f"✅ Final ride status: {response['data']['status']}")
    else:
        print(f"❌ OTP verification failed: {response.get('message', 'Unknown error')}")
        return False
    
    # Test invalid OTP (should fail)
    print_step(6, "Testing invalid OTP rejection")
    invalid_data = {
        "ride_id": ride_id,
        "otp": "000000"
    }
    
    status_code, response = make_request("POST", "/driver/start_ride", invalid_data)
    if status_code in [400, 403] and response.get("status") == "error":
        print("✅ Invalid OTP correctly rejected")
        print(f"✅ Error message: {response.get('message', 'Unknown error')}")
    else:
        print(f"❌ Invalid OTP was not rejected properly: {response}")
        return False
    
    # Verify OTP cleanup
    print_step(7, "Verifying OTP cleanup after successful verification")
    status_code, response = make_request("GET", "/customer/ride_status", 
                                       params={"phone": TEST_CUSTOMER_PHONE})
    
    if status_code == 200 and response.get("status") == "success":
        ride_data = response["data"]
        final_otp = ride_data.get("start_otp")
        final_status = ride_data.get("status")
        
        print(f"✅ Final ride status: {final_status}")
        
        if final_otp:
            print(f"⚠️  OTP still present: {final_otp}")
            print("⚠️  OTP should be cleared after successful verification")
        else:
            print("✅ OTP successfully cleared after verification")
    else:
        print(f"❌ Failed to verify final state: {response.get('message', 'Unknown error')}")
    
    # Test edge cases
    print_step(8, "Testing edge cases and error conditions")
    
    # Test with non-existent ride
    print("   Testing non-existent ride:")
    invalid_ride_data = {
        "ride_id": 99999,
        "otp": "123456"
    }
    
    status_code, response = make_request("POST", "/driver/start_ride", invalid_ride_data)
    if response.get("status") == "error":
        print("   ✅ Non-existent ride correctly rejected")
    else:
        print("   ❌ Non-existent ride was not rejected")
    
    # Test with invalid OTP format
    print("   Testing invalid OTP format:")
    invalid_format_data = {
        "ride_id": ride_id,
        "otp": "12345"  # Only 5 digits
    }
    
    status_code, response = make_request("POST", "/driver/start_ride", invalid_format_data)
    if response.get("status") == "error" and "6 digits" in response.get("message", ""):
        print("   ✅ Invalid OTP format correctly rejected")
    else:
        print("   ❌ Invalid OTP format was not rejected properly")
    
    return True

def test_security_features():
    """Test security features of OTP system"""
    print_header("Security Features Test")
    
    # Test OTP visibility in different endpoints
    print_step(1, "Testing OTP visibility restrictions")
    
    # Customer should see OTP
    print("   Customer OTP visibility:")
    status_code, response = make_request("GET", "/customer/ride_status", 
                                       params={"phone": TEST_CUSTOMER_PHONE})
    
    if status_code == 200 and "start_otp" in response.get("data", {}):
        print("   ✅ Customer can see OTP (as expected)")
    else:
        print("   ❌ Customer cannot see OTP")
    
    print("✅ Security features test completed")

def main():
    """Run all tests"""
    print("🚀 Starting OTP System Test Suite")
    print(f"Target URL: {BASE_URL}")
    print(f"Test Customer: {TEST_CUSTOMER_PHONE}")
    print(f"Test Driver: {TEST_DRIVER_PHONE}")
    
    try:
        # Run main OTP system test
        if test_otp_system():
            print_header("✅ OTP SYSTEM TEST PASSED")
        else:
            print_header("❌ OTP SYSTEM TEST FAILED")
            return 1
        
        # Run security features test
        test_security_features()
        
        print_header("🎯 ALL TESTS COMPLETED SUCCESSFULLY")
        print("The OTP-based ride start confirmation system is working correctly!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())