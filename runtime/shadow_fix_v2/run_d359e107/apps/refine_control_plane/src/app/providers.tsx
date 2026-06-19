"use client";

import React from "react";
import { ConfigProvider, theme, App } from "antd";
import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router";
import { activeDataProvider } from "@/lib/api_provider";
import { ensureSession, clearStoredAccessToken, performLogin, performRegister } from "@/lib/auth";
import { LoginParams, RegisterParams } from "@/types/auth";
import { 
  DollarSign,
  GraduationCap,
  Fingerprint,
  FlaskConical,
  Activity, 
  ShieldAlert, 
  AlertTriangle, 
  BarChart2, 
  Settings, 
  Rocket, 
  Target, 
  CheckCircle, 
  AlertCircle, 
  FileText, 
  Search, 
  Shield, 
  Cpu, 
  Brain, 
  ShieldOff, 
  Zap,
  Boxes,
  ShieldCheck,
  KeyRound
} from "lucide-react";
import { useRefineI18nProvider } from "@/i18n/refine-adapter";

export function Providers({ children }: { children: React.ReactNode }) {
  const i18nProvider = useRefineI18nProvider();

  const accessControlProvider = {
    can: async ({ resource, action }: { resource: string; action: string }) => {
      try {
        const session = await ensureSession();
        if (session && session.kind === "authenticated") {
          const roles = session.identity.roles || (session.identity.role ? [session.identity.role] : []);
          if (roles.includes("admin") || roles.includes("operator") || roles.includes("SOVEREIGN_PRIME") || roles.includes("AUDIT_OBSERVER") || roles.includes("OPS_COMMANDER")) {
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
    login: async (params: LoginParams) => {
      const result = await performLogin(params);
      return result || { success: false, error: new Error("Giriş işlemi yanıt vermedi.") };
    },
    register: async (params: RegisterParams) => {
      const result = await performRegister(params);
      return result || { success: false, error: new Error("Kayıt işlemi yanıt vermedi.") };
    },
    logout: async () => {
      clearStoredAccessToken();
      return { success: true, redirectTo: "/login" };
    },
    check: async () => {
      try {
        const session = await ensureSession();
        return { authenticated: session && session.kind === "authenticated" };
      } catch {
        return { authenticated: false };
      }
    },
    getPermissions: async () => {
      try {
        const session = await ensureSession();
        if (session && session.kind === "authenticated") {
          return session.identity.roles ?? (session.identity.role ? [session.identity.role] : null);
        }
      } catch {}
      return null;
    },
    getIdentity: async () => {
      try {
        const session = await ensureSession();
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
          error: new Error("Oturumunuz sona erdi. Lütfen tekrar giriş yapın."),
        };
      }

      if (error?.status === 403 || error?.statusCode === 403) {
        return {
          error: new Error("Bu işlem için yetkiniz bulunmuyor."),
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
          authProvider={authProvider as any}
          accessControlProvider={accessControlProvider as any}
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
              name: "governance/governor/status",
              list: "/governor",
              meta: { label: "Governor Status", icon: <Activity className="w-4 h-4" />, parent: "governance" },
            },
            {
              name: "governance/governor/cases",
              list: "/governor",
              meta: { label: "Governor Cases", icon: <ShieldAlert className="w-4 h-4" />, parent: "governance" },
            },
            {
              name: "governance/governor/escalations",
              list: "/governor/escalations",
              meta: { label: "resources_escalations", icon: <AlertTriangle className="w-4 h-4" />, parent: "governance" },
            },
            {
              name: "governance/governor/outcomes",
              list: "/governor/outcomes",
              meta: { label: "resources_outcomes", icon: <BarChart2 className="w-4 h-4" />, parent: "governance" },
            },
            {
              name: "governance/governor/scorecard",
              list: "/governor/scorecard",
              meta: { label: "resources_scorecard", icon: <Activity className="w-4 h-4" />, parent: "governance" },
            },
            {
              name: "governance/governor/calibrations",
              list: "/governor/calibrations",
              meta: { label: "resources_calibrations", icon: <Settings className="w-4 h-4" />, parent: "governance" },
            },
            {
              name: "governance/governor/resilience/drills",
              list: "/governor/drills",
              meta: { label: "resources_drills", icon: <Activity className="w-4 h-4" />, parent: "governance" },
            },
            {
              name: "governance/ops/handover",
              list: "/ops/handover-status",
              meta: { label: "resources_handoverStatus", icon: <Rocket className="w-4 h-4" />, hide: true },
            },
            {
              name: "governance/ops/launch-gates",
              list: "/ops/launch-gates",
              meta: { label: "resources_launchGates", icon: <Target className="w-4 h-4" />, hide: true },
            },
            {
              name: "governance/drills",
              list: "/governor/drills",
              meta: { label: "Drills", hide: true },
            },
            {
              name: "governance/approvals",
              list: "/governance/approvals",
              show: "/governance/approvals/:id",
              meta: { label: "resources_approvals", icon: <CheckCircle className="w-4 h-4" /> },
            },
            {
              name: "governance/incidents",
              list: "/governance/incidents",
              show: "/governance/incidents/:id",
              meta: { label: "resources_incidents", icon: <AlertCircle className="w-4 h-4" /> },
            },
            {
              name: "governance/proposals",
              list: "/governance/proposals",
              meta: { label: "resources_policyProposals", icon: <FileText className="w-4 h-4" /> },
            },
            {
              name: "mcp-hub",
              list: "/mcp-hub",
              meta: { label: "resources_mcpHub", icon: <Boxes className="w-4 h-4" /> },
            },
            {
              name: "governance/audit",
              list: "/governance/audit",
              meta: { label: "resources_auditLedger", icon: <Search className="w-4 h-4" /> },
            },
            {
              name: "governance/safety",
              list: "/governance/safety",
              meta: { label: "resources_safety", icon: <Shield className="w-4 h-4" /> },
            },
            {
              name: "governance/compliance",
              list: "/governance/compliance",
              meta: { label: "resources_compliance", icon: <Shield className="w-4 h-4" /> },
            },
            {
              name: "governance/lineage",
              list: "/governance/lineage",
              meta: { label: "Lineage", icon: <Search className="w-4 h-4" /> },
            },
            {
              name: "governance/signoffs",
              list: "/ops/handover-status",
              meta: { label: "Signoffs", icon: <CheckCircle className="w-4 h-4" /> },
            },
            {
              name: "governance/validations",
              list: "/ops/launch-gates",
              meta: { label: "Validations", icon: <Target className="w-4 h-4" /> },
            },
            {
              name: "governance/governor/proof/snapshots",
              list: "/proof/snapshots",
              meta: { label: "Proof Snapshots", parent: "governance/audit" },
            },
            {
              name: "governance/governor/proof",
              list: "/governor/proof",
              meta: { label: "Proof Fabric", parent: "governance/audit" },
            },
            {
              name: "learning",
              meta: { label: "resources_learning", icon: <Brain className="w-4 h-4" /> },
            },
            {
              name: "governance/governor/proof/events",
              list: "/proof/events",
              meta: { label: "Proof Events", parent: "governance/audit" },
            },
            {
              name: "learning/fingerprints",
              list: "/learning/fingerprints",
              meta: { label: "resources_fingerprints", icon: <Cpu className="w-4 h-4" />, parent: "learning" },
            },
            {
              name: "learning/strategy-memory",
              list: "/learning/strategy-memory",
              meta: { label: "resources_strategyMemory", icon: <Brain className="w-4 h-4" />, parent: "learning" },
            },
            {
              name: "learning/negative-patterns",
              list: "/learning/negative-patterns",
              meta: { label: "resources_negativePatterns", icon: <ShieldOff className="w-4 h-4" />, parent: "learning" },
            },
            {
              name: "learning/adaptation-candidates",
              list: "/learning/adaptation-candidates",
              meta: { label: "resources_adaptationCandidates", icon: <Zap className="w-4 h-4" />, parent: "learning" },
            },
            {
              name: "mesh",
              list: "/mesh",
              meta: { label: "resources_mesh", icon: <Activity className="w-4 h-4" /> },
            },
            {
              name: "axiology",
              list: "/axiology",
              meta: { label: "resources_axiology", icon: <Search className="w-4 h-4" /> },
            },
            {
              name: "repair-lab",
              list: "/repair-lab",
              meta: { label: "resources_repairLab", icon: <FlaskConical className="w-4 h-4" /> },
            },
            {
              name: "bilgeapi-ops",
              list: "/bilgeapi-ops",
              meta: { label: "BilgeAPI Ops", icon: <KeyRound className="w-4 h-4" /> },
            },
            {
              name: "meeting-room",
              list: "/meeting-room",
              meta: { label: "resources_meetingRoom", icon: <Boxes className="w-4 h-4" /> },
            },
            {
              name: "fleet",
              list: "/fleet",
              meta: { label: "resources_fleet", icon: <Rocket className="w-4 h-4" /> },
            },
            {
              name: "identity",
              list: "/identity",
              meta: { label: "resources_identity", icon: <Fingerprint className="w-4 h-4" /> },
            },
            {
              name: "costs",
              list: "/costs",
              meta: { label: "resources_costs", icon: <DollarSign className="w-4 h-4" /> },
            },
            {
                name: "prompt-studio",
                list: "/prompt-studio",
                meta: { label: "resources_promptStudio", icon: <Brain className="w-4 h-4" /> }
            },
            {
                name: "system-health",
                list: "/system-health",
                meta: { label: "resources_systemHealth", icon: <Activity className="w-4 h-4" /> }
            },
            {
              name: "training",
              list: "/training",
              meta: { label: "resources_training", icon: <GraduationCap className="w-4 h-4" /> },
            },
            {
              name: "verifiers",
              list: "/verifiers",
              meta: { label: "resources_verifiers" },
            },
            {
              name: "evolution",
              list: "/evolution",
              meta: { label: "resources_evolution" },
            },
            {
              name: "federation",
              list: "/federation",
              meta: { label: "resources_federation" },
            },
            {
              name: "federation/conflicts",
              list: "/federation/conflicts",
              meta: { label: "resources_conflicts", parent: "federation" },
            },
            {
              name: "ui-repair",
              list: "/ui-repair",
              meta: { label: "resources_uiRepair", icon: <ShieldCheck className="w-4 h-4" /> },
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
