import os
import re
import sys

# Dosya yolları
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIDEBAR_PATH = os.path.join(BASE_DIR, "apps", "dashboard", "components", "sidebar.html")
INDEX_PATH = os.path.join(BASE_DIR, "apps", "dashboard", "index.html")
CORE_JS_PATH = os.path.join(BASE_DIR, "apps", "dashboard", "js", "sovereign_core_v121.js")

def check_dashboard_sync():
    """
    Dashboard bileşenleri arasındaki senkronizasyonu denetler.
    Returns: (bool, list): (Başarı durumu, hata mesajları listesi)
    """
    print("[INFO] Dashboard Integrity Guardian Başlatılıyor...")
    errors = []
    
    # 1. Sidebar'dan tokenları oku
    if not os.path.exists(SIDEBAR_PATH):
        return False, [f"CRITICAL: Sidebar dosyası bulunamadı: {SIDEBAR_PATH}"]
        
    try:
        with open(SIDEBAR_PATH, 'r', encoding='utf-8') as f:
            sidebar_content = f.read()
    except Exception as e:
        return False, [f"CRITICAL: Sidebar okuma hatası: {e}"]
        
    tokens = set(re.findall(r"showPage\('([^']+)'\)", sidebar_content))
    print(f"[OK] Sidebar'dan {len(tokens)} navigasyon tokenı çıkarıldı.")

    # 2. index.html'deki page-div'leri kontrol et
    if not os.path.exists(INDEX_PATH):
        return False, [f"CRITICAL: Index dosyası bulunamadı: {INDEX_PATH}"]
        
    try:
        with open(INDEX_PATH, 'r', encoding='utf-8') as f:
            index_content = f.read()
    except Exception as e:
        return False, [f"CRITICAL: Index okuma hatası: {e}"]
        
    for token in tokens:
        div_id = f'id="page-{token}"'
        if div_id not in index_content:
            errors.append(f"MISSING CONTAINER: index.html içerisinde '{div_id}' eksik veya hatalı tanımlanmış.")

    # 3. JS switch case'lerini kontrol et
    if not os.path.exists(CORE_JS_PATH):
        return False, [f"CRITICAL: Core JS dosyası bulunamadı: {CORE_JS_PATH}"]
        
    try:
        with open(CORE_JS_PATH, 'r', encoding='utf-8') as f:
            js_content = f.read()
    except Exception as e:
        return False, [f"CRITICAL: JS okuma hatası: {e}"]
        
    for token in tokens:
        case_pattern = rf"case\s+'{token}':"
        if not re.search(case_pattern, js_content):
            errors.append(f"MISSING ROUTE: sovereign_core_v121.js içerisinde '{token}' case'i bulunamadı. Navigasyon çalışmayacak.")

    # 4. Statik klasörlerde __init__.py kontrolü (Yasaklı)
    static_dirs = [
        os.path.join(BASE_DIR, "apps", "dashboard", "js"),
        os.path.join(BASE_DIR, "apps", "dashboard", "css"),
        os.path.join(BASE_DIR, "apps", "dashboard", "components")
    ]
    
    for s_dir in static_dirs:
        init_file = os.path.join(s_dir, "__init__.py")
        if os.path.exists(init_file):
            errors.append(f"FORBIDDEN FILE: {init_file} statik dizinde Python dosyası bulunmamalıdır (Mimari ihlal).")

    # Sonuç raporu
    if not errors:
        print("[SUCCESS] Dashboard Bütünlüğü Tam: Tüm katmanlar senkronize.")
        return True, []
    else:
        print(f"[FAIL] {len(errors)} Bütünlük Hatası Tespit Edildi.")
        return False, errors

if __name__ == "__main__":
    success = check_dashboard_sync()
    if not success:
        sys.exit(1)
    sys.exit(0)
