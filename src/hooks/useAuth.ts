import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, useCallback } from 'react';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';
import authService from '@/api/services/authService';
import type {
  UserProfile,
  LoginCredentials,
  RegisterData,
  TwoFactorVerifyParams
} from '@/types/auth';

const USER_QUERY_KEY = ['auth', 'user'];

/**
 * Check if any authentication cookies are present
 */
const hasAuthCookies = () => {
  return document.cookie.includes('auth-token') ||
         document.cookie.includes('sessionid') ||
         document.cookie.includes('refresh-token');
};

/**
 * Format error messages consistently
 */
const formatErrorMessage = (error: unknown): string => {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  return 'Unknown error';
};

/**
 * Fetch the current user profile.
 */
export function useUser() {
  // Use state to track cookie presence
  const [hasCookies, setHasCookies] = useState(hasAuthCookies());
  
  // Listen for cookie changes (via polling or events)
  useEffect(() => {
    const checkCookies = () => {
      const cookiesExist = hasAuthCookies();
      if (hasCookies !== cookiesExist) {
        setHasCookies(cookiesExist);
      }
    };
    
    // Check every few seconds
    const interval = setInterval(checkCookies, 3000);
    return () => clearInterval(interval);
  }, [hasCookies]);
  
  // Listen for logout events
  useEffect(() => {
    const handleLogout = () => {
      setHasCookies(false);
    };
    
    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  }, []);

  const query = useQuery({
    queryKey: USER_QUERY_KEY,
    queryFn: () => authService.getProfile(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
    retry: (failureCount, error) => {
      if (failureCount > 0 || error.message?.includes('401')) {
        return false;
      }
      return true;
    },
    enabled: hasCookies,
  });

  return {
    ...query,
    isAuthenticated: Boolean(query.data)
  };
}

/**
 * Hook for logging in.
 */
export function useLogin() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (credentials: LoginCredentials) => authService.login(credentials),
    onSuccess: (data) => {
      // Check for 2FA requirement
      if (data && typeof data === 'object' && 'requires_2fa' in data) {
        return;
      }

      queryClient.setQueryData(USER_QUERY_KEY, data);
      toast.success('Logged in successfully');
    },
    onError: (error) => {
      toast.error(`Login failed: ${formatErrorMessage(error)}`);
    },
  });
  return mutation;
}

/**
 * Hook for registering a new user.
 */
export function useRegister() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (userData: RegisterData) => authService.register(userData),
    onSuccess: (data) => {
      queryClient.setQueryData(USER_QUERY_KEY, data);
      toast.success('Registration successful');
    },
    onError: (error) => {
      toast.error(`Registration failed: ${formatErrorMessage(error)}`);
    },
  });
  return mutation;
}

/**
 * Hook for logging out.
 */
export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  
  // Clear all query cache on logout
  const clearCache = useCallback(() => {
    queryClient.clear();
  }, [queryClient]);
  
  // Listen for logout events
  useEffect(() => {
    window.addEventListener('auth:logout', clearCache);
    return () => window.removeEventListener('auth:logout', clearCache);
  }, [clearCache]);
  
  const mutation = useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      navigate('/', { replace: true });
      toast.info('Logged out successfully');
    },
    onError: (error) => {
      clearCache();
      navigate('/', { replace: true });
      toast.error(`Logout error: ${formatErrorMessage(error)}`);
    },
  });
  return mutation;
}

/**
 * Hook for verifying a two-factor authentication token.
 */
export function useVerifyTwoFactor() {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: (params: TwoFactorVerifyParams) => authService.verifyTwoFactor(params),
    onSuccess: (data) => {
      queryClient.setQueryData(USER_QUERY_KEY, data);
      toast.success('Two-factor authentication verified');
    },
    onError: (error) => {
      toast.error(`Two-factor verification failed: ${formatErrorMessage(error)}`);
    },
  });
  return mutation;
}

/**
 * Main authentication hook to bundle all functionality.
 */
export function useAuth() {
  const userQuery = useUser();
  const loginMutation = useLogin();
  const registerMutation = useRegister();
  const logoutMutation = useLogout();
  const verifyTwoFactorMutation = useVerifyTwoFactor();

  return {
    user: userQuery.data,
    isAuthenticated: userQuery.isAuthenticated,
    isLoading:
      userQuery.isLoading ||
      loginMutation.isPending ||
      registerMutation.isPending ||
      logoutMutation.isPending,
    refetchUser: userQuery.refetch,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    verifyTwoFactor: verifyTwoFactorMutation.mutateAsync,
  };
}