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
            
            const res = await fetch(url, init);
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
                if (parsed.data && typeof parsed.data === 'object' && !Array.isArray(parsed.data)) {
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
    
    // Eğer geçmiş veri de yoksa (İlk açılışta çöktüyse) çaresizce fırlat,
    // ancak Exception handler (ör. React Error Boundary) onu seçecektir.
    throw lastError || new Error("Bilinmeyen Ağ Hatası");
}
