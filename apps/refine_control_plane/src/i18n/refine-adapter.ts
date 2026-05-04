"use client";

import { useMessages, useLocale } from "next-intl";
import { setUserLocale } from "./client";
import type { I18nProvider } from "@refinedev/core";

export function useRefineI18nProvider(): I18nProvider {
  const messages = useMessages() as Record<string, any>;
  const locale = useLocale();

  const fallbackLabel = (key: string): string => {
    const tail = key.split("/").pop() || key;
    return tail.replace(/[-_]/g, " ").replace(/\./g, " ");
  };

  const getNestedValue = (obj: any, path: string) => {
    if (!path || !obj) return undefined;
    
    // Direct match (highest priority)
    if (obj[path] && typeof obj[path] === 'string') return obj[path];

    const parts = path.split('.');
    let current = obj;
    for (const part of parts) {
      if (current === null || current === undefined || typeof current !== 'object') {
          current = undefined;
          break;
      }
      current = current[part];
    }
    
    if (typeof current === 'string') return current;
    return undefined;
  };

  return {
    translate: (key: string, params?: Record<string, any>, defaultMessage?: string) => {
      if (!key) return defaultMessage || "";
      
      // Try exact
      let value = getNestedValue(messages, key);
      
      // Try lowercase
      if (!value && key !== key.toLowerCase()) {
        value = getNestedValue(messages, key.toLowerCase());
      }

      // Try underscore/dot swaps
      if (!value && key.includes('_')) {
          value = getNestedValue(messages, key.replace(/_/g, '.'));
      }
      if (!value && key.includes('.')) {
          value = getNestedValue(messages, key.replace(/\./g, '_'));
      }

      if (value) {
        let result = value;
        if (params) {
          Object.entries(params).forEach(([k, v]) => {
            result = result.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
            result = result.replace(new RegExp(`%\\{${k}\\}`, 'g'), String(v));
          });
        }
        return result;
      }

      return defaultMessage || fallbackLabel(key);
    },
    changeLocale: async (lang: string, options?: any) => {
      await setUserLocale(lang);
    },
    getLocale: () => locale,
  };
}
