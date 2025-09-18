/**
 * Internationalization Utilities
 * Helper functions for i18n operations
 */

import { locales, defaultLocale, type Locale } from './config';

/**
 * Get locale from pathname
 */
export function getLocaleFromPathname(pathname: string): Locale {
  const segments = pathname.split('/');
  const potentialLocale = segments[1] as Locale;

  if (locales.includes(potentialLocale)) {
    return potentialLocale;
  }

  return defaultLocale;
}

/**
 * Remove locale prefix from pathname
 */
export function removeLocaleFromPathname(pathname: string, locale: Locale): string {
  if (locale === defaultLocale) return pathname;

  const segments = pathname.split('/');
  if (segments[1] === locale) {
    segments.splice(1, 1);
  }

  return segments.join('/') || '/';
}

/**
 * Add locale prefix to pathname
 */
export function addLocaleToPathname(pathname: string, locale: Locale): string {
  if (locale === defaultLocale) return pathname;

  // Remove existing locale if present
  const cleanPathname = removeLocaleFromPathname(pathname, getLocaleFromPathname(pathname));

  return `/${locale}${cleanPathname === '/' ? '' : cleanPathname}`;
}

/**
 * Get browser locale
 */
export function getBrowserLocale(): Locale {
  if (typeof window === 'undefined') return defaultLocale;

  const browserLanguage = navigator.language.split('-')[0] as Locale;

  return locales.includes(browserLanguage) ? browserLanguage : defaultLocale;
}

/**
 * Format message with interpolation
 */
export function formatMessage(
  template: string,
  values: Record<string, string | number> = {}
): string {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    return values[key]?.toString() || match;
  });
}

/**
 * Get direction for locale
 */
export function getDirection(locale: Locale): 'ltr' | 'rtl' {
  // For now, all supported locales are LTR
  // Add RTL languages here when needed
  return 'ltr';
}

/**
 * Format number for locale
 */
export function formatNumber(
  value: number,
  locale: Locale,
  options?: Intl.NumberFormatOptions
): string {
  return new Intl.NumberFormat(locale, options).format(value);
}

/**
 * Format currency for locale
 */
export function formatCurrency(
  value: number,
  locale: Locale,
  currency: string = 'USD'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(value);
}

/**
 * Format date for locale
 */
export function formatDate(
  date: Date | string,
  locale: Locale,
  options?: Intl.DateTimeFormatOptions
): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options,
  }).format(dateObj);
}

/**
 * Format relative time for locale
 */
export function formatRelativeTime(
  date: Date | string,
  locale: Locale
): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });

  if (diffInSeconds < 60) {
    return rtf.format(-diffInSeconds, 'second');
  } else if (diffInSeconds < 3600) {
    return rtf.format(-Math.floor(diffInSeconds / 60), 'minute');
  } else if (diffInSeconds < 86400) {
    return rtf.format(-Math.floor(diffInSeconds / 3600), 'hour');
  } else if (diffInSeconds < 2592000) {
    return rtf.format(-Math.floor(diffInSeconds / 86400), 'day');
  } else if (diffInSeconds < 31536000) {
    return rtf.format(-Math.floor(diffInSeconds / 2592000), 'month');
  } else {
    return rtf.format(-Math.floor(diffInSeconds / 31536000), 'year');
  }
}

/**
 * Get locale from accept-language header
 */
export function getLocaleFromAcceptLanguage(acceptLanguage: string): Locale {
  const languages = acceptLanguage
    .split(',')
    .map(lang => lang.split(';')[0].trim().split('-')[0])
    .filter(lang => locales.includes(lang as Locale));

  return (languages[0] as Locale) || defaultLocale;
}