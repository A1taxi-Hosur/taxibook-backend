import { Coordinates } from '../types';
import { API_BASE_URL } from './api';

export interface Zone {
  id: string;
  name: string;
  polygon: Coordinates[];
  rings: {
    inner: Coordinates[];
    outer: Coordinates[];
  };
  active: boolean;
}

export interface ZoneResponse {
  zones: Zone[];
}

// Point-in-polygon algorithm using ray casting
export function isPointInPolygon(point: Coordinates, polygon: Coordinates[]): boolean {
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
    if (zone.active && isPointInPolygon(pickup, zone.polygon)) {
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
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch zones');
    }
    
    const allZones = await response.json();
    
    // Filter to get only active zones
    const activeZones = allZones.filter((zone: any) => zone.is_active);
    
    // Update cache
    zonesCache = activeZones;
    lastZonesFetch = now;
    
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
    if (zone.active && isPointInPolygon(pickup, zone.polygon)) {
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