import { AccessControlProvider } from "@refinedev/core";

/**
 * Sovereign AGI - Access Control Provider (SIF-01)
 * Enforces role-based visibility and action restrictions on the frontend.
 */
export const accessControlProvider: AccessControlProvider = {
  can: async ({ resource, action }) => {
    // 1. Get identity from localStorage (stored during login)
    const auth = localStorage.getItem("auth");
    if (!auth) {
      return { can: false, reason: "Oturum bulunamadı." };
    }

    const { role } = JSON.parse(auth);

    // 2. PRIME (Master Admin) has global access
    if (role === "SOVEREIGN_PRIME") {
      return { can: true };
    }

    // 3. Role-Based Matrix
    const matrix: Record<string, { resources: string[]; actions: string[] }> = {
      AUDIT_OBSERVER: {
        resources: ["audit", "compliance", "lineage"],
        actions: ["list", "show"],
      },
      SECURITY_GUARDIAN: {
        resources: ["incidents", "audit", "compliance", "mesh"],
        actions: ["list", "show", "edit", "resolve"],
      },
      OPS_COMMANDER: {
        resources: ["workflows", "approvals", "fleet", "incidents"],
        actions: ["list", "show", "edit", "create", "approve", "execute"],
      },
    };

    const permissions = matrix[role];

    // If role not defined in matrix, deny by default
    if (!permissions) {
      return { can: false, reason: "Tanımsız rol." };
    }

    // Resource checking
    if (resource && !permissions.resources.includes(resource)) {
      // Allow dashboard anyway
      if (resource === "dashboard") return { can: true };
      
      return { can: false, reason: "Bu kaynağa erişim yetkiniz yok." };
    }

    // Action checking
    if (action && !permissions.actions.includes(action)) {
        // Prime can always do everything (handled above), others restricted
        return { can: false, reason: "Bu işlemi yapmaya yetkiniz yok." };
    }

    return { can: true };
  },
  options: {
    buttons: {
      enableAccessControl: true,
      hideIfUnauthorized: true,
    },
  },
};
