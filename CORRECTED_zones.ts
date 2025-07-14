import { Coordinates } from '../types';
import { API_BASE_URL } from './api';

export interface Zone {
  id: number;  // Backend returns number, not string
  name: string;
  polygon: Coordinates[];
  rings: {
    inner: Coordinates[];
    outer: Coordinates[];
  };
  active: boolean;
  // Additional backend fields
  center_lat: number;
  center_lng: number;
  radius_km: number;
  number_of_rings: number;
  ring_radius_meters: number;
  ring_wait_time_seconds: number;
  expansion_delay_sec: number;
  priority_order: number;
}

export interface ZoneResponse {
  zones: Zone[];
}

// Backend API response format
interface BackendZone {
  id: number;
  zone_name: string;
  polygon_coordinates: number[][];  // Backend format: [[lat, lng], ...]
  is_active: boolean;
  center_lat: number;
  center_lng: number;
  radius_km: number;
  number_of_rings: number;
  ring_radius_meters: number;
  ring_wait_time_seconds: number;
  expansion_delay_sec: number;
  priority_order: number;
}

interface BackendZoneResponse {
  status: string;
  message: string;
  data: {
    zones: BackendZone[];
  };
}

// Convert backend coordinate format to frontend format
function convertCoordinates(backendCoords: number[][]): Coordinates[] {
  return backendCoords.map(([lat, lng]) => ({ lat, lng }));
}

// Convert backend zone to frontend zone format
function convertZone(backendZone: BackendZone): Zone {
  return {
    id: backendZone.id,
    name: backendZone.zone_name,
    polygon: convertCoordinates(backendZone.polygon_coordinates || []),
    rings: {
      inner: [], // Not used in current implementation
      outer: []  // Not used in current implementation
    },
    active: backendZone.is_active,
    center_lat: backendZone.center_lat,
    center_lng: backendZone.center_lng,
    radius_km: backendZone.radius_km,
    number_of_rings: backendZone.number_of_rings,
    ring_radius_meters: backendZone.ring_radius_meters,
    ring_wait_time_seconds: backendZone.ring_wait_time_seconds,
    expansion_delay_sec: backendZone.expansion_delay_sec,
    priority_order: backendZone.priority_order
  };
}

// Point-in-polygon algorithm using ray casting
export function isPointInPolygon(point: Coordinates, polygon: Coordinates[]): boolean {
  if (polygon.length < 3) return false; // Need at least 3 points for a polygon
  
  const { lat, lng } = point;
  let inside = false;
  
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].lng;
    const yi = polygon[i].lat;
    const xj = polygon[j].lng;
    const yj = polygon[j].lat;
    
    if (((yi > lat) !== (yj > lat)) && (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi)) {
      inside = !inside;
    }
  }
  
  return inside;
}

// Check if pickup location is within service zones
export function isPickupInServiceZone(pickup: Coordinates, zones: Zone[]): boolean {
  for (const zone of zones) {
    if (zone.active && zone.polygon.length > 0 && isPointInPolygon(pickup, zone.polygon)) {
      return true;
    }
  }
  return false;
}

// Cache for zones to prevent excessive API calls
let zonesCache: Zone[] | null = null;
let lastZonesFetch: number = 0;
const ZONES_CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Fetch active zones from backend with caching
export async function getActiveZones(): Promise<Zone[]> {
  const now = Date.now();
  
  // Return cached zones if still valid
  if (zonesCache && (now - lastZonesFetch) < ZONES_CACHE_DURATION) {
    return zonesCache;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/admin/api/zones`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const backendResponse: BackendZoneResponse = await response.json();
    
    // Check if backend response is successful
    if (backendResponse.status !== 'success') {
      throw new Error(`Backend error: ${backendResponse.message}`);
    }
    
    // Convert backend zones to frontend format
    const allZones = backendResponse.data.zones.map(convertZone);
    
    // Filter to get only active zones
    const activeZones = allZones.filter((zone: Zone) => zone.active);
    
    // Update cache
    zonesCache = activeZones;
    lastZonesFetch = now;
    
    console.log(`Fetched ${activeZones.length} active zones`);
    return activeZones;
  } catch (error) {
    console.error('Error fetching zones:', error);
    
    // Return cached zones if available, even if expired
    if (zonesCache) {
      console.log('Using cached zones due to network error');
      return zonesCache;
    }
    
    return [];
  }
}

// Check zone coverage and return detailed information
export interface ZoneCoverage {
  inServiceZone: boolean;
  zone?: Zone;
  message?: string;
}

export async function checkZoneCoverage(pickup: Coordinates): Promise<ZoneCoverage> {
  const zones = await getActiveZones();
  
  if (zones.length === 0) {
    return {
      inServiceZone: false,
      message: 'Unable to check service zones. Please try again.',
    };
  }
  
  for (const zone of zones) {
    if (zone.active && zone.polygon.length > 0 && isPointInPolygon(pickup, zone.polygon)) {
      return {
        inServiceZone: true,
        zone,
      };
    }
  }
  
  return {
    inServiceZone: false,
    message: 'We are currently not operating in this area.',
  };
}

// Clear zones cache (useful for testing or when zones are updated)
export function clearZonesCache(): void {
  zonesCache = null;
  lastZonesFetch = 0;
}

// Test function to verify zone API connection
export async function testZoneConnection(): Promise<boolean> {
  try {
    const zones = await getActiveZones();
    console.log('Zone connection test successful:', zones.length, 'zones loaded');
    return true;
  } catch (error) {
    console.error('Zone connection test failed:', error);
    return false;
  }
}