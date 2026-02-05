import React, {
  useEffect,
  useState,
  useMemo,
  useCallback,
  memo
} from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
  useMapEvents,
  ZoomControl,
  AttributionControl,
  Tooltip
} from 'react-leaflet';
import { Icon, LatLngBounds, latLngBounds } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Deal } from '@/types/deals';
import { useGeolocation } from '@/hooks/useGeolocation';
import { useFormatters } from '@/utils/formatters';
import { locationService } from '@/api';
import {
  MapPin,
  Leaf,
  ArrowUpRight,
  Tag,
  Clock
} from 'lucide-react';
import { MapErrorBoundary } from '@/components/map/MapErrorBoundary';

// Marker clustering
import MarkerClusterGroup from 'react-leaflet-markercluster';

// Icon definitions
const userLocationIcon = new Icon({
  iconUrl: '/markers/user-location.svg',
  iconSize: [38, 38],
  iconAnchor: [19, 38],
  popupAnchor: [0, -38]
});

const dealMarkerIcon = new Icon({
  iconUrl: '/markers/deal-marker.svg',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
});

const sustainableDealMarkerIcon = new Icon({
  iconUrl: '/markers/sustainable-deal-marker.svg',
  iconSize: [38, 38],
  iconAnchor: [19, 38],
  popupAnchor: [0, -38]
});

const selectedDealIcon = new Icon({
  iconUrl: '/markers/selected-marker.svg',
  iconSize: [42, 42],
  iconAnchor: [21, 42],
  popupAnchor: [0, -42]
});

// Fallback icon if custom SVGs fail to load
const defaultIcon = new Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Components for loading and error states
const MapLoadingPlaceholder = () => (
  <div className="w-full h-full bg-neutral-900/80 rounded-lg flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500 mx-auto mb-4"></div>
      <p className="text-neutral-300">Loading map data...</p>
    </div>
  </div>
);

const MapErrorDisplay = ({ message }: { message: string }) => (
  <div className="w-full h-full bg-neutral-900/80 rounded-lg flex items-center justify-center p-6">
    <div className="text-center max-w-md">
      <div className="bg-red-500/20 p-3 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
        <MapPin className="text-red-400 w-8 h-8" />
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">Map Error</h3>
      <p className="text-neutral-300 mb-4">{message}</p>
      <button
        onClick={() => window.location.reload()}
        className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
      >
        Refresh
      </button>
    </div>
  </div>
);

// Individual deal marker component
const DealMarker = memo(
  ({
    deal,
    isSelected,
    isSustainable,
    onMarkerClick,
    formatCurrency,
    formatPercentage
  }: {
    deal: Deal;
    isSelected: boolean;
    isSustainable: boolean;
    onMarkerClick: (deal: Deal) => void;
    formatCurrency: (value: number) => string;
    formatPercentage: (value: number) => string;
  }) => {
    // Extract coordinates from deal object, handling both direct and nested properties
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
    
    // Skip rendering if coordinates are missing
    if (lat === null || lng === null) return null;

    // Select appropriate icon based on deal properties
    const icon = isSelected
      ? selectedDealIcon
      : isSustainable
      ? sustainableDealMarkerIcon
      : dealMarkerIcon;

    // Get shop name, handling both string ID and object
    const shopName = 
      typeof deal.shop === 'object' && deal.shop?.name 
        ? deal.shop.name 
        : 'Local Business';

    return (
      <Marker
        position={[lat, lng]}
        icon={icon}
        eventHandlers={{
          click: () => onMarkerClick(deal)
        }}
      >
        <Popup className="deal-popup">
          <div className="deal-popup-content p-1 text-neutral-900">
            <h3 className="font-bold text-base truncate">{deal.title}</h3>
            <p className="text-sm text-primary-700 mb-2">{shopName}</p>
            
            <div className="flex gap-2 mb-2">
              {deal.discount_percentage > 0 && (
                <span className="text-xs bg-accent-100 text-accent-700 px-1.5 py-0.5 rounded flex items-center">
                  <Tag size={10} className="mr-1" />
                  {formatPercentage(deal.discount_percentage)} OFF
                </span>
              )}
              
              {deal.sustainability_score > 0 && (
                <span className="text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded flex items-center">
                  <Leaf size={10} className="mr-1" />
                  {Math.round(deal.sustainability_score * 10)}% Eco
                </span>
              )}
              
              {deal.end_date && (
                <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded flex items-center">
                  <Clock size={10} className="mr-1" />
                  Ends soon
                </span>
              )}
            </div>
            
            {deal.description && (
              <p className="text-xs text-neutral-600 line-clamp-2 mb-2">
                {deal.description}
              </p>
            )}
            
            <div className="flex justify-between items-center border-t border-neutral-200 pt-2 mt-1">
              <div className="flex items-center">
                {deal.original_price && deal.discounted_price && (
                  <div className="flex flex-col">
                    <span className="text-xs text-neutral-500 line-through">
                      {formatCurrency(deal.original_price)}
                    </span>
                    <span className="text-sm font-bold text-accent-600">
                      {formatCurrency(deal.discounted_price)}
                    </span>
                  </div>
                )}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onMarkerClick(deal);
                }}
                className="text-xs text-primary-600 hover:text-primary-800 font-medium flex items-center"
              >
                Details
                <ArrowUpRight size={12} className="ml-0.5" />
              </button>
            </div>
          </div>
        </Popup>
      </Marker>
    );
  }
);

// Tile Loading Tracker Component
const TileLoadTracker = ({ onTilesLoaded }: { onTilesLoaded: () => void }) => {
  const map = useMap();

  useEffect(() => {
    const handleTileLoad = () => onTilesLoaded();
    map.on('baselayerchange', handleTileLoad);
    map.on('load', handleTileLoad);
    if (map.getZoom()) onTilesLoaded();
    return () => {
      map.off('baselayerchange', handleTileLoad);
      map.off('load', handleTileLoad);
    };
  }, [map, onTilesLoaded]);

  return null;
};

// Map Updater Component
const MapUpdater = memo(
  ({
    center,
    bounds,
    zoom
  }: {
    center: [number, number];
    bounds?: LatLngBounds | null;
    zoom?: number;
  }) => {
    const map = useMap();
    useEffect(() => {
      if (bounds && bounds.isValid()) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
      } else if (center) {
        map.setView(center, zoom || map.getZoom());
      }
    }, [center, bounds, map, zoom]);
    return null;
  }
);

// Map Interactions Component
const MapInteractions = memo(
  ({
    onLocationUpdate
  }: {
    onLocationUpdate?: (coords: { latitude: number; longitude: number }) => void;
  }) => {
    useMapEvents({
      locationfound: (e) => {
        const { lat, lng } = e.latlng;
        onLocationUpdate?.({ latitude: lat, longitude: lng });
      },
      locationerror: (e) => console.error('Location error:', e)
    });
    return null;
  }
);

// DealMap Component
interface DealMapProps {
  deals: Deal[];
  height?: string;
  className?: string;
  onDealSelect?: (deal: Deal) => void;
  selectedDealId?: string | number | null;
  zoom?: number;
  showUserLocation?: boolean;
  minSustainabilityScore?: number;
}

const DealMap: React.FC<DealMapProps> = ({
  deals,
  height = '500px',
  className = '',
  onDealSelect,
  selectedDealId = null,
  zoom = 13,
  showUserLocation = true,
  minSustainabilityScore = 6.0
}) => {
  // Use the updated useGeolocation hook
  const {
    latitude,
    longitude,
    loading: locationLoading,
    error: locationError,
    addressString
  } = useGeolocation();

  const { formatCurrency, formatPercentage } = useFormatters();

  const [center, setCenter] = useState<[number, number]>([51.505, -0.09]);
  const [mapError, setMapError] = useState<string | null>(null);
  const [tilesLoaded, setTilesLoaded] = useState(false);
  const [visibleDeals, setVisibleDeals] = useState<Deal[]>([]);

  // Optional performance tracking
  const [renderStats, setRenderStats] = useState({
    markersCount: 0,
    renderTime: 0
  });

  useEffect(() => {
    if (locationError) {
      setMapError('Unable to retrieve location. Please enable location services.');
    }
  }, [locationError]);

  // Helper function to extract coordinates from a deal object
  const getLocationFromDeal = useCallback((deal: Deal): [number, number] | null => {
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
    return lat !== null && lng !== null ? [lat, lng] : null;
  }, []);

  // Process deals: only include those with valid coordinates and meeting sustainability criteria
  const processedDeals = useMemo(() => {
    return deals.filter((deal) => {
      const coords = getLocationFromDeal(deal);
      return coords !== null && 
        (!minSustainabilityScore || (deal.sustainability_score || 0) >= minSustainabilityScore);
    });
  }, [deals, minSustainabilityScore, getLocationFromDeal]);

  // Calculate bounds to include all markers and user location (if available)
  const bounds = useMemo(() => {
    if (!processedDeals.length) return null;
    
    const latLngs = processedDeals
      .map(getLocationFromDeal)
      .filter(Boolean) as [number, number][];
    
    if (latitude && longitude) {
      latLngs.push([latitude, longitude]);
    }
    
    return latLngs.length ? latLngBounds(latLngs) : null;
  }, [processedDeals, latitude, longitude, getLocationFromDeal]);

  // Update center when user location changes
  useEffect(() => {
    if (latitude && longitude) {
      setCenter([latitude, longitude]);
    }
  }, [latitude, longitude]);

  // Progressive loading of markers for performance
  useEffect(() => {
    if (processedDeals.length < 100) {
      setVisibleDeals(processedDeals);
      return;
    }
    
    if (tilesLoaded) {
      // For large datasets, first show nearby deals
      if (latitude && longitude) {
        const nearbyDeals = processedDeals.filter((deal) => {
          const loc = getLocationFromDeal(deal);
          if (!loc) return false;
          
          const distance = locationService.calculateDistance(
            latitude,
            longitude,
            loc[0],
            loc[1]
          );
          return distance < 10; // within 10km
        });
        
        setVisibleDeals(nearbyDeals.slice(0, 20));
        
        // Then progressively show all deals
        const timeoutId = setTimeout(() => {
          setVisibleDeals(processedDeals);
        }, 500);
        
        return () => clearTimeout(timeoutId);
      } else {
        // If no location, just show the first 50 deals
        setVisibleDeals(processedDeals.slice(0, 50));
      }
    } else {
      // Before tiles are loaded, show just a few deals
      setVisibleDeals(processedDeals.slice(0, 20));
    }
  }, [processedDeals, tilesLoaded, latitude, longitude, getLocationFromDeal]);

  // Performance monitoring
  useEffect(() => {
    const startTime = performance.now();
    const timeoutId = setTimeout(() => {
      const endTime = performance.now();
      setRenderStats({
        markersCount: visibleDeals.length,
        renderTime: Math.round(endTime - startTime)
      });
    }, 0);
    
    return () => clearTimeout(timeoutId);
  }, [visibleDeals]);

  // Log performance metrics in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`Rendered ${renderStats.markersCount} markers in ${renderStats.renderTime}ms`);
    }
  }, [renderStats]);

  const handleMarkerClick = useCallback(
    (deal: Deal) => {
      onDealSelect && onDealSelect(deal);
    },
    [onDealSelect]
  );

  // Loading and error states
  if (locationLoading) {
    return <MapLoadingPlaceholder />;
  }
  
  if (mapError) {
    return <MapErrorDisplay message={mapError} />;
  }

  return (
    <div className={`relative rounded-lg overflow-hidden ${className}`} style={{ height }}>
      <MapErrorBoundary>
        <MapContainer 
          center={center} 
          zoom={zoom} 
          style={{ height: '100%', width: '100%' }} 
          className="z-0" 
          zoomControl={false}
        >
          {/* Dark tile layer for better contrast with markers */}
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          <ZoomControl position="bottomright" />

          {/* Map interactions */}
          <MapInteractions 
            onLocationUpdate={(coords) => {
              // Optional: update state or trigger events when map location changes
            }} 
          />

          {/* Track tile loading */}
          <TileLoadTracker onTilesLoaded={() => setTilesLoaded(true)} />

          {/* Update map center and bounds */}
          <MapUpdater center={center} bounds={bounds} zoom={zoom} />

          {/* User location marker */}
          {showUserLocation && latitude && longitude && (
            <Marker position={[latitude, longitude]} icon={userLocationIcon}>
              <Popup>
                <div className="text-neutral-900">
                  <p className="font-medium">Your Location</p>
                  {addressString && <p className="text-sm text-neutral-500">{addressString}</p>}
                </div>
              </Popup>
              {addressString && (
                <Tooltip permanent direction="bottom" offset={[0, 10]} className="location-tooltip">
                  {addressString}
                </Tooltip>
              )}
            </Marker>
          )}

          {/* Deal markers with clustering for performance */}
          <MarkerClusterGroup
            chunkedLoading
            spiderfyOnMaxZoom={true}
            disableClusteringAtZoom={15}
            maxClusterRadius={50}
          >
            {visibleDeals.map((deal) => (
              <DealMarker
                key={deal.id}
                deal={deal}
                isSelected={selectedDealId !== null && deal.id === selectedDealId}
                isSustainable={(deal.sustainability_score || 0) >= minSustainabilityScore}
                onMarkerClick={handleMarkerClick}
                formatCurrency={formatCurrency}
                formatPercentage={formatPercentage}
              />
            ))}
          </MarkerClusterGroup>

          <AttributionControl prefix="Powered by Dealopia" position="bottomright" />
        </MapContainer>
      </MapErrorBoundary>
    </div>
  );
};

export default DealMap;