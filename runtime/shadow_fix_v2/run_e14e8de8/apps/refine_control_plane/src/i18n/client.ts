"use client";

import { COOKIE_NAME, defaultLocale, locales } from "./config";

export async function setUserLocale(nextLocale: string): Promise<void> {
  const locale = locales.includes(nextLocale as (typeof locales)[number])
    ? nextLocale
    : defaultLocale;

  document.cookie = `${COOKIE_NAME}=${locale}; Path=/; Max-Age=31536000; SameSite=Lax`;
  window.location.reload();
}
