/* src/pages/Home.tsx */
import { useState, useRef, useEffect, lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown, ShoppingBag, Leaf } from 'lucide-react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

import SearchBar from '@/components/search/SearchBar';
import SearchSection from '@/components/sections/SearchSection';
import { DealCard } from '@/components/ui/DealCard';
import DealMap from '@/components/map/DealMap';

import { useFeaturedDeals } from '@/hooks/useDeals';
import { useDeals } from '@/hooks/useDeals';           // all deals for the map
import { useCategories } from '@/hooks/useCategories';
import { useSearch } from '@/hooks/useSearch';

const AboutSection  = lazy(() => import('@/components/sections/AboutSection'));
const ShopsSection  = lazy(() => import('@/components/sections/ShopsSection'));
const NearMeSection = lazy(() => import('@/components/sections/NearMeSection'));

gsap.registerPlugin(ScrollTrigger);

/* --------------------------------------------------------------------- */

const SectionPlaceholder = ({ text }: { text: string }) => (
  <div
    className="h-96 flex items-center justify-center bg-gray-100/50 dark:bg-neutral-900/50 backdrop-blur-sm rounded-2xl mx-4 my-8 border border-gray-200 dark:border-neutral-800/50"
    aria-label={`Loading ${text}`}
  >
    <div className="flex flex-col items-center">
      <div className="w-8 h-8 border-4 border-primary-500 dark:border-primary-400 border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-primary-600 dark:text-primary-400 font-medium">{text}</p>
    </div>
  </div>
);

/* --------------------------------------------------------------------- */

const Home = () => {
  const { t } = useTranslation();

  /* ──────────────────── data hooks ──────────────────── */
  const [selectedDeal, setSelectedDeal] = useState<number | null>(null);

  const { searchQuery, handleSearch, results, totalResults, isLoading: isLoadingSearch } = useSearch();
  const { data: rawFeaturedDeals, isLoading: isLoadingFeatured } = useFeaturedDeals();
  const { data: rawAllDeals, isLoading: isLoadingDeals } = useDeals(); // for the map
  const { data: categoriesData } = useCategories();

  // normalise API responses that may be { results: [...] }
  const featuredDeals = Array.isArray(rawFeaturedDeals)
    ? rawFeaturedDeals
    : rawFeaturedDeals?.results || [];

  const allDeals = Array.isArray(rawAllDeals)
    ? rawAllDeals
    : rawAllDeals?.results || [];

  const categories = Array.isArray(categoriesData)
    ? categoriesData
    : categoriesData?.results || [];

  /* ──────────────────── GSAP refs ──────────────────── */
  const heroRef        = useRef<HTMLElement | null>(null);
  const heroInnerRef   = useRef<HTMLDivElement | null>(null);
  const discoverBtnRef = useRef<HTMLButtonElement | null>(null);

  /* ──────────────────── GSAP animations ──────────────────── */
  useEffect(() => {
    if (!heroRef.current) return;

    const ctx = gsap.context(() => {
      gsap.from(heroInnerRef.current, {
        y: 20,
        opacity: 0,
        duration: 0.9,
        ease: 'power2.out',
      });

      gsap.to(heroRef.current, {
        scrollTrigger: {
          trigger: heroRef.current,
          start: 'top top',
          end: '+=300',
          scrub: true,
        },
        opacity: 0,
        scale: 0.8,
        ease: 'none',
      });

      gsap.set(discoverBtnRef.current, { y: 0 });
      discoverBtnRef.current &&
        discoverBtnRef.current.addEventListener('mouseenter', () =>
          gsap.to(discoverBtnRef.current!, { y: -4, duration: 0.25, ease: 'power1.out' })
        );
      discoverBtnRef.current &&
        discoverBtnRef.current.addEventListener('mouseleave', () =>
          gsap.to(discoverBtnRef.current!, { y: 0, duration: 0.25, ease: 'power1.in' })
        );
    });

    return () => ctx.revert();
  }, []);

  const processedCategories = categories.map((c) => ({ id: c.id, name: c.name }));

  const scrollToContent = () =>
    document.getElementById('main-content')?.scrollIntoView({ behavior: 'smooth' });

  /* ───────────────────── render ───────────────────── */
  return (
    <>
      {/* HERO SECTION */}
      {/* Note: Hero background/gradient might need theme-specific adjustments */}
      <section
        ref={heroRef}
        className="relative h-screen w-full overflow-hidden"
        role="banner"
        aria-label="Welcome to DealOpia"
      >
        <div className="absolute inset-0 w-full h-full">
          <img
            src="https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?auto=format&fit=crop&q=80"
            alt=""
            className="object-cover w-full h-full absolute inset-0"
            aria-hidden="true"
          />
          {/* Consider light/dark gradients if needed */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/25 to-black" />
        </div>

        <div
          ref={heroInnerRef}
          className="relative h-full flex flex-col items-center justify-center px-4 py-16"
        >
          <div className="flex items-center justify-center gap-2 mb-4">
            {/* Badge styling might need light/dark adjustments for contrast */}
            <span className="px-4 py-1.5 bg-black/30 backdrop-blur-sm rounded-full text-[#a78bfa] border border-[rgba(139,92,246,0.2)] flex items-center gap-2">
              <Leaf size={16} style={{ color: '#a78bfa' }} />
              <span className="text-sm font-medium">Eco-conscious deals</span>
            </span>
          </div>

          <h1 className="text-4xl md:text-6xl lg:text-7xl
            font-display font-bold
            text-white {/* Hero text often stays white regardless of theme */}
            text-center
            max-w-[90%]
            mx-auto
            mb-6">
            Sustainable shopping, <span className="gradient-text">Better Future</span>
          </h1>

          <p className="hidden md:block text-lg md:text-xl text-gray-200 mb-8 max-w-2xl mx-auto"> {/* Hero text often stays light regardless of theme */}
            Join our community of conscious shoppers and discover amazing local deals while making
            a positive impact on the environment.
          </p>

          <SearchBar
            onSearch={(query, filters) => {
              handleSearch(query, filters);
              if (filters.latitude && filters.longitude) {
                document.getElementById('near-me')?.scrollIntoView({ behavior: 'smooth' });
              }
            }}
            className="max-w-2xl mx-auto"
            categories={processedCategories}
          />

          <div className="max-w-4xl mx-auto">
            <SearchSection
              query={searchQuery}
              results={results}
              totalResults={totalResults}
              isLoading={isLoadingSearch}
              onFilterClick={() => {}}
            />
          </div>

          <button
            ref={discoverBtnRef}
            onClick={scrollToContent}
            className="md:absolute bottom-8 flex flex-col items-center group cursor-pointer mt-12"
            aria-label="Scroll to discover deals"
          >
            {/* Button styling might need light/dark adjustments for contrast */}
            <span className="text-lg font-semibold mb-3 bg-[rgba(139,92,246,0.1)] backdrop-blur-sm px-6 py-2 rounded-full border border-[rgba(139,92,246,0.2)] group-hover:bg-[rgba(139,92,246,0.2)] transition-colors flex items-center gap-2 text-[#a78bfa]">
              <ShoppingBag size={18} />
              Discover More
            </span>
            <ChevronDown className="w-8 h-8 animate-bounce text-primary-400" /> {/* Icon color might need adjustment */}
          </button>
        </div>
      </section>

      {/* ─────────────────── main content ─────────────────── */}
      <main id="main-content">
        {/* FEATURED DEALS */}
        <section className="py-20">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
              <div>
                <span className="text-primary-600 dark:text-primary-400 text-sm font-semibold tracking-wider mb-2 block">
                  DISCOVER
                </span>
                <h2 className="text-3xl font-display font-bold text-gray-900 dark:text-white">Featured Deals</h2>
              </div>

              <div className="flex flex-wrap gap-2">
                {/* Assuming button styles are handled globally or in their own component */}
                <button className="px-4 py-2 rounded-full bg-primary-500 hover:bg-primary-600 text-white font-medium transition-all">
                  View All
                </button>
                <button className="px-4 py-2 rounded-full bg-primary-500/10 hover:bg-primary-500/20 text-primary-600 dark:text-primary-400 font-medium border border-primary-500/20 transition-all">
                  Most Popular
                </button>
              </div>
            </div>

            {isLoadingFeatured ? (
              /* loading skeletons */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className="bg-white/70 dark:bg-neutral-900/50 backdrop-blur-sm rounded-2xl overflow-hidden border border-gray-200 dark:border-neutral-800/50 animate-pulse"
                  >
                    <div className="w-full aspect-video bg-gray-200 dark:bg-neutral-800" />
                    <div className="p-4">
                      <div className="h-5 bg-gray-300 dark:bg-neutral-700 rounded w-3/4 mb-3" />
                      <div className="h-4 bg-gray-300 dark:bg-neutral-700 rounded w-1/3 mb-3" />
                      <div className="h-3 bg-gray-300 dark:bg-neutral-700 rounded w-full" />
                    </div>
                  </div>
                ))}
              </div>
            ) : featuredDeals.length ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                {featuredDeals.map((deal) => (
                  <DealCard
                    key={deal.id}
                    deal={deal}
                    priority={deal.id === selectedDeal}
                    // Apply ring offset based on theme
                    className={`${deal.id === selectedDeal
                      ? 'ring-2 ring-primary-500 ring-offset-4 ring-offset-white dark:ring-offset-black'
                      : ''
                    } transform-gpu`}
                    onClick={() => setSelectedDeal(deal.id)}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-neutral-600 dark:text-neutral-400">No featured deals available at the moment.</p>
              </div>
            )}
          </div>
        </section>

        {/* MAP SECTION */}
        <section id="explore-map" className="py-20 bg-gray-100/50 dark:bg-neutral-950/30 backdrop-blur-sm">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-display font-bold text-gray-900 dark:text-white mb-6">
              {t('Explore on the map')}
            </h2>

            {isLoadingDeals ? (
              <SectionPlaceholder text="Loading map…" />
            ) : (
              <DealMap
                deals={allDeals}
                selectedDealId={selectedDeal}
                onDealSelect={(d) => setSelectedDeal(d.id)}
                height="600px"
              />
            )}
          </div>
        </section>

        {/* NEAR-ME, SHOPS, ABOUT – lazy-loaded */}
        <Suspense fallback={<SectionPlaceholder text="Loading nearby deals…" />}>
          <NearMeSection />
        </Suspense>

        <Suspense fallback={<SectionPlaceholder text="Loading shops…" />}>
          <ShopsSection />
        </Suspense>

        <Suspense fallback={<SectionPlaceholder text="Loading about section…" />}>
          <AboutSection />
        </Suspense>
      </main>
    </>
  );
};

export default Home;
