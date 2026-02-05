import React, { memo, useMemo } from 'react';
import { Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { MapPin, Leaf, Heart } from 'lucide-react';
import { Deal } from '@/types/deals';

/*===========================================================================
  ICON DEFINITIONS
  ---------------------------------------------------------------------------
  The following icon definitions combine your previous marker icons with
  the newer custom icons that were originally in CustomIcons.tsx.
===========================================================================*/

// Regular deal marker icon
const dealMarkerIcon = new Icon({
  iconUrl: '/markers/deal-marker.svg',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
});

// Sustainable deal marker icon
const sustainableDealMarkerIcon = new Icon({
  iconUrl: '/markers/sustainable-deal-marker.svg',
  iconSize: [38, 38],
  iconAnchor: [19, 38],
  popupAnchor: [0, -38],
});

// Highlighted marker for a selected deal
const highlightedIcon = new Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [35, 57], // Slightly larger
  iconAnchor: [17, 57],
  popupAnchor: [1, -54],
  shadowSize: [41, 41],
  className: 'highlighted-marker',
});

// Fallback/default marker icon using a modern custom marker icon
const defaultIcon = new Icon({
  iconUrl:
    'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM3YzNhZWQiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cGF0aCBkPSJNMjEgMTBjMCA3LTkgMTMtOSAxM3MtOS02LTktMTNhOSA5IDAgMCAxIDE4IDB6Ii8+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMCIgcj0iMyIvPjwvc3ZnPg==',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
  className: 'drop-shadow-lg',
});

// Modern user location icon (you can export this if other components need it)
export const userLocationIcon = new Icon({
  iconUrl:
    'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiM3YzNhZWQiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgZmlsbD0iI2VkZTlmZSIvPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjMiIGZpbGw9IiM3YzNhZWQiLz48L3N2Zz4=',
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -16],
  className: 'animate-pulse',
});

interface DealMarkerProps {
  deal: Deal;
  isSelected: boolean;
  isSustainable: boolean;
  minSustainabilityScore: number;
  onMarkerClick: (deal: Deal) => void;
  formatCurrency?: (value: number) => string;
  formatPercentage?: (value: number) => string;
}

const DealMarker: React.FC<DealMarkerProps> = ({
  deal,
  isSelected,
  isSustainable,
  minSustainabilityScore,
  onMarkerClick,
  formatCurrency,
  formatPercentage,
}) => {
  // Extract latitude and longitude from the deal object
  const location = useMemo(() => {
    const lat =
      deal.location?.latitude !== undefined
        ? deal.location.latitude
        : typeof deal.latitude === 'number'
        ? deal.latitude
        : null;
    const lng =
      deal.location?.longitude !== undefined
        ? deal.location.longitude
        : typeof deal.longitude === 'number'
        ? deal.longitude
        : null;
    if (lat === null || lng === null) return null;
    return [lat, lng] as [number, number];
  }, [deal]);

  if (!location) return null;

  // Choose the appropriate icon based on deal status
  const iconToUse = useMemo(() => {
    try {
      if (isSelected) return highlightedIcon;
      if (isSustainable) return sustainableDealMarkerIcon;
      return dealMarkerIcon;
    } catch (e) {
      return isSelected ? highlightedIcon : defaultIcon;
    }
  }, [isSelected, isSustainable]);

  return (
    <Marker
      position={location}
      icon={iconToUse}
      eventHandlers={{
        click: () => onMarkerClick(deal),
      }}
    >
      <Popup>
        <div className="max-w-xs">
          <h3 className="font-bold text-lg mb-2">{deal.title}</h3>
          <div className="flex justify-between items-center mb-2">
            <div>
              <p className="text-sm text-neutral-600">
                {typeof deal.shop === 'object' ? deal.shop?.name : `Shop ID: ${deal.shop}`}
              </p>
              <div className="flex items-center space-x-2">
                <span className="text-primary-500 font-semibold">
                  {formatCurrency ? formatCurrency(deal.discounted_price) : `$${deal.discounted_price.toFixed(2)}`}
                </span>
                <span className="text-neutral-400 line-through text-xs">
                  {formatCurrency ? formatCurrency(deal.original_price) : `$${deal.original_price.toFixed(2)}`}
                </span>
                <span className="bg-primary-500 text-white text-xs px-2 py-0.5 rounded">
                  {formatPercentage
                    ? formatPercentage(((deal.original_price - deal.discounted_price) / deal.original_price) * 100)
                    : `${(((deal.original_price - deal.discounted_price) / deal.original_price) * 100).toFixed(0)}%`}
                </span>
              </div>
            </div>
            {isSustainable && deal.sustainability_score && (
              <div
                className="flex items-center space-x-1 text-green-500 bg-green-500/10 px-2 py-1 rounded"
                title="Sustainable Deal"
              >
                <Leaf size={16} />
                <span className="text-xs font-medium">{deal.sustainability_score.toFixed(1)}</span>
              </div>
            )}
          </div>
          <div className="flex justify-between items-center text-sm text-neutral-500">
            <div className="flex items-center space-x-1">
              <MapPin size={14} />
              <span>{deal.distance?.toFixed(1) || '?'} km</span>
            </div>
            <div className="flex items-center space-x-1">
              <Heart size={14} />
              <span>{deal.clicks_count || 0} saves</span>
            </div>
          </div>
        </div>
      </Popup>
    </Marker>
  );
};

export default memo(DealMarker);
