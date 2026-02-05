import { memo, useState, useRef, useEffect } from 'react';
import { MapPin, Leaf, Clock } from 'lucide-react';
import { Deal } from '@/types/deals';
import { formatDistanceToNow } from '@/utils/date';
import { cn } from '@/utils/cn';

interface DealCardProps {
  deal: Deal;
  priority?: boolean;
  className?: string;
  onClick?: () => void;
}

export const DealCard = memo(function DealCard({ 
  deal, 
  priority = false, 
  className = '',
  onClick
}: DealCardProps) {
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  
  // Calculate discount percentage once
  const discountPercentage = Math.round((1 - deal.discounted_price / deal.original_price) * 100);
  
  // Preload image with low quality placeholder
  useEffect(() => {
    // Check if image is already in browser cache
    if (imgRef.current?.complete) {
      setIsImageLoaded(true);
    }
  }, []);

  // Handle click for deal selection
  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  return (
    <div
      ref={cardRef}
      className={cn(
        'group relative bg-neutral-900 rounded-xl overflow-hidden shadow-card hover:shadow-elevation transition-all duration-300',
        className
      )}
      id={`deal-${deal.id}`}
      onClick={handleClick}
      role="article"
      aria-labelledby={`deal-title-${deal.id}`}
    >
      {/* Image container with fixed aspect ratio */}
      <div className="relative" style={{ aspectRatio: "16/9" }}>
        {/* Background color while loading */}
        <div 
          className={cn(
            "absolute inset-0 bg-neutral-800 transition-opacity duration-300",
            isImageLoaded ? "opacity-0" : "opacity-100"
          )} 
        />
        
        <img
          ref={imgRef}
          src={deal.image}
          alt={deal.title}
          width="800"
          height="450"
          className="absolute inset-0 w-full h-full object-cover transition-opacity duration-300"
          loading={priority ? 'eager' : 'lazy'}
          onLoad={() => setIsImageLoaded(true)}
          style={{ opacity: isImageLoaded ? 1 : 0 }}
        />
        
        {/* Discount badge */}
        <div
          className="absolute top-2 right-2 bg-primary-500 text-white px-3 py-1 rounded-full text-sm font-semibold"
          aria-label={`${discountPercentage}% discount`}
        >
          {discountPercentage}% off
        </div>
      </div>

      {/* Content section */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3
            id={`deal-title-${deal.id}`}
            className="text-lg font-display font-semibold text-neutral-100 line-clamp-2"
            style={{ minHeight: "3.5rem" }}
          >
            {deal.title}
          </h3>
          
          {/* Sustainability score */}
          {deal.sustainability_score && (
            <div
              className="flex items-center space-x-1 text-primary-400"
              aria-label={`Sustainability score: ${deal.sustainability_score}`}
            >
              <Leaf size={16} aria-hidden="true" />
              <span className="text-sm font-medium">{deal.sustainability_score.toFixed(1)}</span>
            </div>
          )}
        </div>

        {/* Description with fixed height */}
        <p
          className="text-neutral-400 text-sm line-clamp-2 mb-3"
          style={{ minHeight: "2.5rem" }}
        >
          {deal.description}
        </p>

        {/* Price information */}
        <div className="flex items-center justify-between">
          <div className="flex items-baseline space-x-2">
            <span className="text-xl font-display font-semibold text-primary-400">
              ${deal.discounted_price.toFixed(2)}
            </span>
            <span className="text-sm text-neutral-500 line-through">
              ${deal.original_price.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Footer metadata */}
        <div className="mt-3 pt-3 border-t border-neutral-800 flex items-center justify-between text-sm">
          {deal.distance !== undefined && (
            <div
              className="flex items-center text-neutral-400"
              aria-label={`${typeof deal.distance === 'number' ? deal.distance.toFixed(1) : deal.distance} kilometers away`}
            >
              <MapPin size={14} className="mr-1" aria-hidden="true" />
              <span>{typeof deal.distance === 'number' ? deal.distance.toFixed(1) : deal.distance}km away</span>
            </div>
          )}
          
          {deal.end_date && (
            <div
              className="flex items-center text-neutral-400"
              aria-label={`Expires ${formatDistanceToNow(new Date(deal.end_date))}`}
            >
              <Clock size={14} className="mr-1" aria-hidden="true" />
              <span>{formatDistanceToNow(new Date(deal.end_date))}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

export default DealCard;