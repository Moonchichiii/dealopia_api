import { Shop } from './shops';
import { Category } from './categories';

export interface Deal {
  id: number;
  title: string;
  description: string;
  shop: number | Shop;
  original_price: number;
  discounted_price: number;
  discount_percentage: number;
  categories: number[] | Category[];
  image: string;
  start_date: string;
  end_date: string;
  is_featured: boolean;
  is_exclusive: boolean;
  is_verified: boolean;
  terms_and_conditions?: string;
  coupon_code?: string;
  redemption_link?: string;
  sustainability_score?: number;
  eco_certifications?: any[];
  views_count: number;
  clicks_count: number;
  created_at: string;
  updated_at: string;
  distance?: number;
  time_left?: string;
  is_new?: boolean;
}

export interface DealFilters {
  shop?: number;
  categories?: number[];
  is_featured?: boolean;
  is_exclusive?: boolean;
  is_verified?: boolean;
  lat?: number;
  lng?: number;
  radius?: number;
  search?: string;
  page?: number;
  page_size?: number;
  ordering?: string;
}