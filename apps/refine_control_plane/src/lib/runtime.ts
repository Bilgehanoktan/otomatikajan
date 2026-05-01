const DEFAULT_BACKEND_ORIGIN = "http://127.0.0.1:8000";

function isLocalDevProcess(): boolean {
  return process.env.NODE_ENV !== "production";
}

function getApiOverride(): string | null {
  const override = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!override) {
    return null;
  }

  // Local development should rely on the canonical 3100 -> /api/v1 path.
  // We keep the env override for production/static preview scenarios.
  if (isLocalDevProcess()) {
    return null;
  }

  return override;
}

function getExplicitBackendOrigin(): string | null {
  const override = process.env.NEXT_PUBLIC_BACKEND_ORIGIN?.trim();
  return override ? trimApiSuffix(override) : null;
}

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function trimApiSuffix(value: string): string {
  return trimTrailingSlash(value).replace(/\/api\/v1$/, "");
}

export function getApiBaseUrl(): string {
  const override = getApiOverride();
  if (override) {
    return trimTrailingSlash(override);
  }

  if (typeof window === "undefined") {
    return `${DEFAULT_BACKEND_ORIGIN}/api/v1`;
  }

  return "/api/v1";
}

export function getBackendOrigin(): string {
  const explicitOrigin = getExplicitBackendOrigin();
  if (explicitOrigin) {
    return explicitOrigin;
  }

  const override = getApiOverride();
  if (override) {
    return trimApiSuffix(override);
  }

  if (typeof window === "undefined") {
    return DEFAULT_BACKEND_ORIGIN;
  }

  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

export function buildWebSocketCandidates(path = "/ws/events"): string[] {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const backendOrigin = getBackendOrigin();
  const backendWs = `${backendOrigin.replace(/^http/, "ws")}${normalizedPath}`;

  if (typeof window === "undefined") {
    return [backendWs];
  }

  const sameOriginWs = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}${normalizedPath}`;
  const isLocalDevUi =
    window.location.port === "3100" &&
    ["localhost", "127.0.0.1"].includes(window.location.hostname);

  return Array.from(new Set(isLocalDevUi ? [backendWs, sameOriginWs] : [sameOriginWs, backendWs]));
}
