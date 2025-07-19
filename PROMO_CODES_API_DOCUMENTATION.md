# A1 Call Taxi - Promo Codes API Documentation

## Overview
The Promo Codes API allows customer apps to display available promotional offers, validate promo codes, and apply discounts during ride booking. The system provides rich display formatting and smart filtering based on ride parameters.

## Base URL
```
http://your-domain.com/customer
```

## API Endpoints

### 1. Get Available Promo Codes

**Endpoint:** `GET /customer/promo_codes/available`

**Description:** Retrieve all active and applicable promo codes for display in customer app.

**Query Parameters (Optional):**
- `ride_type` (string): Filter by ride type ("hatchback", "sedan", "suv")
- `ride_category` (string): Filter by ride category ("regular", "airport", "rental", "outstation")
- `min_fare` (float): Filter by minimum fare amount to show applicable promos

**Request Examples:**
```bash
# Get all available promo codes
GET /customer/promo_codes/available

# Get promo codes for specific ride type
GET /customer/promo_codes/available?ride_type=sedan

# Get promo codes for airport rides above ₹200
GET /customer/promo_codes/available?ride_category=airport&min_fare=200

# Get all applicable promos for a ₹150 hatchback ride
GET /customer/promo_codes/available?ride_type=hatchback&min_fare=150
```

**Response Format:**
```json
{
  "status": "success",
  "message": "Success",
  "data": {
    "promo_codes": [
      {
        "code": "WELCOME50",
        "discount_type": "flat",
        "discount_value": 50.0,
        "min_fare": 100.0,
        "expiry_date": "2025-08-19T23:59:59",
        "ride_type": null,
        "ride_category": null,
        "usage_remaining": 85,
        "max_uses": 100,
        "is_limited": true,
        "display_text": "₹50 OFF",
        "savings_text": "You'll save ₹50 on this ride",
        "terms": [
          "Minimum fare: ₹100",
          "Valid till: 19 Aug 2025",
          "Uses remaining: 85"
        ]
      },
      {
        "code": "FIRST10",
        "discount_type": "percent",
        "discount_value": 10.0,
        "min_fare": 50.0,
        "expiry_date": "2025-09-18T23:59:59",
        "ride_type": null,
        "ride_category": null,
        "usage_remaining": 485,
        "max_uses": 500,
        "is_limited": true,
        "display_text": "10% OFF",
        "savings_text": "You'll save ₹15 (10% off)",
        "terms": [
          "Minimum fare: ₹50",
          "Valid till: 18 Sep 2025",
          "Uses remaining: 485"
        ]
      }
    ],
    "total_available": 2,
    "filters_applied": {
      "ride_type": null,
      "ride_category": null,
      "min_fare": null
    }
  }
}
```

### 2. Validate Promo Code (Existing Endpoint)

**Endpoint:** `POST /customer/validate_promo`

**Description:** Validate a specific promo code for a ride.

**Request Body:**
```json
{
  "promo_code": "WELCOME50",
  "ride_type": "sedan",
  "ride_category": "regular",
  "estimated_fare": 150.0
}
```

**Response Format:**
```json
{
  "status": "success",
  "message": "Promo code is valid",
  "data": {
    "valid": true,
    "discount_amount": 50.0,
    "final_fare": 100.0,
    "promo_code": "WELCOME50",
    "discount_type": "flat",
    "discount_value": 50.0
  }
}
```

## Key Implementation Points

### Display Available Promos
```javascript
// Load and display promo codes
fetch('/customer/promo_codes/available?ride_type=sedan&min_fare=150')
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      const promos = data.data.promo_codes;
      // Display each promo with:
      // - promo.display_text (e.g., "₹50 OFF")
      // - promo.savings_text (calculated savings)
      // - promo.terms (array of conditions)
    }
  });
```

### Smart Filtering
The API automatically filters promo codes based on:
- **Active status**: Only returns active promo codes
- **Expiry dates**: Excludes expired promos
- **Usage limits**: Only shows promos with remaining uses
- **Ride compatibility**: Filters by ride type and category
- **Minimum fare**: Shows only applicable promos for the fare amount

### Display Format
Each promo code includes formatted display elements:
- `display_text`: Ready-to-use badge text ("₹50 OFF", "10% OFF")
- `savings_text`: Contextual savings description
- `terms`: Array of human-readable conditions

### Usage Flow
1. **Get Available Promos**: Call `/promo_codes/available` with ride parameters
2. **Display Promos**: Show formatted promo cards with terms
3. **Validate Selection**: Use existing `/validate_promo` endpoint
4. **Apply Discount**: Use validated promo in booking process

## Example Response Data Structure

```json
{
  "code": "WELCOME50",
  "discount_type": "flat",
  "discount_value": 50.0,
  "min_fare": 100.0,
  "display_text": "₹50 OFF",
  "savings_text": "You'll save ₹50 on this ride",
  "terms": [
    "Minimum fare: ₹100",
    "Valid till: 19 Aug 2025",
    "Uses remaining: 85"
  ]
}
```

This API provides everything needed to create an engaging promo codes section in your customer app with smart filtering and rich display formatting.