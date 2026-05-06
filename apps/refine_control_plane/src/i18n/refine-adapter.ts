"use client";

import { useMessages, useLocale } from "next-intl";
import { setUserLocale } from "./client";
import type { I18nProvider } from "@refinedev/core";

export function useRefineI18nProvider(): I18nProvider {
  const messages = useMessages() as Record<string, any>;
  const locale = useLocale();

  const fallbackLabel = (key: string): string => {
    let cleanKey = key;
    if (key.startsWith("resources_")) cleanKey = key.replace("resources_", "");
    if (key.startsWith("resources.")) cleanKey = key.replace("resources.", "");
    
    const map: Record<string, string> = {
        "learning": "Öğrenim Merkezi",
        "fingerprints": "Nöral Parmak İzleri",
        "evolution": "Sistem Evrimi",
        "safety": "Güvenlik Katmanı",
        "dashboard": "Kontrol Paneli"
    };
    
    if (map[cleanKey]) return map[cleanKey];
    if (map[cleanKey.toLowerCase()]) return map[cleanKey.toLowerCase()];

    const tail = cleanKey.split("/").pop() || cleanKey;
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
      
      const tail = key.split("/").pop() || "";
      const searchKeys = [
          key,
          tail,
          `resources.${key}`,
          `resources.${tail}`,
          `resources_${key.replace(/\//g, "_")}`,
          `resources_${tail}`,
          key.replace(/_/g, "."),
          key.replace(/\./g, "_"),
          key.toLowerCase()
      ];

      let value: string | undefined;
      for (const sk of searchKeys) {
          if (!sk) continue;
          value = getNestedValue(messages, sk);
          if (value) break;
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
