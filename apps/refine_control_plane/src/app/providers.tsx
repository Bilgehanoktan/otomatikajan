"use client";

import React from "react";
import { Refine } from "@refinedev/core";
import routerProvider from "@refinedev/nextjs-router";
import dataProvider from "@refinedev/simple-rest";

const API_URL = "http://localhost:8000/api/v1";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Refine
      routerProvider={routerProvider}
      dataProvider={dataProvider(API_URL)}
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
          meta: { label: "Onaylar" },
        },
        {
          name: "incidents",
          list: "/incidents",
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
          name: "self-tuning",
          list: "/self-tuning",
          meta: { label: "Ayar Konsolu" },
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
  );
}
