#!/usr/bin/env python3

"""
Test script for promo code functionality
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_promo_validation():
    """Test promo code validation endpoint"""
    print("Testing promo code validation...")
    
    url = f"{BASE_URL}/customer/validate_promo"
    
    # Test with a valid promo code
    test_data = {
        "promo_code": "WELCOME50",
        "fare_amount": 150.0,
        "ride_type": "sedan",
        "ride_category": "regular"
    }
    
    response = requests.post(url, json=test_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    return response.status_code == 200

def test_ride_estimate_with_promo():
    """Test ride estimate with promo code"""
    print("\nTesting ride estimate with promo code...")
    
    url = f"{BASE_URL}/customer/ride_estimate"
    
    test_data = {
        "pickup_lat": 13.0827,
        "pickup_lng": 80.2707,
        "drop_lat": 13.0435,
        "drop_lng": 80.2339,
        "promo_code": "WELCOME50",
        "ride_category": "regular"
    }
    
    response = requests.post(url, json=test_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_promo_codes():
    """Test promo code system"""
    print("=== Testing Promo Code System ===")
    
    # Test validation
    validation_success = test_promo_validation()
    
    # Test ride estimate with promo
    estimate_success = test_ride_estimate_with_promo()
    
    print("\n=== Test Results ===")
    print(f"Promo validation: {'✓' if validation_success else '✗'}")
    print(f"Ride estimate with promo: {'✓' if estimate_success else '✗'}")
    
    if validation_success and estimate_success:
        print("✓ All promo code tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False

if __name__ == "__main__":
    test_promo_codes()