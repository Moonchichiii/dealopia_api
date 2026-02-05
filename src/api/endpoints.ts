export const ENDPOINTS = {
    AUTH: {
      LOGIN: '/api/v1/auth/login/',
      REGISTER: '/api/v1/auth/registration/',
      LOGOUT: '/api/v1/auth/logout/',
      ME: '/api/v1/auth/me/',
      VERIFY_EMAIL: '/api/v1/auth/registration/verify-email/',
      REFRESH_TOKEN: '/api/v1/auth/token/refresh/',
      VERIFY_TOKEN: '/api/v1/auth/token/verify/',
      PASSWORD_RESET: '/api/v1/auth/password/reset/',
      PASSWORD_RESET_CONFIRM: '/api/v1/auth/password/reset/confirm/',
      PASSWORD_CHANGE: '/api/v1/auth/password/change/',
      TWO_FACTOR_VERIFY: '/api/v1/auth/2fa/verify/',
      TWO_FACTOR_SETUP: '/api/v1/auth/2fa/setup/',
      TWO_FACTOR_DISABLE: '/api/v1/auth/2fa/disable/',
      SOCIAL_LOGIN: '/api/v1/auth/social-login/',
      SESSION_INFO: '/api/v1/auth/session-info/',
    },
    DEALS: {
      BASE: '/api/v1/deals/',
      FEATURED: '/api/v1/deals/featured/',
      ENDING_SOON: '/api/v1/deals/ending-soon/',
      NEARBY: '/api/v1/deals/nearby/',
      DETAIL: (id: number | string) => `/api/v1/deals/${id}/`,
      TRACK_VIEW: (id: number | string) => `/api/v1/deals/${id}/track_view/`,
      TRACK_CLICK: (id: number | string) => `/api/v1/deals/${id}/track_click/`,
      RELATED: (id: number | string) => `/api/v1/deals/${id}/related/`
    },
    SHOPS: {
      BASE: '/api/v1/shops/',
      FEATURED: '/api/v1/shops/featured/',
      DETAIL: (id: number | string) => `/api/v1/shops/${id}/`,
      DEALS: (id: number | string) => `/api/v1/shops/${id}/deals/`
    },
    CATEGORIES: {
      BASE: '/api/v1/categories/',
      FEATURED: '/api/v1/categories/featured/',
      DETAIL: (id: number | string) => `/api/v1/categories/${id}/`,
      DEALS: (id: number | string) => `/api/v1/categories/${id}/deals/`
    },
    LOCATIONS: {
      BASE: '/api/v1/locations/',
      NEARBY: '/api/v1/locations/nearby/',
      DETAIL: (id: number | string) => `/api/v1/locations/${id}/`
    },
    USERS: {
      FAVORITES: '/api/v1/users/favorites/',
      PROFILE: '/api/v1/users/profile/',
      SETTINGS: '/api/v1/users/settings/'
    }
};

export default ENDPOINTS;
