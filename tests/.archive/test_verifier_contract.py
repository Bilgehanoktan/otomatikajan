from pathlib import Path


def test_patch_verifier_should_not_accept_simulated_success_only() -> None:
    src = Path("core/improvement/verifier.py").read_text(encoding="utf-8")

    # Eski mock stringleri içermemeli
    assert '"print(\'TEST_PASSED\')"' not in src, (
        "Verifier halen simüle edilmiş test çıktısına güveniyor gibi görünüyor."
    )
    assert "target_path.write_text(" in src, "Verifier patch içeriğini dosyaya yazmalı."
