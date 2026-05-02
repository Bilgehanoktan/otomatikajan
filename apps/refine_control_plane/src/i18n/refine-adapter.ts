"use client";

import { useTranslations, useLocale } from "next-intl";
import { setUserLocale } from "./client";
import type { I18nProvider } from "@refinedev/core";

export function useRefineI18nProvider(): I18nProvider {
  const t = useTranslations();
  const locale = useLocale();

  const isLikelyUnsafeI18nKey = (key: string): boolean => {
    if (!key) return true;
    // Refine can emit resource-name-based labels that are not message keys.
    if (key.includes("/")) return true;
    // Guard against malformed duplicated keys like "a.b.a.b".
    const parts = key.split(".");
    if (parts.length >= 4) {
      const left = parts.slice(0, parts.length / 2).join(".");
      const right = parts.slice(parts.length / 2).join(".");
      if (left === right) return true;
    }
    return false;
  };

  const fallbackLabel = (key: string): string => {
    const tail = key.split("/").pop() || key;
    return tail.replace(/[-_]/g, " ");
  };

  return {
    translate: (key: string, params?: Record<string, any>, defaultMessage?: string) => {
      if (isLikelyUnsafeI18nKey(key)) {
        return defaultMessage || fallbackLabel(key);
      }
      try {
        return t(key, params);
      } catch (error) {
        return defaultMessage || fallbackLabel(key);
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
