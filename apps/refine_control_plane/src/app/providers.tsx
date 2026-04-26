"use client";

import React from "react";
import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router";
import dataProvider from "@refinedev/simple-rest";
import { safeHttpClient } from "@/lib/api";

const isServer = typeof window === "undefined";
// Direct backend connection for proper cookie-based auth (proxy strips cookies)
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const mockDataProvider = {
  getList: () => Promise.resolve({ data: [], total: 0 }),
  getOne: () => Promise.resolve({ data: {} }),
  create: () => Promise.resolve({ data: {} }),
  update: () => Promise.resolve({ data: {} }),
  deleteOne: () => Promise.resolve({ data: {} }),
  custom: () => Promise.resolve({ data: {} }),
  getApiUrl: () => API_URL,
} as any;

import { ConfigProvider, theme, App } from "antd";
import type { AuthProvider } from "@refinedev/core";
import { accessControlProvider } from "@/providers/accessControlProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  // Global Resilience Armor: Wrapping dataProvider with safeHttpClient
  const activeDataProvider = isServer 
    ? mockDataProvider 
    : dataProvider(API_URL, safeHttpClient as any);

  const authProvider: AuthProvider = isServer ? {} as any : {
    login: async ({ email, password }) => {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include"
      });
      if (response.ok) return { success: true, redirectTo: "/" };
      return { success: false, error: new Error("Hatalı kimlik bilgileri") };
    },
    logout: async () => {
      await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" });
      return { success: true, redirectTo: "/login" };
    },
    check: async () => {
      try {
        const response = await fetch(`${API_URL}/auth/me`, { credentials: "include" });
        if (response.ok) {
          const data = await response.json();
          localStorage.setItem("auth", JSON.stringify({ role: data.role }));
          return { authenticated: true };
        }
        
        // Dev Mode Auto Login: Eğer token yoksa otonom oturum aç
        if (process.env.NODE_ENV === "development") {
          console.warn("Dev Mode Auto-Login triggered for admin@sovereign.agi");
          const auto = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: "admin@sovereign.agi", password: "admin1234" }),
            credentials: "include"
          });
          if (auto.ok) return { authenticated: true };
        }
      } catch (e) { 
        console.error("Auth check/auto-login failed due to network error", e); 
      }
      
      return { authenticated: false, redirectTo: "/login" };
    },
    getPermissions: async () => {
      try {
        const response = await fetch(`${API_URL}/auth/me`, { credentials: "include" });
        if (response.ok) {
          const data = await response.json();
          localStorage.setItem("auth", JSON.stringify({ role: data.role }));
          return data.roles;
        }
      } catch (e) { console.error("Permission check failed", e); }
      return null;
    },
    getIdentity: async () => {
      try {
        const response = await fetch(`${API_URL}/auth/me`, { credentials: "include" });
        if (response.ok) {
          const data = await response.json();
          return { id: data.id, name: data.email, avatar: "https://api.dicebear.com/7.x/identicon/svg?seed=admin" };
        }
      } catch (e) { console.error("Identity check failed", e); }
      return null;
    },
    onError: async (error) => {
      return { error };
    }
  };

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: "#66fcf1",
          borderRadius: 8,
        },
      }}
      wave={{ disabled: true }}
    >
      <App>
        <Refine
          routerProvider={routerProvider}
          dataProvider={activeDataProvider}
          authProvider={authProvider}
          accessControlProvider={accessControlProvider}
          resources={[
            {
              name: "workflows",
              list: "/workflows",
              show: "/workflows/:id",
              meta: { label: "İş Akışları" },
            },
            {
              name: "approvals",
              list: "/approvals",
              show: "/approvals/:id",
              meta: { label: "Onaylar" },
            },
            {
              name: "incidents",
              list: "/incidents",
              show: "/incidents/:id",
              meta: { label: "Olaylar" },
            },
            {
              name: "projects",
              list: "/fleet/projects",
              meta: { label: "Projeler" },
            },
            {
              name: "analytics/costs",
              list: "/fleet/economics/summary",
              meta: { label: "Maliyet Analizi" },
            },
            {
              name: "costs",
              list: "/costs",
              meta: { label: "Maliyetler" },
            },
            {
              name: "audit",
              list: "/audit",
              meta: { label: "Denetimler" },
            },
            {
              name: "improvements",
              list: "/improvements",
              meta: { label: "İyileştirmeler" },
            },
            {
              name: "federation",
              list: "/federation",
              meta: { label: "Federasyonlar" },
            },
            {
              name: "fleet",
              list: "/fleet",
              meta: { label: "Filo Merkezi" },
            },
            {
              name: "mesh",
              list: "/mesh",
              meta: { label: "Kontrol Ağı" },
            },
            {
              name: "safety",
              list: "/safety",
              meta: { label: "Güvenlik" },
            },
            {
              name: "repair-lab",
              list: "/repair-lab",
              meta: { label: "Otonom Laboratuvar" },
            },
            {
              name: "repair-memory",
              list: "/repair-memory",
              meta: { label: "Belleği Onar" },
            },
            {
              name: "verifiers",
              list: "/verifiers",
              meta: { label: "Doğrulayıcı Ağı" },
            },
            {
              name: "governance-lineage",
              list: "/governance-lineage",
              meta: { label: "Karar Soyağacı" },
            },
            {
              name: "compliance",
              list: "/compliance",
              meta: { label: "Uyum ve Denetim" },
            },
            {
              name: "policy-proposals",
              list: "/policy-proposals",
              meta: { label: "Anayasa Teklifleri" },
            },
            {
              name: "training",
              list: "/training",
              meta: { label: "Tatbikat Merkezi" },
            },
            {
              name: "self-tuning",
              list: "/self-tuning",
              meta: { label: "Ayar Konsolu" },
            },
            {
              name: "compliance/audit-bundles",
              list: "/compliance/audit-bundles",
              meta: { label: "Denetim Paketleri" },
            },
            {
              name: "handover-status",
              list: "/ops/handover-status",
              meta: { label: "Rollout Merkezi" },
            },
            {
              name: "launch-gates",
              list: "/ops/launch-gates",
              meta: { label: "Lansman Kapıları" },
            },
            {
              name: "learning/fingerprints",
              list: "/learning/fingerprints",
              show: "/learning/fingerprints/:id",
              meta: { label: "Hata Parmak İzleri", parent: "learning" },
            },
            {
              name: "learning/strategy-memory",
              list: "/learning/strategy-memory",
              meta: { label: "Strateji Belleği", parent: "learning" },
            },
            {
              name: "learning/negative-patterns",
              list: "/learning/negative-patterns",
              meta: { label: "Negatif Kalıplar", parent: "learning" },
            },
            {
              name: "learning/adaptation-candidates",
              list: "/learning/adaptation-candidates",
              meta: { label: "Adaptasyon AdaylarÄ±", parent: "learning" },
            },
            {
              name: "axiology",
              list: "/axiology",
              show: "/axiology/:id",
              meta: { label: "BiliÅŸsel Denetim" },
            },
          ]}
          options={{
            syncWithLocation: true,
            warnWhenUnsavedChanges: true,
            disableTelemetry: true,
          }}
        >
          {children}
        </Refine>
      </App>
    </ConfigProvider>
  );
}
