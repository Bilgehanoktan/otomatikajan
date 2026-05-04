import dataProvider from "@refinedev/simple-rest";
import { getApiBaseUrl } from "./runtime";
import { safeHttpClient } from "./api";

/**
 * Standardized Data Provider for the Sovereign AGI Control Plane.
 * Uses safeHttpClient for auto-retries, offline fallbacks, and JWT injection.
 */
export const activeDataProvider = dataProvider(getApiBaseUrl(), safeHttpClient as any);
