import { axiosInstance } from '@/api/client';
import { Deal, DealFilters } from '@/types/deals';
import { ENDPOINTS } from '@/api/endpoints';

interface DealResponse {
  results: Deal[];
  count: number;
}

const validateCoordinates = (lat?: number | null, lng?: number | null): boolean => {
  if (lat === undefined || lat === null || lng === undefined || lng === null) {
    return false;
  }

  return (
    !isNaN(lat) &&
    !isNaN(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180
  );
};

const dealService = {
  getDeals: async (filters?: DealFilters): Promise<DealResponse> => {
    try {
      const response = await axiosInstance.get<DealResponse>(
        ENDPOINTS.DEALS.BASE,
        { params: filters }
      );
      return response.data;
    } catch (error) {
      console.error('Deal API error:', error);
      return { results: [], count: 0 };
    }
  },

  getDeal: async (id: string | number): Promise<Deal | null> => {
    if (!id) return null;
    try {
      const response = await axiosInstance.get<Deal>(ENDPOINTS.DEALS.DETAIL(id));
      return response.data;
    } catch (error) {
      console.error('Deal API error:', error);
      return null;
    }
  },

  getFeaturedDeals: async (limit = 6): Promise<Deal[]> => {
    try {
      const response = await axiosInstance.get<Deal[]>(
        ENDPOINTS.DEALS.FEATURED,
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      console.error('Deal API error:', error);
      return [];
    }
  },

  getEndingSoonDeals: async (days = 3, limit = 6): Promise<Deal[]> => {
    try {
      const response = await axiosInstance.get<Deal[]>(
        ENDPOINTS.DEALS.ENDING_SOON,
        { params: { days, limit } }
      );
      return response.data;
    } catch (error) {
      console.error('Deal API error:', error);
      return [];
    }
  },

  getNearbyDeals: async (latitude: number | null, longitude: number | null, radius = 10): Promise<Deal[]> => {
    try {
      if (!validateCoordinates(latitude, longitude)) {
        console.warn('Invalid coordinates for getNearbyDeals:', { latitude, longitude });
        return [];
      }

      const params = {
        latitude: Number(latitude).toFixed(6),
        longitude: Number(longitude).toFixed(6),
        radius: Math.max(0.1, Math.min(radius, 50)).toFixed(1),
      };

      const response = await axiosInstance.get<Deal[] | DealResponse>(
        ENDPOINTS.DEALS.NEARBY,
        { params }
      );
      
      const data = response.data;
      
      if (Array.isArray(data)) {
        return data;
      } else if (data && 'results' in data) {
        return data.results;
      }

      return [];
    } catch (error) {
      console.error('getNearbyDeals error:', error);
      return [];
    }
  },

  searchDeals: async (query: string, filters?: DealFilters): Promise<DealResponse> => {
    if (!query || query.length < 2) return { results: [], count: 0 };
    try {
      const mergedFilters = { search: query, ...filters };
      const response = await axiosInstance.get<DealResponse>(
        ENDPOINTS.DEALS.BASE,
        { params: mergedFilters }
      );
      return response.data;
    } catch (error) {
      console.error('Deal API error:', error);
      return { results: [], count: 0 };
    }
  },

  searchDealsWithLocation: async (
    query: string = '',
    latitude?: number | null,
    longitude?: number | null,
    radius: number = 10,
    additionalFilters: DealFilters = {}
  ): Promise<DealResponse> => {
    try {
      if (validateCoordinates(latitude, longitude)) {
        if (!query || query.length < 2) {
          const deals = await dealService.getNearbyDeals(latitude, longitude, radius);
          return {
            results: deals,
            count: deals.length
          };
        }

        const filters: DealFilters = {
          ...additionalFilters,
          search: query,
          latitude,
          longitude,
          radius
        };

        const response = await axiosInstance.get<DealResponse>(
          ENDPOINTS.DEALS.BASE,
          { params: filters }
        );
        return response.data;
      }

      return await dealService.searchDeals(query, additionalFilters);
    } catch (error) {
      console.error('Deal API error:', error);
      return { results: [], count: 0 };
    }
  },

  trackDealView: async (id: string | number): Promise<boolean> => {
    try {
      await axiosInstance.post(ENDPOINTS.DEALS.TRACK_VIEW(id));
      return true;
    } catch (error) {
      console.warn('Failed to track deal view:', error);
      return false;
    }
  },

  trackDealClick: async (id: string | number): Promise<boolean> => {
    try {
      await axiosInstance.post(ENDPOINTS.DEALS.TRACK_CLICK(id));
      return true;
    } catch (error) {
      console.warn('Failed to track deal click:', error);
      return false;
    }
  },

  getRelatedDeals: async (dealId: string | number, limit = 3): Promise<Deal[]> => {
    try {
      const response = await axiosInstance.get<Deal[]>(
        ENDPOINTS.DEALS.RELATED(dealId),
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      console.error('Deal API error:', error);
      return [];
    }
  },

  getCategoryDeals: async (categoryId: string | number, limit = 12): Promise<Deal[]> => {
    if (!categoryId) return [];
    try {
      const response = await axiosInstance.get<Deal[]>(
        ENDPOINTS.CATEGORIES.DEALS(categoryId),
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      console.error('Deal API error:', error);
      return [];
    }
  },

  getShopDeals: async (shopId: string | number, limit = 12): Promise<Deal[]> => {
    if (!shopId) return [];
    try {
      const response = await axiosInstance.get<Deal[]>(
        ENDPOINTS.SHOPS.DEALS(shopId),
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      console.error('Deal API error:', error);
      return [];
    }
  },

  toggleFavorite: async (dealId: string | number, isFavorite: boolean): Promise<unknown> => {
    try {
      const method = isFavorite ? 'post' : 'delete';
      const endpoint = isFavorite 
        ? ENDPOINTS.USERS.FAVORITES 
        : `${ENDPOINTS.USERS.FAVORITES}deal/${dealId}/`;
      
      const response = await axiosInstance[method](
        endpoint,
        isFavorite ? { type: 'deal', id: dealId } : undefined
      );

      return response.data;
    } catch (error) {
      console.error('Failed to toggle favorite status:', error);
      throw error;
    }
  }
};

export default dealService;