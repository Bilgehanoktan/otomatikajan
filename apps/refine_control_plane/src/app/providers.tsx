"use client";

import React from "react";
import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router";
import dataProvider from "@refinedev/simple-rest";

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

import { ConfigProvider, theme } from "antd";

export function Providers({ children }: { children: React.ReactNode }) {
  const activeDataProvider = isServer ? mockDataProvider : dataProvider(API_URL);

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
      <Refine
        routerProvider={routerProvider}
        dataProvider={activeDataProvider}
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
    </ConfigProvider>
  );
}
