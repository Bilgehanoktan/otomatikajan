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

import { Providers } from "./providers";
import dynamic from "next/dynamic";

const Sidebar = dynamic(() => import("../components/Sidebar"), { ssr: false });
const SystemHeader = dynamic(() => import("../components/SystemHeader"), { ssr: false });

export const metadata: Metadata = {
  title: "Sovereign AGI | Control Plane",
  description: "Refine Ops Control Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark`}>
      <body className="h-full flex bg-[#0b0c10] text-[#c5c6c7] overflow-hidden">
        <Providers>
          <Sidebar />
          <div className="flex-1 flex flex-col h-full overflow-hidden relative">
            <SystemHeader />
            <main className="flex-1 overflow-y-auto overflow-x-hidden relative">
              {/* Background Ambient Glow */}
              <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#66fcf1]/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2" />
              <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-[#45a29e]/5 blur-[120px] rounded-full translate-y-1/2 -translate-x-1/2" />
              
              <div className="relative z-10">
                {children}
              </div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
