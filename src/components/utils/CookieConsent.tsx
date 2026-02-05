import { FC, useState, useEffect, useRef } from 'react';
import CookieConsentBanner from 'react-cookie-consent';
import { useTranslation } from 'react-i18next';
import { X, Info } from 'lucide-react';
import { gsap } from 'gsap';

const CookieConsent: FC = () => {
  const { t } = useTranslation();

  /* -------------------- responsive helpers -------------------- */
  const [isMobile, setIsMobile] = useState<boolean>(() => window.innerWidth < 768);
  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  /* -------------------- state -------------------- */
  const [showMoreInfo, setShowMoreInfo] = useState(false);
  const [declined,     setDeclined]     = useState<boolean>(
    localStorage.getItem('dealopia-essential-only') === 'true'
  );

  /* details box ref for GSAP height tween */
  const detailsRef = useRef<HTMLDivElement|null>(null);

  /* run height animation whenever showMoreInfo toggles */
  useEffect(() => {
    if (!detailsRef.current) return;

    const el   = detailsRef.current;
    const open = showMoreInfo;

    // measure natural height
    const fullH = el.scrollHeight;

    gsap.killTweensOf(el);
    gsap.to(el, {
      height: open ? fullH : 0,
      opacity: open ? 1 : 0,
      duration: .35,
      ease: 'power2.out',
      // important: after closing set display:none to keep content out of flow
      onComplete: () => { if (!open) el.style.display = 'none'; }
    });

    if (open) el.style.display = 'block';
  }, [showMoreInfo]);

  /* -------------------- handlers -------------------- */
  const handleDecline = () => {
    localStorage.setItem('dealopia-essential-only', 'true');
    setDeclined(true);
  };

  /* -------------------- render -------------------- */
  if (declined) {
    return (
      <div className="p-3 text-center bg-neutral-900">
        <p className="text-gray-200 mb-2">
          You've chosen to use only essential cookies.
        </p>
        <p className="text-xs text-gray-400">
          Some features like personalized deals and location-based recommendations may be limited.
        </p>
      </div>
    );
  }

  return (
    <CookieConsentBanner
      location={isMobile ? 'top' : 'bottom'}
      buttonText={t('cookies.accept')}
      declineButtonText={t('cookies.essentialOnly', 'Essential Only')}
      cookieName="dealopia-cookie-consent"
      overlay={false}
      enableDeclineButton
      flipButtons
      extraCookieOptions={{ path: '/' }}
      style={{
        background: 'rgba(12, 10, 9, 0.95)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(139, 92, 246, 0.2)',
        position: 'fixed',
        zIndex: 1400,
        padding: '1rem',
        margin: '1rem',
        width: 'calc(100% - 2rem)',
        maxWidth: 600,
        borderRadius: '1rem',
        boxShadow: '0 10px 25px -5px rgba(0,0,0,.2)',
        transform: isMobile ? 'none' : 'translateX(-50%)',
        left : isMobile ? 0 : '50%',
        right: isMobile ? 0 : 'auto',
        bottom: isMobile ? 'auto' : '1rem',
        top   : isMobile ? '1rem' : 'auto',
      }}
      buttonStyle={{
        background: '#8b5cf6',
        color: '#fff',
        borderRadius: '0.75rem',
        padding: '0.75rem 1.25rem',
        border: 'none',
        cursor: 'pointer',
        fontWeight: 600,
        fontSize: '0.875rem',
        transition: 'background-color .2s',
        flex: '1 1 auto',
        minWidth: 120,
        textAlign: 'center',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
      declineButtonStyle={{
        background: 'rgba(255,255,255,.05)',
        border: '1px solid rgba(139,92,246,.2)',
        color: '#d4d4d4',
        borderRadius: '0.75rem',
        padding: '0.75rem 1.25rem',
        cursor: 'pointer',
        fontWeight: 500,
        fontSize: '0.875rem',
        transition: 'background-color .2s',
        flex: '1 1 auto',
        minWidth: 120,
        textAlign: 'center',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
      }}
      contentStyle={{
        margin: '0 0 1.25rem',
        padding: 0,
        fontSize: '0.875rem',
        lineHeight: 1.5,
        color: '#fff',
      }}
      buttonWrapperClasses="flex flex-col sm:flex-row gap-3 w-full"
      expires={365}
      onAccept={() => {
        localStorage.setItem('dealopia-essential-only', 'false');
      }}
      onDecline={handleDecline}
    >
      <div className="relative pr-5">
        {/* close (decline) button */}
        <button
          onClick={handleDecline}
          className="absolute -top-2 -right-2 rounded-full bg-black/30 p-1 text-gray-400 transition-colors hover:bg-black/50 hover:text-white"
          aria-label="Close cookie notice"
        >
          <X size={16} />
        </button>

        {/* headline + message */}
        <h4 className="text-primary-400 font-semibold mb-1">
          {t('cookies.title', 'Cookie Settings')}
        </h4>
        <p className="mb-2 text-gray-200">
          {t(
            'cookies.message',
            'We use cookies to enhance your experience and show you personalized sustainable deals.'
          )}
        </p>

        {/* show-more toggle */}
        <div className="mb-3">
          <button
            onClick={() => setShowMoreInfo(v => !v)}
            className="flex items-center text-xs text-primary-400 hover:underline"
          >
            <Info size={12} className="mr-1" />
            {showMoreInfo
              ? 'Hide details'
              : "What if I choose 'Essential Only'?"}
          </button>

          {/* details box – hidden by default, animated with GSAP */}
          <div
            ref={detailsRef}
            style={{ height: 0, overflow: 'hidden', opacity: 0, display: 'none' }}
            className="mt-2 rounded-lg border border-neutral-800 bg-black/20 p-3 text-xs"
          >
            <p className="mb-2 text-gray-300">
              If you choose "Essential Only":
            </p>
            <ul className="list-inside list-disc space-y-1 text-gray-400">
              <li>Only cookies required for basic functionality are stored.</li>
              <li>Location-based deal discovery will require manual input.</li>
              <li>Deal recommendations won’t be personalised.</li>
              <li>Your search history won’t persist between sessions.</li>
              <li>You can change your preference at any time in Settings.</li>
            </ul>
          </div>
        </div>

        <p className="text-xs leading-tight text-gray-400">
          We prioritise your privacy. DealOpia uses first-party cookies only to
          improve your eco-friendly shopping experience.
        </p>
      </div>
    </CookieConsentBanner>
  );
};

export default CookieConsent;
