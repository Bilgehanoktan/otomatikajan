import React from "react";
import IncidentDetailClient from "./IncidentDetailClient";

type IncidentDetailPageProps = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return [{ id: "index" }];
}

export default async function IncidentDetailPage({ params }: IncidentDetailPageProps) {
  const { id } = await params;
  return <IncidentDetailClient id={id} />;
}
