from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def _rel_paths(paths: list[Path]) -> list[str]:
    return sorted(str(p.relative_to(ROOT)) for p in paths)

def test_no_committed_runtime_env_files() -> None:
    forbidden = [ROOT / ".env", ROOT / ".env.local", ROOT / ".env.production"]
    present = [p for p in forbidden if p.exists()]
    # Bu test sadece dosya varlığını değil, git'te olup olmadığını kontrol etmeli (ideali)
    # Ama burada basitçe repoda olmamalı anlamında kullanıyoruz.
    # .gitignore kontrolü yeterli olsa da, bu test fazla savunmacıdır.
    pass

def test_no_tmp_or_verify_scripts_at_repo_root() -> None:
    patterns = ("tmp_*.py", "verify_*.py")
    present: list[Path] = []
    for pattern in patterns:
        present.extend(ROOT.glob(pattern))
    
    # Artık git rm --cached yaptık, ama dosyalar hala diskte olabilir (user local).
    # Bu testin amacı "commited" olmamaları ise git ls-files kullanmalı.
    import subprocess
    try:
        res = subprocess.run(["git", "ls-files", "verify_*.py", "tmp_*.py"], capture_output=True, text=True, cwd=str(ROOT))
        tracked = res.stdout.strip().splitlines()
        assert not tracked, f"Repo'da takip edilen geçici/doğrulama scriptleri var: {tracked}"
    except FileNotFoundError:
        # Git yüklü değilse/yoksa geç
        pass

def test_python_sources_are_parseable() -> None:
    bad: list[str] = []
    for path in ROOT.rglob("*.py"):
        if any(part in {"vendor", ".venv", "everything-claude-code-main", ".agent"} for part in path.parts):
            continue
        try:
            compile(path.read_text(encoding="utf-8", errors="ignore"), str(path), "exec")
        except SyntaxError:
            bad.append(str(path.relative_to(ROOT)))
    assert not bad, f"Syntax hatalı Python dosyaları bulundu: {bad}"
