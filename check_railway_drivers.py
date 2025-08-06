#!/usr/bin/env python3

import requests
import re
from bs4 import BeautifulSoup

# Login to admin panel
login_url = "https://taxibook-backend-production.up.railway.app/admin/login"
drivers_url = "https://taxibook-backend-production.up.railway.app/admin/drivers"

session = requests.Session()

# Login with form data
login_data = {
    'username': 'admin', 
    'password': 'admin123'
}

print("🔐 Attempting admin login to Railway...")
login_response = session.post(login_url, data=login_data)

if "Dashboard" in login_response.text or login_response.status_code == 302:
    print("✅ Admin login successful!")
    
    # Get drivers page
    print("📋 Fetching drivers list...")
    drivers_response = session.get(drivers_url)
    
    if drivers_response.status_code == 200:
        # Parse HTML to extract driver data
        soup = BeautifulSoup(drivers_response.text, 'html.parser')
        
        # Look for driver data in tables or cards
        driver_data = []
        
        # Try to find driver information in the HTML
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 3:
                # Extract username, phone, etc from table cells
                row_text = ' '.join([cell.get_text().strip() for cell in cells])
                if 'DRV' in row_text:
                    driver_data.append(row_text)
        
        # Also look for driver cards or divs
        for div in soup.find_all('div', class_=re.compile('driver|card')):
            text = div.get_text()
            if 'DRV' in text:
                driver_data.append(text.strip())
        
        print(f"🚗 Found {len(driver_data)} drivers:")
        for i, data in enumerate(driver_data[:5]):  # Show first 5
            print(f"{i+1}. {data}")
            
        # Look for any JavaScript data or API endpoints
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and ('DRV' in script.string or 'driver' in script.string.lower()):
                print("📄 Found driver data in JavaScript:")
                print(script.string[:200])
                
    else:
        print(f"❌ Failed to fetch drivers page: {drivers_response.status_code}")
        print(drivers_response.text[:200])
        
else:
    print("❌ Admin login failed!")
    print(f"Status: {login_response.status_code}")
    print(login_response.text[:200])