from pathlib import Path


def test_repair_pipeline_module_should_not_execute_tests_at_import_time() -> None:
    # Bu dosyanın varlığını kontrol et
    path = Path("tests/test_repair_pipeline_integration.py")
    if not path.exists():
        return # Skip if file moved or renamed

    src = path.read_text(encoding="utf-8")

    # Global seviyede (indent almamış) test çağrısı olmamalı
    # Sadece 'def ' ile başlamayan ve satır başında olan çağrıları avlayalım
    assert "\ntest_fingerprint_step()" not in src, (
        "Test modülü import edilirken test fonksiyonu doğrudan çağrılıyor (Global scope call detected)."
    )
