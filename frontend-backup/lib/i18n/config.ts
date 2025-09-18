/**
 * Internationalization Configuration
 * Supports multiple languages for the job matching system
 */

export const locales = ['en', 'ja', 'es', 'fr', 'de'] as const;
export type Locale = typeof locales[number];

export const defaultLocale: Locale = 'en';

// Locale configuration with native names
export const localeConfig: Record<Locale, {
  label: string;
  nativeLabel: string;
  flag: string;
  dir: 'ltr' | 'rtl';
  dateFormat: string;
}> = {
  en: {
    label: 'English',
    nativeLabel: 'English',
    flag: '🇺🇸',
    dir: 'ltr',
    dateFormat: 'MM/dd/yyyy',
  },
  ja: {
    label: 'Japanese',
    nativeLabel: '日本語',
    flag: '🇯🇵',
    dir: 'ltr',
    dateFormat: 'yyyy/MM/dd',
  },
  es: {
    label: 'Spanish',
    nativeLabel: 'Español',
    flag: '🇪🇸',
    dir: 'ltr',
    dateFormat: 'dd/MM/yyyy',
  },
  fr: {
    label: 'French',
    nativeLabel: 'Français',
    flag: '🇫🇷',
    dir: 'ltr',
    dateFormat: 'dd/MM/yyyy',
  },
  de: {
    label: 'German',
    nativeLabel: 'Deutsch',
    flag: '🇩🇪',
    dir: 'ltr',
    dateFormat: 'dd.MM.yyyy',
  },
};

// Path names for different locales
export const pathnames = {
  '/': {
    en: '/',
    ja: '/',
    es: '/',
    fr: '/',
    de: '/',
  },
  '/jobs': {
    en: '/jobs',
    ja: '/jobs',
    es: '/empleos',
    fr: '/emplois',
    de: '/jobs',
  },
  '/companies': {
    en: '/companies',
    ja: '/companies',
    es: '/empresas',
    fr: '/entreprises',
    de: '/unternehmen',
  },
  '/dashboard': {
    en: '/dashboard',
    ja: '/dashboard',
    es: '/panel',
    fr: '/tableau-de-bord',
    de: '/dashboard',
  },
  '/profile': {
    en: '/profile',
    ja: '/profile',
    es: '/perfil',
    fr: '/profil',
    de: '/profil',
  },
  '/about': {
    en: '/about',
    ja: '/about',
    es: '/acerca-de',
    fr: '/a-propos',
    de: '/uber-uns',
  },
  '/contact': {
    en: '/contact',
    ja: '/contact',
    es: '/contacto',
    fr: '/contact',
    de: '/kontakt',
  },
} as const;

// Currency configuration by locale
export const currencyConfig: Record<Locale, {
  currency: string;
  symbol: string;
  position: 'before' | 'after';
}> = {
  en: { currency: 'USD', symbol: '$', position: 'before' },
  ja: { currency: 'JPY', symbol: '¥', position: 'before' },
  es: { currency: 'EUR', symbol: '€', position: 'after' },
  fr: { currency: 'EUR', symbol: '€', position: 'after' },
  de: { currency: 'EUR', symbol: '€', position: 'after' },
};

// Time zone configuration
export const timezoneConfig: Record<Locale, string> = {
  en: 'America/New_York',
  ja: 'Asia/Tokyo',
  es: 'Europe/Madrid',
  fr: 'Europe/Paris',
  de: 'Europe/Berlin',
};