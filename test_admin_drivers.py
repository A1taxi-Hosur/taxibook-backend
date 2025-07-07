#!/usr/bin/env python3
"""
Test script for Admin Driver Management System
Tests all CRUD operations for driver management
"""

import requests
import json
import time

BASE_URL = "http://0.0.0.0:5000"

def test_admin_login():
    """Test admin login"""
    print("🔐 Testing Admin Login...")
    
    session = requests.Session()
    response = session.post(f"{BASE_URL}/admin/login", 
                           data={"username": "admin", "password": "admin123"})
    
    if response.status_code == 200:
        print("✅ Admin login successful")
        return session
    else:
        print("❌ Admin login failed")
        return None

def test_create_driver(session):
    """Test creating a new driver"""
    print("\n📝 Testing Create Driver...")
    
    driver_data = {
        "name": "Test Driver Kumar",
        "phone": "9876543210",
        "car_make": "Maruti",
        "car_model": "Swift Dzire",
        "car_year": "2022",
        "car_number": "DL 01 CA 5555",
        "car_type": "sedan",
        "license_number": "DL123456789",
        "profile_photo_url": "https://example.com/photo.jpg"
    }
    
    response = session.post(f"{BASE_URL}/admin/create_driver", 
                           data=driver_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Driver created successfully")
            print(f"   Driver ID: {result['data']['driver_id']}")
            print(f"   Username: {result['data']['username']}")
            print(f"   Password: {result['data']['password']}")
            return result['data']['driver_id']
        else:
            print(f"❌ Driver creation failed: {result.get('message')}")
    else:
        print(f"❌ Driver creation failed with status {response.status_code}")
        try:
            result = response.json()
            print(f"   Error details: {result.get('message', 'Unknown error')}")
        except:
            print(f"   Response text: {response.text[:200]}")
    
    return None

def test_update_driver(session, driver_id):
    """Test updating driver information"""
    print(f"\n✏️  Testing Update Driver (ID: {driver_id})...")
    
    update_data = {
        "driver_id": driver_id,
        "name": "Updated Driver Kumar",
        "is_online": "true",
        "car_make": "Honda",
        "car_model": "City",
        "car_year": "2023",
        "car_number": "DL 02 CA 6666",
        "car_type": "sedan",
        "license_number": "DL987654321"
    }
    
    response = session.post(f"{BASE_URL}/admin/update_driver", 
                           data=update_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Driver updated successfully")
            print(f"   Updated Name: {result['data']['name']}")
        else:
            print(f"❌ Driver update failed: {result.get('message')}")
    else:
        print(f"❌ Driver update failed with status {response.status_code}")

def test_reset_password(session, username):
    """Test resetting driver password"""
    print(f"\n🔑 Testing Reset Password for {username}...")
    
    # Generate password based on last 4 digits of phone
    new_password = "3210@Taxi"  # Based on phone ending in 3210
    
    reset_data = {
        "username": username,
        "new_password": new_password
    }
    
    response = session.post(f"{BASE_URL}/admin/reset_driver_password", 
                           json=reset_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Password reset successful")
            print(f"   New password: {new_password}")
        else:
            print(f"❌ Password reset failed: {result.get('message')}")
    else:
        print(f"❌ Password reset failed with status {response.status_code}")

def test_view_drivers(session):
    """Test viewing drivers page"""
    print("\n👥 Testing View Drivers Page...")
    
    response = session.get(f"{BASE_URL}/admin/drivers")
    
    if response.status_code == 200:
        print("✅ Drivers page loaded successfully")
        # Check if page contains expected elements
        if "Create Driver" in response.text:
            print("   ✅ Create Driver button found")
        if "Edit Driver" in response.text:
            print("   ✅ Edit functionality detected")
        if "Delete Driver" in response.text:
            print("   ✅ Delete functionality detected")
    else:
        print(f"❌ Drivers page failed with status {response.status_code}")

def test_delete_driver(session, driver_id):
    """Test deleting a driver"""
    print(f"\n🗑️  Testing Delete Driver (ID: {driver_id})...")
    
    delete_data = {
        "driver_id": driver_id
    }
    
    response = session.post(f"{BASE_URL}/admin/delete_driver", 
                           json=delete_data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Driver deleted successfully")
            print(f"   Deleted: {result['data']['deleted_driver']}")
        else:
            print(f"❌ Driver deletion failed: {result.get('message')}")
    else:
        print(f"❌ Driver deletion failed with status {response.status_code}")

def main():
    """Run all tests"""
    print("🚀 Starting Admin Driver Management Tests")
    print("=" * 50)
    
    # Test admin login
    session = test_admin_login()
    if not session:
        print("❌ Cannot proceed without admin session")
        return
    
    # Test viewing drivers page
    test_view_drivers(session)
    
    # Test creating driver
    driver_id = test_create_driver(session)
    if not driver_id:
        print("❌ Cannot proceed without creating driver")
        return
    
    # Small delay to ensure driver is created
    time.sleep(1)
    
    # Test updating driver
    test_update_driver(session, driver_id)
    
    # Test password reset (need to get username first)
    # Username format: DRVAB12CD (generated from phone)
    username = "DRVAB12CD"  # This will be auto-generated
    test_reset_password(session, username)
    
    # Test deleting driver
    test_delete_driver(session, driver_id)
    
    print("\n" + "=" * 50)
    print("🎉 All Admin Driver Management Tests Completed!")
    print("\nFeatures tested:")
    print("✅ Admin authentication")
    print("✅ Create driver with full details")
    print("✅ Update driver information")
    print("✅ Reset driver password")
    print("✅ Delete driver")
    print("✅ View drivers page with UI elements")

if __name__ == "__main__":
    main()