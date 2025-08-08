#!/usr/bin/env python3

import requests
import json

# Actual Railway production driver from the screenshot
base_url = "https://taxibook-backend-production.up.railway.app"

# Driver credentials from Railway production database
driver_data = {
    "username": "DRIVERMQO",  # From screenshot
    "phone": "9876543210",    # From screenshot
    "name": "test",           # From screenshot
}

# Calculate password using the formula: last 4 digits + @Taxi
password = f"{driver_data['phone'][-4:]}@Taxi"

print(f"🚗 Testing Railway Production Driver:")
print(f"Username: {driver_data['username']}")
print(f"Phone: {driver_data['phone']}")
print(f"Name: {driver_data['name']}")
print(f"Calculated Password: {password}")
print()

# Test login
print("📱 Testing driver login...")
response = requests.post(f"{base_url}/driver/login", json={
    "username": driver_data["username"],
    "password": password
})

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("✅ LOGIN SUCCESS!")
    try:
        data = response.json()
        if data.get('success'):
            print("✅ Driver authentication successful!")
            print(f"Driver ID: {data.get('driver', {}).get('driver_id')}")
            print(f"Online Status: {data.get('driver', {}).get('status')}")
        else:
            print(f"❌ Login failed: {data.get('message')}")
    except:
        print("❌ Could not parse response as JSON")
else:
    print("❌ Login failed")
    print(f"Error details: {response.text[:200]}")

# Also test some variations in case there are issues
print("\n🔄 Testing password variations:")
variations = [
    f"{driver_data['phone'][-4:]}@Taxi",  # 3210@Taxi
    f"{driver_data['phone'][-4:]}@taxi",  # 3210@taxi  
    f"{driver_data['phone'][-4:]}Taxi",   # 3210Taxi
    driver_data['phone'][-4:],            # 3210
]

for pwd in variations:
    response = requests.post(f"{base_url}/driver/login", json={
        "username": driver_data["username"],
        "password": pwd
    })
    status = "✅" if response.status_code == 200 else "❌"
    print(f"{status} Password '{pwd}': {response.status_code}")