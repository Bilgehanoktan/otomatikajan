import type { Metadata } from "next";
import React, { Suspense } from "react";
import "./globals.css";
import { Providers } from "./providers";
import LayoutWrapper from "../components/LayoutWrapper";


export const metadata: Metadata = {
  title: "Egemen YAZ | Kontrol Düzlemi",
  description: "Otonom Yazılım Geliştirme Operasyonları Kontrol Paneli",
};

import { AntdRegistry } from "@ant-design/nextjs-registry";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" className="min-h-screen antialiased dark">
      <body className="min-h-screen bg-[#0b0c10] text-[#c5c6c7]" suppressHydrationWarning>
        <Suspense fallback={<div className="h-full bg-[#0b0c10]" />}>
          <AntdRegistry>
            <Providers>
              <LayoutWrapper>
                {children}
              </LayoutWrapper>
            </Providers>
          </AntdRegistry>
        </Suspense>
      </body>
    </html>
  );
}
