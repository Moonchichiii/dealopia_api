// src/types/auth.ts
import { Location } from './locations';
import { Category } from './categories';

export interface UserProfile {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  avatar?: string;
  preferred_language?: string;
  location?: number | Location;
  favorite_categories?: number[] | Category[];
  notification_preferences?: Record<string, any>;
  has_2fa_enabled?: boolean;
  date_joined?: string;
  last_login?: string;
  sustainability_preference?: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
  remember?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  preferred_language?: string;
}

export interface TwoFactorVerifyParams {
  userId: string;
  token: string;
}

export interface PasswordResetParams {
  token: string;
  password: string;
  passwordConfirm: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}