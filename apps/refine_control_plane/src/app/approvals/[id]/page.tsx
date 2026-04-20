import React from "react";
import ApprovalDetailClient from "./ApprovalDetailClient";

export function generateStaticParams() {
  // For static export, we generate a dummy path so the page is built.
  // Real routing will be handled client-side by Refine.
  return [{ id: "index" }];
}

export default function ApprovalDetailPage() {
  return <ApprovalDetailClient />;
}
