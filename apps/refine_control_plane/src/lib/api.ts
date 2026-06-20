/**
 * Standardized API client utility for the Sovereign AGI Control Plane.
 * Prevents "Unexpected token I" errors by verifying response content-type
 * and providing detailed error diagnostics.
 */
import { getApiBaseUrl } from "@/lib/runtime";

interface SafeFetchOptions extends RequestInit {
    retries?: number;
    useOfflineFallback?: boolean;
    skipAuthRefresh?: boolean;
    suppressConsoleError?: boolean;
}

export class ApiResponseError extends Error {
    status: number;
    detail: string;

    constructor(status: number, detail: string) {
        super(`API ERROR [${status}]: ${detail}`);
        this.name = "ApiResponseError";
        this.status = status;
        this.detail = detail;
    }
}

const coerceApiErrorDetail = (rawDetail: unknown): string => {
    if (typeof rawDetail === "string") {
        return rawDetail;
    }

    if (rawDetail == null) {
        return "";
    }

    if (Array.isArray(rawDetail)) {
        return rawDetail
            .map((item) => coerceApiErrorDetail(item))
            .filter(Boolean)
            .join(" | ");
    }

    if (typeof rawDetail === "object") {
        const record = rawDetail as Record<string, unknown>;
        for (const key of ["detail", "message", "msg", "error", "reason", "title"]) {
            const nested = coerceApiErrorDetail(record[key]);
            if (nested) {
                return nested;
            }
        }

        try {
            return JSON.stringify(rawDetail);
        } catch {
            return String(rawDetail);
        }
    }

    return String(rawDetail);
};

const normalizeApiErrorDetail = (status: number, rawDetail: unknown): string => {
    const detail = coerceApiErrorDetail(rawDetail).trim();
    const lowered = detail.toLowerCase();

    if (status === 401) {
        return "Oturum suresi doldu veya kimlik dogrulama eksik. Lutfen tekrar giris yapin.";
    }

    if (status === 403) {
        if (lowered.includes("missing required permission") || lowered.includes("access denied")) {
            return `Erisim Engellendi: ${detail}. Mevcut rolunuz bu aksiyonu desteklemiyor olabilir.`;
        }
        return "Bu islem icin yeterli yetkiniz yok. Lutfen OPERATOR yetkisine sahip bir hesapla giris yapin veya oturumunuzu yenileyin.";
    }

    if (status === 404) {
        if (detail && detail.toLowerCase() !== "not found") return detail;
        return "Istenen endpoint bu ortamda kullanilamiyor veya bulunamadi.";
    }

    return detail || `HTTP ${status}`;
};

const normalizeApiRequestUrl = (url: string): string => {
    const [pathWithOrigin, query = ""] = url.split("?", 2);
    const normalizedPath = pathWithOrigin.replace(/(\/api\/v1\/.+)\/$/, "$1");
    return query ? `${normalizedPath}?${query}` : normalizedPath;
};

/**
 * Basic Data Sealing (Demonstration level obfuscation)
 * Note: Since localStorage is not truly encrypted unless we use SubtleCrypto with a derived key,
 * this is officially termed as 'Sealed Offline Cache' rather than 'Encrypted' to maintain accurate security terminology.
 */
const SQV_SECRET = "BASE-10.2-PROTECTED";
const TOKEN_KEY = "sqv_access_token";
const DEV_AUTO_LOGIN_ENABLED = process.env.NEXT_PUBLIC_ENABLE_DEV_AUTO_LOGIN === "true";
const DEV_OPERATOR_EMAIL = process.env.NEXT_PUBLIC_DEV_OPERATOR_EMAIL?.trim() || "";
const DEV_OPERATOR_PASSWORD = process.env.NEXT_PUBLIC_DEV_OPERATOR_PASSWORD?.trim() || "";

const readAccessToken = (): string | null => {
    if (typeof window === "undefined") return null;
    return window.sessionStorage.getItem(TOKEN_KEY) || window.localStorage.getItem(TOKEN_KEY);
};

const storeAccessToken = (token: string): void => {
    if (typeof window === "undefined") return;
    window.sessionStorage.setItem(TOKEN_KEY, token);
    window.localStorage.removeItem(TOKEN_KEY);
};
const seal = (data: string): string => {
    return btoa(data.split('').map((c, i) =>
        String.fromCharCode(c.charCodeAt(0) ^ SQV_SECRET.charCodeAt(i % SQV_SECRET.length))
    ).join(''));
};

const unseal = (cipher: string): string => {
    try {
        const decoded = atob(cipher);
        return decoded.split('').map((c, i) =>
            String.fromCharCode(c.charCodeAt(0) ^ SQV_SECRET.charCodeAt(i % SQV_SECRET.length))
        ).join('');
    } catch { return ""; }
};

let refreshInFlight: Promise<boolean> | null = null;

async function tryDevAutoLogin(): Promise<boolean> {
    if (
        typeof window === "undefined" ||
        process.env.NODE_ENV !== "development" ||
        !DEV_AUTO_LOGIN_ENABLED ||
        !DEV_OPERATOR_EMAIL ||
        !DEV_OPERATOR_PASSWORD
    ) {
        return false;
    }

    try {
        const loginUrl = `${getApiBaseUrl()}/auth/login`;
        const res = await fetch(loginUrl, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: DEV_OPERATOR_EMAIL,
                password: DEV_OPERATOR_PASSWORD,
            }),
        });

        if (!res.ok) {
            console.warn(`[Auth] Gelistirme otomatik girisi basarisiz: ${res.status}`);
            return false;
        }

        const data = await res.json().catch(() => null);
        const token = data?.access_token;
        if (token) {
            storeAccessToken(token);
            console.info("[Auth] Gelistirme otomatik girisi ile oturum yenilendi.");
            return true;
        }

        return false;
    } catch (err) {
        console.error("[Auth] Gelistirme otomatik giris hatasi:", err);
        return false;
    }
}

async function tryRefreshSession(): Promise<boolean> {
    if (refreshInFlight) return refreshInFlight;
    refreshInFlight = (async () => {
        try {
            const refreshUrl = `${getApiBaseUrl()}/auth/refresh`;
            const res = await fetch(refreshUrl, {
                method: "POST",
                credentials: "include",
                headers: { "Content-Type": "application/json" },
                body: "{}",
            });

            if (!res.ok) {
                console.warn(`[Auth] Yenileme baÅŸarÄ±sÄ±z: ${res.status}`);
                return await tryDevAutoLogin();
            }
            
            const data = await res.json().catch(() => null);
            const token = data?.access_token;
            if (token && typeof window !== "undefined") {
                storeAccessToken(token);
                return true;
            }
            return await tryDevAutoLogin();
        } catch (err) {
            console.error("[Auth] Yenileme hatasÄ±:", err);
            return await tryDevAutoLogin();
        } finally {
            refreshInFlight = null;
        }
    })();
    return refreshInFlight;
}

export async function safeFetchJson<T = any>(url: string, options: SafeFetchOptions = {}): Promise<T> {
    const { retries = 2, useOfflineFallback = true, skipAuthRefresh = false, suppressConsoleError = false, ...init } = options;
    const cache_key = `sqv_cache_${btoa(url).replace(/=/g, "").slice(0, 32)}`;
    let lastError: Error | null = null;

    // 1. Otonom Tekrar Deneme (Auto-Retry & Jitter)
    for (let attempt = 0; attempt <= retries; attempt++) {
        try {
            if (attempt > 0) {
                console.warn(`[Mesh API] Tekrar deneniyor... (${attempt}/${retries}) -> URL: ${url}`);
                await new Promise(res => setTimeout(res, Math.min(1500 * Math.pow(2, attempt - 1), 8000)));
            }

            // Phase 32: Force include cookies for Auth
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout (increased for SIF-02 reliability)

            // Phase 32: Auto-prefix relative URLs with /api/v1 if needed
            let finalUrl = url;
            if (typeof window !== "undefined" && !url.startsWith("http") && !url.startsWith("/api/")) {
                const base = getApiBaseUrl(); // "/api/v1"
                finalUrl = `${base}${url.startsWith("/") ? "" : "/"}${url}`;
            }

            finalUrl = normalizeApiRequestUrl(finalUrl);

            const fetchInit: RequestInit = { 
                ...init, 
                credentials: "include" as RequestCredentials,
                signal: controller.signal,
                cache: "no-store"
            };
            
            let res: Response;
            try {
                // SIF-01 Enhancement: Inject Bearer Token if available in localStorage
                if (typeof window !== "undefined") {
                    const token = readAccessToken();
                    const headers = new Headers(fetchInit.headers || {});
                    
                    if (token && !headers.has("Authorization")) {
                        headers.set("Authorization", `Bearer ${token}`);
                    }

                    // CRITICAL: Ensure Content-Type is application/json for POST/PUT/PATCH requests with bodies
                    if (fetchInit.body && !headers.has("Content-Type")) {
                        headers.set("Content-Type", "application/json");
                    }

                    fetchInit.headers = headers;
                }

                res = await fetch(finalUrl, fetchInit);
            } finally {
                clearTimeout(timeoutId);
            }

            const contentType = res.headers.get("content-type") || "";
            const raw = await res.text();

            if (!res.ok) {
                if (
                    res.status === 401 &&
                    !skipAuthRefresh &&
                    typeof window !== "undefined" &&
                    !url.includes("/auth/login") &&
                    !url.includes("/auth/refresh")
                ) {
                    console.info(`[Auth] 401 Tespit Edildi: ${url}. Yenileniyor...`);
                    const refreshed = await tryRefreshSession();
                    if (refreshed) {
                        return safeFetchJson<T>(url, { ...options, skipAuthRefresh: true });
                    } else if (!url.includes("/auth/me") && !window.location.pathname.startsWith("/login")) {
                        console.warn("[Auth] Session expired and refresh failed. Redirecting to /login.");
                        storeAccessToken("");
                        window.location.href = "/login?expired=true";
                        return new Promise(() => {}); // prevent further execution by returning a pending promise
                    }
                }

                let detail = "Bilinmeyen sunucu hatasÃ„Â±.";
                try {
                    const jsonErr = JSON.parse(raw);
                    detail = jsonErr.detail ?? jsonErr.msg ?? jsonErr.error ?? jsonErr.message ?? raw;
                } catch { 
                    detail = raw ? raw.slice(0, 200) : `HTTP ${res.status}`; 
                }
                throw new ApiResponseError(res.status, normalizeApiErrorDetail(res.status, detail));
            }

            if (!contentType.includes("application/json")) {
                throw new Error(`GeÃƒÂ§ersiz YanÃ„Â±t FormatÃ„Â±: "${contentType}". Raw: ${raw.slice(0, 100)}...`);
            }

            const data = JSON.parse(raw) as T;

            // 2. BaÃ…Å¸arÃ„Â±lÃ„Â± veriyi Cache'e mÃƒÂ¼hÃƒÂ¼rle (Sealed Offline Cache)
            if (useOfflineFallback && typeof window !== 'undefined') {
                try {
                    const payload = JSON.stringify({
                        timestamp: Date.now(),
                        data: data
                    });
                    window.localStorage.setItem(cache_key, seal(payload));
                } catch {
                    // Ãƒâ€¡erez veya storage sÃ„Â±nÃ„Â±rÃ„Â± hatalarÃ„Â±nÃ„Â± sessizce yut.
                }
            }

            return data;

        } catch (err: unknown) {
            lastError = err instanceof Error ? err : new Error(String(err));
            if (err instanceof ApiResponseError && (err.status === 401 || err.status === 403)) {
                break;
            }
        }
    }

    if (lastError instanceof ApiResponseError && (lastError.status === 401 || lastError.status === 403)) {
        throw lastError;
    }

    // TÃƒÂ¼m aÃ„Å¸ denemeleri ÃƒÂ§ÃƒÂ¶ktÃƒÂ¼.
    if (!suppressConsoleError) {
        console.error(`[Mesh API] Ã„Â°letiÃ…Å¸im tamamen ÃƒÂ§ÃƒÂ¶ktÃƒÂ¼: ${url}. Hata: ${lastError?.message}`);
    }

    // 3. Degraded Mode: Ãƒâ€¡evrimdÃ„Â±Ã…Å¸Ã„Â± Geri DÃƒÂ¶nÃƒÂ¼Ã…Å¸ (Sealed Offline Cache)
    if (useOfflineFallback && typeof window !== 'undefined') {
        try {
            const cipher = window.localStorage.getItem(cache_key);
            if (cipher) {
                const raw_payload = unseal(cipher);
                if (!raw_payload) throw new Error("MÃƒÂ¼hÃƒÂ¼rlÃƒÂ¼ veri bozulmuÃ…Å¸.");

                const parsed = JSON.parse(raw_payload);
                const ageSeconds = Math.floor((Date.now() - parsed.timestamp) / 1000);

                console.info(`[Degraded Mode] Aktif API reddedildi. Son baÃ…Å¸arÃ„Â±lÃ„Â± GÃƒÂ¶lge-Veri (T-${ageSeconds}s) sunuluyor.`);

                // Stale veri gÃƒÂ¶rÃƒÂ¼nÃƒÂ¼rlÃƒÂ¼Ã„Å¸ÃƒÂ¼ iÃƒÂ§in metadata enjeksiyonu
                if (parsed.data && typeof parsed.data === "object") {
                    (parsed.data as Record<string, unknown>)["__sqv_meta"] = {
                        is_stale: true,
                        age_seconds: ageSeconds,
                        source: "sealed_local_cache",
                        endpoint: url
                    };
                }

                return parsed.data as T;
            }
        } catch (cacheErr) {
            console.error("[Degraded Mode] Yerel cache okunamadÃ„Â± veya mÃƒÂ¼hÃƒÂ¼r bozuk.", cacheErr);
        }
    }

    // EÃ„Å¸er geÃƒÂ§miÃ…Å¸ veri de yoksa (ilk aÃƒÂ§Ã„Â±lÃ„Â±Ã…Å¸ta ÃƒÂ§ÃƒÂ¶ktÃƒÂ¼yse) ÃƒÂ§aresizce fÃ„Â±rlat
    throw lastError || new Error("Bilinmeyen AÃ„Å¸ HatasÃ„Â±");
}

/**
 * Standard fetch adapter that wraps safeFetchJson for standard data-providers (Refine).
 */
export async function safeFetchAdapter(url: string, options: SafeFetchOptions = {}): Promise<Response> {
    try {
        const { retries = 2, useOfflineFallback = true, skipAuthRefresh = false, ...init } = options;
        
        // Phase 12.1: We need the actual Response object to extract headers for Refine (x-total-count)
        let finalUrl = url;
        if (typeof window !== "undefined" && !url.startsWith("http") && !url.startsWith("/api/")) {
            const base = getApiBaseUrl();
            finalUrl = `${base}${url.startsWith("/") ? "" : "/"}${url}`;
        }
        finalUrl = normalizeApiRequestUrl(finalUrl);

        const fetchInit: RequestInit = { 
            ...init, 
            credentials: "include" as RequestCredentials,
            cache: "no-store"
        };
        
        if (typeof window !== "undefined") {
            const token = readAccessToken();
            const headers = new Headers(fetchInit.headers || {});
            if (token && !headers.has("Authorization")) {
                headers.set("Authorization", `Bearer ${token}`);
            }
            if (fetchInit.body && !headers.has("Content-Type")) {
                headers.set("Content-Type", "application/json");
            }
            fetchInit.headers = headers;
        }

        const res = await fetch(finalUrl, fetchInit);
        
        if (!res.ok) {
            if (res.status === 401 && !skipAuthRefresh && typeof window !== "undefined") {
                const refreshed = await tryRefreshSession();
                if (refreshed) {
                    return safeFetchAdapter(url, { ...options, skipAuthRefresh: true });
                } else if (!url.includes("/auth/me") && !window.location.pathname.startsWith("/login")) {
                    console.warn("[Auth] Session expired and refresh failed in safeFetchAdapter. Redirecting to /login.");
                    storeAccessToken("");
                    window.location.href = "/login?expired=true";
                    return new Promise(() => {}); // prevent further execution by returning a pending promise
                }
            }
            const raw = await res.text();
            let detail = raw;
            try {
                const jsonErr = JSON.parse(raw);
                detail = jsonErr.detail ?? jsonErr.msg ?? jsonErr.error ?? jsonErr.message ?? raw;
            } catch { }
            throw new ApiResponseError(res.status, normalizeApiErrorDetail(res.status, detail));
        }

        return res; // Return the actual response so headers are preserved
    } catch (err: unknown) {
        const status = err instanceof ApiResponseError ? err.status : 500;
        const detail = err instanceof Error ? err.message : String(err);
        
        return new Response(JSON.stringify({
            error: status === 500 ? "internal_server_error" : "api_error",
            detail: detail
        }), {
            status: status,
            headers: { "Content-Type": "application/json" }
        });
    }
}

export interface HttpClientConfig extends SafeFetchOptions {
    url?: string;
}

export interface HttpClientResponse<T> {
    data: T;
    status: number;
    statusText: string;
    headers: Record<string, string>;
    config: HttpClientConfig;
}

export const safeHttpClient = {
    get: async <T = unknown>(url: string, config: HttpClientConfig = {}): Promise<HttpClientResponse<T>> => {
        const data = await safeFetchJson<T>(url, { ...config, method: "GET" });
        return { data, status: 200, statusText: "OK", headers: {}, config };
    },
    post: async <T = unknown>(url: string, body: unknown, config: HttpClientConfig = {}): Promise<HttpClientResponse<T>> => {
        const responseData = await safeFetchJson<T>(url, { ...config, method: "POST", body: JSON.stringify(body) });
        return { data: responseData, status: 200, statusText: "OK", headers: {}, config };
    },
    put: async <T = unknown>(url: string, body: unknown, config: HttpClientConfig = {}): Promise<HttpClientResponse<T>> => {
        const responseData = await safeFetchJson<T>(url, { ...config, method: "PUT", body: JSON.stringify(body) });
        return { data: responseData, status: 200, statusText: "OK", headers: {}, config };
    },
    patch: async <T = unknown>(url: string, body: unknown, config: HttpClientConfig = {}): Promise<HttpClientResponse<T>> => {
        const responseData = await safeFetchJson<T>(url, { ...config, method: "PATCH", body: JSON.stringify(body) });
        return { data: responseData, status: 200, statusText: "OK", headers: {}, config };
    },
    delete: async <T = unknown>(url: string, config: HttpClientConfig = {}): Promise<HttpClientResponse<T>> => {
        const data = await safeFetchJson<T>(url, { ...config, method: "DELETE" });
        return { data, status: 200, statusText: "OK", headers: {}, config };
    },
    request: async <T = unknown>(config: HttpClientConfig & { url: string }): Promise<HttpClientResponse<T>> => {
        const data = await safeFetchJson<T>(config.url, config);
        return { data, status: 200, statusText: "OK", headers: {}, config };
    },
};

/**
 * Validates the shape of Observability responses to prevent runtime UI crashes.
 */
export const validateObservabilityResponse = (type: "alerts" | "drifts" | "metrics", data: unknown) => {
    if (!data) return false;
    if (type === "alerts" || type === "drifts") {
        return Array.isArray(data);
    }
    if (type === "metrics") {
        return typeof data === "object" && !Array.isArray(data);
    }
    return true;
};
