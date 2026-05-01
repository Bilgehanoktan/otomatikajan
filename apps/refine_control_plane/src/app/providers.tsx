"use client";

import React from "react";
import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router";
import dataProvider from "@refinedev/simple-rest";
import { safeHttpClient } from "@/lib/api";
import { clearStoredAccessToken, ensureSession, fetchCurrentOperator } from "@/lib/auth";
import { getApiBaseUrl } from "@/lib/runtime";
import { useRefineI18nProvider } from "../i18n/refine-adapter";

const isServer = typeof window === "undefined";
const API_URL = getApiBaseUrl();

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
  const activeDataProvider = isServer 
    ? mockDataProvider 
    : dataProvider(API_URL, safeHttpClient as any);

  const i18nProvider = useRefineI18nProvider();

  const authProvider: AuthProvider = isServer ? {} as any : {
    login: async ({ email, password }) => {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
        credentials: "include"
      });
      if (response.ok) {
        try {
          const payload = await response.json();
          if (payload?.access_token && typeof window !== "undefined") {
            window.localStorage.setItem("sqv_access_token", payload.access_token);
          }
        } catch {
          // Cookie session yeterliyse token parse zorunlu değil.
        }
        return { success: true, redirectTo: "/" };
      }
      return { success: false, error: new Error("Hatalı kimlik bilgileri") };
    },
    logout: async () => {
      clearStoredAccessToken();
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("auth");
      }
      await fetch(`${API_URL}/auth/logout`, { method: "POST", credentials: "include" });
      return { success: true, redirectTo: "/login" };
    },
    check: async () => {
      const session = await ensureSession();
      if (session.kind === "authenticated") {
        return { authenticated: true };
      }
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("auth");
      }
      return {
        authenticated: false,
        redirectTo: "/login",
        ...(session.kind === "network-error" ? { error: session.error } : {}),
      };
    },
    getPermissions: async () => {
      const session = await fetchCurrentOperator();
      if (session.kind === "authenticated") {
        return session.identity.roles ?? (session.identity.role ? [session.identity.role] : null);
      }
      return null;
    },
    getIdentity: async () => {
      const session = await fetchCurrentOperator();
      if (session.kind === "authenticated") {
        return {
          id: session.identity.id,
          name: session.identity.email,
          avatar: "https://api.dicebear.com/7.x/identicon/svg?seed=admin",
        };
      }
      return null;
    },
    onError: async (error: any) => {
      // SIF-01 Hardening: Handle session expiration (401/403)
      if (error?.status === 401 || error?.status === 403 || error?.statusCode === 401 || error?.statusCode === 403) {
        clearStoredAccessToken();
        return { 
          logout: true,
          error: new Error("Oturum süreniz doldu. Lütfen tekrar giriş yapın.") 
        };
      }
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
          i18nProvider={i18nProvider}
          resources={[
            {
              name: "dashboard",
              list: "/",
              meta: { label: "resources.dashboard" },
            },
            {
              name: "workflows",
              list: "/workflows",
              create: "/workflows/create",
              show: "/workflows/:id",
              meta: { label: "resources.workflows" },
            },
            {
              name: "governance/approvals",
              list: "/governance/approvals",
              show: "/governance/approvals/:id",
              meta: { label: "resources.approvals" },
            },
            {
              name: "governance/incidents",
              list: "/governance/incidents",
              show: "/governance/incidents/:id",
              meta: { label: "resources.incidents" },
            },
            {
              name: "workflows",
              list: "/workflows",
              meta: { label: "resources.projects" },
            },
            {
              name: "analytics/costs/summary",
              list: "/governance/analytics/costs/summary",
              meta: { label: "resources.costs" },
            },
            {
              name: "governance/compliance/audit-bundles",
              list: "/governance/compliance/audit-bundles",
              meta: { label: "resources.audit" },
            },
            {
              name: "repair-lab/improvements",
              list: "/repair-lab/improvements",
              meta: { label: "resources.improvements" },
            },
            {
              name: "federation",
              list: "/federation",
              meta: { label: "resources.federation" },
            },
            {
              name: "fleet",
              list: "/fleet",
              meta: { label: "resources.fleet", icon: "🚀" },
            },
            {
              name: "fleet/agents",
              list: "/fleet/agents",
              meta: { label: "resources.agents", parent: "fleet" },
            },
            {
              name: "fleet/operations",
              list: "/fleet/operations",
              meta: { label: "resources.operations", parent: "fleet" },
            },
            {
              name: "mesh",
              list: "/mesh",
              meta: { label: "resources.mesh" },
            },
            {
              name: "safety",
              list: "/safety",
              meta: { label: "resources.safety" },
            },
            {
              name: "repair-lab/dashboard",
              list: "/repair-lab",
              meta: { label: "resources.repairLab" },
            },
            {
              name: "repair-lab/repair-memory",
              list: "/repair-lab/repair-memory",
              meta: { label: "resources.repairMemory" },
            },
            {
              name: "verifiers",
              list: "/repair-lab/verifiers",
              meta: { label: "resources.verifiers" },
            },
            {
              name: "governance-lineage",
              list: "/governance/lineage",
              meta: { label: "resources.lineage" },
            },
            {
              name: "governance/compliance/policies",
              list: "/governance/compliance/policies",
              meta: { label: "resources.compliance" },
            },
            {
              name: "governance/proposals",
              list: "/governance/proposals",
              meta: { label: "resources.policyProposals" },
            },
            {
              name: "training",
              list: "/training",
              meta: { label: "resources.training" },
            },
            {
              name: "repair-lab/suggestions",
              list: "/repair-lab/suggestions",
              meta: { label: "resources.selfTuning" },
            },
            {
              name: "governance/ops/handover-status",
              list: "/governance/ops/handover-status",
              meta: { label: "resources.handoverStatus" },
            },
            {
              name: "governance/ops/launch-gates",
              list: "/governance/ops/launch-gates",
              meta: { label: "resources.launchGates" },
            },
            {
              name: "learning",
              meta: { label: "resources.learning" },
            },
            {
              name: "learning/fingerprints",
              list: "/learning/fingerprints",
              show: "/learning/fingerprints/:id",
              meta: { label: "resources.fingerprints", parent: "learning" },
            },
            {
              name: "learning/strategy-memory",
              list: "/learning/strategy-memory",
              meta: { label: "resources.strategyMemory", parent: "learning" },
            },
            {
              name: "learning/negative-patterns",
              list: "/learning/negative-patterns",
              meta: { label: "resources.negativePatterns", parent: "learning" },
            },
            {
              name: "learning/adaptation-candidates",
              list: "/learning/adaptation-candidates",
              meta: { label: "resources.adaptationCandidates", parent: "learning" },
            },
            {
              name: "axiology",
              list: "/governance/axiology-logs",
              show: "/governance/axiology-logs/:id",
              meta: { label: "resources.axiology" },
            },
            {
              name: "governance",
              meta: { label: "resources.governance" },
            },
            {
              name: "governance/governor/cases",
              list: "/governor",
              show: "/governor/:id",
              meta: { label: "resources.governorInbox", icon: "🛡️" },
            },
            {
              name: "governance/governor/escalations",
              list: "/governor/escalations",
              meta: { label: "resources.escalations", parent: "governance/governor/cases" },
            },
            {
              name: "governance/governor/scorecard",
              list: "/governor/scorecard",
              meta: { label: "resources.scorecard", parent: "governance/governor/cases" },
            },
            {
              name: "governance/governor/outcomes",
              list: "/governor/outcomes",
              meta: { label: "resources.outcomes", parent: "governance/governor/cases" },
            },
            {
              name: "governance/governor/calibrations",
              list: "/governor/calibrations",
              meta: { label: "resources.calibrations", parent: "governance/governor/cases" },
            },
            {
              name: "governance/governor/federated",
              list: "/governor/federated",
              meta: { label: "resources.federated", parent: "governance/governor/cases" },
            },
            {
              name: "governance/governor/conflicts",
              list: "/governor/conflicts",
              meta: { label: "resources.conflicts", parent: "governance/governor/cases" },
            },
            {
              name: "governor/resilience/status",
              list: "/governor/resilience",
              meta: { label: "resources.resilience", parent: "governance/governor/cases" },
            },
            {
              name: "governor/resilience/drills",
              list: "/governor/drills",
              meta: { label: "resources.drills", parent: "governance/governor/cases" },
            },
            {
              name: "governor/observability",
              list: "/governor/observability",
              meta: { label: "resources.observability", parent: "governance/governor/cases" },
            },
            {
              name: "governor/drifts",
              list: "/governor/drifts",
              show: "/governor/drifts/:id",
              meta: { label: "resources.drifts", parent: "governance/governor/cases" },
            },
            {
              name: "governance/inbox/governor/proof",
              list: "/governor/proof",
              show: "/governor/proof/snapshots/:id",
              meta: { label: "resources.proofFabric", parent: "governance/governor/cases" },
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
