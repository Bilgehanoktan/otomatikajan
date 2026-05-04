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
  // CRITICAL: Always use the relative proxy path in the browser to avoid CORS.
  if (typeof window !== "undefined") {
    return "/api/v1";
  }

  // Server-side default
  return "http://127.0.0.1:8000/api/v1";
}

export function getBackendOrigin(): string {
  if (typeof window !== "undefined") {
    // Phase 32: Use the same origin as the UI in the browser. 
    // The Next.js proxy will handle routing to the real backend.
    return window.location.origin;
  }

  const explicitOrigin = getExplicitBackendOrigin();
  if (explicitOrigin) {
    return explicitOrigin;
  }

  return "http://127.0.0.1:8000";
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

  // If we're on port 3100, sameOriginWs is ws://localhost:3100 which won't work for WebSockets.
  // We MUST try ws://localhost:8000 (the real backend) as the primary candidate.
  const localhost8000Ws = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.hostname}:8000${normalizedPath}`;

  return Array.from(new Set(isLocalDevUi ? [localhost8000Ws, sameOriginWs] : [sameOriginWs, backendWs]));
}
