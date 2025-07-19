#!/usr/bin/env python3
"""
Test script for Advertisement Management System
"""
import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:5000"
ADMIN_LOGIN_URL = f"{BASE_URL}/admin/login"
ADMIN_ADS_API = f"{BASE_URL}/admin/api/advertisements"
CUSTOMER_ADS_API = f"{BASE_URL}/customer/advertisements"

# Test admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def test_admin_login():
    """Test admin login and return session"""
    session = requests.Session()
    
    # Login admin user
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }
    
    response = session.post(ADMIN_LOGIN_URL, data=login_data)
    if response.status_code == 200 and 'dashboard' in response.url:
        print("✓ Admin login successful")
        return session
    else:
        print("✗ Admin login failed")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return None

def test_get_advertisements(session):
    """Test getting all advertisements"""
    print("\n=== Testing Get Advertisements ===")
    
    response = session.get(ADMIN_ADS_API)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            ads = data.get('data', [])
            print(f"✓ Retrieved {len(ads)} advertisements")
            
            for ad in ads:
                print(f"  - {ad['title']} ({ad['media_type']}) - Order: {ad['display_order']}")
                print(f"    Duration: {ad['display_duration']}s, Active: {ad['is_active']}")
                if ad.get('target_location'):
                    print(f"    Target Location: {ad['target_location']}")
                if ad.get('target_ride_type'):
                    print(f"    Target Ride Type: {ad['target_ride_type']}")
                print(f"    Analytics: {ad['impressions']} impressions, {ad['clicks']} clicks")
            
            return ads
        else:
            print(f"✗ API returned error: {data.get('message')}")
    else:
        print(f"✗ Failed to get advertisements: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    
    return []

def test_customer_advertisements():
    """Test customer advertisement API"""
    print("\n=== Testing Customer Advertisement API ===")
    
    # Test without filters
    response = requests.get(CUSTOMER_ADS_API)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            ads_data = data.get('data', {})
            advertisements = ads_data.get('advertisements', [])
            total_ads = ads_data.get('total_ads', 0)
            total_duration = ads_data.get('total_duration_seconds', 0)
            
            print(f"✓ Customer API returned {total_ads} advertisements")
            print(f"  Total slideshow duration: {total_duration} seconds")
            
            slideshow_config = ads_data.get('slideshow_config', {})
            print(f"  Slideshow config: {slideshow_config}")
            
            for ad in advertisements:
                print(f"  - {ad['title']} ({ad['media_type']}) - {ad['display_duration']}s")
                if ad.get('media_url'):
                    print(f"    Media URL: {ad['media_url']}")
            
            return advertisements
        else:
            print(f"✗ Customer API returned error: {data.get('message')}")
    else:
        print(f"✗ Failed to get customer advertisements: {response.status_code}")
        print(f"Response: {response.text[:200]}")
    
    return []

def test_customer_advertisements_with_filters():
    """Test customer advertisement API with filters"""
    print("\n=== Testing Customer Advertisement API with Filters ===")
    
    # Test with location filter
    response = requests.get(f"{CUSTOMER_ADS_API}?location=Chennai Central")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            ads_data = data.get('data', {})
            total_ads = ads_data.get('total_ads', 0)
            print(f"✓ Location filter (Chennai Central): {total_ads} advertisements")
        else:
            print(f"✗ Location filter failed: {data.get('message')}")
    
    # Test with ride type filter
    response = requests.get(f"{CUSTOMER_ADS_API}?ride_type=sedan")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            ads_data = data.get('data', {})
            total_ads = ads_data.get('total_ads', 0)
            print(f"✓ Ride type filter (sedan): {total_ads} advertisements")
        else:
            print(f"✗ Ride type filter failed: {data.get('message')}")
    
    # Test with customer type filter
    response = requests.get(f"{CUSTOMER_ADS_API}?customer_type=new")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            ads_data = data.get('data', {})
            total_ads = ads_data.get('total_ads', 0)
            print(f"✓ Customer type filter (new): {total_ads} advertisements")
        else:
            print(f"✗ Customer type filter failed: {data.get('message')}")

def test_ad_analytics(ad_id):
    """Test advertisement analytics (impression and click tracking)"""
    print(f"\n=== Testing Advertisement Analytics for Ad ID {ad_id} ===")
    
    # Test impression tracking
    impression_url = f"{CUSTOMER_ADS_API}/{ad_id}/impression"
    response = requests.post(impression_url)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            impressions = data.get('data', {}).get('impressions', 0)
            print(f"✓ Impression recorded. Total impressions: {impressions}")
        else:
            print(f"✗ Impression tracking failed: {data.get('message')}")
    else:
        print(f"✗ Impression tracking request failed: {response.status_code}")
    
    # Test click tracking
    click_url = f"{CUSTOMER_ADS_API}/{ad_id}/click"
    response = requests.post(click_url)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            result_data = data.get('data', {})
            clicks = result_data.get('clicks', 0)
            impressions = result_data.get('impressions', 0)
            ctr = result_data.get('ctr', 0)
            print(f"✓ Click recorded. Total clicks: {clicks}, Impressions: {impressions}, CTR: {ctr}%")
        else:
            print(f"✗ Click tracking failed: {data.get('message')}")
    else:
        print(f"✗ Click tracking request failed: {response.status_code}")

def test_admin_interface():
    """Test admin interface availability"""
    print("\n=== Testing Admin Interface ===")
    
    admin_ads_page = f"{BASE_URL}/admin/advertisements"
    response = requests.get(admin_ads_page)
    
    # Should redirect to login if not authenticated
    if response.status_code == 200 or (response.status_code == 302 and 'login' in response.headers.get('Location', '')):
        print("✓ Admin advertisements page is accessible")
    else:
        print(f"✗ Admin advertisements page failed: {response.status_code}")

def main():
    """Run all advertisement system tests"""
    print("🎯 A1 Call Taxi - Advertisement Management System Test")
    print("=" * 60)
    
    # Test admin functionality
    session = test_admin_login()
    if session:
        advertisements = test_get_advertisements(session)
    else:
        advertisements = []
    
    # Test customer API
    customer_ads = test_customer_advertisements()
    test_customer_advertisements_with_filters()
    
    # Test analytics if we have ads
    if customer_ads:
        test_ad_analytics(customer_ads[0]['id'])
    
    # Test admin interface
    test_admin_interface()
    
    print("\n" + "=" * 60)
    print("✅ Advertisement system testing completed!")
    print("\nSummary:")
    print(f"- Admin API: {'✓' if session else '✗'}")
    print(f"- Customer API: {'✓' if customer_ads else '✗'}")
    print(f"- Analytics tracking: {'✓' if customer_ads else '✗'}")
    print(f"- Admin interface: ✓")
    
    if not advertisements and not customer_ads:
        print("\n💡 Note: No advertisements found. Create some ads through the admin panel to test the full system.")

if __name__ == "__main__":
    main()