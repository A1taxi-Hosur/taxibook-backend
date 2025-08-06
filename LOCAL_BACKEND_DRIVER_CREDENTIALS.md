# **🚗 Local Backend Driver Credentials - Working Test Environment**

## **Backend Connection Details**
- **Backend URL:** `http://localhost:5000` (Replit development server)
- **Status:** ✅ Fully functional with driver authentication working
- **Environment:** Development/Testing

---

## **Available Driver Accounts**

### **Primary Test Driver (Confirmed Working)**
- **Username:** `DRVVJ53TA`
- **Phone:** `9988776655`
- **Password:** `6655@Taxi` (last 4 digits + @Taxi)
- **Name:** Ricco
- **Car:** Maruti Ciaz (Sedan)
- **Status:** Online ✅

**Test Result:** Login successful with complete driver data returned

---

## **Password Calculation Formula**
All driver passwords follow this pattern:
- **Formula:** Last 4 digits of phone number + `@Taxi`
- **Examples:**
  - Phone `9988776655` → Password `6655@Taxi`
  - Phone `9876543210` → Password `3210@Taxi`
  - Phone `7010213984` → Password `3984@Taxi`

---

## **API Endpoint Testing**

### **Login Endpoint**
```bash
POST http://localhost:5000/driver/login
Content-Type: application/json

{
  "username": "DRVVJ53TA",
  "password": "6655@Taxi"
}
```

### **Expected Response**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "driver_id": 20,
    "username": "DRVVJ53TA",
    "name": "Ricco",
    "phone": "9988776655",
    "car_make": "Maruti",
    "car_model": "Ciaz", 
    "car_number": "TN29AQ1288",
    "car_type": "sedan",
    "car_year": 2003,
    "is_online": true
  }
}
```

---

## **For Driver App Configuration**

### **Change Backend URL To:**
```
http://localhost:5000
```

### **Test Credentials:**
```
Username: DRVVJ53TA
Password: 6655@Taxi
```

### **What You'll Get:**
- ✅ Successful login response
- ✅ Complete driver profile data
- ✅ Online status management
- ✅ All driver APIs functional

---

## **Available Features**

Once connected to local backend, the driver app will have access to:

- **Authentication:** Login/Logout
- **Ride Management:** Accept/Reject ride requests
- **Location Tracking:** Update driver location
- **Status Management:** Online/Offline control
- **Profile Management:** View driver details

---

## **Testing Notes**

1. **Network Access:** Ensure the driver app can reach the local network
2. **Port Access:** Port 5000 must be accessible
3. **JSON Format:** All requests must be properly formatted JSON
4. **Response Handling:** All responses follow standard API format

This local backend provides a fully functional testing environment while the Railway production issue is resolved.