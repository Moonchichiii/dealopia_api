/* src/layout/Layout.tsx */
import { lazy, Suspense, useEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { ScrollTrigger, useGSAP } from '@/utils/useGsap';

import CookieConsent   from '@/components/utils/CookieConsent';
import Header          from '@/components/layout/Header';
import Loader          from '@/components/ui/Loader';
import { ScrollToTopButton } from '@/components/utils/ScrollToTop';
import { useTheme }    from '@/context/ThemeContext';

const Footer = lazy(() => import('@/components/layout/Footer'));

const Layout = () => {
  const { pathname }  = useLocation();
  const isHome        = pathname === '/';

  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  /* ───────────── Body background – pure CSS classes, no inline styles ───────────── */
  useEffect(() => {
    const body = document.body;
    body.classList.toggle('home-page', isHome);
    body.classList.toggle('dark',       isDark);
    body.classList.toggle('light',     !isDark);

    // gradient backgrounds via Tailwind utilities (defined once in globals.css)
    body.classList.toggle('bg-home-dark',  isHome && isDark);
    body.classList.toggle('bg-home-light', isHome && !isDark);
    body.classList.toggle('bg-base-dark',  !isHome && isDark);
    body.classList.toggle('bg-base-light', !isHome && !isDark);

    return () => {
      body.removeAttribute('class');
    };
  }, [isHome, isDark]);

  /* ───────────── Global GSAP config ───────────── */
  useGSAP(() => {
    ScrollTrigger.config({ autoRefreshEvents: 'visibilitychange,DOMContentLoaded,load,resize' });
    return () => ScrollTrigger.getAll().forEach((t) => t.kill());
  }, []);

  /* ───────────── Lazy footer via IntersectionObserver ───────────── */
  const [showFooter, setShowFooter] = useState(false);

  useEffect(() => {
    const placeholder = document.getElementById('footer-placeholder');
    if (!placeholder) return;

    const io = new IntersectionObserver(
      ([entry]) => entry.isIntersecting && setShowFooter(true),
      { rootMargin: '200px' }
    );

    io.observe(placeholder);
    return () => io.disconnect();
  }, []);

  /* ───────────── Layout ───────────── */
  return (
    <div className="min-h-screen flex flex-col relative text-gray-900 dark:text-gray-100">
      <Header isDarkMode={isDark} toggleTheme={toggleTheme} />

      <main className={`flex-grow w-full ${isHome ? 'p-0' : 'pt-16 px-4 md:px-8'} relative z-10`}>
        <Suspense fallback={<Loader progress={50} />}>
          <Outlet />
        </Suspense>
      </main>

      {/* footer placeholder for IO */}
      <div id="footer-placeholder" className="h-px" />

      {showFooter && (
        <Suspense fallback={<div className="h-px" />}>
          <Footer />
        </Suspense>
      )}

      <CookieConsent />
      <ScrollToTopButton />
    </div>
  );
};

export default Layout;
