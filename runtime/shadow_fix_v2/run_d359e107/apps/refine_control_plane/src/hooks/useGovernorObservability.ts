import { useList, useOne, useUpdate, useCreate } from "@refinedev/core";
import { useCallback } from "react";

export const useGovernorObservability = () => {
  // 1. Alerts Hook
  const useAlerts = (filters?: any[]) => {
    return {
      query: useList({
        resource: "governance/governor/alerts",
        pagination: { mode: "off" },
        filters: filters || [],
      })
    };
  };

  // 2. Alert Detail Hook
  const useAlert = (id: string) => {
    return useOne({
      resource: "governance/governor/alerts",
      id,
    });
  };

  // 3. Drifts Hook
  const useDrifts = (limit: number = 50) => {
    return {
      query: useList({
        resource: "governance/governor/drifts",
        pagination: { pageSize: limit },
      })
    };
  };

  // 4. Metrics Hook
  const useMetrics = () => {
    return {
      query: useList({
        resource: "governance/governor/metrics",
        pagination: { mode: "off" },
      })
    };
  };

  // 5. Actions
  const { mutate: updateAlertStatus } = useUpdate();

  const ackAlert = useCallback((id: string, owner: string) => {
    return updateAlertStatus({
      resource: "governance/governor/alerts",
      id,
      values: { status: "ACKNOWLEDGED", owner_id: owner },
      meta: {
        endpoint: `/api/v1/governance/governor/alerts/${id}/ack`,
        method: "post",
      },
    });
  }, [updateAlertStatus]);

  const resolveAlert = useCallback((id: string, justification: string) => {
    return updateAlertStatus({
      resource: "governance/governor/alerts",
      id,
      values: { status: "RESOLVED", summary: justification },
      meta: {
        endpoint: `/api/v1/governance/governor/alerts/${id}/resolve`,
        method: "post",
      },
    });
  }, [updateAlertStatus]);

  const suppressAlert = useCallback((id: string, reason: string) => {
    return updateAlertStatus({
      resource: "governance/governor/alerts",
      id,
      values: { status: "SUPPRESSED", summary: reason },
      meta: {
        endpoint: `/api/v1/governance/governor/alerts/${id}/suppress`,
        method: "post",
      },
    });
  }, [updateAlertStatus]);

  // 6. Manual Scan
  const { mutate: triggerScan } = useCreate();
  const runScan = useCallback(() => {
    return triggerScan({
      resource: "governance/governor/scan",
      values: {},
      meta: {
        endpoint: "/api/v1/governance/governor/scan",
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
