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

import { safeFetchJson } from "@/lib/api";

async function authFetch<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  return safeFetchJson<T>(url, init);
}

export async function fetchCurrentOperator(): Promise<SessionState> {
  try {
    const payload = await authFetch<AuthIdentity>("/auth/me/");
    if (payload) {
      if (typeof window !== "undefined" && payload.role) {
        window.localStorage.setItem("auth", JSON.stringify({ role: payload.role }));
      }
      return { kind: "authenticated", identity: payload };
    }
    return { kind: "error", status: 500, detail: "Kimlik yanıtı okunamadı." };
  } catch (error: any) {
    if (error?.status === 401) {
      return { kind: "unauthorized", status: 401 };
    }
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

  console.warn("[Auth] Oturum bulunamadı, otomatik giriş deneniyor...");

  try {
    const payload = await authFetch<{ access_token?: string | null }>("/auth/login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(DEV_OPERATOR),
    });

    if (payload?.access_token) {
        storeAccessToken(payload.access_token);
        console.info("[Auth] Otomatik giriş başarılı.");
        return fetchCurrentOperator();
    }
  } catch (error) {
    console.error("[Auth] Otomatik giriş başarısız:", error);
    return {
      kind: "network-error",
      error: error instanceof Error ? error : new Error("Otomatik giriş başarısız oldu."),
    };
  }

  return current;
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
