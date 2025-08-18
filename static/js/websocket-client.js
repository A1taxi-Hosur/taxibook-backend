/**
 * WebSocket Client for A1 Taxi Platform
 * Handles real-time communication for admin dashboard, live map, and mobile apps
 */

class WebSocketClient {
    constructor(config = {}) {
        this.config = {
            serverUrl: window.location.origin,
            autoConnect: true,
            reconnectInterval: 5000,
            maxReconnectAttempts: 10,
            debug: false,
            ...config
        };
        
        this.socket = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.eventHandlers = {};
        this.connectionType = null;
        this.authToken = null;
        
        if (this.config.autoConnect) {
            this.connect();
        }
    }
    
    /**
     * Connect to WebSocket server
     */
    connect(authToken = null) {
        if (this.socket && this.connected) {
            this.log('Already connected');
            return;
        }
        
        this.authToken = authToken;
        this.log('Connecting to WebSocket server...');
        
        // Import Socket.IO library
        if (typeof io === 'undefined') {
            console.error('Socket.IO library not loaded');
            return;
        }
        
        const socketConfig = {
            transports: ['websocket', 'polling'],
            upgrade: true,
            rememberUpgrade: true,
            timeout: 10000,           // 10 second connection timeout
            forceNew: false,          // Reuse connections when possible
            multiplex: true,          // Share connection across namespaces
            reconnection: true,       // Enable auto-reconnection
            reconnectionAttempts: 5,  // Limit reconnection attempts
            reconnectionDelay: 2000,  // 2 second delay between attempts
            maxReconnectionAttempts: 5
        };
        
        // Add auth token if provided
        if (authToken) {
            socketConfig.auth = {
                token: authToken
            };
            socketConfig.extraHeaders = {
                'Authorization': `Bearer ${authToken}`
            };
        }
        
        this.socket = io(this.config.serverUrl, socketConfig);
        
        this.setupEventListeners();
    }
    
    /**
     * Setup Socket.IO event listeners
     */
    setupEventListeners() {
        this.socket.on('connect', () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            this.log('Connected to WebSocket server');
            this.trigger('connected');
        });
        
        this.socket.on('disconnect', (reason) => {
            this.connected = false;
            this.log(`Disconnected from WebSocket server: ${reason}`);
            this.trigger('disconnected', reason);
            
            // Auto-reconnect if connection lost unexpectedly
            if (reason === 'io server disconnect' || reason === 'io client disconnect') {
                this.scheduleReconnect();
            }
        });
        
        this.socket.on('connect_error', (error) => {
            this.log(`Connection error: ${error.message}`);
            this.trigger('connection_error', error);
            this.scheduleReconnect();
        });
        
        this.socket.on('error', (data) => {
            this.log(`Server error: ${data.message}`);
            this.trigger('server_error', data);
        });
        
        this.socket.on('connection_established', (data) => {
            this.log('Connection established:', data);
            this.connectionType = data.type || 'unknown';
            this.trigger('connection_established', data);
        });
        
        // Driver location updates
        this.socket.on('driver_location_updated', (data) => {
            this.trigger('driver_location_updated', data);
        });
        
        // Ride status updates
        this.socket.on('ride_status_updated', (data) => {
            this.trigger('ride_status_updated', data);
        });
        
        // Dashboard stats updates
        this.socket.on('dashboard_stats_updated', (data) => {
            this.trigger('dashboard_stats_updated', data);
        });
        
        // Driver list updates for live map
        this.socket.on('driver_list_updated', (data) => {
            this.trigger('driver_list_updated', data);
        });
        
        // New ride requests (for drivers)
        this.socket.on('new_ride_request', (data) => {
            this.trigger('new_ride_request', data);
        });
    }
    
    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
            this.log('Max reconnection attempts reached');
            this.trigger('max_reconnect_attempts_reached');
            return;
        }
        
        this.reconnectAttempts++;
        this.log(`Scheduling reconnection attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts}`);
        
        setTimeout(() => {
            if (!this.connected) {
                this.connect(this.authToken);
            }
        }, this.config.reconnectInterval);
    }
    
    /**
     * Connect as admin dashboard
     */
    connectAsAdmin() {
        this.connect();
        this.socket.emit('admin_connect', {});
    }
    
    /**
     * Connect as live map viewer
     */
    connectAsLiveMap() {
        this.connect();
        this.socket.emit('live_map_connect', {});
    }
    
    /**
     * Connect as driver with authentication
     */
    connectAsDriver(authToken, driverPhone = null) {
        this.connect(authToken);
        // Extract phone from token or use provided phone
        const connectData = {};
        
        // Try to get driver phone from JWT token
        if (authToken) {
            try {
                const tokenPayload = JSON.parse(atob(authToken.split('.')[1]));
                if (tokenPayload.phone) {
                    connectData.driver_phone = tokenPayload.phone;
                }
            } catch (e) {
                console.debug('Could not parse JWT token for phone');
            }
        }
        
        // Use provided phone if available
        if (driverPhone) {
            connectData.driver_phone = driverPhone;
        }
        
        this.socket.emit('driver_connect', connectData);
    }
    
    /**
     * Connect as customer with authentication
     */
    connectAsCustomer(authToken) {
        this.connect(authToken);
        this.socket.emit('customer_connect', {});
    }
    
    /**
     * Send driver location update
     */
    updateDriverLocation(locationData) {
        if (!this.connected) {
            this.log('Not connected - cannot send location update');
            return false;
        }
        
        this.socket.emit('driver_location_update', locationData);
        return true;
    }
    
    /**
     * Send driver status change
     */
    updateDriverStatus(status) {
        if (!this.connected) {
            this.log('Not connected - cannot send status update');
            return false;
        }
        
        this.socket.emit('driver_status_change', { status });
        return true;
    }
    
    /**
     * Register event handler
     */
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }
    
    /**
     * Remove event handler
     */
    off(event, handler) {
        if (!this.eventHandlers[event]) return;
        
        const index = this.eventHandlers[event].indexOf(handler);
        if (index > -1) {
            this.eventHandlers[event].splice(index, 1);
        }
    }
    
    /**
     * Trigger event handlers
     */
    trigger(event, data = null) {
        if (!this.eventHandlers[event]) return;
        
        this.eventHandlers[event].forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`Error in event handler for ${event}:`, error);
            }
        });
    }
    
    /**
     * Disconnect from server
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.connected = false;
        this.connectionType = null;
    }
    
    /**
     * Get connection status
     */
    isConnected() {
        return this.connected && this.socket && this.socket.connected;
    }
    
    /**
     * Get connection info
     */
    getConnectionInfo() {
        return {
            connected: this.connected,
            connectionType: this.connectionType,
            reconnectAttempts: this.reconnectAttempts,
            socketId: this.socket ? this.socket.id : null
        };
    }
    
    /**
     * Debug logging
     */
    log(message, data = null) {
        if (!this.config.debug) return;
        
        const timestamp = new Date().toISOString();
        console.log(`[WebSocket ${timestamp}] ${message}`, data || '');
    }
}

// Global WebSocket client instance
window.wsClient = null;

/**
 * Initialize WebSocket client for admin dashboard
 */
function initAdminWebSocket() {
    if (window.wsClient) {
        window.wsClient.disconnect();
    }
    
    window.wsClient = new WebSocketClient({ 
        debug: true,
        autoConnect: false 
    });
    
    // Setup admin-specific event handlers
    window.wsClient.on('connected', () => {
        console.log('✅ Admin WebSocket connected');
    });
    
    window.wsClient.on('driver_location_updated', (data) => {
        console.log('📍 Driver location updated:', data);
        // Update live map if it exists
        if (typeof updateDriverMarker === 'function') {
            updateDriverMarker(data);
        }
    });
    
    window.wsClient.on('dashboard_stats_updated', (data) => {
        console.log('📊 Dashboard stats updated:', data);
        // Update dashboard stats if the function exists
        if (typeof updateDashboardStats === 'function') {
            updateDashboardStats(data);
        }
    });
    
    window.wsClient.on('ride_status_updated', (data) => {
        console.log('🚗 Ride status updated:', data);
        // Refresh dashboard if needed
        if (typeof refreshStats === 'function') {
            refreshStats();
        }
    });
    
    // Connect as admin
    window.wsClient.connectAsAdmin();
}

/**
 * Initialize WebSocket client for live map
 */
function initLiveMapWebSocket() {
    if (window.wsClient) {
        window.wsClient.disconnect();
    }
    
    window.wsClient = new WebSocketClient({ 
        debug: true,
        autoConnect: false 
    });
    
    // Setup live map specific event handlers
    window.wsClient.on('connected', () => {
        console.log('✅ Live Map WebSocket connected');
    });
    
    window.wsClient.on('driver_location_updated', (data) => {
        console.log('📍 Driver location updated:', data);
        // Update map markers in real-time
        if (typeof updateDriverMarker === 'function') {
            updateDriverMarker(data);
        }
    });
    
    window.wsClient.on('driver_list_updated', (data) => {
        console.log('👥 Driver list updated:', data);
        // Refresh entire driver list
        if (typeof refreshDriverList === 'function') {
            refreshDriverList(data);
        }
    });
    
    // Connect as live map viewer
    window.wsClient.connectAsLiveMap();
}

/**
 * Initialize WebSocket client for driver app
 */
function initDriverWebSocket(authToken, driverPhone = null) {
    if (window.wsClient) {
        window.wsClient.disconnect();
    }
    
    window.wsClient = new WebSocketClient({ 
        debug: true,
        autoConnect: false 
    });
    
    // Setup driver-specific event handlers
    window.wsClient.on('connected', () => {
        console.log('✅ Driver WebSocket connected');
    });
    
    window.wsClient.on('connection_established', (data) => {
        console.log('🔗 Driver connection established:', data);
    });
    
    window.wsClient.on('location_update_confirmed', (data) => {
        console.log('📍 Location update confirmed:', data);
    });
    
    window.wsClient.on('new_ride_request', (data) => {
        console.log('🚗 New ride request:', data);
        // Handle new ride request notification
        if (typeof handleNewRideRequest === 'function') {
            handleNewRideRequest(data);
        }
    });
    
    window.wsClient.on('ride_status_updated', (data) => {
        console.log('🚗 Ride status updated:', data);
        // Update current ride status
        if (typeof updateRideStatus === 'function') {
            updateRideStatus(data);
        }
    });
    
    window.wsClient.on('error', (data) => {
        console.error('❌ WebSocket error:', data);
    });
    
    // Connect as driver with phone identification
    window.wsClient.connectAsDriver(authToken, driverPhone);
}