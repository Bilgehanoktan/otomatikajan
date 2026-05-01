"use client";

import { useTranslations, useLocale } from "next-intl";
import { setUserLocale } from "./client";
import type { I18nProvider } from "@refinedev/core";

export function useRefineI18nProvider(): I18nProvider {
  const t = useTranslations();
  const locale = useLocale();

  return {
    translate: (key: string, params?: Record<string, any>, defaultMessage?: string) => {
      // next-intl throws if key doesn't exist by default, but we can use fallback logic
      // In next-intl, there is a `t.has(key)` or we can just try to translate
      // Refine usually passes keys like "buttons.create" or "documentTitle.default"
      try {
        return t(key, params);
      } catch (error) {
        return defaultMessage || key;
      }
    },
    changeLocale: async (lang: string, options?: any) => {
      // Update the cookie using the server action
      await setUserLocale(lang);
      // Optional: if options handles routing or similar, we don't need it because Next.js handles refreshing state
    },
    getLocale: () => locale,
  };
}
