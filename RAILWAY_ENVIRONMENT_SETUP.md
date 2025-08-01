# Railway Deployment - Environment Variables Setup

## Quick Fix for Google Maps Issue

Your Google Maps works perfectly in Replit but fails on Railway because Railway doesn't have the correct API key. Here's the exact fix:

### Step 1: Set Google Maps API Key in Railway
1. Go to your Railway project dashboard
2. Click on your service/app
3. Navigate to **"Variables"** tab
4. Click **"New Variable"**
5. Set:
   - **Variable Name**: `GOOGLE_MAPS_API_KEY`
   - **Variable Value**: `AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo`

### Step 2: Set Other Required Environment Variables
Add these variables in Railway:

```
FLASK_SECRET_KEY=your-production-secret-key-here
DATABASE_URL=your-postgresql-database-url
FLASK_ENV=production
FLASK_DEBUG=False
```

### Step 3: Deploy and Test
After setting the variables:
1. Redeploy your app on Railway
2. Test the ride estimate API: `POST /customer/ride_estimate`
3. Check Railway logs for "200 OK" responses from Google Maps
4. No more "REQUEST_DENIED" errors

## Why This Happens
- **Replit**: Uses Replit Secrets system
- **Railway**: Uses its own environment variables system
- **GitHub**: Only has the .env file with wrong API key

## Alternative: Railway CLI Method
If you prefer command line:
```bash
railway login
railway link [your-project-id]
railway variables set GOOGLE_MAPS_API_KEY=AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo
```

## Verification
After deployment, check Railway logs for:
```
DEBUG:urllib3.connectionpool:https://maps.googleapis.com:443 "GET /maps/api/distancematrix/json?...&key=AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo&units=metric HTTP/1.1" 200 716
```

The key should be `AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo` and response should be `200`, not `REQUEST_DENIED`.

---

**Summary**: Set `GOOGLE_MAPS_API_KEY=AIzaSyBIt8z_VD5s9lo8RpDKdJVhqgtwn0zVBBo` in Railway environment variables and redeploy.