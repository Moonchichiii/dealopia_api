import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { categoryService, dealService } from '@/api/index';

/**
 * Fetch all categories
 */
export const useCategories = (params?: { parent?: number; is_active?: boolean; limit?: number }) => {
  return useQuery({
    queryKey: ['categories', params],
    queryFn: () => categoryService.getCategories(params),
    staleTime: 1000 * 60 * 60,
  });
};

/**
 * Fetch a single category
 */
export const useCategory = (id?: number | string) => {
  return useQuery({
    queryKey: ['category', id],
    queryFn: () => categoryService.getCategory(id!),
    enabled: !!id,
    staleTime: 1000 * 60 * 30,
  });
};

/**
 * Search deals with infinite scrolling
 */
export const useSearchDeals = (query: string, categoryId?: number) => {
  return useInfiniteQuery({
    queryKey: ['deals', 'search', query, categoryId],
    queryFn: async ({ pageParam = 1 }) => {
      const filters: any = {
        search: query,
        page: pageParam,
      };
      
      if (categoryId) {
        filters.categories = categoryId;
      }
      
      const response = await dealService.getDeals(filters);
      return {
        deals: response.results,
        currentPage: pageParam,
        totalPages: Math.ceil(response.count / 20),
        totalResults: response.count,
      };
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      if (lastPage.currentPage < lastPage.totalPages) {
        return lastPage.currentPage + 1;
      }
      return undefined;
    },
    enabled: query.length >= 3,
  });
};