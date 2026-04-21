/**
 * Standardized API client utility for the Sovereign AGI Control Plane.
 * Prevents "Unexpected token I" errors by verifying response content-type
 * and providing detailed error diagnostics.
 */

interface SafeFetchOptions extends RequestInit {
    retries?: number;
    useOfflineFallback?: boolean;
}

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

export async function safeFetchJson<T = any>(url: string, options: SafeFetchOptions = {}): Promise<T> {
    const { retries = 2, useOfflineFallback = true, ...init } = options;
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
            const fetchInit = { ...init, credentials: "include" as RequestCredentials };
            const res = await fetch(url, fetchInit);
            const contentType = res.headers.get("content-type") || "";
            const raw = await res.text();
            
            if (!res.ok) {
                let detail = raw;
                try {
                    const jsonErr = JSON.parse(raw);
                    detail = jsonErr.detail || jsonErr.msg || raw;
                } catch { detail = raw.slice(0, 500); }
                throw new Error(`API ERROR [${res.status}]: ${detail}`);
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
                } catch (e) { /* Çerez Sınırı hatasını göz ardı et */ }
            }
            
            return data;
            
        } catch (err: any) {
            lastError = err;
        }
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
                
                console.info(`[Degraded Mode] ⚠️ Aktif API reddedildi. Son başarılı Gölge-Veri (T-${ageSeconds}s) sunuluyor.`);
                
                // Stale veri görünürlüğü için metadata enjeksiyonu
                if (parsed.data && typeof parsed.data === 'object') {
                    (parsed.data as any)["__sqv_meta"] = {
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
    
    // Eğer geçmiş veri de yoksa (İlk açılışta çöktüyse) çaresizce fırlat
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
    } catch (err: any) {
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

/**
 * Axios-compatible wrapper for safeFetchJson.
 * The Refine simple-rest provider expects an object with method functions (get, post, etc.)
 * and each method must return an object with a 'data' property (AxiosResponse).
 */
export const safeHttpClient = {
    get: async (url: string, config: any = {}) => {
        const data = await safeFetchJson(url, { ...config, method: "GET" });
        return { data, status: 200, statusText: "OK", headers: {}, config };
    },
    post: async (url: string, data: any, config: any = {}) => {
        const responseData = await safeFetchJson(url, { ...config, method: "POST", body: JSON.stringify(data) });
        return { data: responseData, status: 200, statusText: "OK", headers: {}, config };
    },
    put: async (url: string, data: any, config: any = {}) => {
        const responseData = await safeFetchJson(url, { ...config, method: "PUT", body: JSON.stringify(data) });
        return { data: responseData, status: 200, statusText: "OK", headers: {}, config };
    },
    patch: async (url: string, data: any, config: any = {}) => {
        const responseData = await safeFetchJson(url, { ...config, method: "PATCH", body: JSON.stringify(data) });
        return { data: responseData, status: 200, statusText: "OK", headers: {}, config };
    },
    delete: async (url: string, config: any = {}) => {
        const data = await safeFetchJson(url, { ...config, method: "DELETE" });
        return { data, status: 200, statusText: "OK", headers: {}, config };
    },
    request: async (config: any = {}) => {
        const data = await safeFetchJson(config.url, config);
        return { data, status: 200, statusText: "OK", headers: {}, config };
    },
};
