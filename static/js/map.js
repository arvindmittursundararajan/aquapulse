// === MINIMAL MAP WITH BASIC FUNCTIONALITY ===

let map;
let markers = [];

// Initialize the map
function initMap() {
    console.log('🗺️ Initializing Map...');
    
    // Create map with minimal styling
    map = L.map('pollution-map', {
        center: [20, 0],
            zoom: 2,
        zoomControl: false,
        attributionControl: false
        });

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        opacity: 0.9
    }).addTo(map);

    // Add zoom controls
        L.control.zoom({
        position: 'topright'
    }).addTo(map);

    // Load sensor data and create markers
    loadSensorData();
    
    console.log('✅ Map Initialized!');
}

// Load sensor data and create markers
function loadSensorData() {
    fetch('/api/sensor-data')
        .then(response => response.json())
        .then(data => {
            console.log('📊 Loading sensor data:', data.length, 'sensors');
            createSensorMarkers(data);
        })
        .catch(error => {
            console.error('❌ Error loading sensor data:', error);
            // No fallback to demo data
        });
}

// Create sensor markers
function createSensorMarkers(sensorData) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    sensorData.forEach((sensor, index) => {
        const marker = createMarker(sensor, index);
        markers.push(marker);
        marker.addTo(map);

        // Add click event
        marker.on('click', () => showSensorDetails(sensor));
        });

    console.log(`✅ Created ${markers.length} sensor markers`);
    }

// Create marker
function createMarker(sensor, index) {
    const pollutionLevel = sensor.pollution_level;
    const color = getPollutionColor(pollutionLevel);
    const size = getPollutionSize(pollutionLevel);
    
    // Create custom icon
    const icon = L.divIcon({
        className: 'sensor-marker',
            html: `
            <div class="marker-container" style="
                width: ${size}px; 
                height: ${size}px; 
                background: ${color};
                    border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                position: relative;
            ">
                <div class="marker-data" style="
                    position: absolute;
                    top: -25px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0,0,0,0.8);
                    color: white;
                    padding: 3px 6px;
                    border-radius: 3px;
                    font-size: 9px;
                    white-space: nowrap;
                    opacity: 0;
                    transition: opacity 0.2s;
                ">${sensor.location}<br>Level: ${pollutionLevel}</div>
                </div>
            `,
        iconSize: [size + 10, size + 10],
        iconAnchor: [(size + 10) / 2, (size + 10) / 2]
        });
    
    const marker = L.marker([sensor.lat, sensor.lng], { icon: icon });
    
    // Add hover effects
    marker.on('mouseover', function() {
        const markerElement = this.getElement();
        if (markerElement) {
            const dataElement = markerElement.querySelector('.marker-data');
            if (dataElement) dataElement.style.opacity = '1';
        }
    });
    
    marker.on('mouseout', function() {
        const markerElement = this.getElement();
        if (markerElement) {
            const dataElement = markerElement.querySelector('.marker-data');
            if (dataElement) dataElement.style.opacity = '0';
        }
    });
    
    return marker;
}

// Get pollution color
function getPollutionColor(level) {
    if (level <= 3) return '#10b981'; // Green
    if (level <= 7) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
}

// Get pollution size
function getPollutionSize(level) {
    return Math.max(6, Math.min(14, level * 1.2));
}

// Show sensor details
function showSensorDetails(sensor) {
    const modal = new bootstrap.Modal(document.getElementById('sensorModal'));
    document.getElementById('sensorModalTitle').textContent = `Sensor: ${sensor.location}`;
    document.getElementById('sensorModalBody').innerHTML = `
        <div class="sensor-details">
            <div class="row">
                <div class="col-md-6">
                    <h6>Location</h6>
                    <p>${sensor.location}</p>
                    <h6>Coordinates</h6>
                    <p>${sensor.lat.toFixed(4)}, ${sensor.lng.toFixed(4)}</p>
                    <h6>Status</h6>
                    <span class="badge bg-${sensor.status === 'active' ? 'success' : 'warning'}">${sensor.status}</span>
                </div>
                <div class="col-md-6">
                    <h6>Pollution Level</h6>
                    <div class="progress mb-2">
                        <div class="progress-bar bg-${sensor.pollution_level > 7 ? 'danger' : sensor.pollution_level > 4 ? 'warning' : 'success'}" 
                             style="width: ${sensor.pollution_level * 10}%"></div>
                    </div>
                    <p>Level: ${sensor.pollution_level}/10</p>
                    <h6>Microplastics</h6>
                    <p>${sensor.microplastics} particles/L</p>
                    </div>
                </div>
            </div>
        `;
    modal.show();
}

// Toggle map layer
function toggleMapLayer() {
    console.log('🗺️ Toggling map layer...');
    // Add layer switching functionality here
}

// Refresh data
function refreshData() {
    console.log('🔄 Refreshing map data...');
    loadSensorData();
    }

// Cleanup function
function cleanupMap() {
    // Clear markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 DOM loaded, initializing map...');
    initMap();
});

// Export functions for global access
window.initMap = initMap;
window.toggleMapLayer = toggleMapLayer;
window.refreshData = refreshData;
window.cleanupMap = cleanupMap;
