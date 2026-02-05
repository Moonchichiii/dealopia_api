import { useState } from 'react';
import { ChevronDown, ChevronUp, Grid, Map } from 'lucide-react';
import SearchResults from '@/components/search/SearchResults';
import { DealCard } from '@/components/ui/DealCard';
import DealMap from '@/components/map/DealMap';

interface SearchSectionProps {
  query: string;
  results: any[];
  totalResults: number;
  isLoading: boolean;
  onFilterClick?: () => void;
}

const SearchSection: React.FC<SearchSectionProps> = ({
  query,
  results,
  totalResults,
  isLoading,
  onFilterClick,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'map'>('grid');
  const [selectedDeal, setSelectedDeal] = useState<number | null>(null);

  // Skip rendering if no query or no results and not loading
  if (!query && !isLoading && !results?.length) {
    return null;
  }

  return (
    <div className="mt-6 pb-6 border-b border-gray-200 dark:border-gray-800">
      <div className="flex items-center justify-between">
        <SearchResults
          query={query}
          totalResults={totalResults}
          isLoading={isLoading}
          onFilterClick={onFilterClick}
        />

        <div className="flex items-center gap-2">
          {/* View toggle */}
          {results && results.length > 0 && (
            <div className="bg-neutral-200 dark:bg-neutral-800 rounded-full p-1 flex">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-1 rounded-full text-sm flex items-center gap-1 ${
                  viewMode === 'grid'
                    ? 'bg-primary-500 text-white' // Active state often keeps consistent text color
                    : 'text-neutral-500 hover:text-gray-900 dark:text-neutral-400 dark:hover:text-white'
                }`}
              >
                <Grid size={16} />
                <span className="hidden sm:inline">Grid</span>
              </button>
              <button
                onClick={() => setViewMode('map')}
                className={`px-3 py-1 rounded-full text-sm flex items-center gap-1 ${
                  viewMode === 'map'
                    ? 'bg-primary-500 text-white' // Active state often keeps consistent text color
                    : 'text-neutral-500 hover:text-gray-900 dark:text-neutral-400 dark:hover:text-white'
                }`}
              >
                <Map size={16} />
                <span className="hidden sm:inline">Map</span>
              </button>
            </div>
          )}

          {/* Collapse/Expand button */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 bg-neutral-200 hover:bg-neutral-300 text-gray-900 dark:bg-neutral-800 dark:hover:bg-neutral-700 dark:text-white rounded-full"
            aria-label={collapsed ? "Expand results" : "Collapse results"}
          >
            {collapsed ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="mt-4">
          {/* Content based on state */}
          {isLoading ? (
            // Loading skeleton
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, index) => (
                <div key={index} className="bg-white/70 dark:bg-neutral-900/50 backdrop-blur-sm rounded-2xl overflow-hidden border border-neutral-200 dark:border-neutral-800/50 animate-pulse">
                  <div className="w-full aspect-video bg-neutral-200 dark:bg-neutral-800"></div>
                  <div className="p-4">
                    <div className="h-5 bg-neutral-200 dark:bg-neutral-800 rounded w-3/4 mb-3"></div>
                    <div className="h-4 bg-neutral-200 dark:bg-neutral-800 rounded w-1/3 mb-3"></div>
                    <div className="h-3 bg-neutral-200 dark:bg-neutral-800 rounded w-full"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : results?.length > 0 ? (
            <>
              {/* Map view */}
              {viewMode === 'map' && (
                <div className="mb-8 rounded-xl overflow-hidden border border-neutral-200 dark:border-neutral-800/50">
                  <DealMap
                    deals={results}
                    height="500px"
                    selectedDealId={selectedDeal}
                    onDealSelect={(deal) => setSelectedDeal(deal.id)}
                    showUserLocation={true}
                  />
                </div>
              )}

              {/* Grid view */}
              {viewMode === 'grid' && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {results.map((deal) => (
                    <DealCard
                      key={deal.id}
                      deal={deal}
                      id={`deal-${deal.id}`}
                      priority={deal.id === selectedDeal}
                      className={
                        deal.id === selectedDeal
                          ? 'ring-2 ring-primary-500 ring-offset-4 ring-offset-white dark:ring-offset-black' // Adjusted ring offset for light/dark
                          : ''
                      }
                      onClick={() => setSelectedDeal(deal.id)}
                    />
                  ))}
                </div>
              )}
            </>
          ) : query ? (
            // No results
            <div className="bg-white/50 dark:bg-neutral-900/30 backdrop-blur-sm rounded-xl border border-neutral-200 dark:border-neutral-800/50 p-8 text-center">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No results found for "{query}"
              </h3>
              <p className="text-neutral-600 dark:text-neutral-400 mb-4 max-w-md mx-auto">
                Try different search terms or browse deals near you
              </p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default SearchSection;