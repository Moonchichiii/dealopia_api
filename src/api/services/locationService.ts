import axios from 'axios';
import { axiosInstance } from '@/api/client';
import { Location } from '@/types/locations';
import { ENDPOINTS } from '@/api/endpoints';

type LocationStats = {
  total_locations: number;
  countries_count: number;
  cities_count: number;
  top_countries: unknown[];
}

type GeocodedAddress = {
  address: string;
  city: string | undefined;
  state: string | undefined;
  country: string | undefined;
  postal_code: string | undefined;
}

// Separated instance for external apis
const externalApiClient = axios.create({
  timeout: 10000,
  headers: { Accept: 'application/json' },
});

const locationService = {
  getLocation: async (id: string | number): Promise<Location | null> => {
    if (!id) return null;
    try {
      const response = await axiosInstance.get<Location>(ENDPOINTS.LOCATIONS.DETAIL(id));
      return response.data;
    } catch (error) {
      console.error('Location service error:', error);
      return null;
    }
  },

  getLocations: async (search?: string): Promise<Location[]> => {
    try {
      const params = search ? { search } : undefined;
      const response = await axiosInstance.get<Location[]>(ENDPOINTS.LOCATIONS.BASE, { params });
      return response.data;
    } catch (error) {
      console.error('Location service error:', error);
      return [];
    }
  },

  getNearbyLocations: async (
    latitude: number,
    longitude: number,
    radius = 10
  ): Promise<Location[]> => {
    try {
      console.info(`Executing PostGIS spatial query: Locations within ${radius}km of (${latitude.toFixed(6)}, ${longitude.toFixed(6)})`);
      
      const safeRadius = Math.max(0.1, Math.min(radius, 50));
      const startTime = performance.now();
      
      const response = await axiosInstance.get<Location[]>(
        ENDPOINTS.LOCATIONS.NEARBY,
        { params: { lat: latitude, lng: longitude, radius: safeRadius } }
      );
      
      const queryTime = (performance.now() - startTime).toFixed(2);
      console.info(`PostGIS spatial query completed in ${queryTime}ms, found ${response.data.length} locations`);
      
      // Track PostGIS usage if needed
      if (typeof window !== 'undefined') {
        window._postgisQueriesCount = (window._postgisQueriesCount || 0) + 1;
      }
      
      return response.data;
    } catch (error) {
      console.error('PostGIS spatial query failed:', error);
      return [];
    }
  },

  getPopularCities: async (country?: string, limit = 10): Promise<unknown[]> => {
    try {
      const safeLimit = Math.min(Math.max(1, limit), 50);
      const params: Record<string, unknown> = { limit: safeLimit };
      if (country) params.country = country;
      
      const response = await axiosInstance.get<unknown[]>(
        `${ENDPOINTS.LOCATIONS.BASE}popular_cities/`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Location service error:', error);
      return [];
    }
  },

  getLocationStats: async (): Promise<LocationStats> => {
    try {
      const response = await axiosInstance.get<LocationStats>(`${ENDPOINTS.LOCATIONS.BASE}stats/`);
      return response.data;
    } catch (error) {
      console.error('Location service error:', error);
      return {
        total_locations: 0,
        countries_count: 0,
        cities_count: 0,
        top_countries: [],
      };
    }
  },

  geocodeAddress: async (
    address: string
  ): Promise<{ latitude: number; longitude: number } | null> => {
    try {
      const response = await externalApiClient.get('https://nominatim.openstreetmap.org/search', {
        params: { q: address, format: 'json', limit: 1 },
      });
      
      if (response.data?.length > 0) {
        const { lat, lon } = response.data[0];
        return { latitude: parseFloat(lat), longitude: parseFloat(lon) };
      }
      return null;
    } catch (error) {
      console.error('Geocoding error:', error);
      return null;
    }
  },

  reverseGeocode: async (
    latitude: number,
    longitude: number
  ): Promise<GeocodedAddress | null> => {
    try {
      const response = await externalApiClient.get('https://nominatim.openstreetmap.org/reverse', {
        params: { lat: latitude, lon: longitude, format: 'json' },
      });
      
      if (response.data?.address) {
        const { address } = response.data;
        return {
          address: [address.road, address.house_number].filter(Boolean).join(' '),
          city: address.city || address.town || address.village,
          state: address.state,
          country: address.country,
          postal_code: address.postcode,
        };
      }
      return null;
    } catch (error) {
      console.error('Reverse geocoding error:', error);
      return null;
    }
  },

  calculateDistance: (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const earthRadius = 6371; // km
    const toRadians = (degrees: number) => (degrees * Math.PI) / 180;
    
    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);
    
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(dLon / 2) ** 2;
      
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return earthRadius * c;
  },

  formatLocation: (location: Location | null): string => {
    if (!location) return '';
    return [location.city, location.state, location.country].filter(Boolean).join(', ');
  },
};

export { locationService };
export default locationService;