import React, { useEffect, useState, useCallback } from 'react';
import { useGeolocation } from '@/hooks/useGeolocation';
import { locationService } from '@/api';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import { userLocationIcon } from '@/components/map/DealMarker';
import Loader from '@/components/ui/Loader';
import { Location } from '@/types/locations';
import { MapPin, Navigation, Search, Compass } from 'lucide-react';

const LocationTracker: React.FC = () => {
  const { latitude, longitude, loading: geolocationLoading, error: geolocationError, getLocation, addressString } = useGeolocation({ autoDetect: true });
  const [nearbyLocations, setNearbyLocations] = useState<Location[]>([]);
  const [nearbyLoading, setNearbyLoading] = useState<boolean>(false);
  const [nearbyError, setNearbyError] = useState<string | null>(null);
  const [searchRadius, setSearchRadius] = useState<number>(10);
  const [locationsCount, setLocationsCount] = useState<number>(0);

  // Fetch nearby locations
  const fetchNearbyLocations = useCallback(async () => {
    if (!latitude || !longitude) return;
    
    setNearbyLoading(true);
    setNearbyError(null);
    
    try {
      console.info(`Executing PostGIS spatial query: Finding locations within ${searchRadius}km of (${latitude}, ${longitude})`);
      // This uses your backend's GeoDjango/PostGIS capability
      const locations = await locationService.getNearbyLocations(latitude, longitude, searchRadius);
      setNearbyLocations(Array.isArray(locations) ? locations : []);
      setLocationsCount(locations.length);
      
      // Log to demonstrate the PostGIS query is working
      console.info(`Found ${locations.length} locations within ${searchRadius}km using PostGIS spatial query`);
    } catch (err) {
      console.error('Error fetching nearby locations:', err);
      setNearbyError('Failed to fetch nearby locations.');
    } finally {
      setNearbyLoading(false);
    }
  }, [latitude, longitude, searchRadius]);

  // Get location if not already available
  useEffect(() => {
    if (!latitude && !longitude && !geolocationLoading && !geolocationError) {
      getLocation().catch((err) => {
        console.error('Error explicitly getting location:', err);      
      });
    }
  }, [latitude, longitude, getLocation, geolocationLoading, geolocationError]);

  // Fetch nearby locations when coordinates change
  useEffect(() => {
    if (latitude && longitude) {
      fetchNearbyLocations();
    }
  }, [latitude, longitude, searchRadius, fetchNearbyLocations]);

  // Show loading state
  if (geolocationLoading) {
    return <Loader progress={50} />;
  }

  // Show error state
  if (geolocationError) {
    return (
      <div className="p-4 text-center">
        <p className="text-red-500 mb-4">{geolocationError}</p>
        <button
          onClick={getLocation}
          className="px-4 py-2 bg-primary-500 text-white rounded hover:bg-primary-600 transition-colors"
        >
          Retry Location Detection
        </button>
      </div>
    );
  }

  const mapCenter: [number, number] = latitude && longitude ? [latitude, longitude] : [51.505, -0.09]; // Default center if location unknown

  return (
    <div className="my-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-4 gap-3">
        <h2 className="text-2xl font-bold">Your Location & Nearby Places</h2>
        
        <div className="flex items-center gap-3">
          {/* Search radius selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-neutral-400">Radius:</span>
            <select 
              value={searchRadius} 
              onChange={(e) => setSearchRadius(Number(e.target.value))}
              className="bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-white text-sm"
            >
              <option value={1}>1 km</option>
              <option value={5}>5 km</option>
              <option value={10}>10 km</option>
              <option value={25}>25 km</option>
              <option value={50}>50 km</option>
            </select>
          </div>
          
          {/* Refresh button */}
          <button
            onClick={fetchNearbyLocations}
            disabled={!latitude || !longitude || nearbyLoading}
            className="flex items-center gap-1 px-3 py-1.5 bg-primary-500/20 text-primary-400 text-sm rounded border border-primary-500/30 hover:bg-primary-500/30 transition-colors disabled:opacity-50"
          >
            <Compass size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>
      
      {/* Location status display */}
      {addressString && (
        <div className="mb-4 p-3 bg-neutral-800/50 rounded-lg border border-neutral-700/30">
          <div className="flex items-center gap-2 text-neutral-300">
            <MapPin size={16} className="text-primary-400" />
            <span>{addressString}</span>
          </div>
        </div>
      )}
      
      {/* PostGIS highlight */}
      {latitude && longitude && !nearbyLoading && (
        <div className="mb-4 p-3 bg-black/30 rounded-lg border border-primary-800/30">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-primary-500/20 rounded-full">
              <Search size={14} className="text-primary-400" />
            </div>
            <p className="text-sm text-neutral-300">
              <span className="text-primary-400 font-medium">PostGIS Spatial Query:</span> Found 
              <span className="text-white font-medium mx-1">{locationsCount}</span> 
              locations within <span className="text-white font-medium">{searchRadius}km</span> of your position
            </p>
          </div>
        </div>
      )}
      
      {latitude && longitude ? (
        <div className="rounded-lg overflow-hidden border border-neutral-700/50 shadow-lg">
          <MapContainer center={mapCenter} zoom={13} style={{ height: '450px', width: '100%' }}>
            {/* Dark theme tile layer for better aesthetics */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            
            {/* User location marker */}
            <Marker position={mapCenter} icon={userLocationIcon}>
              <Popup>
                <div className="p-2">
                  <h3 className="font-bold">Your Location</h3>
                  <p className="text-sm">{addressString || "Current position"}</p>
                  <p className="text-xs text-gray-600 mt-1">Coordinates for PostGIS query:</p>
                  <p className="text-xs font-mono">{latitude.toFixed(6)}, {longitude.toFixed(6)}</p>
                </div>
              </Popup>
            </Marker>
            
            {/* Search radius visualization */}
            <CircleMarker 
              center={mapCenter}
              radius={50} // Visual radius on map
              pathOptions={{ 
                color: '#8b5cf6',
                fillColor: '#8b5cf680',
                fillOpacity: 0.1,
                weight: 1,
                dashArray: '5, 5',
              }}
            />
            
            {/* Nearby locations */}
            {nearbyLocations.map(loc => (
              <Marker 
                key={loc.id} 
                position={[
                  loc.latitude || 0, 
                  loc.longitude || 0
                ]}
              >
                <Popup>
                  <div className="p-2">
                    <h3 className="font-bold text-base">{loc.name || "Location"}</h3>
                    <p className="text-sm font-medium">{loc.address}</p>
                    <p className="text-xs text-gray-600">{loc.city}, {loc.country}</p>
                    <p className="text-xs mt-2">
                      <span className="font-medium">PostGIS ID:</span> {loc.id}
                    </p>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      ) : (
        <div className="p-4 text-center text-gray-600">
          Detecting your location... If prompted, please allow location access.
        </div>
      )}
      
      {/* Loading and error states */}
      {nearbyLoading && (
        <div className="text-center mt-4 p-3 bg-neutral-800/50 rounded-lg animate-pulse">
          <p className="text-neutral-300">
            Running PostGIS spatial query to find locations within {searchRadius}km...
          </p>
        </div>
      )}
      
      {nearbyError && (
        <div className="text-center mt-4 p-3 bg-red-900/20 border border-red-800/40 rounded-lg">
          <p className="text-red-400">{nearbyError}</p>
        </div>
      )}
      
      {/* PostGIS attribution */}
      <div className="mt-4 text-center text-xs text-neutral-500">
        <p>Powered by PostGIS and Django GeoDjango spatial database extensions</p>
      </div>
    </div>
  );
};

export default LocationTracker;