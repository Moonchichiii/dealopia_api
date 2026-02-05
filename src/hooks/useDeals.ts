import {
  useQuery,
  useInfiniteQuery,
  useMutation,
  useQueryClient
} from '@tanstack/react-query';
import { toast } from 'react-toastify';
import dealService from '@/api/services/dealService';
import { Deal, DealFilters } from '@/types/deals';

// Query key factory for better cache management
const dealKeys = {
  all: ['deals'] as const,
  lists: () => [...dealKeys.all, 'list'] as const,
  list: (filters: DealFilters = {}) => [...dealKeys.lists(), filters] as const,
  details: () => [...dealKeys.all, 'detail'] as const,
  detail: (id: string | number) => [...dealKeys.details(), id] as const,
  featured: () => [...dealKeys.all, 'featured'] as const,
  nearby: (lat?: number, lng?: number, radius?: number) =>
    [...dealKeys.all, 'nearby', lat, lng, radius] as const,
  ending: () => [...dealKeys.all, 'ending-soon'] as const,
  search: (query: string) => [...dealKeys.all, 'search', query] as const,
  favorites: () => [...dealKeys.all, 'favorites'] as const,
};

/**
 * Hook for fetching paginated deals with filters
 */
export const useDeals = (filters?: DealFilters) => {
  return useQuery({
    queryKey: dealKeys.list(filters),
    queryFn: () => dealService.getDeals(filters),
    keepPreviousData: true,
    staleTime: 60 * 1000, // 1 minute cache
  });
};

/**
 * Hook for fetching infinite scrolling deals list
 * Efficient for browsing large datasets
 */
export const useInfiniteDeals = (filters?: DealFilters) => {
  return useInfiniteQuery({
    queryKey: [...dealKeys.lists(), 'infinite', filters],
    queryFn: async ({ pageParam = 1 }) => {
      const response = await dealService.getDeals({
        ...filters,
        page: pageParam,
      });
      
      return {
        deals: response.results,
        currentPage: pageParam,
        totalPages: Math.ceil(response.count / (filters?.page_size || 20)),
      };
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.currentPage < lastPage.totalPages) {
        return lastPage.currentPage + 1;
      }
      return undefined;
    },
    staleTime: 60 * 1000, // 1 minute
  });
};

/**
 * Hook for fetching a single deal by ID
 */
export const useDeal = (id?: string | number) => {
  return useQuery({
    queryKey: id ? dealKeys.detail(id) : dealKeys.details(),
    queryFn: () => dealService.getDeal(id!),
    enabled: !!id,
    staleTime: 3 * 60 * 1000, // 3 minutes
  });
};

/**
 * Hook for fetching featured deals for homepage
 */
export const useFeaturedDeals = (limit: number = 6) => {
  return useQuery({
    queryKey: [...dealKeys.featured(), limit],
    queryFn: () => dealService.getFeaturedDeals(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes cache
  });
};

/**
 * Hook for fetching deals ending soon
 */
export const useEndingSoonDeals = (days: number = 3, limit: number = 6) => {
  return useQuery({
    queryKey: [...dealKeys.ending(), days, limit],
    queryFn: () => dealService.getEndingSoonDeals(days, limit),
    staleTime: 3 * 60 * 1000, // 3 minutes
  });
};

/**
 * Hook for fetching nearby deals based on user location
 * Updated to use a literal queryKey array as provided.
 */
export const useNearbyDeals = (
  latitude?: number | null,
  longitude?: number | null,
  radius: number = 10
) => {
  return useQuery({
    queryKey: ['deals', 'nearby', latitude, longitude, radius],
    queryFn: () => dealService.getNearbyDeals(latitude!, longitude!, radius),
    enabled: !!latitude && !!longitude,
    staleTime: 2 * 60 * 1000, // 2 minutes - shorter cache for location-specific data
    retry: 1,
  });
};

/**
 * Hook for searching deals
 * Includes debounce handling in the component that uses it
 */
export const useSearchDeals = (query: string) => {
  return useQuery({
    queryKey: dealKeys.search(query),
    queryFn: () => dealService.searchDeals(query),
    enabled: query.length > 2, // Only search when query is substantial
    staleTime: 1 * 60 * 1000, // 1 minute cache for search results
  });
};

/**
 * Hook for toggling deal favorite status
 * Uses optimistic updates for better UX
 */
export const useToggleDealFavorite = () => {
  const queryClient = useQueryClient();
 
  return useMutation({
    mutationFn: ({ dealId, isFavorite }: { dealId: string | number; isFavorite: boolean }) =>
      dealService.toggleFavorite(dealId, isFavorite),
    
    // Optimistic update for better UX
    onMutate: async ({ dealId, isFavorite }) => {
      // Cancel any outgoing refetches 
      await queryClient.cancelQueries({ queryKey: dealKeys.detail(dealId) });
      
      // Snapshot the previous value
      const previousDeal = queryClient.getQueryData<Deal>(dealKeys.detail(dealId));
     
      // Optimistically update to the new value
      if (previousDeal) {
        queryClient.setQueryData(dealKeys.detail(dealId), {
          ...previousDeal,
          isFavorite
        });
      }
     
      return { previousDeal };
    },
    
    // Show success message
    onSuccess: (_, { isFavorite }) => {
      toast.success(
        isFavorite
          ? '✓ Deal added to favorites'
          : '✓ Deal removed from favorites'
      );
    },
    
    // If there's an error, revert to the previous state
    onError: (error, { dealId }, context) => {
      if (context?.previousDeal) {
        queryClient.setQueryData(dealKeys.detail(dealId), context.previousDeal);
      }
      toast.error('Failed to update favorites. Please try again.');
    },
    
    // Always refetch to ensure consistency
    onSettled: (_, __, { dealId }) => {
      queryClient.invalidateQueries({ queryKey: dealKeys.detail(dealId) });
      queryClient.invalidateQueries({ queryKey: dealKeys.favorites() });
    },
  });
};

/**
 * Hook for fetching deals by shop
 */
export const useDealsByShop = (shopId?: string | number, limit: number = 12) => {
  return useQuery({
    queryKey: [...dealKeys.lists(), 'shop', shopId, limit],
    queryFn: () => dealService.getShopDeals(shopId!, limit),
    enabled: !!shopId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook for fetching deals by category
 */
export const useDealsByCategory = (categoryId?: string | number, limit: number = 12) => {
  return useQuery({
    queryKey: [...dealKeys.lists(), 'category', categoryId, limit],
    queryFn: () => dealService.getCategoryDeals(categoryId!, limit),
    enabled: !!categoryId,
    staleTime: 10 * 60 * 1000, // 10 minutes - category data changes less frequently
  });
};

/**
 * Hook for fetching related deals
 */
export const useRelatedDeals = (dealId?: string | number, limit: number = 3) => {
  return useQuery({
    queryKey: [...dealKeys.details(), 'related', dealId, limit],
    queryFn: () => dealService.getRelatedDeals(dealId!, limit),
    enabled: !!dealId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook for tracking a deal view
 */
export const useTrackDealView = () => {
  return useMutation({
    mutationFn: (dealId: string | number) => dealService.trackDealView(dealId),
    // No need for complex error handling here - fire and forget
    onError: () => {
      // Silent failure is acceptable for analytics
    }
  });
};

/**
 * Hook for tracking a deal click
 */
export const useTrackDealClick = () => {
  return useMutation({
    mutationFn: (dealId: string | number) => dealService.trackDealClick(dealId),
    // No need for complex error handling here - fire and forget
    onError: () => {
      // Silent failure is acceptable for analytics
    }
  });
};

/**
 * Combined hook for a deal detail page that needs multiple related data pieces
 */
export const useDealDetailPage = (dealId?: string | number) => {
  const dealQuery = useDeal(dealId);
  const relatedDealsQuery = useRelatedDeals(dealId);
  const trackView = useTrackDealView();
  
  // Track view when the deal loads successfully
  useEffect(() => {
    if (dealId && dealQuery.isSuccess) {
      trackView.mutate(dealId);
    }
  }, [dealId, dealQuery.isSuccess, trackView]);

  return {
    deal: dealQuery.data,
    isLoading: dealQuery.isLoading,
    error: dealQuery.error,
    relatedDeals: relatedDealsQuery.data || [],
    isLoadingRelated: relatedDealsQuery.isLoading
  };
};

// Export default object with all hooks
export default {
  useDeals,
  useInfiniteDeals,
  useDeal,
  useFeaturedDeals,
  useEndingSoonDeals,
  useNearbyDeals,
  useSearchDeals,
  useToggleDealFavorite,
  useDealsByShop,
  useDealsByCategory,
  useRelatedDeals,
  useTrackDealView,
  useTrackDealClick,
  useDealDetailPage
};