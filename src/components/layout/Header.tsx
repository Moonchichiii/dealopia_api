import {
  useEffect,
  useMemo,
  useCallback,
  useState,
  useRef,
} from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LogIn,
  MapPin,
  Menu,
  Moon,
  Store,
  Sun,
  Tag,
  UserPlus,
  X,
  Globe,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { createPortal } from 'react-dom';
import { gsap } from 'gsap';

import { useTranslation }   from 'react-i18next';
import { useAuthModal }     from '@/components/auth/AuthModal';
import { useAuth }          from '@/hooks/useAuth';
import { useTheme }         from '@/context/ThemeContext';
import { cn }               from '@/utils/cn';

/* ------------------------------------------------------------------ */

interface LanguageOption  { code:string; name:string; }
interface NavigationItem  { name:string; href:string; icon?:React.ComponentType<{size?:number}>; }
interface HeaderProps     { isDarkMode:boolean; toggleTheme:()=>void; }

/* ------------------------------------------------------------------ */

const Header = ({ isDarkMode, toggleTheme }: HeaderProps) => {
  /* ————————————————————————————————————————————————————— state */
  const { t, i18n }         = useTranslation();
  const location            = useLocation();
  const navigate            = useNavigate();
  const [isMenuOpen, setIsMenuOpen]                 = useState(false);
  const [hasScrolled, setHasScrolled]               = useState(false);
  const [isLanguageOpen, setIsLanguageOpen]         = useState(false);
  const [isMobileLanguageOpen, setIsMobileLanguageOpen] = useState(false);

  const { user, logout, isAuthenticated }           = useAuth();
  const { openSignIn, openSignUp, AuthModal }       = useAuthModal();

  /* overlay + sidebar DOM refs (for GSAP) */
  const overlayRef  = useRef<HTMLDivElement|null>(null);
  const sidebarRef  = useRef<HTMLDivElement|null>(null);

  /* ———————————————————————————————————————————————————— helpers */
  const languages: LanguageOption[] = useMemo(() => [
    { code:'en', name:'English'  },
    { code:'de', name:'Deutsch'  },
    { code:'fr', name:'Français' },
    { code:'es', name:'Español'  },
    { code:'it', name:'Italiano' },
    { code:'nl', name:'Nederlands' },
  ], []);

  const navigation: NavigationItem[] = useMemo(() => {
    const base = [
      { name:'Home',  href:'/' },
      { name:'Shops', href:'/shops', icon:Store },
      // keep the same order, but make “About” a hash-link ⬇︎
      { name:'About', href:'/#about' },
    ];
    return isAuthenticated ? [...base, { name:'Dashboard', href:'/dashboard' }] : base;
  }, [isAuthenticated]);

  const currentLangName =
    languages.find(l => l.code === i18n.language)?.name ?? 'English';

  /* ———————————————————————————— scroll / header glass blur */
  useEffect(() => {
    const onScroll = () => setHasScrolled(window.scrollY > window.innerHeight * .03);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* ———————————————————————————— close menus on route-change */
  useEffect(() => {
    setIsMenuOpen(false);
    setIsLanguageOpen(false);
    setIsMobileLanguageOpen(false);
  }, [location.pathname]);

  /* ———————————————————————————— body scroll-lock while menu */
  useEffect(() => {
    document.body.style.overflow = isMenuOpen ? 'hidden' : 'unset';
    return () => { document.body.style.overflow = 'unset'; };
  }, [isMenuOpen]);

  /* ———————————————————————————— hide desktop lang pop-up click-outside */
  useEffect(() => {
    if (!isLanguageOpen) return;
    const close = (e:MouseEvent) => {
      if (!(e.target as HTMLElement).closest('.language-selector')) setIsLanguageOpen(false);
    };
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, [isLanguageOpen]);

  /* ———————————————————————————— handle “Near Me” smart scroll */
  const handleNearMeClick = useCallback(() => {
    if (location.pathname === '/') {
      document.getElementById('near-me')?.scrollIntoView({behavior:'smooth'});
    } else {
      navigate('/?scrollTo=near-me');
    }
  }, [location.pathname, navigate]);

  /* ———————————————————————————— handle “About” smart scroll */
  const handleAboutClick = useCallback(() => {
    if (location.pathname === '/') {
      document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' });
    } else {
      navigate('/#about');        // go home, hash already in URL
    }
  }, [location.pathname, navigate]);

  /* ———————————————————————————— auth + language + menu toggles */
  const handleLogout         = () => logout().catch(console.error);
  const toggleMenu           = () => { if (!isMenuOpen) setIsMenuOpen(true); };
  const openLanguageDesktop  = () => setIsLanguageOpen(v=>!v);
  const toggleMobileLanguage = () => setIsMobileLanguageOpen(v=>!v);

  /* ———————————————————————————— GSAP – animate sidebar in/out */
  const closeMenu = useCallback(() => {
    if (!sidebarRef.current || !overlayRef.current) { setIsMenuOpen(false); return; }

    const tl = gsap.timeline({
      defaults:{ ease:'power3.inOut', duration:0.4 },
      onComplete: () => setIsMenuOpen(false),
    });
    tl.to(sidebarRef.current,  { x:'100%' }, 0)
      .to(overlayRef.current,  { opacity:0 }, 0);
  }, []);

  /* when menu first opens, mount elements THEN animate them */
  useEffect(() => {
    if (!isMenuOpen) return;

    // initial states
    if (overlayRef.current) {
      gsap.set(overlayRef.current, { opacity:0 });
    }
    if (sidebarRef.current) {
      gsap.set(sidebarRef.current, { x:'100%' });
    }

    const tl = gsap.timeline({ defaults:{ ease:'power3.out', duration:0.45 } });
    tl.to(overlayRef.current!, { opacity:1 }, 0)
      .to(sidebarRef.current!, { x:0         }, 0);

  }, [isMenuOpen]);

  /* ------------------------------------------------------------------ */
  /*                                  RENDER                            */
  /* ------------------------------------------------------------------ */

  const headerGlass: React.CSSProperties = hasScrolled
    ? { background:'rgba(10,10,10,.20)', backdropFilter:'blur(12px)',
        borderBottom:'1px solid rgba(38,38,38,.5)' }
    : { background:'transparent' };

  return (
    <>
      {/* ──────────────────────────────  DESKTOP HEADER  ────────────────────────────── */}
      <header
        className="fixed top-0 left-0 right-0 z-150 transition-all duration-300"
        style={headerGlass}
      >
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">

            {/* logo */}
            <Link to="/" className="flex items-center space-x-2 group">
              <div className="p-2 rounded-xl transition-colors bg-[rgba(139,92,246,.1)] group-hover:bg-[rgba(139,92,246,.2)]">
                <Tag className="w-6 h-6 text-primary-400" />
              </div>
              <span className="text-xl font-display font-bold gradient-text">DealOpia</span>
            </Link>

            {/* desktop nav */}
            <nav className="hidden md:flex items-center gap-6">
              {navigation.map(item => (
                <Link
                  key={item.name}
                  to={item.href}
                  className="text-sm font-medium flex items-center gap-2 transition-colors"
                  style={{color: location.pathname===item.href ? '#a78bfa' : '#d4d4d4'}}
                  onClick={item.name === 'About' ? handleAboutClick : undefined}
                >
                  {item.icon && <item.icon size={16} />}
                  {item.name}
                </Link>
              ))}
              <button
                onClick={handleNearMeClick}
                className="flex items-center gap-2 text-sm font-medium text-gray-300 transition-colors hover:text-primary-300"
              >
                <MapPin size={16} /> <span>Near Me</span>
              </button>
            </nav>

            {/* desktop right actions */}
            <div className="hidden md:flex items-center gap-4">
              {/* theme toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-full hover:bg-primary-500/20 transition-colors"
              >
                {isDarkMode ? <Sun size={20} className="text-primary-300" />
                             : <Moon size={20} className="text-primary-300" />}
              </button>

              {/* language selector */}
              <div className="relative language-selector">
                <button
                  onClick={openLanguageDesktop}
                  className="flex items-center gap-2 p-2 rounded-lg hover:bg-primary-500/10 transition-colors"
                >
                  <Globe size={18} className="text-primary-400" />
                  <span className="text-sm">{currentLangName}</span>
                  {isLanguageOpen ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
                </button>

                {isLanguageOpen && (
                  <div
                    className="absolute top-full right-0 mt-1 z-50 w-40 overflow-hidden rounded-lg border border-neutral-800/50 bg-neutral-900/90 backdrop-blur shadow-lg"
                  >
                    {languages.map(lang => (
                      <button
                        key={lang.code}
                        onClick={() => { i18n.changeLanguage(lang.code); setIsLanguageOpen(false); }}
                        className={cn(
                          'flex w-full items-center px-4 py-2 text-sm',
                          lang.code===i18n.language
                            ? 'bg-primary-500/10 text-primary-400 font-medium'
                            : 'text-neutral-300 hover:bg-neutral-800/50'
                        )}
                      >
                        {lang.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* auth buttons */}
              {isAuthenticated ? (
                <>
                  <Link
                    to="/dashboard"
                    className="flex items-center gap-2 rounded-lg bg-primary-500/15 px-4 py-2 text-primary-300 hover:bg-primary-500/25"
                  >
                    {user?.first_name ?? 'Dashboard'}
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="rounded-lg bg-white/5 px-4 py-2 text-gray-300 hover:bg-white/10"
                  >
                    Sign out
                  </button>
                </>
              ) : (
                <>
                  {/* ✅  OLD “PURPLE-GLASS” SIGN-IN BUTTON */}
                  <button
                    onClick={openSignIn}
                    className="flex items-center gap-2 bg-[rgba(139,92,246,0.1)] text-[#a78bfa] px-4 py-2 rounded-lg font-medium transition-colors hover:bg-[rgba(139,92,246,0.2)]"
                  >
                    <LogIn size={18} aria-hidden="true" />
                    <span>Sign&nbsp;In</span>
                  </button>

                  {/* ✅  OLD “SOLID PURPLE” SIGN-UP BUTTON */}
                  <button
                    onClick={openSignUp}
                    className="flex items-center gap-2 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    <UserPlus size={18} aria-hidden="true" />
                    <span>Sign&nbsp;Up</span>
                  </button>
                </>
              )}
            </div>

            {/* mobile buttons */}
            <div className="flex md:hidden items-center gap-2">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg bg-primary-500/15"
              >
                {isDarkMode ? <Sun size={18} className="text-primary-300"/> :
                               <Moon size={18} className="text-primary-300"/>}
              </button>
              <button
                onClick={toggleMenu}
                className="p-2 rounded-lg bg-gray-900/50"
                aria-label="open menu"
              >
                {isMenuOpen ? <X   className="w-6 h-6 text-gray-300"/> :
                               <Menu className="w-6 h-6 text-gray-300"/>}
              </button>
            </div>
          </div>
        </div>
      </header>

      {AuthModal}

      {/* ───────────────────────────  MOBILE OVERLAY + SIDEBAR  ───────────────────── */}
      {isMenuOpen &&
        createPortal(
          <>
            <div
              ref={overlayRef}
              className="mobile-menu-overlay md:hidden"
              onClick={closeMenu}
            />
            <aside
              ref={sidebarRef}
              className="mobile-menu-container md:hidden"
            >
              {/* — top bar — */}
              <div className="flex items-center justify-end p-4 border-b border-gray-700/50">
                <button onClick={closeMenu} className="p-1 rounded-lg hover:bg-gray-800/40">
                  <X className="w-5 h-5 text-gray-400"/>
                </button>
              </div>

              {/* — nav items — */}
              <nav className="flex-1 overflow-y-auto p-4 space-y-2">
                {navigation.map(item => (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => {
                      closeMenu();
                      if (item.name === 'About') { handleAboutClick(); }
                    }}
                    className={cn(
                      'flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium',
                      location.pathname===item.href
                        ? 'bg-primary-500/10 text-primary-400'
                        : 'text-gray-300 hover:bg-gray-800/40'
                    )}
                  >
                    {item.icon && <item.icon size={18}/>}
                    {item.name}
                  </Link>
                ))}
                <button
                  onClick={() => { closeMenu(); handleNearMeClick(); }}
                  className="flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium text-gray-300 hover:bg-gray-800/40 w-full"
                >
                  <MapPin size={18}/> Near Me
                </button>

                {/* language mobile accordion */}
                <button
                  onClick={toggleMobileLanguage}
                  className="mt-1 flex w-full items-center justify-between rounded-lg px-4 py-3 text-sm text-gray-300 hover:bg-gray-800/40"
                >
                  <span className="flex items-center gap-2">
                    <Globe size={18} className="text-primary-400"/> Language
                  </span>
                  {isMobileLanguageOpen ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
                </button>
                {isMobileLanguageOpen &&
                  <div className="mt-1 overflow-hidden rounded-lg border border-gray-700/40">
                    {languages.map(lang => (
                      <button
                        key={lang.code}
                        onClick={() => { i18n.changeLanguage(lang.code); setIsMobileLanguageOpen(false); }}
                        className={cn(
                          'flex w-full items-center px-4 py-2 text-sm',
                          lang.code===i18n.language
                            ? 'bg-primary-500/10 text-primary-400'
                            : 'text-gray-300 hover:bg-gray-800/30'
                        )}
                      >
                        {lang.name}
                      </button>
                    ))}
                  </div>}
              </nav>

              {/* — auth actions — */}
              <div className="border-t border-gray-700/50 p-4 space-y-3">
                {isAuthenticated ? (
                  <>
                    <Link
                      to="/dashboard"
                      onClick={closeMenu}
                      className="block w-full rounded-lg bg-primary-500/15 px-4 py-2 text-center text-primary-300"
                    >
                      {user?.first_name ?? 'Dashboard'}
                    </Link>
                    <button
                      onClick={() => { closeMenu(); handleLogout(); }}
                      className="block w-full rounded-lg bg-white/5 px-4 py-2 text-gray-300"
                    >
                      Sign out
                    </button>
                  </>
                ) : (
                  <>
                    {/* ✅  OLD MOBILE SIGN-IN BUTTON */}
                    <button
                      onClick={() => { closeMenu(); openSignIn(); }}
                      className="block w-full rounded-lg bg-[rgba(139,92,246,0.1)] px-4 py-2 text-[#a78bfa] font-medium transition-colors hover:bg-[rgba(139,92,246,0.2)]"
                    >
                      <LogIn size={16} className="inline mr-2" />
                      Sign&nbsp;In
                    </button>

                    {/* ✅  OLD MOBILE SIGN-UP BUTTON */}
                    <button
                      onClick={() => { closeMenu(); openSignUp(); }}
                      className="block w-full rounded-lg bg-[#8b5cf6] hover:bg-[#7c3aed] px-4 py-2 text-white font-medium transition-colors"
                    >
                      <UserPlus size={16} className="inline mr-2" />
                      Sign&nbsp;Up
                    </button>
                  </>
                )}
              </div>
            </aside>
          </>,
          document.getElementById('overlay-root')!
        )}
    </>
  );
};

export default Header;
