import { getApiBaseUrl } from "@/lib/runtime";

const DEV_OPERATOR = {
  email: "admin@sovereign.agi",
  password: "admin1234",
};

const TOKEN_KEY = "sqv_access_token";

export interface AuthIdentity {
  id: string;
  email: string;
  role?: string | null;
  roles?: string[] | null;
}

export type SessionState =
  | { kind: "authenticated"; identity: AuthIdentity }
  | { kind: "unauthorized"; status: number }
  | { kind: "network-error"; error: Error }
  | { kind: "error"; status: number; detail: string };

function storeAccessToken(token?: string | null) {
  if (!token || typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredAccessToken() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
}

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

async function readJsonSafely<T>(response: Response): Promise<T | null> {
  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

async function authFetch(path: string, init: RequestInit = {}): Promise<Response> {
  return fetch(`${getApiBaseUrl()}${path}`, {
    credentials: "include",
    ...init,
  });
}

export async function fetchCurrentOperator(): Promise<SessionState> {
  try {
    const response = await authFetch("/auth/me");
    if (response.ok) {
      const payload = await readJsonSafely<AuthIdentity>(response);
      if (payload) {
        if (typeof window !== "undefined" && payload.role) {
          window.localStorage.setItem("auth", JSON.stringify({ role: payload.role }));
        }
        return { kind: "authenticated", identity: payload };
      }
      return { kind: "error", status: response.status, detail: "Kimlik yanıtı okunamadı." };
    }

    if (response.status === 401) {
      return { kind: "unauthorized", status: response.status };
    }

    const body = await response.text();
    return {
      kind: "error",
      status: response.status,
      detail: body.slice(0, 300) || "Kimlik doğrulama başarısız oldu.",
    };
  } catch (error) {
    return {
      kind: "network-error",
      error: error instanceof Error ? error : new Error("Kimlik ağına ulaşılamadı."),
    };
  }
}

export async function ensureSession(): Promise<SessionState> {
  const current = await fetchCurrentOperator();
  if (current.kind === "authenticated") {
    return current;
  }

  if (current.kind !== "unauthorized" || process.env.NODE_ENV !== "development") {
    return current;
  }

  try {
    const loginResponse = await authFetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(DEV_OPERATOR),
    });

    if (!loginResponse.ok) {
      return { kind: "unauthorized", status: loginResponse.status };
    }

    const payload = await readJsonSafely<{ access_token?: string | null }>(loginResponse);
    storeAccessToken(payload?.access_token);
  } catch (error) {
    return {
      kind: "network-error",
      error: error instanceof Error ? error : new Error("Otomatik giriş başarısız oldu."),
    };
  }

  return fetchCurrentOperator();
}

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const cached = getStoredAccessToken();
  if (cached) {
    return { Authorization: `Bearer ${cached}` };
  }

  const session = await ensureSession();
  if (session.kind !== "authenticated") {
    return {};
  }

  const token = getStoredAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
