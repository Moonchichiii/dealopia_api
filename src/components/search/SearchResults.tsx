import { useTranslation } from 'react-i18next';
import { Filter } from 'lucide-react';

interface SearchResultsProps {
  query: string;
  totalResults: number;
  isLoading: boolean;
  onFilterClick?: () => void;
}

const SearchResults: React.FC<SearchResultsProps> = ({
  query,
  totalResults,
  isLoading,
  onFilterClick,
}) => {
  const { t } = useTranslation();

  return (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h2 className="text-xl font-semibold mb-1">
          {isLoading
            ? t('search.searching')
            : totalResults > 0
              ? t('search.results', { query })
              : t('search.noResults', { query })}
        </h2>
        {totalResults > 0 && !isLoading && (
          <p className="text-neutral-500">
            {t('search.foundDeals', { count: totalResults })}
          </p>
        )}
      </div>

      {totalResults > 0 && !isLoading && onFilterClick && (
        <button
          onClick={onFilterClick}
          className="flex items-center gap-2 px-4 py-2 bg-neutral-100 dark:bg-neutral-800 rounded-full hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-colors"
        >
          <Filter size={18} />
          <span>{t('search.filters')}</span>
        </button>
      )}
    </div>
  );
};

export default SearchResults;
