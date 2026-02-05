import { useState, useEffect, useRef, useCallback } from 'react';
import { useNearbyDeals } from '@/hooks/useDeals';
import { useGeolocation } from '@/hooks/useGeolocation';
import { DealCard } from '@/components/ui/DealCard';
import { MapPin, Navigation, Compass, List, Grid, ArrowUpRight, AlertTriangle, Leaf } from 'lucide-react';
import { Deal } from '@/types/deals';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import type L from 'leaflet';
import 'leaflet/dist/leaflet.css';

gsap.registerPlugin(ScrollTrigger);


// NearMeBackground SVG uses hardcoded colors, which won't adapt to theme changes automatically.
// For full theme support, this would need CSS variables or separate SVGs.
// Keeping it as is for now based on the prompt.
const NearMeBackground = () => (
  <div className="absolute inset-0 -z-10 w-full h-full overflow-hidden opacity-60 dark:opacity-60 opacity-30">
    <svg viewBox="0 0 1200 600" xmlns="http://www.w3.org/2000/svg" className="w-full h-full md:scale-100 scale-150 origin-center">
      <defs>
        <linearGradient id="mapGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0a1a24" />
          <stop offset="100%" stopColor="#071520" />
        </linearGradient>
        <pattern id="pinPattern" patternUnits="userSpaceOnUse" width="100" height="100" patternTransform="rotate(10)">
          <path d="M50,20 C65,20 75,35 75,50 C75,65 60,85 50,95 C40,85 25,65 25,50 C25,35 35,20 50,20 Z" fill="none" stroke="#3a6a9f" strokeWidth="1" opacity="0.15" />
          <circle cx="50" cy="45" r="5" fill="none" stroke="#3a6a9f" strokeWidth="1" opacity="0.15" />
        </pattern>
        <pattern id="gridPattern" patternUnits="userSpaceOnUse" width="200" height="200">
          <path d="M0,0 L200,0 M0,50 L200,50 M0,100 L200,100 M0,150 L200,150 M0,200 L200,200" stroke="#2b5a8a" strokeWidth="0.5" opacity="0.1" />
          <path d="M0,0 L0,200 M50,0 L50,200 M100,0 L100,200 M150,0 L150,200 M200,0 L200,200" stroke="#2b5a8a" strokeWidth="0.5" opacity="0.1" />
        </pattern>
        <pattern id="compassPattern" patternUnits="userSpaceOnUse" width="200" height="200" patternTransform="scale(0.5) rotate(5)">
          <circle cx="100" cy="100" r="80" fill="none" stroke="#3a6a9f" strokeWidth="1" opacity="0.08" />
          <circle cx="100" cy="100" r="60" fill="none" stroke="#3a6a9f" strokeWidth="1" opacity="0.08" />
          <path d="M100,10 L100,50 M100,150 L100,190 M10,100 L50,100 M150,100 L190,100" stroke="#3a6a9f" strokeWidth="1" opacity="0.08" />
          <path d="M100,20 L95,30 L105,30 Z" fill="#3a6a9f" opacity="0.1" />
          <path d="M100,180 L95,170 L105,170 Z" fill="#3a6a9f" opacity="0.1" />
          <path d="M20,100 L30,95 L30,105 Z" fill="#3a6a9f" opacity="0.1" />
          <path d="M180,100 L170,95 L170,105 Z" fill="#3a6a9f" opacity="0.1" />
        </pattern>
      </defs>
      {/* The background gradient is dark-specific. A light theme might need a different SVG or approach */}
      <rect width="100%" height="100%" fill="url(#mapGradient)" />
      <rect width="100%" height="100%" fill="url(#pinPattern)" />
      <rect width="100%" height="100%" fill="url(#gridPattern)" opacity="0.7" />
      <rect width="100%" height="100%" fill="url(#compassPattern)" />
      <circle cx="100" cy="100" r="300" fill="#1a3a55" opacity="0.04" />
      <circle cx="1100" cy="500" r="350" fill="#1a3a55" opacity="0.04" />
      <g opacity="0.1">
        <path d="M0,300 C200,320 400,250 600,300 C800,350 1000,280 1200,300" fill="none" stroke="#3a6a9f" strokeWidth="5" />
        <path d="M300,0 C320,200 250,400 300,600" fill="none" stroke="#3a6a9f" strokeWidth="5" />
        <path d="M900,0 C880,200 950,400 900,600" fill="none" stroke="#3a6a9f" strokeWidth="5" />
        <circle cx="300" cy="300" r="20" fill="#3a6a9f" />
        <circle cx="600" cy="350" r="15" fill="#3a6a9f" />
        <circle cx="900" cy="250" r="25" fill="#3a6a9f" />
      </g>
      <g transform="translate(1100, 100)" opacity="0.15">
        <circle cx="0" cy="0" r="60" fill="none" stroke="#5a8aB7" strokeWidth="1" />
        <path d="M0,-50 L0,50 M-50,0 L50,0" stroke="#5a8aB7" strokeWidth="1" />
        <path d="M0,-40 L-5,-30 L5,-30 Z" fill="#5a8aB7" />
        <text x="0" y="-55" fill="#5a8aB7" textAnchor="middle" fontSize="10">N</text>
        <text x="55" y="0" fill="#5a8aB7" textAnchor="middle" fontSize="10" dominantBaseline="middle">E</text>
        <text x="0" y="55" fill="#5a8aB7" textAnchor="middle" fontSize="10">S</text>
        <text x="-55" y="0" fill="#5a8aB7" textAnchor="middle" fontSize="10" dominantBaseline="middle">W</text>
      </g>
    </svg>
  </div>
);

interface LeafletMapProps {
  deals: Deal[];
  selectedDealId: number | null;
  onDealSelect: (deal: Deal) => void;
  latitude: number | null;
  longitude: number | null;
}

const LeafletMap: React.FC<LeafletMapProps> = ({ deals = [], selectedDealId, onDealSelect, latitude, longitude }) => {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<Map<number, L.Marker>>(new Map());
  const userMarkerRef = useRef<L.Marker | null>(null);
  const LRef = useRef<typeof L | null>(null);

  useEffect(() => {
    let mapInstance: L.Map | null = null;

    const initializeMap = async () => {
      if (!mapRef.current && mapContainerRef.current && latitude && longitude && !LRef.current) {
        const L = await import('leaflet');
        LRef.current = L;

        if (!mapContainerRef.current) return;

        mapInstance = L.map(mapContainerRef.current, {
            zoomControl: false
        }).setView([latitude, longitude], 13);
        mapRef.current = mapInstance;

        // Consider using a map provider that supports dark mode tiles or applying a CSS filter
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
          minZoom: 3,
          // Example: Add class for potential CSS filtering in dark mode
          // className: 'map-tiles'
        }).addTo(mapInstance);

        L.control.zoom({ position: 'bottomright' }).addTo(mapInstance);

        // User icon colors are kept specific, might not need theme change
        const userIcon = L.divIcon({
          html: `<div class="w-6 h-6 bg-blue-500 rounded-full border-2 border-white flex items-center justify-center shadow-md"><div class="w-2 h-2 bg-white rounded-full"></div></div>`,
          className: 'user-location-marker',
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });

        userMarkerRef.current = L.marker([latitude, longitude], { icon: userIcon, zIndexOffset: 1000 }) // Ensure user marker is on top
          .addTo(mapInstance)
          .bindPopup('You are here');
               }
    };

    initializeMap();

        return () => {
      if (mapInstance) {
        mapInstance.remove();
        mapRef.current = null;
        userMarkerRef.current = null;
        markersRef.current.clear();
        LRef.current = null;
      }
    };
  }, [latitude, longitude]);


  useEffect(() => {
    const map = mapRef.current;
    const L = LRef.current;
    if (!map || !L) return;

    const currentDealIds = new Set(deals.map(d => d.id));
    const markersMap = markersRef.current;


    const createDealIcon = (deal: Deal) => {
      const isSelected = selectedDealId === deal.id;
      // Deal icon colors are kept specific, might not need theme change
      return L.divIcon({
        html: `<div class="w-8 h-8 ${isSelected ? 'bg-primary-500 scale-110' : 'bg-accent-500'} rounded-full border-2 border-white flex items-center justify-center transform transition-all duration-300 hover:scale-110 shadow-lg"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2 L12 6"></path><path d="M12 18 L12 22"></path><path d="M4.93 4.93 L7.76 7.76"></path><path d="M16.24 16.24 L19.07 19.07"></path><path d="M2 12 L6 12"></path><path d="M18 12 L22 12"></path><path d="M4.93 19.07 L7.76 16.24"></path><path d="M16.24 7.76 L19.07 4.93"></path></svg></div>`,
        className: `deal-marker-${deal.id} ${isSelected ? 'deal-marker-selected' : ''}`,
        iconSize: [32, 32],
        iconAnchor: [16, 32]
      });
    };

    const createPopupContent = (deal: Deal) => `
      <div class="p-1 max-w-xs bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 rounded-md shadow-lg">
        <h3 class="font-bold text-base mb-0.5">${deal.title}</h3>
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">${deal.business_name}</p>
        <p class="text-xs mt-1 line-clamp-2">${deal.description}</p>
        <button class="mt-2 text-primary-600 dark:text-primary-400 hover:text-primary-500 dark:hover:text-primary-300 text-sm font-medium view-deal-button" data-deal-id="${deal.id}">View Deal →</button>
      </div>
    `;

      deals.forEach(deal => {
      const existingMarker = markersMap.get(deal.id);
      const newIcon = createDealIcon(deal);

      if (existingMarker) {

        existingMarker.setIcon(newIcon);


      } else {

        const marker = L.marker([deal.latitude, deal.longitude], { icon: newIcon })
          .addTo(map)
          .bindPopup(createPopupContent(deal), {
            closeButton: false,
            className: 'custom-deal-popup' // Add custom class for styling
          });

        marker.on('click', () => {
          onDealSelect(deal);
          map.setView([deal.latitude, deal.longitude], 15, { animate: true, duration: 0.5 });
        });



        marker.on('popupopen', () => {

            marker.getElement()?.classList.add('popup-open');
        });
        marker.on('popupclose', () => {

            marker.getElement()?.classList.remove('popup-open');
        });


        markersMap.set(deal.id, marker);
      }
    });

    // --- Remove Markers for Deals No Longer Present ---
    markersMap.forEach((marker, dealId) => {
      if (!currentDealIds.has(dealId)) {
        map.removeLayer(marker);
        markersMap.delete(dealId);
      }
    });

    // --- Handle Map View Based on Selection ---
    if (selectedDealId) {
      const selectedDealData = deals.find(deal => deal.id === selectedDealId);
      if (selectedDealData) {
        // Pan smoothly to the selected deal
        map.setView([selectedDealData.latitude, selectedDealData.longitude], 15, {
          animate: true,
          duration: 0.7,
          easeLinearity: 0.5
        });
        // Optionally open the popup for the selected marker
        const selectedMarker = markersMap.get(selectedDealId);
        selectedMarker?.openPopup();
      }
    } else if (latitude && longitude && !map.getBounds().contains([latitude, longitude])) {
      // If no deal is selected and user is outside current view, pan back to user
      // map.setView([latitude, longitude], 13, { animate: true, duration: 1 });
    }

  }, [deals, selectedDealId, onDealSelect, latitude, longitude]); // Re-run when data changes

  // Effect for handling popup button clicks via delegation
  useEffect(() => {
    const mapElement = mapContainerRef.current;
    if (!mapElement) return;

    const handlePopupClick = (event: MouseEvent) => {
        const target = event.target as HTMLElement;
        if (target.matches('.view-deal-button')) {
            const dealId = target.getAttribute('data-deal-id');
            if (dealId) {
                const deal = deals.find(d => d.id === parseInt(dealId, 10));
                if (deal) {
                    onDealSelect(deal);
                    mapRef.current?.closePopup(); // Close popup after clicking
                }
            }
        }
    };

    mapElement.addEventListener('click', handlePopupClick);

    return () => {
        mapElement.removeEventListener('click', handlePopupClick);
    };
  }, [deals, onDealSelect]); // Re-run if deals change to ensure correct deal data


  return (
    <div className="w-full h-[500px] rounded-xl overflow-hidden shadow-lg shadow-primary-200/20 dark:shadow-primary-900/20 border border-neutral-200/50 dark:border-neutral-800/50 relative">
      {/* Added light/dark background */}
      <div ref={mapContainerRef} className="w-full h-full bg-neutral-200/50 dark:bg-neutral-900/50" />
      {/* Add loading/placeholder if needed while map initializes */}
      {!mapRef.current && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-neutral-900/80 text-neutral-500 dark:text-neutral-400">
          Loading Map...
        </div>
      )}
    </div>
  );
};

// --- View Mode Type ---
type ViewMode = 'grid' | 'list' | 'map';

// --- Reusable Deal Item Wrapper ---
interface DealItemWrapperProps {
  deal: Deal;
  selectedDealId: number | null;
  onClick: (deal: Deal) => void;
  children: React.ReactNode;
  className?: string;
  viewMode: ViewMode;
}

const DealItemWrapper: React.FC<DealItemWrapperProps> = ({ deal, selectedDealId, onClick, children, className = '', viewMode }) => {
  const isSelected = deal.id === selectedDealId;
  const baseClasses = "transition-all duration-300 rounded-xl overflow-hidden cursor-pointer";
  // Adjusted selection ring offset for light/dark
  const selectedClasses = "ring-2 ring-primary-500 ring-offset-4 ring-offset-white dark:ring-offset-neutral-950 shadow-xl shadow-primary-300/20 dark:shadow-primary-500/20";
  // Adjusted hover styles for light/dark
  const hoverClasses = viewMode === 'grid'
    ? 'hover:shadow-lg hover:shadow-primary-200/10 dark:hover:shadow-primary-900/10 hover:ring-1 hover:ring-primary-500/30'
    : 'bg-white/60 dark:bg-neutral-900/60 backdrop-blur-sm border border-neutral-200/50 dark:border-neutral-800/50 hover:border-primary-500/30 hover:shadow-lg hover:shadow-primary-200/10 dark:hover:shadow-primary-900/10';

  return (
    <div
      id={`deal-${deal.id}`}
      className={`deal-card ${baseClasses} ${isSelected ? selectedClasses : hoverClasses} ${className}`}
      onClick={() => onClick(deal)}
      role="button"
      aria-pressed={isSelected}
      tabIndex={0} // Make it focusable
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onClick(deal)} // Basic keyboard interaction
    >
      {children}
    </div>
  );
};


// --- NearMeSection Component (Refactored) ---
const NearMeSection: React.FC = () => {
  const [selectedDealId, setSelectedDealId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const sectionRef = useRef<HTMLDivElement>(null);
  const dealsContainerRef = useRef<HTMLDivElement>(null); // Ref for deals container

  const {
    latitude,
    longitude,
    loading: locationLoading,
    error: locationError,
    getLocation,
    addressString
  } = useGeolocation({ autoDetect: true });

  const {
    data: nearbyDeals = [],
    isLoading: dealsLoading,
    error: dealsError
  } = useNearbyDeals(latitude, longitude, 10, {
    enabled: !!latitude && !!longitude && !locationLoading
  });

  const isLoading = locationLoading || dealsLoading;

  // --- GSAP Animations Effect ---
  useEffect(() => {
    if (!sectionRef.current) return;

    // Use gsap.context for proper cleanup
    const ctx = gsap.context(() => {
      // Animate section title and controls
      gsap.fromTo('.near-me-title-animate',
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 80%', // Start animation earlier
            toggleActions: 'play none none reverse'
          }
        }
      );

      // Animate map container (only if viewMode is map initially or switches to it)
      // We target a specific class added only when map is visible
      gsap.fromTo('.map-view-animate',
        { y: 50, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 1,
          delay: 0.2, // Slight delay after title
          ease: 'power3.out',
          scrollTrigger: {
            trigger: sectionRef.current,
            start: 'top 70%',
            toggleActions: 'play none none reverse'
          }
        }
      );

      // Animate deal cards (grid/list)
      // Ensure the trigger element exists before animating
      if (dealsContainerRef.current && (viewMode === 'grid' || viewMode === 'list')) {
        gsap.fromTo('.deal-card-animate', // Use a dedicated class for animation targeting
          { y: 40, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.6,
            stagger: 0.1, // Stagger effect
            ease: 'power2.out',
            scrollTrigger: {
              trigger: dealsContainerRef.current, // Use the ref
              start: 'top 85%', // Start when container enters view
              toggleActions: 'play none none reverse'
            }
          }
        );
      }
    }, sectionRef); // Scope animations to the sectionRef

    // Cleanup function
    return () => ctx.revert();

  }, [nearbyDeals, viewMode, isLoading]); // Re-run animations when deals, viewMode, or loading state changes

  // --- Deal Selection Handler ---
  const handleDealSelect = useCallback((deal: Deal) => {
    setSelectedDealId(prevId => (prevId === deal.id ? null : deal.id)); // Toggle selection

    // Scroll to selected deal in grid/list view
    if (viewMode !== 'map' && deal.id !== selectedDealId) { // Only scroll if selecting a new item
      // Use requestAnimationFrame to ensure the element is available after state update
      requestAnimationFrame(() => {
        const dealElement = document.getElementById(`deal-${deal.id}`);
        if (dealElement) {
          dealElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    }
  }, [viewMode, selectedDealId]); // Include selectedDealId dependency

  // --- Reset View Handler ---
  const handleResetView = useCallback(() => {
    setSelectedDealId(null);
    // Optionally reset map view if needed (LeafletMap handles centering on selection clear)
    // Accessing mapRef directly here is tricky as it's inside LeafletMap.
    // We might need to pass a reset function down or rely on LeafletMap's effect.
    // For now, just clearing selection. LeafletMap effect might recenter if user is out of bounds.
    // if (viewMode === 'map' && mapRef.current && latitude && longitude) {
    //     mapRef.current.setView([latitude, longitude], 13, { animate: true, duration: 0.7 });
    // }
  }, [/* viewMode, latitude, longitude */]); // Dependencies removed as mapRef isn't directly accessible


  // --- Render Loading/Error/No Deals States ---
  const renderStatusMessages = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center items-center py-16 text-center">
          <div>
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500 mx-auto mb-4"></div>
            {/* Adjusted text color */}
            <p className="text-neutral-500 dark:text-neutral-400">{locationLoading ? 'Getting your location...' : 'Finding deals near you...'}</p>
          </div>
        </div>
      );
    }

    if (locationError) {
      return (
        // Adjusted background, border, text colors
        <div className="bg-red-100/50 dark:bg-red-900/20 border border-red-300/60 dark:border-red-800/40 rounded-lg p-6 my-8 max-w-2xl mx-auto">
          <div className="flex items-start">
            <AlertTriangle className="w-6 h-6 text-red-500 dark:text-red-400 mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-medium text-red-700 dark:text-red-300 mb-2">Location Error</h3>
              <p className="text-red-600 dark:text-red-200 mb-4">{locationError}</p>
              <button
                onClick={getLocation}
                // Adjusted button colors
                className="px-4 py-2 bg-red-600 hover:bg-red-500 dark:bg-red-800 dark:hover:bg-red-700 text-white rounded-lg transition-colors text-sm font-medium"
              >
                Try Enabling Location
              </button>
            </div>
          </div>
        </div>
      );
    }

    if (dealsError) {
      return (
        // Adjusted background, border, text colors
        <div className="bg-yellow-100/50 dark:bg-yellow-900/20 border border-yellow-300/60 dark:border-yellow-800/40 rounded-lg p-6 my-8 max-w-2xl mx-auto">
          <div className="flex items-start">
            <AlertTriangle className="w-6 h-6 text-yellow-500 dark:text-yellow-400 mr-3 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-medium text-yellow-700 dark:text-yellow-300 mb-2">Error Loading Deals</h3>
              <p className="text-yellow-600 dark:text-yellow-200">{(dealsError as Error).message || 'Failed to load deals near you. Please try again later.'}</p>
            </div>
          </div>
        </div>
      );
    }

    if (!isLoading && nearbyDeals.length === 0 && latitude && longitude) {
      return (
        // Adjusted background, border, text colors
        <div className="bg-neutral-100/60 dark:bg-neutral-900/60 backdrop-blur-sm rounded-xl border border-neutral-200/50 dark:border-neutral-800/50 p-8 text-center my-8 max-w-lg mx-auto">
          <Leaf size={40} className="text-primary-500 mx-auto mb-4 opacity-50" />
          <h3 className="text-xl font-semibold text-neutral-900 dark:text-white mb-2">No Sustainable Deals Found Nearby</h3>
          <p className="text-neutral-600 dark:text-neutral-300">
            We couldn't find any eco-friendly deals in your immediate area right now. Try expanding your search or check back later!
          </p>
        </div>
      );
    }

    return null; // No status message needed
  };

  // --- Render Main Content Based on View Mode ---
  const renderDealContent = () => {
    if (isLoading || locationError || dealsError || nearbyDeals.length === 0) {
      return null; // Handled by renderStatusMessages
    }

    return (
      <>
        {viewMode === 'map' && (
          <div className="my-8 map-view-animate"> {/* Added animation class */}
            <LeafletMap
              deals={nearbyDeals}
              selectedDealId={selectedDealId}
              onDealSelect={handleDealSelect}
              latitude={latitude}
              longitude={longitude}
            />
          </div>
        )}

        {(viewMode === 'grid' || viewMode === 'list') && (
          <div
            ref={dealsContainerRef} // Attach ref here
            className={`my-8 ${viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}`}
          >
            {nearbyDeals.map((deal) => (
              <DealItemWrapper
                key={deal.id}
                deal={deal}
                selectedDealId={selectedDealId}
                onClick={handleDealSelect}
                viewMode={viewMode}
                className="deal-card-animate" // Add animation class to the wrapper
              >
                {viewMode === 'grid' ? (
                  // DealCard needs its own internal theme adjustments
                  <DealCard deal={deal} priority={deal.id === selectedDealId} className="h-full" />
                ) : (
                  // List View Item Structure - Adjusted colors
                  <div className="flex flex-col md:flex-row">
                    <div className="md:w-1/3 relative flex-shrink-0">
                      <img
                        src={deal.image || "/api/placeholder/400/300"}
                        alt={deal.title}
                        className="w-full h-48 md:h-full object-cover"
                        loading="lazy"
                        width={400} // Add dimensions for performance
                        height={300}
                      />
                      {/* Badge colors kept specific */}
                      <div className="absolute top-3 left-3 bg-accent-500 text-white text-xs font-semibold px-2 py-1 rounded shadow">
                        {deal.deal_type === 'discount' ? 'DISCOUNT' :
                         deal.deal_type === 'bogo' ? 'BOGO' : 'GIFT'}
                      </div>
                    </div>
                    <div className="p-5 md:w-2/3 flex flex-col justify-between">
                      <div>
                        <div className="flex justify-between items-start mb-1 gap-2">
                          {/* Adjusted text color */}
                          <h3 className="text-lg font-display font-semibold text-neutral-900 dark:text-white flex-1">{deal.title}</h3>
                          {/* Adjusted badge background/text */}
                          <span className="bg-primary-100/50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 text-xs px-2 py-1 rounded-full flex items-center flex-shrink-0 whitespace-nowrap">
                            <Leaf size={12} className="mr-1" />
                            <span className="font-bold">{deal.sustainability_score}%</span>
                          </span>
                        </div>
                         {/* Adjusted text color */}
                        <p className="text-sm text-primary-600 dark:text-primary-400 mb-3">{deal.business_name}</p>
                         {/* Adjusted text color */}
                        <p className="text-neutral-600 dark:text-neutral-300 text-sm line-clamp-3">{deal.description}</p>
                      </div>
                      <div className="flex justify-between items-center mt-4 text-sm">
                         {/* Adjusted text color */}
                        <div className="flex items-center text-neutral-500 dark:text-neutral-400">
                          <MapPin size={14} className="mr-1.5 flex-shrink-0" />
                          <span>{deal.distance ? `${deal.distance.toFixed(1)} miles away` : 'Nearby'}</span>
                        </div>
                         {/* Adjusted text color */}
                        <div className="text-primary-600 dark:text-primary-400 hover:text-primary-500 dark:hover:text-primary-300 flex items-center font-medium">
                          <span className="mr-1">Details</span>
                          <ArrowUpRight size={14} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </DealItemWrapper>
            ))}
          </div>
        )}
      </>
    );
  };

  // --- Render View Mode Controls ---
  const renderViewControls = () => {
    if (isLoading || locationError || dealsError || nearbyDeals.length === 0) {
      return null;
    }

    return (
      // Adjusted background color
      <div className="bg-neutral-200/80 dark:bg-neutral-800/80 backdrop-blur-sm rounded-full p-1 flex shadow-inner">
        {(['grid', 'list', 'map'] as ViewMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            // Adjusted text/background colors for selected/hover states
            className={`px-3 py-1.5 rounded-full text-sm flex items-center gap-1.5 transition-all duration-200 ${
              viewMode === mode
                ? "bg-primary-600 text-white shadow" // Selected state remains distinct
                : "text-neutral-600 dark:text-neutral-300 hover:text-neutral-900 dark:hover:text-white"
            }`}
            aria-label={`Switch to ${mode} view`}
            aria-pressed={viewMode === mode}
          >
            {mode === 'grid' && <Grid size={16} />}
            {mode === 'list' && <List size={16} />}
            {mode === 'map' && <MapPin size={16} />}
            <span className="capitalize hidden sm:inline">{mode}</span>
          </button>
        ))}
      </div>
    );
  };

  // --- Render Location/Reset Buttons ---
  const renderActionButtons = () => (
    <div className="flex items-center gap-3">
       {(locationError || (!latitude && !locationLoading && !isLoading)) && (
        <button
          onClick={getLocation}
          disabled={locationLoading}
          // Button colors kept specific for primary action
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-full transition-colors disabled:opacity-60 disabled:cursor-not-allowed text-sm font-medium shadow"
        >
          <Navigation size={16} />
          <span>Enable Location</span>
        </button>
      )}

      {latitude && longitude && nearbyDeals.length > 0 && selectedDealId !== null && (
        <button
          onClick={handleResetView}
          // Adjusted background, text, border, hover colors
          className="flex items-center gap-2 px-4 py-2 bg-white/80 dark:bg-neutral-800/80 backdrop-blur-sm hover:bg-neutral-200/90 dark:hover:bg-neutral-700/90 text-neutral-900 dark:text-white rounded-full transition-colors border border-neutral-300/50 dark:border-neutral-700/50 text-sm font-medium shadow"
          aria-label="Reset view and clear selection"
        >
          <Compass size={16} />
          <span>Reset View</span>
        </button>
      )}
    </div>
  );

  return (
    <section
      ref={sectionRef}
      id="near-me"
      // Adjusted background gradient for light/dark
      className="py-16 md:py-24 relative near-me-section bg-gradient-to-b from-neutral-100 to-neutral-200 dark:from-neutral-900 dark:to-neutral-950 overflow-hidden"
      aria-labelledby="near-me-heading"
    >
      <NearMeBackground />

      <div className="container mx-auto px-4 relative z-10">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 md:mb-12 gap-6 near-me-title-animate">
          <div className="md:flex-1">
            {/* Adjusted text color */}
            <span className="text-primary-600 dark:text-primary-400 text-sm font-semibold tracking-wider mb-2 block uppercase">
              Discover Nearby
            </span>
            {/* Heading gradient kept specific */}
            <h2 id="near-me-heading" className="text-3xl md:text-4xl font-display font-bold text-gray-900 dark:text-white bg-gradient-to-r from-primary-500 via-primary-600 to-accent-500 dark:from-primary-300 dark:via-white dark:to-accent-300 bg-clip-text text-transparent pb-1 leading-tight">
              Sustainable Deals Near You
            </h2>
            {addressString && !locationLoading && (
               // Adjusted text color
              <p className="text-gray-600 dark:text-gray-400 mt-3 flex items-center text-sm">
                <MapPin size={15} className="inline mr-2 text-primary-500 dark:text-primary-400 flex-shrink-0" />
                Showing deals near: <span className="font-medium ml-1">{addressString}</span>
              </p>
            )}
             {!addressString && !locationLoading && latitude && (
                  // Adjusted text color
                 <p className="text-gray-600 dark:text-gray-400 mt-3 flex items-center text-sm">
                    <MapPin size={15} className="inline mr-2 text-primary-500 dark:text-primary-400 flex-shrink-0" />
                    Showing deals for your current location.
                 </p>
             )}
             {/* Adjusted text color */}
            <p className="text-neutral-600 dark:text-neutral-300 mt-3 max-w-2xl text-base">
              Find eco-friendly businesses and exclusive offers right in your neighborhood. Support local and sustainable practices.
            </p>
          </div>

          {/* Controls Area */}
          <div className="flex flex-col sm:flex-row items-start sm:items-end gap-4">
             {renderViewControls()}
             {renderActionButtons()}
          </div>
        </div>

        {/* Status Messages */}
        {renderStatusMessages()}

        {/* Main Content Area (Map or Deals) */}
        {renderDealContent()}

      </div>
    </section>
  );
};

export default NearMeSection;
