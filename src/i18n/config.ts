import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import HttpBackend from 'i18next-http-backend';

// Initialize i18n configuration
const initI18n = () => {
  i18n
    .use(HttpBackend)
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      fallbackLng: 'en',
      supportedLngs: ['en', 'de', 'fr', 'es', 'it', 'nl'],
      
      interpolation: {
        escapeValue: false,
      },
      
      cache: {
        enabled: true,
        expirationTime: 7 * 24 * 60 * 60 * 1000,
      },
      
      
      resources: {
        en: {
          translation: {
            search: {
              placeholder: 'Search for deals, shops, categories...',
              button: 'Search',
              filters: 'Filters',
              nearMe: 'Near Me',
              clearAll: 'Clear all',
              categories: 'Categories',
              done: 'Done',
              noResults: 'No results for "{{query}}"',
              results: 'Results for "{{query}}"',
              foundDeals: 'Found {{count}} deal',
              foundDeals_plural: 'Found {{count}} deals',
              searching: 'Searching...',
              startSearch: 'Search for deals',
              startSearchDesc: 'Enter keywords above to search for deals, shops, or categories. Discover exclusive discounts and special offers from your favorite local businesses.',
            },
            currency: {
              EUR: '€',
              GBP: '£',
            },
            cookies: {
              message: 'We use cookies to enhance your experience. By continuing to visit this site you agree to our use of cookies.',
              accept: 'Accept',
              decline: 'Decline',
            },
          },
        },
        de: {
          translation: {
            cookies: {
              message: 'Wir verwenden Cookies, um Ihre Erfahrung zu verbessern. Durch die weitere Nutzung dieser Website stimmen Sie der Verwendung von Cookies zu.',
              accept: 'Akzeptieren',
              decline: 'Ablehnen',
            },
          },
        },
        fr: {
          translation: {
            cookies: {
              message: 'Nous utilisons des cookies pour améliorer votre expérience. En continuant à visiter ce site, vous acceptez notre utilisation des cookies.',
              accept: 'Accepter',
              decline: 'Refuser',
            },
          },
        },
      },
    });
    
  return i18n;
};

export default initI18n();
