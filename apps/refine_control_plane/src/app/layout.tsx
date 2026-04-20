import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

import React, { Suspense } from "react";
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
    <html lang="tr" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}>
      <body className="h-full bg-[#0b0c10] text-[#c5c6c7] overflow-hidden" suppressHydrationWarning>
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
