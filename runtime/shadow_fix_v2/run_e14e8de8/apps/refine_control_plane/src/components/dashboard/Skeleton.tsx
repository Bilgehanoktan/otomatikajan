"use client";

import React from "react";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-white/[0.04] ${className}`}
      style={{ animationDuration: '1.8s' }}
    />
  );
}
