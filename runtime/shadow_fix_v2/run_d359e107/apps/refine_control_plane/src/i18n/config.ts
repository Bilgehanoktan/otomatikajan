export const locales = ['en', 'tr'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'en';
export const COOKIE_NAME = 'NEXT_LOCALE';
