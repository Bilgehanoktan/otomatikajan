from pathlib import Path


def test_env_files_should_not_ship_inside_repo_artifact() -> None:
    forbidden = [".env.production", ".env.local"] # .env genelde kalır ama production/local asla kalmamalı
    existing = [p for p in forbidden if Path(p).exists()]
    assert not existing, f"Repo içinde yasaklı env dosyaları bulundu: {existing}"
