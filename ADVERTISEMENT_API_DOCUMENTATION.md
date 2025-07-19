# A1 Call Taxi - Advertisement API Documentation

## Overview
The Advertisement API allows customer apps to display promotional content in a slideshow format with precise timing controls and analytics tracking. The system supports images and videos with configurable display durations, targeting options, and real-time analytics.

## Base URL
```
http://your-domain.com/customer
```

## API Endpoints

### 1. Get Advertisements for Slideshow

**Endpoint:** `GET /customer/advertisements`

**Description:** Retrieve active advertisements for display in the customer app slideshow area.

**Query Parameters (Optional):**
- `location` (string): Filter ads by target location (e.g., "Chennai Central")
- `ride_type` (string): Filter ads by ride type ("hatchback", "sedan", "suv")
- `customer_type` (string): Filter ads by customer type ("new", "regular", "premium")

**Request Example:**
```bash
# Get all active advertisements
GET /customer/advertisements

# Get advertisements for specific filters
GET /customer/advertisements?location=Chennai%20Central&ride_type=sedan&customer_type=new
```

**Response Format:**
```json
{
  "status": "success",
  "message": "Success",
  "data": {
    "advertisements": [
      {
        "id": 1,
        "title": "Summer Sale - 50% Off",
        "description": "Limited time offer for all rides",
        "media_type": "image",
        "media_filename": "uuid_filename.jpg",
        "media_url": "/static/ads/uuid_filename.jpg",
        "display_duration": 5,
        "display_order": 1,
        "target_location": null,
        "target_ride_type": null,
        "target_customer_type": "new",
        "start_date": "2025-07-19T00:00:00",
        "end_date": "2025-07-30T23:59:59",
        "active_hours_start": "09:00",
        "active_hours_end": "21:00",
        "is_active": true,
        "impressions": 1250,
        "clicks": 45,
        "created_at": "2025-07-19T15:30:00",
        "updated_at": "2025-07-19T15:30:00"
      },
      {
        "id": 2,
        "title": "Premium Service Launch",
        "description": "Experience luxury rides",
        "media_type": "video",
        "media_filename": "uuid_video.mp4",
        "media_url": "/static/ads/uuid_video.mp4",
        "display_duration": 8,
        "display_order": 2,
        "target_location": "Chennai Central",
        "target_ride_type": "suv",
        "target_customer_type": null,
        "start_date": null,
        "end_date": null,
        "active_hours_start": null,
        "active_hours_end": null,
        "is_active": true,
        "impressions": 890,
        "clicks": 32,
        "created_at": "2025-07-19T16:00:00",
        "updated_at": "2025-07-19T16:00:00"
      }
    ],
    "total_ads": 2,
    "total_duration_seconds": 13,
    "slideshow_config": {
      "auto_advance": true,
      "loop": true,
      "show_controls": false
    }
  }
}
```

### 2. Record Advertisement Impression

**Endpoint:** `POST /customer/advertisements/{ad_id}/impression`

**Description:** Record when an advertisement is viewed (displayed to user).

**Path Parameters:**
- `ad_id` (integer): The unique ID of the advertisement

**Request Example:**
```bash
POST /customer/advertisements/1/impression
```

**Response Format:**
```json
{
  "status": "success",
  "message": "Success",
  "data": {
    "ad_id": 1,
    "impressions": 1251,
    "message": "Impression recorded"
  }
}
```

### 3. Record Advertisement Click

**Endpoint:** `POST /customer/advertisements/{ad_id}/click`

**Description:** Record when a user interacts with (clicks/taps) an advertisement.

**Path Parameters:**
- `ad_id` (integer): The unique ID of the advertisement

**Request Example:**
```bash
POST /customer/advertisements/1/click
```

**Response Format:**
```json
{
  "status": "success",
  "message": "Success",
  "data": {
    "ad_id": 1,
    "clicks": 46,
    "impressions": 1251,
    "ctr": 3.68,
    "message": "Click recorded"
  }
}
```

## Implementation Guide for Customer App

### 1. Slideshow Component Setup

```javascript
class AdvertisementSlideshow {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.currentIndex = 0;
    this.advertisements = [];
    this.isPlaying = false;
    this.timer = null;
    this.options = {
      autoAdvance: true,
      loop: true,
      showControls: false,
      baseUrl: 'http://your-domain.com/customer',
      ...options
    };
  }

  async loadAdvertisements(filters = {}) {
    try {
      const params = new URLSearchParams(filters);
      const response = await fetch(`${this.options.baseUrl}/advertisements?${params}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.advertisements = data.data.advertisements;
        this.setupSlideshow();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to load advertisements:', error);
      return false;
    }
  }

  setupSlideshow() {
    if (this.advertisements.length === 0) {
      this.container.innerHTML = '<div class="no-ads">No advertisements available</div>';
      return;
    }

    this.renderCurrentAd();
    if (this.options.autoAdvance) {
      this.startSlideshow();
    }
  }

  renderCurrentAd() {
    if (this.advertisements.length === 0) return;
    
    const ad = this.advertisements[this.currentIndex];
    
    // Record impression
    this.recordImpression(ad.id);
    
    let mediaHtml = '';
    if (ad.media_type === 'image') {
      mediaHtml = `
        <img src="${ad.media_url}" 
             alt="${ad.title}" 
             class="ad-media" 
             onclick="this.handleAdClick(${ad.id})">
      `;
    } else if (ad.media_type === 'video') {
      mediaHtml = `
        <video class="ad-media" 
               autoplay 
               muted 
               onclick="this.handleAdClick(${ad.id})">
          <source src="${ad.media_url}" type="video/mp4">
        </video>
      `;
    }
    
    this.container.innerHTML = `
      <div class="advertisement-slide" data-ad-id="${ad.id}">
        ${mediaHtml}
        <div class="ad-overlay">
          <h3 class="ad-title">${ad.title}</h3>
          ${ad.description ? `<p class="ad-description">${ad.description}</p>` : ''}
        </div>
      </div>
    `;
  }

  startSlideshow() {
    if (this.advertisements.length <= 1) return;
    
    this.isPlaying = true;
    this.scheduleNext();
  }

  scheduleNext() {
    if (!this.isPlaying) return;
    
    const currentAd = this.advertisements[this.currentIndex];
    const duration = currentAd.display_duration * 1000; // Convert to milliseconds
    
    this.timer = setTimeout(() => {
      this.nextSlide();
    }, duration);
  }

  nextSlide() {
    this.currentIndex = (this.currentIndex + 1) % this.advertisements.length;
    this.renderCurrentAd();
    this.scheduleNext();
  }

  handleAdClick(adId) {
    this.recordClick(adId);
    // Add your click handling logic here (e.g., open promotional page)
  }

  async recordImpression(adId) {
    try {
      await fetch(`${this.options.baseUrl}/advertisements/${adId}/impression`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Failed to record impression:', error);
    }
  }

  async recordClick(adId) {
    try {
      await fetch(`${this.options.baseUrl}/advertisements/${adId}/click`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Failed to record click:', error);
    }
  }

  stop() {
    this.isPlaying = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  start() {
    if (!this.isPlaying && this.advertisements.length > 1) {
      this.startSlideshow();
    }
  }
}
```

### 2. CSS Styling

```css
.advertisement-slideshow {
  width: 100%;
  height: 200px;
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.advertisement-slide {
  width: 100%;
  height: 100%;
  position: relative;
  cursor: pointer;
}

.ad-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ad-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  color: white;
  padding: 20px;
}

.ad-title {
  font-size: 18px;
  font-weight: bold;
  margin: 0 0 5px 0;
}

.ad-description {
  font-size: 14px;
  margin: 0;
  opacity: 0.9;
}

.no-ads {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-style: italic;
}
```

### 3. Usage Example

```javascript
// Initialize slideshow
const slideshow = new AdvertisementSlideshow('ad-container', {
  baseUrl: 'http://your-domain.com/customer'
});

// Load advertisements with optional filters
slideshow.loadAdvertisements({
  location: 'Chennai Central',
  ride_type: 'sedan',
  customer_type: 'new'
});

// Control slideshow
// slideshow.stop();   // Stop slideshow
// slideshow.start();  // Start slideshow
```

### 4. HTML Structure

```html
<div class="advertisement-container">
  <div id="ad-container" class="advertisement-slideshow">
    <!-- Advertisements will be dynamically loaded here -->
  </div>
</div>
```

## Data Structure Reference

### Advertisement Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique advertisement ID |
| `title` | string | Advertisement title |
| `description` | string | Optional description text |
| `media_type` | string | "image" or "video" |
| `media_filename` | string | Filename of uploaded media |
| `media_url` | string | Full URL to access the media file |
| `display_duration` | integer | Display time in seconds |
| `display_order` | integer | Order in slideshow sequence |
| `target_location` | string/null | Target location filter |
| `target_ride_type` | string/null | Target ride type filter |
| `target_customer_type` | string/null | Target customer type filter |
| `start_date` | string/null | ISO date when ad becomes active |
| `end_date` | string/null | ISO date when ad expires |
| `active_hours_start` | string/null | Daily start time (HH:MM) |
| `active_hours_end` | string/null | Daily end time (HH:MM) |
| `is_active` | boolean | Whether ad is currently active |
| `impressions` | integer | Total view count |
| `clicks` | integer | Total click count |
| `created_at` | string | ISO timestamp of creation |
| `updated_at` | string | ISO timestamp of last update |

## Error Handling

All API endpoints follow a consistent error format:

```json
{
  "status": "error",
  "message": "Error description",
  "data": null
}
```

Common HTTP status codes:
- `200`: Success
- `404`: Advertisement not found
- `500`: Internal server error

## Performance Recommendations

1. **Preload Media**: Download media files when loading advertisements to ensure smooth playback
2. **Lazy Loading**: Only load advertisements when the slideshow area becomes visible
3. **Caching**: Cache advertisement data for a reasonable time (e.g., 5-10 minutes)
4. **Analytics Batching**: Consider batching impression/click requests to reduce API calls
5. **Error Recovery**: Implement fallback behavior when advertisements fail to load

## Testing

Use the provided test script to verify the API integration:

```bash
python test_advertisements.py
```

This will test all endpoints and provide feedback on the implementation status.