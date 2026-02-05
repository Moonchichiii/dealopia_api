import type { AxiosError } from 'axios';
import { axiosInstance } from '@/api/client';
import type { UserProfile, LoginCredentials, RegisterData, TwoFactorVerifyParams } from '@/types/auth';
import { ENDPOINTS } from '@/api/endpoints';

class AuthService {
  async login(credentials: LoginCredentials): Promise<UserProfile> {
    try {
      const response = await axiosInstance.post<UserProfile>(ENDPOINTS.AUTH.LOGIN, credentials);
      return response.data;
    } catch (error) {
      throw this.formatErrorMessage(error);
    }
  }

  async getProfile(): Promise<UserProfile> {
    try {
      const response = await axiosInstance.get<UserProfile>(ENDPOINTS.AUTH.ME);
      return response.data;
    } catch (error) {
      throw this.formatErrorMessage(error);
    }
  }

  async register(userData: RegisterData): Promise<UserProfile> {
    try {
      const response = await axiosInstance.post<UserProfile>(ENDPOINTS.AUTH.REGISTER, userData);
      return response.data;
    } catch (error) {
      throw this.formatErrorMessage(error);
    }
  }

  async logout(): Promise<void> {
    try {
      await axiosInstance.post(ENDPOINTS.AUTH.LOGOUT, {}, {
        withCredentials: true
      });
      
      localStorage.clear();
      sessionStorage.clear();
      
      window.location.href = '/';
    } catch (error) {
      console.error('Logout failed:', error);
      window.location.href = '/';
    }
  }

  async verifyTwoFactor(params: TwoFactorVerifyParams): Promise<{ verified: boolean }> {
    try {
      const response = await axiosInstance.post<{ verified: boolean }>(
        ENDPOINTS.AUTH.TWO_FACTOR_VERIFY,
        { token: params.token }
      );
      return response.data;
    } catch (error) {
      throw this.formatErrorMessage(error);
    }
  }

  async refreshToken(): Promise<void> {
    try {
      await axiosInstance.post(ENDPOINTS.AUTH.REFRESH_TOKEN);
    } catch (error) {
      const errorMessage = this.formatErrorMessage(error);
      console.error('Token refresh failed:', errorMessage);
      throw errorMessage;
    }
  }

  private formatErrorMessage(error: unknown): Error {
    if (this.isAxiosError(error)) {
      const response = error.response;
      
      if (response?.data) {
        const { data } = response;
        
        if (typeof data === 'string' && data.trim()) {
          return new Error(data.trim());
        }
        
        if (typeof data === 'object' && data !== null) {
          if (typeof data.detail === 'string' && data.detail.trim()) {
            return new Error(data.detail.trim());
          }
          
          if (Array.isArray(data.non_field_errors) && data.non_field_errors.length > 0) {
            return new Error(data.non_field_errors.map(String).join(', '));
          }
          
          if (typeof data.error === 'string' && data.error.trim()) {
            return new Error(data.error.trim());
          }
          
          if (typeof data.message === 'string' && data.message.trim()) {
            return new Error(data.message.trim());
          }
          
          const fieldErrors = this.formatFieldErrors(data);
          if (fieldErrors) {
            return new Error(fieldErrors);
          }
        }
        
        if (response.statusText) {
          return new Error(`Request failed: ${response.status} ${response.statusText}`);
        }
        
        return new Error(`An error occurred (Status: ${response.status}). Please try again.`);
      }
      
      if (error.request) {
        return new Error('No response received from server. Check network connection or server status.');
      }
      
      return new Error(error.message || 'Error sending request.');
    }
    
    if (error instanceof Error) {
      return error;
    }
    
    if (typeof error === 'string' && error.trim()) {
      return new Error(error.trim());
    }
    
    return new Error('An unexpected error occurred. Please try again.');
  }

  private formatFieldErrors(data: Record<string, unknown>): string | null {
    const excludedKeys = new Set(['status', 'code', 'detail', 'non_field_errors', 'error', 'message']);
    
    const errors = Object.entries(data)
      .filter(([key]) => !excludedKeys.has(key))
      .map(([field, errors]) => {
        const errorText = Array.isArray(errors) ? errors.join(', ') : String(errors);
        const formattedField = field.charAt(0).toUpperCase() + field.slice(1).replace(/_/g, ' ');
        return `${formattedField}: ${errorText}`;
      });
    
    return errors.length > 0 ? errors.join('; ') : null;
  }
  
  private isAxiosError(error: unknown): error is AxiosError {
    return typeof error === 'object' && error !== null && 'isAxiosError' in error && error.isAxiosError === true;
  }
}

export default new AuthService();
