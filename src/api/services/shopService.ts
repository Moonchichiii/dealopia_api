import { axiosInstance } from '@/api/client';
import { Deal, DealFilters } from '@/types/deals';
import { ENDPOINTS } from '@/api/endpoints';

const dealService = {
  getDeals: async (filters?: DealFilters): Promise<{ results: Deal[]; count: number }> => {
    try {
      const response = await axiosInstance.get<string | { results: Deal[]; count: number }>(
        ENDPOINTS.DEALS.BASE,
        { params: filters }
      );

      // If the server accidentally sent HTML, bail out early
      if (typeof response.data === 'string') {
        throw new Error(`Expected JSON, got HTML. Check proxy/API URL. First 100 chars: ${
          response.data.slice(0, 100)
        }`);
      }

      // Assuming the API returns { results: Deal[], count: number }
      if ('results' in response.data && 'count' in response.data) {
        return response.data;
      } else {
          // Handle cases where the structure might be different or log an error
          console.error('Unexpected response structure for getDeals:', response.data);
          throw new Error('Unexpected response structure for getDeals');
      }

    } catch (error) {
      console.error('Deal service error (getDeals):', error);
      // Return a default structure that matches the Promise return type
      return { results: [], count: 0 };
    }
  },

  getDeal: async (id: string | number): Promise<Deal | null> => {
    if (!id) return null;
    try {
      const response = await axiosInstance.get<string | Deal>(ENDPOINTS.DEALS.DETAIL(id));

      // If the server accidentally sent HTML, bail out early
      if (typeof response.data === 'string') {
        throw new Error(`Expected JSON, got HTML. Check proxy/API URL. First 100 chars: ${
          response.data.slice(0, 100)
        }`);
      }

      // Check if the response data is a valid Deal object (basic check)
      if (typeof response.data === 'object' && response.data !== null && 'id' in response.data) {
          return response.data;
      } else {
          console.error('Unexpected response structure for getDeal:', response.data);
          throw new Error('Unexpected response structure for getDeal');
      }

    } catch (error) {
      console.error('Deal service error (getDeal):', error);
      return null;
    }
  },

  getFeaturedDeals: async (limit = 4): Promise<Deal[]> => {
    try {
      const response = await axiosInstance.get<string | { results: Deal[] } | Deal[]>(
        ENDPOINTS.DEALS.FEATURED,
        { params: { limit } }
      );

      // If the server accidentally sent HTML, bail out early
      if (typeof response.data === 'string') {
        throw new Error(`Expected JSON, got HTML. Check proxy/API URL. First 100 chars: ${
          response.data.slice(0, 100)
        }`);
      }

      // Handle both { results: Deal[] } and Deal[] structures
      return Array.isArray(response.data) ? response.data : ('results' in response.data ? response.data.results : []);

    } catch (error) {
      console.error('Deal service error (getFeaturedDeals):', error);
      return [];
    }
  },

  getDealsByCategory: async (categoryId: string | number, limit = 8): Promise<Deal[]> => {
    if (!categoryId) return [];
    try {
      // Assuming the endpoint returns { results: Deal[] } or Deal[]
      const response = await axiosInstance.get<string | { results: Deal[] } | Deal[]>(
        ENDPOINTS.DEALS.BASE, // Or a specific category endpoint if available
        {
          params: {
            categories: categoryId, // Adjust param name if needed
            limit
          }
        }
      );

      // If the server accidentally sent HTML, bail out early
      if (typeof response.data === 'string') {
        throw new Error(`Expected JSON, got HTML. Check proxy/API URL. First 100 chars: ${
          response.data.slice(0, 100)
        }`);
      }

      // Handle both { results: Deal[] } and Deal[] structures
      return Array.isArray(response.data) ? response.data : ('results' in response.data ? response.data.results : []);

    } catch (error) {
      console.error('Deal service error (getDealsByCategory):', error);
      return [];
    }
  },

  searchDeals: async (query: string, filters?: DealFilters): Promise<Deal[]> => {
    if (!query || query.length < 2) return [];
    try {
      // Assuming the endpoint returns { results: Deal[] } or Deal[]
      const response = await axiosInstance.get<string | { results: Deal[] } | Deal[]>(
        ENDPOINTS.DEALS.BASE, // Or a specific search endpoint if available
        { params: { search: query, ...filters } }
      );

      // If the server accidentally sent HTML, bail out early
      if (typeof response.data === 'string') {
        throw new Error(`Expected JSON, got HTML. Check proxy/API URL. First 100 chars: ${
          response.data.slice(0, 100)
        }`);
      }

      // Handle both { results: Deal[] } and Deal[] structures
      return Array.isArray(response.data) ? response.data : ('results' in response.data ? response.data.results : []);

    } catch (error) {
      console.error('Deal service error (searchDeals):', error);
      return [];
    }
  },

  // Add other deal service methods here if they exist...

  // Helper function (example, adjust as needed)
  formatPrice: (price: number | undefined): string => {
    if (price === undefined || price === null) return 'N/A';
    return `$${price.toFixed(2)}`;
  },

  // Helper function (example, adjust as needed)
  getDealImage: (deal: Deal | null): string =>
    deal?.images?.[0]?.image || '/assets/images/deal-default.png', // Use optional chaining

};

export default dealService;
