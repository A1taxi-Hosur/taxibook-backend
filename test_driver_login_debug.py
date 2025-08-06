#!/usr/bin/env python3

import requests
import json

# Test driver login with exact credentials from database
base_url = "https://taxibook-backend-production.up.railway.app"

# Test data from database
drivers = [
    {"username": "DRVVJ53TA", "phone": "9988776655"},
    {"username": "DRVSUVTEST", "phone": "9876543210"}, 
    {"username": "DRVON80EJ", "phone": "7010213984"}
]

for driver in drivers:
    username = driver["username"] 
    phone = driver["phone"]
    password = f"{phone[-4:]}@Taxi"
    
    print(f"\n=== Testing Driver: {username} ===")
    print(f"Phone: {phone}")
    print(f"Generated Password: {password}")
    
    # Test login
    response = requests.post(f"{base_url}/driver/login", json={
        "username": username,
        "password": password
    })
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ LOGIN SUCCESS!")
        break
    else:
        print("❌ Login failed")

print("\n=== Testing different password variations ===")
test_passwords = [
    "6655@Taxi",    # Standard format
    "6655@taxi",    # lowercase
    "6655@TAXI",    # uppercase 
    "6655Taxi",     # no @
    "6655",         # just digits
    "password123",  # generic
    "123456"        # simple
]

username = "DRVVJ53TA"
for pwd in test_passwords:
    response = requests.post(f"{base_url}/driver/login", json={
        "username": username,
        "password": pwd
    })
    
    print(f"Password '{pwd}': {response.status_code} - {response.text[:50]}")