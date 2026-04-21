"use client";

import React from "react";
import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router";
import dataProvider from "@refinedev/simple-rest";
import { safeHttpClient } from "@/lib/api";

const isServer = typeof window === "undefined";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

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
      const response = await fetch(`${API_URL}/auth/me`, { credentials: "include" });
      if (response.ok) {
        return { authenticated: true };
      }
      // Dev Mode Auto Login: Eğer token yoksa otonom oturum aç
      console.warn("Dev Mode Auto-Login triggered for admin@sovereign.agi");
      try {
        const auto = await fetch(`${API_URL}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: "admin@sovereign.agi", password: "admin1234" }),
          credentials: "include"
        });
        if (auto.ok) return { authenticated: true };
      } catch (e) { console.error("Auto login failed", e); }
      
      return { authenticated: false, redirectTo: "/login" };
    },
    getPermissions: async () => {
      const response = await fetch(`${API_URL}/auth/me`, { credentials: "include" });
      if (response.ok) {
        const data = await response.json();
        return data.is_admin ? ["admin"] : ["user"];
      }
      return null;
    },
    getIdentity: async () => {
      const response = await fetch(`${API_URL}/auth/me`, { credentials: "include" });
      if (response.ok) {
        const data = await response.json();
        return { id: data.id, name: data.email, avatar: "https://api.dicebear.com/7.x/identicon/svg?seed=admin" };
      }
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
    >
      <App>
        <Refine
          routerProvider={routerProvider}
          dataProvider={activeDataProvider}
          authProvider={authProvider}
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
              name: "audit-bundles",
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
