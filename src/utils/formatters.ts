import { useTranslation } from 'react-i18next';

/**
 * Format a number as a currency string, respecting the user's locale
 */
export function formatCurrency(value: number, currencyCode: string = 'USD'): string {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: currencyCode,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format a date using the user's locale
 */
export function formatDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
  const dateObject = typeof date === 'string' ? new Date(date) : date;
  return new Intl.DateTimeFormat(undefined, options).format(dateObject);
}

/**
 * Format a percentage
 */
export function formatPercentage(value: number, fractionDigits: number = 0): string {
  return `${value.toFixed(fractionDigits)}%`;
}

/**
 * React hook for formatting currency with i18n support
 */
export function useFormatters() {
  const { i18n } = useTranslation();
  
  return {
    formatCurrency: (value: number, currencyCode: string = 'USD') => {
      return new Intl.NumberFormat(i18n.language, {
        style: 'currency',
        currency: currencyCode,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(value);
    },
    
    formatDate: (date: Date | string, options?: Intl.DateTimeFormatOptions) => {
      const dateObject = typeof date === 'string' ? new Date(date) : date;
      return new Intl.DateTimeFormat(i18n.language, options).format(dateObject);
    },
    
    formatPercentage: (value: number, fractionDigits: number = 0) => {
      return `${value.toFixed(fractionDigits)}%`;
    }
  };
}