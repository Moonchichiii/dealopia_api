import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

export const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:logout'));
    }
    return Promise.reject(error);
  }
);

export async function fetchApi<T>(endpoint: string, options?: {
  method?: string;
  data?: any;
  params?: Record<string, any>;
}): Promise<T> {
  try {
    const response = await axiosInstance({
      url: endpoint,
      method: options?.method || 'GET',
      data: options?.data,
      params: options?.params
    });
    return response.data;
  } catch (error) {
    throw error;
  }
}
