import React from "react";
import WorkflowDetailClient from "../_components/WorkflowDetailClient";

type WorkflowDetailPageProps = {
  params: Promise<{ id: string }>;
};

export function generateStaticParams() {
  return [{ id: "index" }];
}

export default async function WorkflowDetailPage({ params }: WorkflowDetailPageProps) {
  const { id } = await params;
  return <WorkflowDetailClient id={id} />;
}
