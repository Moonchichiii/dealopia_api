import { useEffect } from 'react';
import { useMap } from 'react-leaflet';

interface TileLoadTrackerProps {
  onTilesLoaded: () => void;
}

const TileLoadTracker: React.FC<TileLoadTrackerProps> = ({ onTilesLoaded }) => {
  const map = useMap();
  
  useEffect(() => {
    const handleTileLoad = () => {
      // Set tiles as loaded when base layer is ready
      onTilesLoaded();
    };
    
    map.on('baselayerchange', handleTileLoad);
    map.on('load', handleTileLoad);
    
    // If map is already loaded, update state
    if (map.getZoom()) {
      onTilesLoaded();
    }
    
    return () => {
      map.off('baselayerchange', handleTileLoad);
      map.off('load', handleTileLoad);
    };
  }, [map, onTilesLoaded]);
  
  return null;
};

export default TileLoadTracker;