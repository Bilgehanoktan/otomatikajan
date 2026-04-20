import React from "react";
import IncidentDetailClient from "./IncidentDetailClient";

export function generateStaticParams() {
  return [{ id: "index" }];
}

export default function IncidentDetailPage() {
  return <IncidentDetailClient />;
}
