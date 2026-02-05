import { useState, useRef, useCallback, useMemo, useEffect } from 'react';
import { Search, Filter, X, MapPin } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useGeolocation } from '@/hooks/useGeolocation';
import { cn } from '@/utils/cn';

interface Category {
  id: number;
  name: string;
}

interface SearchBarProps {
  onSearch: (query: string, filters?: Record<string, any>) => void;
  initialQuery?: string;
  className?: string;
  categories?: Category[];
  initialFilters?: Record<string, any>;
  placeholder?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  initialQuery = '',
  className = '',
  categories = [],
  initialFilters = {},
  placeholder,
}) => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<number[]>(
    initialFilters.categories || []
  );
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);
  
  // Use geolocation hook with autoDetect for optimal user experience
  const { latitude, longitude, loading: locationLoading } = useGeolocation({
    autoDetect: true,
  });
 
  // Track the last search params to prevent identical searches
  const lastSearchParamsRef = useRef<{ query: string; filtersString: string }>({
    query: '',
    filtersString: '',
  });
 
  // Memoize filters to avoid unnecessary re-renders
  const currentFilters = useMemo(() => {
    const filters = {
      ...initialFilters,
      categories: selectedCategories,
    };
   
    // Only add location if available and user hasn't manually cleared it
    if (latitude && longitude) {
      filters.latitude = latitude;
      filters.longitude = longitude;
      filters.radius = 10;
    }
   
    return filters;
  }, [initialFilters, selectedCategories, latitude, longitude]);

  // Handle click outside to close filter dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setShowFilters(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Focus input on mount and preselect text
  useEffect(() => {
    const inputElement = formRef.current?.querySelector('input');
    if (inputElement && initialQuery) {
      inputElement.focus();
      inputElement.select();
    }
  }, [initialQuery]);

  // Manual search handler for form submit
  const handleSearch = useCallback((e?: React.FormEvent) => {
    if (e) e.preventDefault();
   
    // Stringify filters for comparison
    const filtersString = JSON.stringify(currentFilters);
   
    // Don't make the same search twice
    if (
      searchQuery === lastSearchParamsRef.current.query &&
      filtersString === lastSearchParamsRef.current.filtersString
    ) {
      return;
    }
   
    // Update last search params
    lastSearchParamsRef.current = {
      query: searchQuery,
      filtersString,
    };
   
    onSearch(searchQuery, currentFilters);
  }, [searchQuery, currentFilters, onSearch]);

  // Toggle category selection
  const toggleCategory = useCallback((categoryId: number) => {
    setSelectedCategories(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
  }, []);

  // Clear all selected categories
  const clearAllCategories = useCallback(() => {
    setSelectedCategories([]);
  }, []);

  // Near me search handler - optimized to minimize requests
  const handleNearMeSearch = useCallback(() => {
    if (latitude && longitude) {
      // Update last search params with location
      const filtersWithLocation = {
        ...currentFilters,
        latitude,
        longitude,
        radius: 10,
      };
     
      const filtersString = JSON.stringify(filtersWithLocation);
     
      // Don't make the same search twice
      if (
        searchQuery === lastSearchParamsRef.current.query &&
        filtersString === lastSearchParamsRef.current.filtersString
      ) {
        return;
      }
     
      // Update last search params
      lastSearchParamsRef.current = {
        query: searchQuery,
        filtersString,
      };
     
      onSearch(searchQuery, filtersWithLocation);
    }
  }, [searchQuery, currentFilters, latitude, longitude, onSearch]);

  // Clear search query
  const handleClearSearch = useCallback(() => {
    setSearchQuery('');
    
    // Only trigger a new search if there was a previous query
    if (lastSearchParamsRef.current.query) {
      // Small delay to let the state update first
      setTimeout(() => {
        lastSearchParamsRef.current.query = '';
        onSearch('', currentFilters);
      }, 0);
    }
  }, [currentFilters, onSearch]);

  return (
    <div className={cn("relative", className)} ref={searchContainerRef}>
      <form onSubmit={handleSearch} className="relative" ref={formRef}>
        <div className="flex items-center gap-2 p-2 bg-white/90 dark:bg-black/90 backdrop-blur-sm rounded-full shadow-soft">
          {/* Search Input */}
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder={placeholder || t('search.placeholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-transparent border-none pl-12 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500/50 rounded-full text-black dark:text-white"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={handleClearSearch}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="Clear search"
              >
                <X size={16} />
              </button>
            )}
          </div>

          {/* Near Me Button */}
          {latitude && longitude && (
            <button
              type="button"
              onClick={() => {
                handleNearMeSearch();
                // Smoothly scroll to near-me section if it exists
                const nearMeSection = document.getElementById('near-me');
                nearMeSection?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="hidden md:flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white rounded-full transition-colors"
              aria-label="Search near my location"
              disabled={locationLoading}
            >
              <MapPin size={18} className={locationLoading ? 'animate-pulse' : ''} />
              <span>{t('search.nearMe')}</span>
            </button>
          )}

          {/* Filter Toggle */}
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "p-2 rounded-full transition-colors",
              showFilters
                ? "bg-primary-500 text-white"
                : "text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
            )}
            aria-label="Toggle filters"
            aria-expanded={showFilters}
          >
            <Filter size={20} />
          </button>

          {/* Search Button */}
          <button
            type="submit"
            className="hidden md:flex items-center justify-center bg-primary-500 hover:bg-primary-600 text-white px-6 py-2 rounded-full font-medium transition-colors"
          >
            {t('search.button')}
          </button>
        </div>

        {/* Filters Dropdown */}
        {showFilters && (
          <div className="absolute top-full mt-2 w-full bg-white/95 dark:bg-black/95 backdrop-blur-sm rounded-xl shadow-elevation p-4 border border-gray-200 dark:border-gray-800 z-20">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-black dark:text-white">{t('search.filters')}</h3>
              {selectedCategories.length > 0 && (
                <button
                  onClick={clearAllCategories}
                  className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  {t('search.clearAll')}
                </button>
              )}
            </div>

            {/* Categories */}
            {categories.length > 0 && (
              <div>
                <h4 className="text-sm text-gray-500 dark:text-gray-400 mb-2">{t('search.categories')}</h4>
                <div className="flex flex-wrap gap-2">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      type="button"
                      onClick={() => toggleCategory(category.id)}
                      className={cn(
                        "px-3 py-1 rounded-full text-sm transition-colors",
                        selectedCategories.includes(category.id)
                          ? "bg-primary-500 text-white"
                          : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
                      )}
                    >
                      {category.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Apply Filters Button (for mobile) */}
            <button
              type="submit"
              className="mt-4 w-full md:hidden bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              {t('search.button')}
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

export default SearchBar;