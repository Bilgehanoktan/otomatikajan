import { getRequestConfig } from 'next-intl/server';
import { locales, defaultLocale } from './config';

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;

  if (!locale || !locales.includes(locale as any)) {
    locale = defaultLocale;
  }

  // Load app-specific messages
  // Using .default because JSON imports in ESM return an object with a default key
  const appMessages = await import(`../messages/${locale}.json`);
  
  // Load Refine common messages
  const refineMessages = await import(`../messages/refine/${locale}-common.json`);

  const messages = {
    ...(appMessages.default || appMessages),
    refine: (refineMessages.default || refineMessages)
  };

  return {
    locale,
    messages
  };
});
