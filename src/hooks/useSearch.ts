import { useState, useCallback, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dealService } from '@/api/index';
import { DealFilters } from '@/types/deals';

const DEBOUNCE_DELAY_MS = 800;
const MIN_SEARCH_LENGTH = 3;
const RATE_LIMIT_DELAY_MS = 800;

export function useSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFilters, setSearchFilters] = useState<DealFilters>({});
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [debouncedFilters, setDebouncedFilters] = useState<DealFilters>({});

  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSearchTimeRef = useRef<number>(0);
  const prevFiltersStringRef = useRef<string>('');
  const isInitialMountRef = useRef(true);

  useEffect(() => {
    if (isInitialMountRef.current && searchQuery === '') {
      isInitialMountRef.current = false;
      return;
    }

    const currentFiltersString = JSON.stringify(searchFilters);

    if (
      prevFiltersStringRef.current === currentFiltersString &&
      debouncedQuery === searchQuery
    ) {
      return;
    }

    prevFiltersStringRef.current = currentFiltersString;

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      const queryLength = searchQuery.trim().length;
      if (queryLength >= MIN_SEARCH_LENGTH || queryLength === 0) {
        setDebouncedQuery(searchQuery);
        setDebouncedFilters(searchFilters);
      }
    }, DEBOUNCE_DELAY_MS);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [searchQuery, searchFilters, debouncedQuery]);

  const shouldFetch = debouncedQuery.trim().length >= MIN_SEARCH_LENGTH;
  const queryKey = ['deals', 'search', debouncedQuery, JSON.stringify(debouncedFilters)];

  const { data, isLoading, error, isFetching } = useQuery({
    queryKey: queryKey,
    queryFn: () => dealService.searchDeals(debouncedQuery, debouncedFilters),
    enabled: shouldFetch,
    staleTime: 60 * 1000, // 1 minute
    keepPreviousData: true,
  });

  const handleSearch = useCallback((query: string, filters: DealFilters = {}) => {
    const now = Date.now();
    if (now - lastSearchTimeRef.current < RATE_LIMIT_DELAY_MS) {
      return;
    }

    const filtersString = JSON.stringify(filters);
    const currentFiltersString = JSON.stringify(searchFilters);
    if (query === searchQuery && filtersString === currentFiltersString) {
      return;
    }

    lastSearchTimeRef.current = now;
    setSearchQuery(query);
    setSearchFilters(filters);
  }, [searchQuery, searchFilters]); // Dependencies include values read inside the callback

  return {
    searchQuery,
    searchFilters,
    results: data?.results ?? [],
    totalResults: data?.count ?? 0,
    isLoading: isLoading || isFetching, // Combine loading states for better UX
    error,
    handleSearch,
  };
}
