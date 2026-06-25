import { getApiBaseUrl } from "@/lib/runtime";
import { safeFetchJson } from "@/lib/api";

const TOKEN_KEY = "sqv_access_token";
const DEV_AUTO_LOGIN_ENABLED = process.env.NODE_ENV === "development" && process.env.NEXT_PUBLIC_ENABLE_DEV_AUTO_LOGIN === "true";
const DEV_OPERATOR_EMAIL = process.env.NODE_ENV === "development" ? (process.env.NEXT_PUBLIC_DEV_OPERATOR_EMAIL?.trim() || "") : "";
const DEV_OPERATOR_PASSWORD = process.env.NODE_ENV === "development" ? (process.env.NEXT_PUBLIC_DEV_OPERATOR_PASSWORD?.trim() || "") : "";

type AuthFetchOptions = RequestInit & {
  retries?: number;
  skipAuthRefresh?: boolean;
  suppressConsoleError?: boolean;
};

import { 
  AuthIdentity, 
  SessionState, 
  LoginParams, 
  RegisterParams 
} from "@/types/auth";

function storeAccessToken(token?: string | null) {
  if (!token || typeof window === "undefined") {
    return;
  }
  window.sessionStorage.setItem(TOKEN_KEY, token);
  window.localStorage.removeItem(TOKEN_KEY);
}

export function clearStoredAccessToken() {
  if (typeof window === "undefined") {
    return;
  }
  window.sessionStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(TOKEN_KEY);
}

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.sessionStorage.getItem(TOKEN_KEY) || window.localStorage.getItem(TOKEN_KEY);
}

function getDevOperatorCredentials(): { email: string; password: string } | null {
  if (!DEV_AUTO_LOGIN_ENABLED || !DEV_OPERATOR_EMAIL || !DEV_OPERATOR_PASSWORD) {
    return null;
  }
  return {
    email: DEV_OPERATOR_EMAIL,
    password: DEV_OPERATOR_PASSWORD,
  };
}

/**
 * Standardized fetch wrapper for auth-related operations.
 */
async function authFetch<T = unknown>(path: string, init: AuthFetchOptions = {}): Promise<T> {
  const url = `${getApiBaseUrl()}${path}`;
  return safeFetchJson<T>(url, init);
}

export async function fetchCurrentOperator(): Promise<SessionState> {
  try {
    const payload = await authFetch<AuthIdentity>("/auth/me", {
      retries: 0,
      skipAuthRefresh: true,
      suppressConsoleError: true,
    });
    if (payload && (payload.id || payload.email)) {
      if (typeof window !== "undefined") {
        if (payload.role) window.localStorage.setItem("auth", JSON.stringify({ role: payload.role }));
        if (payload.email) window.localStorage.setItem("sqv_operator_email", payload.email);
        
        // Persist to global window for legacy component access
        (window as { __SQV_IDENTITY__?: AuthIdentity | null } & Window).__SQV_IDENTITY__ = payload;
      }
      return { kind: "authenticated", identity: payload };
    }
    return { kind: "error", status: 500, detail: "Sunucudan geçersiz kimlik verisi alındı." };
  } catch (error: unknown) {
    if (error && typeof error === "object" && "status" in error && error.status === 401) {
      return { kind: "unauthorized", status: 401 };
    }
    console.warn("[Auth] fetchCurrentOperator hatası:", error);
    return {
      kind: "network-error",
      error: error instanceof Error ? error : new Error("Kimlik ağına ulaşılamadı."),
    };
  }
}

let lastAutoLoginTime = 0;
const AUTO_LOGIN_COOLDOWN = 10000; // 10 seconds
let autoLoginInFlight: Promise<SessionState> | null = null;

export async function ensureSession(): Promise<SessionState> {
  const current = await fetchCurrentOperator();
  if (current.kind === "authenticated") {
    return current;
  }

  if (current.kind !== "unauthorized" || process.env.NODE_ENV !== "development") {
    return current;
  }

  const devCredentials = getDevOperatorCredentials();
  if (!devCredentials) {
    return current;
  }

  if (autoLoginInFlight) {
    return autoLoginInFlight;
  }

  // Prevent rapid-fire automatic login attempts that cause loops.
  const now = Date.now();
  if (now - lastAutoLoginTime < AUTO_LOGIN_COOLDOWN) {
    const cached = getStoredAccessToken();
    if (cached) {
      return fetchCurrentOperator();
    }
    console.warn("[Auth] Otomatik giris beklemede (cooldown active).");
    return current;
  }
  lastAutoLoginTime = now;

  console.warn("[Auth] Oturum bulunamadi, otomatik giris deneniyor...");

  autoLoginInFlight = (async () => {
    const payload = await authFetch<{ access_token?: string | null }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(devCredentials),
    });

    if (payload?.access_token) {
      storeAccessToken(payload.access_token);
      console.info("[Auth] Otomatik giris basarili.");
      return fetchCurrentOperator();
    }

    return current;
  })();

  try {
    return await autoLoginInFlight;
  } catch (error) {
    console.error("[Auth] Otomatik giris basarisiz:", error);
    return {
      kind: "network-error",
      error: error instanceof Error ? error : new Error("Otomatik giris basarisiz oldu."),
    };
  } finally {
    autoLoginInFlight = null;
  }
}
export interface AuthActionResult {
  success: boolean;
  redirectTo?: string;
  error?: Error;
}

export async function performLogin(params: LoginParams): Promise<AuthActionResult> {
  try {
    const payload = await authFetch<{ access_token?: string | null }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    if (payload?.access_token) {
      storeAccessToken(payload.access_token);
      if (typeof window !== "undefined" && typeof params.email === "string") {
        window.localStorage.setItem("sqv_operator_email", params.email);
      }
      return { success: true, redirectTo: "/" };
    }
    
    return { 
      success: false, 
      error: new Error("Giriş başarısız. Lütfen bilgilerinizi kontrol edin.")
    };
  } catch (error: unknown) {
    console.error("[Auth] Giriş hatası:", error);
    return { 
      success: false, 
      error: error instanceof Error ? error : new Error("Sunucuya bağlanılamadı.")
    };
  }
}

export async function performRegister(params: RegisterParams): Promise<{ success: boolean; error?: Error }> {
  try {
    const payload = await authFetch<AuthIdentity>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    if (payload && (payload.id || payload.email)) {
      return { success: true };
    }
    
    return { 
      success: false, 
      error: new Error("Kayıt işlemi başarısız oldu. Sunucu geçerli bir yanıt dönmedi.")
    };
  } catch (error: unknown) {
    console.error("[Auth] Kayıt hatası:", error);
    return { 
      success: false, 
      error: error instanceof Error ? error : new Error("Sunucuya bağlanılamadı.")
    };
  }
}

export async function performLogout(): Promise<void> {
    clearStoredAccessToken();
    if (typeof window !== "undefined") {
        (window as { __SQV_IDENTITY__?: AuthIdentity | null } & Window).__SQV_IDENTITY__ = null;
        window.localStorage.removeItem("auth");
        window.localStorage.removeItem("sqv_operator_email");
    }
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
