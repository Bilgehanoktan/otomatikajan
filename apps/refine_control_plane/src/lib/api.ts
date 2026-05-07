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

const normalizeApiErrorDetail = (status: number, rawDetail: string): string => {
    const detail = (rawDetail || "").trim();
    const lowered = detail.toLowerCase();

    if (status === 401) {
        return "Oturum suresi doldu veya kimlik dogrulama eksik. Lutfen tekrar giris yapin.";
    }

    if (status === 403) {
        if (lowered.includes("missing required permission") || lowered.includes("access denied")) {
            return "Bu islem icin gerekli yetkiniz bulunmuyor.";
        }
        return "Bu islem icin erisim izniniz yok.";
    }

    if (status === 404) {
        return "Istenen endpoint bu ortamda kullanilamiyor veya bulunamadi.";
    }

    return detail || `HTTP ${status}`;
};

/**
 * Basic Data Sealing (Demonstration level obfuscation)
 * Note: Since localStorage is not truly encrypted unless we use SubtleCrypto with a derived key,
 * this is officially termed as 'Sealed Offline Cache' rather than 'Encrypted' to maintain accurate security terminology.
 */
const SQV_SECRET = "BASE-10.2-PROTECTED";
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
                console.warn(`[Auth] Yenileme başarısız: ${res.status}`);
                return false;
            }
            
            const data = await res.json().catch(() => null);
            const token = data?.access_token;
            if (token && typeof window !== "undefined") {
                localStorage.setItem("sqv_access_token", token);
                return true;
            }
            return false;
        } catch (err) {
            console.error("[Auth] Yenileme hatası:", err);
            return false;
        } finally {
            refreshInFlight = null;
        }
    })();
    return refreshInFlight;
}

export async function safeFetchJson<T = unknown>(url: string, options: SafeFetchOptions = {}): Promise<T> {
    const { retries = 2, useOfflineFallback = true, skipAuthRefresh = false, ...init } = options;
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

            const fetchInit: RequestInit = { 
                ...init, 
                credentials: "include" as RequestCredentials,
                signal: controller.signal
            };
            
            let res: Response;
            try {
                // SIF-01 Enhancement: Inject Bearer Token if available in localStorage
                if (typeof window !== "undefined") {
                    const token = localStorage.getItem("sqv_access_token");
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

                res = await fetch(url, fetchInit);
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
                    }
                }

                let detail = "Bilinmeyen sunucu hatası.";
                try {
                    const jsonErr = JSON.parse(raw);
                    detail = jsonErr.detail || jsonErr.msg || raw;
                } catch { 
                    detail = raw ? raw.slice(0, 200) : `HTTP ${res.status}`; 
                }
                throw new ApiResponseError(res.status, normalizeApiErrorDetail(res.status, detail));
            }

            if (!contentType.includes("application/json")) {
                throw new Error(`Geçersiz Yanıt Formatı: "${contentType}". Raw: ${raw.slice(0, 100)}...`);
            }

            const data = JSON.parse(raw) as T;

            // 2. Başarılı veriyi Cache'e mühürle (Sealed Offline Cache)
            if (useOfflineFallback && typeof window !== 'undefined') {
                try {
                    const payload = JSON.stringify({
                        timestamp: Date.now(),
                        data: data
                    });
                    localStorage.setItem(cache_key, seal(payload));
                } catch {
                    // Çerez veya storage sınırı hatalarını sessizce yut.
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

    // Tüm ağ denemeleri çöktü.
    console.error(`[Mesh API] İletişim tamamen çöktü: ${url}. Hata: ${lastError?.message}`);

    // 3. Degraded Mode: Çevrimdışı Geri Dönüş (Sealed Offline Cache)
    if (useOfflineFallback && typeof window !== 'undefined') {
        try {
            const cipher = localStorage.getItem(cache_key);
            if (cipher) {
                const raw_payload = unseal(cipher);
                if (!raw_payload) throw new Error("Mühürlü veri bozulmuş.");

                const parsed = JSON.parse(raw_payload);
                const ageSeconds = Math.floor((Date.now() - parsed.timestamp) / 1000);

                console.info(`[Degraded Mode] Aktif API reddedildi. Son başarılı Gölge-Veri (T-${ageSeconds}s) sunuluyor.`);

                // Stale veri görünürlüğü için metadata enjeksiyonu
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
            console.error("[Degraded Mode] Yerel cache okunamadı veya mühür bozuk.", cacheErr);
        }
    }

    // Eğer geçmiş veri de yoksa (ilk açılışta çöktüyse) çaresizce fırlat
    throw lastError || new Error("Bilinmeyen Ağ Hatası");
}

/**
 * Standard fetch adapter that wraps safeFetchJson for standard data-providers (Refine).
 */
export async function safeFetchAdapter(url: string, options: RequestInit = {}): Promise<Response> {
    try {
        const data = await safeFetchJson(url, options as SafeFetchOptions);

        // Return a polyfilled Response object that Refine expectations
        return new Response(JSON.stringify(data), {
            status: 200,
            statusText: "OK",
            headers: {
                "Content-Type": "application/json",
                // Pass back the stale flag if exists so the data-provider doesn't block it
                "X-Sqv-Stale": data?.__sqv_meta?.is_stale ? "true" : "false"
            }
        });
    } catch (err: unknown) {
        if (err instanceof ApiResponseError) {
            return new Response(JSON.stringify({
                error: "api_error",
                detail: err.detail
            }), {
                status: err.status,
                statusText: err.status === 401 ? "Unauthorized" : err.status === 403 ? "Forbidden" : "API Error",
                headers: { "Content-Type": "application/json" }
            });
        }
        // If everything fails, return a 500 JSON response instead of a raw crash
        return new Response(JSON.stringify({
            error: "internal_server_error",
            detail: err.message
        }), {
            status: 500,
            statusText: "Internal Server Error",
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
