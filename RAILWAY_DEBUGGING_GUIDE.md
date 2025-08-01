# Railway Deployment - Complete Debugging Guide

## Root Cause Found ✅

Your app.py has `load_dotenv()` which loads from the .env file. In Railway deployment:

1. **Replit**: Uses Replit Secrets (working key: `AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo`)
2. **Railway**: Uses .env file first, then environment variables
3. **Problem**: Your .env file has wrong key: `AIzaSyDw7eAaQOKVOrurvnqTyR6yK3tDdXnjsFk`

## Complete Solution

### Option 1: Update .env File Before Pushing (Recommended)
Before pushing to GitHub, update your .env file:
```env
FLASK_SECRET_KEY=dev-placeholder-key
DATABASE_URL=sqlite:///dev.db
GOOGLE_MAPS_API_KEY=AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo
```

### Option 2: Railway Environment Variables Override
Set in Railway dashboard with higher priority:
- Go to Railway → Your Project → Variables
- Add: `GOOGLE_MAPS_API_KEY` = `AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo`
- Ensure it overrides the .env file

### Option 3: Remove .env from Deployment
Add to .gitignore:
```
.env
```
Then rely only on Railway environment variables.

## Verification Steps

### Step 1: Check Railway Logs
Look for these log patterns after deployment:
```
✅ GOOD: DEBUG:urllib3.connectionpool:https://maps.googleapis.com:443 "GET /maps/api/distancematrix/json?...&key=AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo&units=metric HTTP/1.1" 200 716

❌ BAD: ERROR:root:Google Maps API error: REQUEST_DENIED - You must enable Billing
```

### Step 2: Test API Endpoints
Test on your Railway deployment:
```bash
curl -X POST https://your-railway-app.railway.app/customer/ride_estimate \
-H "Content-Type: application/json" \
-d '{
  "pickup_lat": 12.7400,
  "pickup_lng": 77.8253,
  "drop_lat": 12.7500,
  "drop_lng": 77.8353
}'
```

Expected response:
```json
{
  "success": true,
  "distance_km": 1.55,
  "estimates": {
    "hatchback": {"final_fare": 43.64}
  }
}
```

## Environment Loading Order

Your app.py loads in this order:
1. `load_dotenv()` → Loads .env file
2. `os.environ.get()` → Uses environment variables as fallback

Railway environment variables should override .env, but make sure both are set correctly.

## Production Environment Variables for Railway

Set ALL these in Railway:
```
GOOGLE_MAPS_API_KEY=AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo
FLASK_SECRET_KEY=your-secure-production-key
DATABASE_URL=your-postgresql-production-url
FLASK_ENV=production
FLASK_DEBUG=False
```

## Files Using Google Maps API

All these files properly use `os.environ.get("GOOGLE_MAPS_API_KEY")`:
- `utils/maps.py` (line 11, 91)
- `routes/admin.py` (line 1015, 1031)
- `templates/admin/zones.html` (line 239)
- `templates/admin/live_map.html` (line 575)

## Quick Test Commands

Test if your Railway deployment has the correct API key:
```bash
# Check Railway environment
railway run printenv | grep GOOGLE_MAPS_API_KEY

# Test direct API call
curl "https://maps.googleapis.com/maps/api/distancematrix/json?origins=12.74,77.82&destinations=12.75,77.83&key=YOUR_RAILWAY_API_KEY&units=metric"
```

Expected: `"status": "OK"` not `"status": "REQUEST_DENIED"`