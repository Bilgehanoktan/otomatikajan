"use client";

import React from "react";
import { ConfigProvider, theme, App } from "antd";
import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router";
import { activeDataProvider } from "@/lib/api_provider";
import { fetchCurrentOperator, clearStoredAccessToken, performLogin, performRegister } from "@/lib/auth";
import { useRefineI18nProvider } from "@/i18n/refine-adapter";

export function Providers({ children }: { children: React.ReactNode }) {
  const i18nProvider = useRefineI18nProvider();

  const accessControlProvider = {
    can: async ({ resource, action }: any) => {
      try {
        const session = await fetchCurrentOperator();
        if (session && session.kind === "authenticated") {
          const roles = session.identity.roles || (session.identity.role ? [session.identity.role] : []);
          if (roles.includes("admin") || roles.includes("operator") || roles.includes("SOVEREIGN_PRIME") || roles.includes("AUDIT_OBSERVER")) {
            return { can: true };
          }
        }
      } catch (e) {
        console.error("[Auth] AccessControl check failed:", e);
      }
      return { can: false, reason: "Unauthorized" };
    },
  };

  const authProvider = {
    login: async (params: any) => {
      const result = await performLogin(params);
      return result || { success: false, error: new Error("Giriş işlemi yanıt vermedi.") };
    },
    register: async (params: any) => {
      const result = await performRegister(params);
      return result || { success: false, error: new Error("Kayıt işlemi yanıt vermedi.") };
    },
    logout: async () => {
      clearStoredAccessToken();
      return { success: true, redirectTo: "/login" };
    },
    check: async () => {
      try {
        const session = await fetchCurrentOperator();
        return { authenticated: session && session.kind === "authenticated" };
      } catch {
        return { authenticated: false };
      }
    },
    getPermissions: async () => {
      try {
        const session = await fetchCurrentOperator();
        if (session && session.kind === "authenticated") {
          return session.identity.roles ?? (session.identity.role ? [session.identity.role] : null);
        }
      } catch {}
      return null;
    },
    getIdentity: async () => {
      try {
        const session = await fetchCurrentOperator();
        if (session && session.kind === "authenticated") {
          return {
            id: session.identity.id,
            name: session.identity.email,
            email: session.identity.email,
            avatar: `https://api.dicebear.com/7.x/identicon/svg?seed=${session.identity.email}`,
          };
        }
      } catch {}
      return null;
    },
    onError: async (error: any) => {
      if (error?.status === 401 || error?.statusCode === 401) {
        clearStoredAccessToken();
        return {
          logout: true,
          error: new Error("Oturumunuz sona erdi. Lutfen tekrar giris yapin."),
        };
      }

      if (error?.status === 403 || error?.statusCode === 403) {
        return {
          error: new Error("Bu islem icin yetkiniz bulunmuyor."),
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
              meta: { label: "resources_dashboard" },
            },
            {
              name: "workflows",
              list: "/workflows",
              create: "/workflows/create",
              show: "/workflows/:id",
              meta: { label: "resources_workflows" },
            },
            {
              name: "governance/approvals",
              list: "/governance/approvals",
              show: "/approvals/:id",
              meta: { label: "resources_approvals" },
            },
            {
              name: "governance/incidents",
              list: "/governance/incidents",
              show: "/incidents/:id",
              meta: { label: "resources_incidents" },
            },
            {
              name: "governance/analytics/costs",
              list: "/costs",
              meta: { label: "resources_costs" },
            },
            {
              name: "governance/compliance/audit-bundles",
              list: "/governance/compliance/audit-bundles",
              meta: { label: "resources_auditBundles" },
            },
            {
              name: "audit",
              list: "/audit",
              meta: { label: "resources_auditLedger" },
            },
            {
              name: "governance/improvements",
              list: "/improvements",
              meta: { label: "resources_improvements" },
            },
            {
              name: "federation",
              list: "/federation",
              meta: { label: "resources_federation" },
            },
            {
              name: "fleet",
              list: "/fleet",
              meta: { label: "resources_fleet", icon: "🚀" },
            },
            {
              name: "fleet/ops/agents",
              list: "/fleet/agents",
              meta: { label: "resources_agents", parent: "fleet" },
            },
            {
              name: "fleet/ops",
              list: "/fleet/operations",
              meta: { label: "resources_operations", parent: "fleet" },
            },
            {
              name: "mesh",
              list: "/mesh",
              meta: { label: "resources_mesh" },
            },
            {
              name: "safety",
              list: "/safety",
              meta: { label: "resources_safety" },
            },
            {
              name: "repair-lab/dashboard",
              list: "/repair-lab",
              meta: { label: "resources_repairLab" },
            },
            {
              name: "repair-lab/repair-memory",
              list: "/repair-memory",
              meta: { label: "resources_repairMemory" },
            },
            {
              name: "verifiers",
              list: "/verifiers",
              meta: { label: "resources_verifiers" },
            },
            {
              name: "governance/lineage",
              list: "/governance-lineage",
              meta: { label: "resources_lineage" },
            },
            {
              name: "governance/compliance/policies",
              list: "/compliance",
              meta: { label: "resources_compliance" },
            },
            {
              name: "governance/proposals",
              list: "/policy-proposals",
              meta: { label: "resources_policyProposals" },
            },
            {
              name: "training",
              list: "/training",
              meta: { label: "resources_training" },
            },
            {
              name: "governance/inbox/handover",
              list: "/governance/handover",
              meta: { label: "resources_handoverStatus" },
            },
            {
              name: "governance/inbox/launch-gates",
              list: "/governance/launch-gates",
              meta: { label: "resources_launchGates" },
            },
            {
              name: "learning",
              list: "/learning/fingerprints",
              meta: { label: "resources_learning" },
            },
            {
              name: "learning/fingerprints",
              list: "/learning/fingerprints",
              meta: { label: "resources_fingerprints", parent: "learning" },
            },
            {
              name: "learning/strategy-memory",
              list: "/learning/strategy-memory",
              meta: { label: "resources_strategyMemory", parent: "learning" },
            },
            {
              name: "learning/negative-patterns",
              list: "/learning/negative-patterns",
              meta: { label: "resources_negativePatterns", parent: "learning" },
            },
            {
              name: "adaptation-candidates",
              list: "/learning/adaptation-candidates",
              meta: { label: "resources_adaptationCandidates" },
            },
            {
              name: "governance/axiology",
              list: "/axiology",
              meta: { label: "resources_axiology" },
            },
            {
              name: "governance/inbox/governor/cases",
              list: "/governor",
              show: "/governor/cases/:id",
              meta: { label: "resources_governorInbox" },
            },
            {
              name: "governance/inbox/escalations",
              list: "/governor/escalations",
              meta: { label: "resources_escalations" },
            },
            {
               name: "governance/analytics/scorecard",
               list: "/scorecard",
               meta: { label: "resources_scorecard" },
            },
            {
              name: "governance/analytics/outcomes",
              list: "/outcomes",
              meta: { label: "resources_outcomes" },
            },
            {
              name: "governance/improvements",
              list: "/improvements",
              meta: { label: "resources_improvements" },
            },
            {
              name: "governance/inbox/governor/calibrations",
              list: "/calibrations",
              meta: { label: "resources_calibrations" },
            },
            {
              name: "federation/decisions",
              list: "/federation/decisions",
              meta: { label: "resources_federated", parent: "federation" },
            },
            {
              name: "federation/conflicts",
              list: "/federation/conflicts",
              meta: { label: "resources_conflicts", parent: "federation" },
            },
            {
              name: "governance/resilience",
              list: "/governor/resilience",
              meta: { label: "resources_resilience", parent: "governance/inbox/governor/cases" },
            },
            {
              name: "governance/drills",
              list: "/drills",
              meta: { label: "resources_drills", parent: "governance/inbox/governor/cases" },
            },
            {
              name: "governance/observability",
              list: "/observability",
              meta: { label: "resources_observability", parent: "governance/inbox/governor/cases" },
            },
            {
              name: "governance/analytics/drifts",
              list: "/drifts",
              meta: { label: "resources_drifts", parent: "governance/inbox/governor/cases" },
            },
            {
              name: "governance/proof",
              list: "/governor/proof",
              show: "/governor/proof/snapshots/:id",
              meta: { label: "resources_proofFabric", parent: "governance/inbox/governor/cases" },
            },
            {
              name: "evolution",
              list: "/evolution",
              meta: { label: "resources_evolution" },
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
