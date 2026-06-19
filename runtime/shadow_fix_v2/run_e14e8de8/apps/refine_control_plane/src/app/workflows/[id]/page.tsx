import React from "react";
import WorkflowDetailClient from "../_components/WorkflowDetailClient";

type WorkflowDetailPageProps = {
  params: Promise<{ id: string }> | { id: string };
};

export const dynamic = "force-dynamic";
export const dynamicParams = true;

export default async function WorkflowDetailPage({ params }: WorkflowDetailPageProps) {
  const { id } = await Promise.resolve(params);
  return <WorkflowDetailClient id={id} />;
}
