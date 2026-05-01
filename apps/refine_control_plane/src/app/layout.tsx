import type { Metadata } from "next";
import React, { Suspense } from "react";
import "./globals.css";
import { Providers } from "./providers";
import LayoutWrapper from "../components/LayoutWrapper";
import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages } from 'next-intl/server';


export const metadata: Metadata = {
  title: "Egemen YAZ | Kontrol Düzlemi",
  description: "Otonom Yazılım Geliştirme Operasyonları Kontrol Paneli",
};

import { AntdRegistry } from "@ant-design/nextjs-registry";

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} className="min-h-screen antialiased dark">
      <body className="min-h-screen bg-[#0b0c10] text-[#c5c6c7]" suppressHydrationWarning>
        <Suspense fallback={<div className="h-full bg-[#0b0c10]" />}>
          <NextIntlClientProvider messages={messages}>
            <AntdRegistry>
              <Providers>
                <LayoutWrapper>
                  {children}
                </LayoutWrapper>
              </Providers>
            </AntdRegistry>
          </NextIntlClientProvider>
        </Suspense>
      </body>
    </html>
  );
}
