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
        },
        {
          name: "improvements",
          list: "/improvements",
        },
      ]}
      options={{
        syncWithLocation: true,
        warnWhenUnsavedChanges: true,
      }}
    >
      {children}
    </Refine>
  );
}
