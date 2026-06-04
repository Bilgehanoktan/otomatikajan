"use client";

import dynamic from "next/dynamic";

const GovernorDrillsClient = dynamic(() => import("./GovernorDrillsClient"), {
  ssr: false,
  loading: () => <div className="min-h-screen bg-[#060a12]" />,
});

export default function GovernorDrillsPage() {
  return <GovernorDrillsClient />;
}
