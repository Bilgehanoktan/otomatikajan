import React from "react";
import ProjectFactoryClient from "../_components/ProjectFactoryClient";

type ProjectFactoryDetailPageProps = {
  params: Promise<{ project_id: string }> | { project_id: string };
};

export const dynamic = "force-dynamic";
export const dynamicParams = true;

export default async function ProjectFactoryDetailPage({ params }: ProjectFactoryDetailPageProps) {
  const { project_id } = await Promise.resolve(params);
  return <ProjectFactoryClient projectId={project_id} />;
}
