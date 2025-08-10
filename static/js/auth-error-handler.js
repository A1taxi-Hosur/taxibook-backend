/**
 * Universal Authentication Error Handler for A1 Taxi Customer App
 * Handles JWT token expiration and authentication errors across all pages
 */

class AuthErrorHandler {
    constructor() {
        this.API_BASE_URL = 'https://taxibook-backend-production.up.railway.app';
        this.AUTH_TOKEN_KEY = 'authToken';
        this.USER_DATA_KEY = 'userData';
        this.isHandlingAuthError = false;
        
        // Initialize error handling
        this.setupGlobalErrorHandling();
        this.checkAuthOnPageLoad();
    }
    
    /**
     * Setup global error handling for all API calls
     */
    setupGlobalErrorHandling() {
        // Override fetch to handle auth errors globally
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const response = await originalFetch(...args);
            
            // Check for authentication errors in responses
            if (response.status === 401) {
                try {
                    const data = await response.clone().json();
                    if (data.message && this.isAuthError(data.message)) {
                        this.handleAuthError(data.message);
                        return response; // Return the response for the caller to handle
                    }
                } catch (e) {
                    // If parsing fails, check status code
                    this.handleAuthError('Authentication required');
                }
            }
            
            return response;
        };
    }
    
    /**
     * Check if error message indicates authentication failure
     */
    isAuthError(message) {
        const authErrorPatterns = [
            'token has expired',
            'invalid token',
            'authentication required',
            'please login again',
            'token is required',
            'authentication failed',
            'session has expired'
        ];
        
        const lowerMessage = message.toLowerCase();
        return authErrorPatterns.some(pattern => lowerMessage.includes(pattern));
    }
    
    /**
     * Handle authentication errors consistently
     */
    handleAuthError(errorMessage = 'Your session has expired') {
        if (this.isHandlingAuthError) return; // Prevent multiple simultaneous handling
        
        this.isHandlingAuthError = true;
        
        console.log('Authentication error detected:', errorMessage);
        
        // Clear expired tokens and user data
        this.clearAuthData();
        
        // Show user-friendly message
        this.showAuthErrorMessage(errorMessage);
        
        // Redirect to login after a brief delay
        setTimeout(() => {
            this.redirectToLogin();
        }, 2000);
    }
    
    /**
     * Clear all authentication data
     */
    clearAuthData() {
        localStorage.removeItem(this.AUTH_TOKEN_KEY);
        localStorage.removeItem(this.USER_DATA_KEY);
        sessionStorage.removeItem(this.AUTH_TOKEN_KEY);
        sessionStorage.removeItem(this.USER_DATA_KEY);
    }
    
    /**
     * Show authentication error message to user
     */
    showAuthErrorMessage(message) {
        // Remove any existing auth error messages
        const existingMessage = document.getElementById('auth-error-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Create new error message
        const errorDiv = document.createElement('div');
        errorDiv.id = 'auth-error-message';
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10000;
            background: #ff4444;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif;
            font-size: 14px;
            text-align: center;
            max-width: 90%;
            animation: slideDown 0.3s ease-out;
        `;
        
        errorDiv.innerHTML = `
            <div style="margin-bottom: 8px; font-weight: bold;">⚠️ Authentication Error</div>
            <div>${message}</div>
            <div style="margin-top: 8px; font-size: 12px; opacity: 0.9;">Redirecting to login...</div>
        `;
        
        // Add CSS animation
        if (!document.getElementById('auth-error-styles')) {
            const style = document.createElement('style');
            style.id = 'auth-error-styles';
            style.textContent = `
                @keyframes slideDown {
                    from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
                    to { transform: translateX(-50%) translateY(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(errorDiv);
    }
    
    /**
     * Redirect to login page
     */
    redirectToLogin() {
        // Update URL to login page or reload to trigger login flow
        const currentUrl = window.location.href;
        
        if (currentUrl.includes('login') || currentUrl.includes('auth')) {
            // Already on login page, just reload
            window.location.reload();
        } else {
            // Redirect to login (adjust path as needed for your app structure)
            const loginUrl = this.getLoginUrl();
            window.location.href = loginUrl;
        }
        
        this.isHandlingAuthError = false;
    }
    
    /**
     * Get appropriate login URL based on current page
     */
    getLoginUrl() {
        const baseUrl = window.location.origin;
        
        // Check if we're in a customer app subdirectory
        if (window.location.pathname.includes('/customer')) {
            return `${baseUrl}/customer/login`;
        }
        
        // Default login page
        return `${baseUrl}/login`;
    }
    
    /**
     * Check authentication status on page load
     */
    checkAuthOnPageLoad() {
        const token = this.getAuthToken();
        
        if (!token) {
            // No token found, redirect to login
            this.handleAuthError('Please login to continue');
            return false;
        }
        
        // Validate token format
        if (!this.isValidTokenFormat(token)) {
            this.handleAuthError('Invalid authentication format');
            return false;
        }
        
        return true;
    }
    
    /**
     * Get authentication token from storage
     */
    getAuthToken() {
        return localStorage.getItem(this.AUTH_TOKEN_KEY) || 
               sessionStorage.getItem(this.AUTH_TOKEN_KEY);
    }
    
    /**
     * Validate token format (basic check)
     */
    isValidTokenFormat(token) {
        if (!token || typeof token !== 'string') return false;
        
        // JWT tokens have 3 parts separated by dots
        const parts = token.split('.');
        return parts.length === 3;
    }
    
    /**
     * Make authenticated API request with automatic error handling
     */
    async makeAuthenticatedRequest(url, options = {}) {
        const token = this.getAuthToken();
        
        if (!token) {
            this.handleAuthError('Authentication required');
            throw new Error('No authentication token available');
        }
        
        // Add auth header
        const authOptions = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, authOptions);
            
            // Handle auth errors
            if (response.status === 401) {
                const data = await response.clone().json();
                if (data.message && this.isAuthError(data.message)) {
                    this.handleAuthError(data.message);
                    throw new Error('Authentication failed');
                }
            }
            
            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    /**
     * Initialize auth error handling for a specific page
     */
    initPageAuth(pageName) {
        console.log(`Initializing authentication for ${pageName} page`);
        
        // Check if user is authenticated
        if (!this.checkAuthOnPageLoad()) {
            return false;
        }
        
        // Add auth status indicator
        this.addAuthStatusIndicator();
        
        return true;
    }
    
    /**
     * Add authentication status indicator to page
     */
    addAuthStatusIndicator() {
        const token = this.getAuthToken();
        const isAuthenticated = !!token;
        
        // Create status indicator
        const statusDiv = document.createElement('div');
        statusDiv.id = 'auth-status-indicator';
        statusDiv.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 9999;
            background: ${isAuthenticated ? '#4CAF50' : '#ff4444'};
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-family: Arial, sans-serif;
            opacity: 0.8;
        `;
        
        statusDiv.textContent = isAuthenticated ? '🔒 Authenticated' : '🔓 Not Authenticated';
        
        document.body.appendChild(statusDiv);
        
        // Auto-hide after 3 seconds
        setTimeout(() => {
            if (statusDiv.parentNode) {
                statusDiv.remove();
            }
        }, 3000);
    }
}

// Initialize global auth handler
window.AuthErrorHandler = new AuthErrorHandler();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AuthErrorHandler;
}