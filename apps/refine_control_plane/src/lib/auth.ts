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
    if (payload && (payload.id || payload.email)) {
      if (typeof window !== "undefined") {
        if (payload.role) window.localStorage.setItem("auth", JSON.stringify({ role: payload.role }));
        if (payload.email) window.localStorage.setItem("sqv_operator_email", payload.email);
      }
      return { kind: "authenticated", identity: payload };
    }
    return { kind: "error", status: 500, detail: "Sunucudan geçersiz kimlik verisi alındı." };
  } catch (error: any) {
    console.warn("[Auth] fetchCurrentOperator hatası:", error);
    if (error?.status === 401) {
      return { kind: "unauthorized", status: 401 };
    }
    return {
      kind: "network-error",
      error: error instanceof Error ? error : new Error(error?.message || "Kimlik ağına ulaşılamadı."),
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

export async function performLogin(params: any): Promise<{ success: boolean; redirectTo?: string; error?: any }> {
  console.log("[Auth] Giriş denemesi:", params.email);
  try {
    const payload = await authFetch<{ access_token?: string | null }>("/auth/login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    console.log("[Auth] Giriş yanıtı:", payload);

    if (payload?.access_token) {
      storeAccessToken(payload.access_token);
      if (typeof window !== "undefined") {
        window.localStorage.setItem("sqv_operator_email", params.email);
      }
      return { success: true, redirectTo: "/" };
    }
    
    return { 
      success: false, 
      error: new Error("Giriş başarısız. Lütfen bilgilerinizi kontrol edin.")
    };
  } catch (error: any) {
    console.error("[Auth] Giriş hatası:", error);
    return { 
      success: false, 
      error: error instanceof Error ? error : new Error(error?.message || "Sunucuya bağlanılamadı.")
    };
  }
}

export async function performRegister(params: any): Promise<{ success: boolean; error?: any }> {
  console.log("[Auth] Kayıt denemesi:", params.email);
  try {
    const payload = await authFetch<any>("/auth/register/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });

    console.log("[Auth] Kayıt yanıtı:", payload);

    // Backend returns the user object on success
    if (payload && (payload.id || payload.email)) {
      return { success: true };
    }
    
    return { 
      success: false, 
      error: new Error("Kayıt işlemi başarısız oldu. Sunucu geçerli bir yanıt dönmedi.")
    };
  } catch (error: any) {
    console.error("[Auth] Kayıt hatası:", error);
    return { 
      success: false, 
      error: error instanceof Error ? error : new Error(error?.message || "Sunucuya bağlanılamadı.")
    };
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
