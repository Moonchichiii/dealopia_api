import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { debounce } from 'lodash';
import { locationService } from '@/api/services/locationService';
interface GeolocationState {
  latitude: number | null;
  longitude: number | null;
  accuracy: number | null;
  loading: boolean;
  error: string | null;
  timestamp: number | null;
  addressString: string | null;
}

interface GeolocationOptions {
  enableHighAccuracy?: boolean;
  timeout?: number;
  maximumAge?: number;
  autoDetect?: boolean;
  onLocationSuccess?: (coords: { latitude: number; longitude: number }) => void;
}

export interface GeolocationResult extends GeolocationState {
  getLocation: () => Promise<void>;
  clearLocation: () => void;
}

const DEFAULT_OPTIONS: Readonly<GeolocationOptions> = {
  enableHighAccuracy: true,
  timeout: 10000,
  maximumAge: 0,
  autoDetect: false,
};

const LOCATION_CACHE_KEY = 'dealopia_user_location';
const CONSENT_COOKIE_KEY = 'dealopia-cookie-consent';
const PERMISSION_DENIED_KEY = 'location_permanently_denied';
const CACHE_TTL = 24 * 60 * 60 * 1000;
const GEOCODE_DEBOUNCE_MS = 1000;
const EVENT_DISPATCH_DELAY_MS = 100;

const hasConsentCookie = (): boolean => {
  return document.cookie
    .split('; ')
    .some(row => row.startsWith(CONSENT_COOKIE_KEY));
};

const hasDeniedPermission = (): boolean => {
  try {
    return localStorage.getItem(PERMISSION_DENIED_KEY) === 'true';
  } catch {
    return false;
  }
};

const getCachedLocation = (): GeolocationState | null => {
  try {
    const cachedData = localStorage.getItem(LOCATION_CACHE_KEY);
    if (!cachedData) return null;

    const parsed = JSON.parse(cachedData);
    if (Date.now() - (parsed.timestamp || 0) < CACHE_TTL) {
      return {
        latitude: parsed.latitude ?? null,
        longitude: parsed.longitude ?? null,
        accuracy: parsed.accuracy ?? null,
        timestamp: parsed.timestamp ?? null,
        addressString: parsed.addressString ?? null,
        loading: false,
        error: null,
      };
    }
  } catch (error) {
    console.warn('Failed to read or parse cached location:', error);
  }
  return null;
};

const cacheLocation = (data: {
  latitude: number;
  longitude: number;
  accuracy: number | null;
  timestamp: number;
  addressString?: string | null;
}): void => {
  try {
  
    const dataToCache = {
      latitude: data.latitude,
      longitude: data.longitude,
      accuracy: data.accuracy,
      timestamp: data.timestamp,
      addressString: data.addressString ?? null
    };
    
    localStorage.setItem(LOCATION_CACHE_KEY, JSON.stringify(dataToCache));
    localStorage.removeItem(PERMISSION_DENIED_KEY);
  } catch (error) {
    console.warn('Failed to cache location:', error);
  }
};

const updateCachedAddress = (addressString: string): void => {
  try {
    const cachedData = localStorage.getItem(LOCATION_CACHE_KEY);
    if (cachedData) {
      const parsedData = JSON.parse(cachedData);
      cacheLocation({ 
        ...parsedData, 
        addressString,
  
        latitude: parsedData.latitude || 0,
        longitude: parsedData.longitude || 0,
        accuracy: parsedData.accuracy || null,
        timestamp: parsedData.timestamp || Date.now()
      });
    }
  } catch (error) {
    console.warn('Failed to update location cache with address:', error);
  }
};

const dispatchLocationEvent = (latitude: number, longitude: number): void => {
  
  setTimeout(() => {
    const locationEvent = new CustomEvent('dealopiaLocationAvailable', {
      detail: { latitude, longitude },
    });
    document.dispatchEvent(locationEvent);
  }, EVENT_DISPATCH_DELAY_MS);
};

export function useGeolocation(options: GeolocationOptions = {}): GeolocationResult {
  const mergedOptions = useMemo(
    () => ({ ...DEFAULT_OPTIONS, ...options }),
    [options]
  );

  const initialConsent = useMemo(hasConsentCookie, []);
  const initialDenied = useMemo(hasDeniedPermission, []);
  const initialCachedLocation = useMemo(getCachedLocation, []);

  const [state, setState] = useState<GeolocationState>(() => {
    const canUseCached =
      mergedOptions.autoDetect &&
      initialConsent &&
      !initialDenied &&
      initialCachedLocation;

    return canUseCached
      ? initialCachedLocation
      : {
          latitude: null,
          longitude: null,
          accuracy: null,
          loading: mergedOptions.autoDetect && initialConsent && !initialDenied,
          error: initialDenied ? 'Location access was previously denied.' : null,
          timestamp: null,
          addressString: null,
        };
  });

  const autoDetectTriggered = useRef(!!initialCachedLocation);
  const eventDispatched = useRef(false);

  const debouncedGeocode = useMemo(
    () =>
      debounce(async (latitude: number, longitude: number) => {
        try {
          const addressData = await locationService.reverseGeocode(latitude, longitude);
          const addressString = addressData?.address || null;
          if (addressString) {
            setState(prev => ({ ...prev, addressString }));
            updateCachedAddress(addressString);
          }
        } catch (error) {
          console.error('Reverse geocoding failed:', error);
        }
      }, GEOCODE_DEBOUNCE_MS),
    []
  );

  const handleLocationSuccess = useCallback(
    (position: GeolocationPosition) => {
      const { latitude, longitude, accuracy } = position.coords;
      const timestamp = Date.now();

      setState({
        latitude,
        longitude,
        accuracy,
        loading: false,
        error: null,
        timestamp,
        addressString: null,
      });

      cacheLocation({ latitude, longitude, accuracy, timestamp });
      dispatchLocationEvent(latitude, longitude);
      mergedOptions.onLocationSuccess?.({ latitude, longitude });
      debouncedGeocode(latitude, longitude);
    },
    [debouncedGeocode, mergedOptions.onLocationSuccess]
  );

  const handleLocationError = useCallback((error: any) => {
    let errorMessage = 'Location detection failed.';
        
    if (error && typeof error.code === 'number') {
      switch (error.code) {
        case 1:
          errorMessage = 'Please allow location access to show nearby deals.';
          try {
            localStorage.setItem(PERMISSION_DENIED_KEY, 'true');
          } catch (storageError) {
            console.warn('Failed to set permission denied flag:', storageError);
          }
          break;
        case 2:
          errorMessage = 'Location information is unavailable.';
          break;
        case 3:
          errorMessage = 'The request to get user location timed out.';
          break;
      }
    } else if (error instanceof Error) {
      errorMessage = error.message;
    }
    
    setState(prev => ({
      ...prev,
      latitude: null,
      longitude: null,
      accuracy: null,
      loading: false,
      error: errorMessage,
      timestamp: null,
      addressString: null,
    }));
  }, []);

  const getLocation = useCallback(async (): Promise<void> => {
    if (!hasConsentCookie()) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Cookie consent is required to use location services.',
      }));
      return;
    }

    if (hasDeniedPermission()) {
       setState(prev => ({
        ...prev,
        loading: false,
        error: 'Location access was previously denied.',
      }));
      return;
    }

    if (!navigator.geolocation) {
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Geolocation is not supported by this browser.',
      }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          {
            enableHighAccuracy: mergedOptions.enableHighAccuracy,
            timeout: mergedOptions.timeout,
            maximumAge: mergedOptions.maximumAge,
          }
        );
      });
      handleLocationSuccess(position);
    } catch (error) {
      handleLocationError(error);
    }
  }, [
    mergedOptions.enableHighAccuracy,
    mergedOptions.maximumAge,
    mergedOptions.timeout,
    handleLocationSuccess,
    handleLocationError,
  ]);

  const clearLocation = useCallback(() => {
    try {
      localStorage.removeItem(LOCATION_CACHE_KEY);
      localStorage.removeItem(PERMISSION_DENIED_KEY);
    } catch (error) {
      console.warn('Failed to clear location cache/flags:', error);
    }
    setState({
      latitude: null,
      longitude: null,
      accuracy: null,
      loading: false,
      error: null,
      timestamp: null,
      addressString: null,
    });
    
    autoDetectTriggered.current = false;
    eventDispatched.current = false;
  }, []);

  useEffect(() => {
    if (
      mergedOptions.autoDetect &&
      !state.latitude && 
      !state.loading &&
      !autoDetectTriggered.current &&
      hasConsentCookie() &&
      !hasDeniedPermission()
    ) {
      autoDetectTriggered.current = true;
      getLocation().catch(err => {
        console.error("Error during auto-detect getLocation call:", err);
      });
    }
  }, [
    mergedOptions.autoDetect,
    state.latitude,
    state.loading,
    getLocation,
  ]);

  useEffect(() => {
    
    if (
      !eventDispatched.current && 
      initialCachedLocation?.latitude && 
      initialCachedLocation?.longitude
    ) {
      eventDispatched.current = true;
      dispatchLocationEvent(initialCachedLocation.latitude, initialCachedLocation.longitude);
      
      
      setTimeout(() => {
        mergedOptions.onLocationSuccess?.({
          latitude: initialCachedLocation.latitude,
          longitude: initialCachedLocation.longitude
        });
      }, EVENT_DISPATCH_DELAY_MS);
    }
  }, [initialCachedLocation, mergedOptions.onLocationSuccess]);

  useEffect(() => {
    
    return () => {
      debouncedGeocode.cancel();
    };
  }, [debouncedGeocode]);

  return { ...state, getLocation, clearLocation };
}