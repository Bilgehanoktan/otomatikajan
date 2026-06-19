import React from "react";
import ProjectFactoryPortfolioClient from "./_components/ProjectFactoryPortfolioClient";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Project Factory | Control Plane",
  description: "Global archive index and portfolio view for all Project Factory instances.",
};

export default function ProjectFactoryPage() {
  return <ProjectFactoryPortfolioClient />;
}
