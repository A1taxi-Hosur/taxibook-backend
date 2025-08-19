<script>
// Global error handler for Google Maps API
window.gm_authFailure = function() {
    console.warn('Google Maps API authentication failed - billing not enabled');
    handleMapsUnavailable();
};

function handleMapsUnavailable() {
    document.getElementById('map').innerHTML = `
        <div class="text-center p-4">
            <i class="bi bi-map display-4 text-muted"></i>
            <p class="mt-2 text-muted">Google Maps not available</p>
            <small class="text-muted">You can still add zones using coordinates</small>
        </div>
    `;
    
    // Hide modal map as well
    const modalMap = document.getElementById('modalMap');
    if (modalMap) {
        modalMap.innerHTML = `
            <div class="text-center p-4">
                <i class="bi bi-map display-4 text-muted"></i>
                <p class="mt-2 text-muted">Map preview not available</p>
                <small class="text-muted">Enter coordinates manually</small>
            </div>
        `;
    }
}

// Initialize Google Maps or handle gracefully
function initializeGoogleMaps() {
    try {
        if (typeof google !== 'undefined' && google.maps) {
            initMap();
        } else {
            handleMapsUnavailable();
        }
    } catch (error) {
        console.warn('Google Maps initialization failed:', error);
        handleMapsUnavailable();
    }
}

// Load Google Maps API with error handling
if (typeof google === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://maps.googleapis.com/maps/api/js?key={{ google_maps_api_key }}&libraries=geometry,drawing&callback=initializeGoogleMaps';
    script.async = true;
    script.defer = true;
    script.onerror = function() {
        console.warn('Failed to load Google Maps API');
        handleMapsUnavailable();
    };
    document.head.appendChild(script);
} else {
    initializeGoogleMaps();
}
</script>
<script>
let selectedZoneId = null;

function refreshZones() {
    document.getElementById('zones-container').innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">Loading zones...</p>
        </div>
    `;
    
    fetch('/admin/api/zones', {
            method: 'GET',
            credentials: 'same-origin',  // Include cookies for authentication
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            console.log('Zone API Response Status:', response.status, response.statusText);
            if (response.status === 302) {
                // Session expired - redirect to login
                window.location.href = '/admin/login';
                return;
            }
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data) return; // Handle redirect case
            console.log('Zone API Data:', data);
            if (data.status === 'success') {
                displayZones(data.data.zones);
            } else {
                showError('Failed to load zones: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error loading zones:', error);
            showError('Network error: ' + error.message);
        });
}

function displayZones(zones) {
    const container = document.getElementById('zones-container');
    
    if (zones.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-geo-alt display-1 text-muted"></i>
                <p class="mt-3 text-muted">No zones configured yet</p>
                <button class="btn btn-primary" onclick="openAddZoneModal()">
                    <i class="bi bi-plus-circle"></i> Add First Zone
                </button>
            </div>
        `;
        return;
    }
    
    let html = '';
    zones.forEach(zone => {
        const statusBadge = zone.is_active ? 
            '<span class="badge bg-success">Active</span>' : 
            '<span class="badge bg-secondary">Inactive</span>';
        
        html += `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h5 class="card-title">
                                ${zone.zone_name}
                                ${statusBadge}
                            </h5>
                            <p class="card-text">
                                <strong>Center:</strong> ${zone.center_lat.toFixed(6)}, ${zone.center_lng.toFixed(6)}<br>
                                <strong>Radius:</strong> ${zone.radius_km} km<br>
                                <strong>Created:</strong> ${formatDateTime(zone.created_at)}
                            </p>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="btn-group" role="group">
                                <button class="btn btn-sm btn-outline-primary" onclick="editZone(${zone.id})">
                                    <i class="bi bi-pencil"></i> Edit
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteZone(${zone.id}, '${zone.zone_name}')">
                                    <i class="bi bi-trash"></i> Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function openAddZoneModal() {
    document.getElementById('zoneModalLabel').textContent = 'Add Zone';
    document.getElementById('zoneForm').reset();
    document.getElementById('zoneId').value = '';
    document.getElementById('isActive').checked = true;
    
    // Set default coordinates for Hosur
    document.getElementById('centerLat').value = '12.7400';
    document.getElementById('centerLng').value = '77.8253';
    document.getElementById('radiusKm').value = '5.0';
    
    const modal = new bootstrap.Modal(document.getElementById('zoneModal'));
    modal.show();
    
    // Initialize modal map when modal is shown
    const modalElement = document.getElementById('zoneModal');
    modalElement.addEventListener('shown.bs.modal', function () {
        setTimeout(() => {
            initModalMap();
        }, 100);
    }, { once: true });
}

function editZone(zoneId) {
    fetch(`/admin/api/zones/${zoneId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const zone = data.data;
                
                document.getElementById('zoneModalLabel').textContent = 'Edit Zone';
                document.getElementById('zoneId').value = zone.id;
                document.getElementById('zoneName').value = zone.zone_name;
                document.getElementById('centerLat').value = zone.center_lat;
                document.getElementById('centerLng').value = zone.center_lng;
                document.getElementById('radiusKm').value = zone.radius_km;
                document.getElementById('isActive').checked = zone.is_active;
                
                const modal = new bootstrap.Modal(document.getElementById('zoneModal'));
                modal.show();
                
                // Initialize modal map when modal is shown
                const modalElement = document.getElementById('zoneModal');
                modalElement.addEventListener('shown.bs.modal', function () {
                    setTimeout(() => {
                        initModalMap();
                        
                        // Center map on existing zone and add marker
                        const center = { lat: parseFloat(zone.center_lat), lng: parseFloat(zone.center_lng) };
                        modalMap.setCenter(center);
                        
                        // Add marker at existing location
                        if (window.modalMarker) {
                            window.modalMarker.setMap(null);
                        }
                        window.modalMarker = new google.maps.Marker({
                            position: center,
                            map: modalMap,
                            title: 'Zone Center'
                        });
                    }, 100);
                }, { once: true });
            } else {
                showError('Failed to load zone details');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Network error occurred');
        });
}

function deleteZone(zoneId, zoneName) {
    selectedZoneId = zoneId;
    
    document.getElementById('deleteZoneInfo').innerHTML = `
        <p><strong>Zone:</strong> ${zoneName}</p>
        <p><strong>ID:</strong> ${zoneId}</p>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('deleteZoneModal'));
    modal.show();
}

function confirmDeleteZone() {
    if (!selectedZoneId) {
        showError('No zone selected for deletion');
        return;
    }
    
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Deleting...';
    
    fetch(`/admin/api/zones/${selectedZoneId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccess('Zone deleted successfully');
            bootstrap.Modal.getInstance(document.getElementById('deleteZoneModal')).hide();
            refreshZones();
            loadZonesOnMap(); // Refresh map display
        } else {
            showError(data.message || 'Failed to delete zone');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Network error occurred');
    })
    .finally(() => {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="bi bi-trash"></i> Delete Zone';
    });
}

// Form submission handler
document.getElementById('zoneForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const saveBtn = document.getElementById('saveZoneBtn');
    
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Saving...';
    
    const data = {
        zone_name: formData.get('zone_name'),
        center_lat: parseFloat(formData.get('center_lat')),
        center_lng: parseFloat(formData.get('center_lng')),
        radius_km: parseFloat(formData.get('radius_km')),
        is_active: formData.get('is_active') === 'on'
    };
    
    // Add polygon coordinates if available
    if (polygonCoordinates.length > 0) {
        data.polygon_coordinates = polygonCoordinates;
    }
    
    // Add enhanced zone fields
    data.number_of_rings = parseInt(formData.get('number_of_rings')) || 3;
    data.ring_radius_km = parseFloat(formData.get('ring_radius_km')) || 2.0;
    data.ring_radius_meters = parseInt(formData.get('ring_radius_meters')) || 1000;
    data.ring_wait_time_seconds = parseInt(formData.get('ring_wait_time_seconds')) || 15;
    data.expansion_delay_sec = parseInt(formData.get('expansion_delay_sec')) || 15;
    data.priority_order = parseInt(formData.get('priority_order')) || 1;
    
    const zoneId = formData.get('zone_id');
    const isEdit = zoneId && zoneId !== '';
    
    const url = isEdit ? `/admin/api/zones/${zoneId}` : '/admin/api/zones';
    const method = isEdit ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showSuccess(isEdit ? 'Zone updated successfully' : 'Zone created successfully');
            bootstrap.Modal.getInstance(document.getElementById('zoneModal')).hide();
            refreshZones();
            loadZonesOnMap(); // Refresh map display
        } else {
            showError(data.message || `Failed to ${isEdit ? 'update' : 'create'} zone`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Network error occurred');
    })
    .finally(() => {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-save"></i> Save Zone';
    });
});

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function showError(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const main = document.querySelector('main .pt-3');
    main.insertBefore(alert, main.firstChild);
}

function showSuccess(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const main = document.querySelector('main .pt-3');
    main.insertBefore(alert, main.firstChild);
}

// Initialize Google Maps (if available)
let map;
let modalMap;
let zoneCircles = [];

function initMap() {
    if (typeof google !== 'undefined' && google.maps) {
        // Initialize main map
        map = new google.maps.Map(document.getElementById('map'), {
            zoom: 12,
            center: { lat: 12.7400, lng: 77.8253 }, // Hosur coordinates
            mapTypeId: 'roadmap'
        });
        
        // Load and display existing zones
        loadZonesOnMap();
    }
}

function initModalMap() {
    if (typeof google !== 'undefined' && google.maps) {
        modalMap = new google.maps.Map(document.getElementById('modalMap'), {
            zoom: 12,
            center: { lat: 12.7400, lng: 77.8253 }, // Hosur coordinates
            mapTypeId: 'roadmap'
        });
        
        // Initialize drawing manager
        initDrawingManager();
        
        // Add click listener to set coordinates
        modalMap.addListener('click', function(e) {
            document.getElementById('centerLat').value = e.latLng.lat().toFixed(6);
            document.getElementById('centerLng').value = e.latLng.lng().toFixed(6);
            
            // Add marker at clicked location
            if (window.modalMarker) {
                window.modalMarker.setMap(null);
            }
            window.modalMarker = new google.maps.Marker({
                position: e.latLng,
                map: modalMap,
                title: 'Zone Center'
            });
        });
    }
}

function loadZonesOnMap() {
    fetch('/admin/api/zones')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayZonesOnMap(data.data.zones);
            }
        })
        .catch(error => {
            console.error('Error loading zones for map:', error);
        });
}

function displayZonesOnMap(zones) {
    // Clear existing circles
    zoneCircles.forEach(circle => circle.setMap(null));
    zoneCircles = [];
    
    // Add circles for each zone
    zones.forEach(zone => {
        const circle = new google.maps.Circle({
            strokeColor: zone.is_active ? '#0066CC' : '#999999',
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: zone.is_active ? '#0066CC' : '#999999',
            fillOpacity: 0.15,
            map: map,
            center: { lat: zone.center_lat, lng: zone.center_lng },
            radius: zone.radius_km * 1000 // Convert km to meters
        });
        
        // Add info window
        const infoWindow = new google.maps.InfoWindow({
            content: `
                <div>
                    <h6>${zone.zone_name}</h6>
                    <p>Radius: ${zone.radius_km} km<br>
                    Status: ${zone.is_active ? 'Active' : 'Inactive'}</p>
                </div>
            `
        });
        
        circle.addListener('click', function() {
            infoWindow.setPosition(circle.getCenter());
            infoWindow.open(map);
        });
        
        zoneCircles.push(circle);
    });
}

// Drawing Manager and Shape Handling
let drawingManager;
let currentShape = null;
let polygonCoordinates = [];

function initDrawingManager() {
    if (typeof google !== 'undefined' && google.maps && google.maps.drawing) {
        drawingManager = new google.maps.drawing.DrawingManager({
            drawingMode: null,
            drawingControl: false,
            circleOptions: {
                fillColor: '#ff0000',
                fillOpacity: 0.2,
                strokeWeight: 2,
                clickable: false,
                editable: true,
                zIndex: 1
            },
            polygonOptions: {
                fillColor: '#ff0000',
                fillOpacity: 0.2,
                strokeWeight: 2,
                clickable: false,
                editable: true,
                zIndex: 1
            }
        });
        
        drawingManager.setMap(modalMap);
        
        // Handle shape completion
        google.maps.event.addListener(drawingManager, 'circlecomplete', function(circle) {
            if (currentShape) {
                currentShape.setMap(null);
            }
            currentShape = circle;
            
            // Update form fields with circle center and radius
            const center = circle.getCenter();
            const radius = circle.getRadius() / 1000; // Convert to km
            
            document.getElementById('centerLat').value = center.lat().toFixed(6);
            document.getElementById('centerLng').value = center.lng().toFixed(6);
            document.getElementById('radiusKm').value = radius.toFixed(2);
            
            // Clear polygon coordinates
            polygonCoordinates = [];
            
            // Stop drawing
            drawingManager.setDrawingMode(null);
            
            // Update button states
            updateDrawingButtons();
        });
        
        google.maps.event.addListener(drawingManager, 'polygoncomplete', function(polygon) {
            if (currentShape) {
                currentShape.setMap(null);
            }
            currentShape = polygon;
            
            // Get polygon coordinates
            const path = polygon.getPath();
            polygonCoordinates = [];
            
            for (let i = 0; i < path.getLength(); i++) {
                const point = path.getAt(i);
                polygonCoordinates.push([point.lat(), point.lng()]);
            }
            
            // Calculate polygon center
            let centerLat = 0;
            let centerLng = 0;
            
            polygonCoordinates.forEach(coord => {
                centerLat += coord[0];
                centerLng += coord[1];
            });
            
            centerLat /= polygonCoordinates.length;
            centerLng /= polygonCoordinates.length;
            
            document.getElementById('centerLat').value = centerLat.toFixed(6);
            document.getElementById('centerLng').value = centerLng.toFixed(6);
            
            // Stop drawing
            drawingManager.setDrawingMode(null);
            
            // Update button states
            updateDrawingButtons();
        });
        
        // Initialize drawing buttons
        setupDrawingButtons();
    } else {
        console.error('Google Maps Drawing Library not available');
    }
}

function setupDrawingButtons() {
    // Circle drawing button
    document.getElementById('drawCircleBtn').addEventListener('click', function() {
        if (drawingManager) {
            drawingManager.setDrawingMode(google.maps.drawing.OverlayType.CIRCLE);
            updateDrawingButtons('circle');
        }
    });
    
    // Polygon drawing button
    document.getElementById('drawPolygonBtn').addEventListener('click', function() {
        if (drawingManager) {
            drawingManager.setDrawingMode(google.maps.drawing.OverlayType.POLYGON);
            updateDrawingButtons('polygon');
        }
    });
    
    // Clear shapes button
    document.getElementById('clearShapesBtn').addEventListener('click', function() {
        if (currentShape) {
            currentShape.setMap(null);
            currentShape = null;
        }
        if (drawingManager) {
            drawingManager.setDrawingMode(null);
        }
        polygonCoordinates = [];
        updateDrawingButtons();
    });
}

function updateDrawingButtons(activeMode = null) {
    const circleBtn = document.getElementById('drawCircleBtn');
    const polygonBtn = document.getElementById('drawPolygonBtn');
    const clearBtn = document.getElementById('clearShapesBtn');
    
    // Reset button states
    circleBtn.classList.remove('active');
    polygonBtn.classList.remove('active');
    
    // Set active state
    if (activeMode === 'circle') {
        circleBtn.classList.add('active');
    } else if (activeMode === 'polygon') {
        polygonBtn.classList.add('active');
    }
    
    // Enable/disable clear button
    clearBtn.disabled = !currentShape;
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    refreshZones();
});

// Initialize map when Google Maps API is loaded
function initializeGoogleMaps() {
    initMap();
}

// Wait for Google Maps to load
window.addEventListener('load', function() {
    // Check if Google Maps is available
    if (typeof google !== 'undefined' && google.maps) {
        initMap();
    } else {
        // Wait for Google Maps to load
        let attempts = 0;
        const maxAttempts = 30; // 3 seconds total
        
        const checkGoogleMaps = () => {
            attempts++;
            if (typeof google !== 'undefined' && google.maps) {
                clearInterval(checkGoogleMaps);
                initMap();
            } else if (attempts >= maxAttempts) {
                clearInterval(checkGoogleMaps);
                // Fallback if Google Maps is not available
                document.getElementById('map').innerHTML = `
                    <div class="text-center p-4">
                        <i class="bi bi-map display-4 text-muted"></i>
                        <p class="mt-2 text-muted">Google Maps not available</p>
                        <small class="text-muted">You can still add zones using coordinates</small>
                    </div>
                `;
            }
        }, 100);
    }
});
</script>
<script>
// Load zones when page loads
document.addEventListener('DOMContentLoaded', function() {
    refreshZones();
});
</script>
