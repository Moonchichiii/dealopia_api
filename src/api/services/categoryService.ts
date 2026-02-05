import { axiosInstance } from '@/api/client';
import { Category } from '@/types/categories';
import { ENDPOINTS } from '@/api/endpoints';

const categoryService = {
  getCategories: async (
    params?: { parent?: number; is_active?: boolean; limit?: number }
  ): Promise<Category[]> => {
    try {
      const response = await axiosInstance.get<Category[]>(ENDPOINTS.CATEGORIES.BASE, { params });
      return response.data;
    } catch (error) {
      console.error('Category service error:', error);
      return [];
    }
  },

  getCategory: async (id: number | string): Promise<Category | null> => {
    if (!id) return null;
    try {
      const response = await axiosInstance.get<Category>(ENDPOINTS.CATEGORIES.DETAIL(id));
      return response.data;
    } catch (error) {
      console.error('Category service error:', error);
      return null;
    }
  },

  getFeaturedCategories: async (limit: number = 6): Promise<Category[]> => {
    try {
      const response = await axiosInstance.get<Category[]>(
        ENDPOINTS.CATEGORIES.FEATURED,
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      console.error('Category service error:', error);
      return [];
    }
  },

  getCategoryDeals: async (categoryId: number | string, limit: number = 12): Promise<Category[]> => {
    if (!categoryId) return [];
    try {
      const response = await axiosInstance.get<Category[]>(
        ENDPOINTS.CATEGORIES.DEALS(categoryId),
        { params: { limit } }
      );
      return response.data;
    } catch (error) {
      console.error('Category service error:', error);
      return [];
    }
  },

  getCategoryTree: async (): Promise<Category[]> => {
    try {
      const allCategories: Category[] = await categoryService.getCategories({ is_active: true });
      const rootCategories = allCategories.filter((cat) => !cat.parent);
      rootCategories.forEach((root) => {
        root.subcategories = allCategories.filter((cat) => cat.parent === root.id);
      });
      return rootCategories;
    } catch (error) {
      console.error('Category service error:', error);
      return [];
    }
  },

  getCategoryBreadcrumbs: async (categoryId: number | string): Promise<Category[]> => {
    if (!categoryId) return [];
    try {
      const category = await categoryService.getCategory(categoryId);
      if (!category) return [];
      const breadcrumbs = [category];
      if (category.parent) {
        const parents = await categoryService.getCategoryBreadcrumbs(category.parent);
        return [...parents, category];
      }
      return breadcrumbs;
    } catch (error) {
      console.error('Category service error:', error);
      return [];
    }
  },

  getRelatedCategories: async (categoryId: number | string, limit: number = 5): Promise<Category[]> => {
    if (!categoryId) return [];
    try {
      const category = await categoryService.getCategory(categoryId);
      if (!category) return [];
      if (category.parent) {
        const response = await axiosInstance.get<Category[]>(
          ENDPOINTS.CATEGORIES.BASE,
          { params: { parent: category.parent, is_active: true } }
        );
        const siblings = response.data;
        return siblings.filter((cat) => cat.id !== category.id).slice(0, limit);
      }

      const response = await axiosInstance.get<Category[]>(
        ENDPOINTS.CATEGORIES.BASE,
        { params: { parent: null, is_active: true } }
      );
      return response.data
        .filter((cat) => cat.id !== category.id)
        .slice(0, limit);
    } catch (error) {
      console.error('Category service error:', error);
      return [];
    }
  },

  searchCategories: async (query: string): Promise<Category[]> => {
    if (!query || query.length < 2) return [];
    try {
      const response = await axiosInstance.get<Category[]>(
        ENDPOINTS.CATEGORIES.BASE,
        { params: { search: query } }
      );
      return response.data;
    } catch (error) {
      console.error('Category service error:', error);
      return [];
    }
  },

  getCategoryIcon: (category: Category | null): string => {
    return category && category.icon ? category.icon : '/assets/icons/category-default.svg';
  },

  getCategoryImage: (category: Category | null): string => {
    return category && category.image ? category.image : '/assets/images/category-default.jpg';
  },
};

export default categoryService;