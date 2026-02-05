import { axiosInstance } from '@/api/client';
import { ENDPOINTS } from '@/api/endpoints';

interface NotificationPreferences {
  [key: string]: unknown;
}

interface UserSettings {
  [key: string]: unknown;
}

interface FavoriteResponse {
  id: string | number;
  type: 'deal' | 'shop';
  [key: string]: unknown;
}

class UserService {
  public async getFavorites(): Promise<FavoriteResponse[]> {
    const response = await axiosInstance.get<FavoriteResponse[]>(ENDPOINTS.USERS.FAVORITES);
    return response.data;
  }

  public async addFavorite(type: 'deal' | 'shop', id: number | string): Promise<FavoriteResponse> {
    const response = await axiosInstance.post<FavoriteResponse>(
      ENDPOINTS.USERS.FAVORITES, 
      { type, id }
    );
    return response.data;
  }

  public async removeFavorite(type: 'deal' | 'shop', id: number | string): Promise<void> {
    await axiosInstance.delete(`${ENDPOINTS.USERS.FAVORITES}${type}/${id}/`);
  }

  public async getSettings(): Promise<UserSettings> {
    const response = await axiosInstance.get<UserSettings>(ENDPOINTS.USERS.SETTINGS);
    return response.data;
  }

  public async updateSettings(settings: UserSettings): Promise<UserSettings> {
    const response = await axiosInstance.patch<UserSettings>(
      ENDPOINTS.USERS.SETTINGS, 
      settings
    );
    return response.data;
  }

  public async getNotificationPreferences(): Promise<NotificationPreferences> {
    const response = await axiosInstance.get<NotificationPreferences>(
      `${ENDPOINTS.USERS.SETTINGS}notifications/`
    );
    return response.data;
  }

  public async updateNotificationPreferences(
    preferences: NotificationPreferences
  ): Promise<NotificationPreferences> {
    const response = await axiosInstance.patch<NotificationPreferences>(
      `${ENDPOINTS.USERS.SETTINGS}notifications/`, 
      preferences
    );
    return response.data;
  }
}

const userService = new UserService();
export default userService;