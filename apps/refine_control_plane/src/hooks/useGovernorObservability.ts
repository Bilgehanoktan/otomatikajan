import { useList, useOne, useUpdate, useCreate } from "@refinedev/core";
import { useCallback } from "react";

export const useGovernorObservability = () => {
  // 1. Alerts Hook
  const useAlerts = (filters?: any) => {
    return useList({
      resource: "governor-alerts",
      pagination: { mode: "off" },
      filters: filters || [],
      meta: {
        endpoint: "/governance/observability/alerts",
      },
    });
  };

  // 2. Alert Detail Hook
  const useAlert = (id: string) => {
    return useOne({
      resource: "governor-alerts",
      id,
      meta: {
        endpoint: `/governance/observability/alerts/${id}`,
      },
    });
  };

  // 3. Drifts Hook
  const useDrifts = (limit: number = 50) => {
    return useList({
      resource: "governor-drifts",
      pagination: { pageSize: limit },
      meta: {
        endpoint: "/governance/observability/drifts",
      },
    });
  };

  // 4. Metrics Hook
  const useMetrics = () => {
    return useList({
      resource: "governor-metrics",
      pagination: { mode: "off" },
      meta: {
        endpoint: "/governance/observability/metrics",
      },
    });
  };

  // 5. Actions
  const { mutate: updateAlertStatus } = useUpdate();

  const ackAlert = useCallback((id: string, owner: string) => {
    return updateAlertStatus({
      resource: "governor-alerts",
      id,
      values: { status: "ACKNOWLEDGED", owner_id: owner },
      meta: {
        endpoint: `/governance/observability/alerts/${id}/ack`,
        method: "post",
      },
    });
  }, [updateAlertStatus]);

  const resolveAlert = useCallback((id: string, justification: string) => {
    return updateAlertStatus({
      resource: "governor-alerts",
      id,
      values: { status: "RESOLVED", summary: justification },
      meta: {
        endpoint: `/governance/observability/alerts/${id}/resolve`,
        method: "post",
      },
    });
  }, [updateAlertStatus]);

  const suppressAlert = useCallback((id: string, reason: string) => {
    return updateAlertStatus({
      resource: "governor-alerts",
      id,
      values: { status: "SUPPRESSED", summary: reason },
      meta: {
        endpoint: `/governance/observability/alerts/${id}/suppress`,
        method: "post",
      },
    });
  }, [updateAlertStatus]);

  // 6. Manual Scan
  const { mutate: triggerScan } = useCreate();
  const runScan = useCallback(() => {
    return triggerScan({
      resource: "governor-observability",
      values: {},
      meta: {
        endpoint: "/governance/observability/scan",
        method: "post",
      },
    });
  }, [triggerScan]);

  return {
    useAlerts,
    useAlert,
    useDrifts,
    useMetrics,
    ackAlert,
    resolveAlert,
    suppressAlert,
    runScan,
  };
};
