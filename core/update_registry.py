import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from observability.logging import get_logger

logger = get_logger("update_registry")


class SystemUpdateRegistry:
    """Sistemin kendi üzerinde yaptığı güncellemelerin sicilini tutar."""

    def __init__(self, registry_path: str = "workspace/system_state.json"):
        self.registry_path = Path(registry_path)
        self._lock = threading.RLock()
        self._ensure_exists()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "current_version": "v13.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "updates": [],
        }

    def _ensure_exists(self) -> None:
        with self._lock:
            if not self.registry_path.exists():
                self.registry_path.parent.mkdir(parents=True, exist_ok=True)
                self._atomic_write_json(self._default_state())
                logger.info(f"Registry oluşturuldu: {self.registry_path}")

    def _read_json(self) -> Dict[str, Any]:
        with self._lock:
            self._ensure_exists()
            try:
                with self.registry_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                corrupt_backup = self.registry_path.with_suffix(".corrupt.json")
                try:
                    os.replace(self.registry_path, corrupt_backup)
                    logger.error(f"Bozuk registry yedeklendi: {corrupt_backup}")
                except Exception as backup_err:
                    logger.error(f"Bozuk registry yedeklenemedi: {backup_err}")

                default_state = self._default_state()
                self._atomic_write_json(default_state)
                return default_state

    def _atomic_write_json(self, data: Dict[str, Any]) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            prefix="system_state_",
            suffix=".tmp",
            dir=str(self.registry_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(data, tmp_file, indent=4, ensure_ascii=False)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(temp_path, self.registry_path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _bump_version(self, current_version: str) -> str:
        raw = (current_version or "v13.0").strip().lower().removeprefix("v")
        parts = raw.split(".")
        numeric_parts: List[int] = []

        for part in parts:
            try:
                numeric_parts.append(int(part))
            except ValueError:
                numeric_parts.append(0)

        if not numeric_parts:
            return "v1.0"

        numeric_parts[-1] += 1
        return "v" + ".".join(str(p) for p in numeric_parts)

    def get_state(self) -> Dict[str, Any]:
        return self._read_json()

    def log_update(
        self,
        target_file: str,
        description: str,
        rationale: str,
        backup_path: Optional[str] = None,
        status: str = "applied",
        diff_summary: Optional[str] = None,
        changed_symbols: Optional[List[str]] = None,
        test_result: Optional[Dict[str, Any]] = None,
        git_commit: Optional[str] = None,
        bump_version: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Güncelleme kaydı ekler.
        status='applied' ise default olarak sürüm artırılır.
        Rejected/failed gibi durumlarda bump_version=False verilebilir.
        """
        with self._lock:
            data = self._read_json()
            previous_version = data.get("current_version", "v13.0")

            if bump_version is None:
                bump_version = status == "applied"

            next_version = (
                self._bump_version(previous_version)
                if bump_version
                else previous_version
            )

            new_update = {
                "date": datetime.now(timezone.utc).isoformat(),
                "target_file": target_file,
                "description": description,
                "rationale": rationale,
                "backup_path": backup_path,
                "status": status,
                "version_before": previous_version,
                "version_after": next_version,
                "diff_summary": diff_summary,
                "changed_symbols": changed_symbols or [],
                "test_result": test_result or {},
                "git_commit": git_commit,
            }

            data.setdefault("updates", []).append(new_update)
            data["current_version"] = next_version
            data["last_updated"] = new_update["date"]

            self._atomic_write_json(data)

            logger.info(
                f"📜 Registry kaydı işlendi: {target_file} | "
                f"{previous_version} -> {next_version} | status={status}"
            )
            return new_update

    def get_recent_updates(self, limit: int = 5) -> str:
        """Ajan promptuna eklenecek okunabilir son update özeti."""
        try:
            data = self._read_json()
            updates = data.get("updates", [])[-limit:]
            if not updates:
                return "Henüz sistem güncellemesi yapılmadı."

            version = data.get("current_version", "bilinmiyor")
            lines = [f"--- SON SİSTEM GÜNCELLEMELERİ (MEVCUT SÜRÜM: {version}) ---"]

            for item in updates:
                dt = item.get("date", "")[:16]
                target = item.get("target_file", "bilinmeyen_dosya")
                desc = item.get("description", "açıklama yok")
                reason = item.get("rationale", "sebep yok")
                status = item.get("status", "unknown")
                symbols = ", ".join(item.get("changed_symbols", [])[:5]) or "yok"

                lines.append(
                    f"- [{dt}] {target} | status={status} | "
                    f"değişiklik={desc} | sebep={reason} | semboller={symbols}"
                )

            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Sicil okunamadı: {e}")
            return "Sicil okunamadı."
