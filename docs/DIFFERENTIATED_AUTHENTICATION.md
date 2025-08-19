# DIFFERENTIATED AUTHENTICATION SYSTEM

## 🔐 AUTHENTICATION DESIGN PROBLEM SOLVED

### **PREVIOUS ISSUE:**
The system had a **unified login endpoint** that couldn't properly handle the different authentication requirements:
- **Drivers**: Need `username` + `password` (traditional secure login)
- **Customers**: Need `name` + `phone` (simple registration/login)

### **NEW SOLUTION: SEPARATE AUTHENTICATION ENDPOINTS**

## 📱 **DRIVER APP AUTHENTICATION**

### **Endpoint**: `POST /auth/driver/login`

### **Request Format**:
```json
{
  "username": "testdriver",    // Driver username or phone number
  "password": "driver123"      // Driver password (required)
}
```

### **Response Format**:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 123,
      "name": "Test Driver",
      "phone": "9999888777",
      "username": "testdriver",
      "user_type": "driver",
      "car_type": "sedan",
      "car_number": "KA01AB1234"
    },
    "auth": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in": 86400
    }
  }
}
```

### **Driver App Login Flow**:
1. **Login Screen**: Username/Password fields
2. **API Call**: `POST /auth/driver/login` with credentials
3. **Store Tokens**: Save access_token and refresh_token securely
4. **Use Bearer Token**: Include `Authorization: Bearer <token>` in all API calls

## 👤 **CUSTOMER APP AUTHENTICATION**

### **Endpoint**: `POST /auth/customer/login`

### **Request Format**:
```json
{
  "name": "Jane Smith",      // Customer name
  "phone": "8888777666"      // Phone number (no password needed)
}
```

### **Response Format**:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 456,
      "name": "Jane Smith",
      "phone": "8888777666",
      "user_type": "customer"
    },
    "auth": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in": 86400
    }
  }
}
```

### **Customer App Login Flow**:
1. **Login Screen**: Name + Phone fields only
2. **Auto-Registration**: Creates new customer if phone doesn't exist
3. **API Call**: `POST /auth/customer/login` with name and phone
4. **Store Tokens**: Save access_token and refresh_token securely
5. **Use Bearer Token**: Include `Authorization: Bearer <token>` in all API calls

## 🔒 **SECURITY DIFFERENCES**

### **Driver Authentication**:
- **Required**: Username/phone + password
- **Security Level**: High (password-protected accounts)
- **Login Method**: Traditional credential validation
- **Account Creation**: Admin-controlled (drivers must be added by admin)

### **Customer Authentication**:
- **Required**: Name + phone only
- **Security Level**: Medium (phone-based identification)
- **Login Method**: Auto-registration if new phone number
- **Account Creation**: Self-service (auto-creates on first login)

## 📊 **API ENDPOINT SUMMARY**

| App Type | Endpoint | Required Fields | Auto-Registration |
|----------|----------|----------------|-------------------|
| Driver | `/auth/driver/login` | username + password | ❌ No |
| Customer | `/auth/customer/login` | name + phone | ✅ Yes |
| Deprecated | `/auth/login` | N/A | ❌ Disabled |

## 🛡️ **ERROR HANDLING**

### **Driver Login Errors**:
- Missing username/password: "Username and password are required"
- Invalid credentials: "Invalid username or password"
- No password set: "Driver account not properly configured"

### **Customer Login Errors**:
- Missing name/phone: "Name and phone number are required"
- Invalid phone format: "Invalid phone number format"

## 🎯 **MOBILE APP IMPLEMENTATION**

### **Driver App Login Screen**:
```javascript
// Driver login function
async function driverLogin(username, password) {
  const response = await fetch('/auth/driver/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  if (data.success) {
    // Store tokens
    localStorage.setItem('access_token', data.data.auth.access_token);
    localStorage.setItem('refresh_token', data.data.auth.refresh_token);
    localStorage.setItem('user_data', JSON.stringify(data.data.user));
    // Navigate to driver dashboard
  }
}
```

### **Customer App Login Screen**:
```javascript
// Customer login function
async function customerLogin(name, phone) {
  const response = await fetch('/auth/customer/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, phone })
  });
  
  const data = await response.json();
  if (data.success) {
    // Store tokens
    localStorage.setItem('access_token', data.data.auth.access_token);
    localStorage.setItem('refresh_token', data.data.auth.refresh_token);
    localStorage.setItem('user_data', JSON.stringify(data.data.user));
    // Navigate to customer dashboard
  }
}
```

## ✅ **SYSTEM STATUS**

- **✅ Driver Authentication**: Username + password required
- **✅ Customer Authentication**: Name + phone with auto-registration
- **✅ Differentiated Endpoints**: Separate /driver/login and /customer/login
- **✅ Unified JWT Tokens**: Same token format for both user types
- **✅ Deprecated Old Endpoint**: /auth/login properly deprecated
- **✅ Error Handling**: Appropriate error messages for each flow
- **✅ Security**: Password protection for drivers, phone-based for customers

The authentication system now properly handles the different requirements for drivers and customers while maintaining a unified JWT token system for API access.

---
*Differentiated Authentication System Implemented: August 19, 2025*