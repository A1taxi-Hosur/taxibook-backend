#!/usr/bin/env python3
"""
Test script to check driver login functionality
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import app, db
from models import Driver
import requests
import json

def test_driver_login():
    """Test driver login functionality"""
    print("Testing Driver Login Functionality")
    print("=" * 50)
    
    with app.app_context():
        # Get all drivers
        drivers = Driver.query.all()
        
        if not drivers:
            print("❌ No drivers found in database")
            return
        
        print(f"Found {len(drivers)} drivers in database:")
        print()
        
        for driver in drivers:
            print(f"Driver: {driver.name}")
            print(f"  Username: {driver.username}")
            print(f"  Phone: {driver.phone}")
            print(f"  Has Password: {'Yes' if driver.password_hash else 'No'}")
            print(f"  Is Online: {driver.is_online}")
            
            if driver.phone:
                expected_password = f"{driver.phone[-4:]}@Taxi"
                print(f"  Expected Password: {expected_password}")
                
                # Test login
                login_data = {
                    "username": driver.username,
                    "password": expected_password
                }
                
                try:
                    response = requests.post(
                        "http://localhost:5000/driver/login",
                        json=login_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    result = response.json()
                    
                    if result.get("success"):
                        print(f"  Login Test: ✅ SUCCESS")
                    else:
                        print(f"  Login Test: ❌ FAILED - {result.get('message', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"  Login Test: ❌ ERROR - {str(e)}")
                    
            print("-" * 30)

if __name__ == "__main__":
    test_driver_login()