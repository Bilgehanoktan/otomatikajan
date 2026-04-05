import ast
import difflib
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from core.git_ops import GitOps
from core.shadow_runner import ShadowRunner
from core.system_indexer import SystemIndexer
from core.update_registry import SystemUpdateRegistry
from llm.model_orchestrator import ModelOrchestrator
from observability.logging import get_logger

logger = get_logger("self_updater")


class SelfUpdater:
    """
    Sistemin kendi Python dosyalarını kontrollü biçimde güncelleyen modül.

    Akış:
    1) hedef dosyayı doğrula
    2) mevcut kodu oku
    3) registry geçmişini al
    4) code index üzerinden ilgili bağlamı al
    5) LLM'den güncel TAM dosyayı iste
    6) syntax doğrula
    7) shadow workspace + pytest ile test et
    8) backup al
    9) canlı dosyaya atomik yaz
    10) git commit
    11) registry'ye işle
    """

    # Permitted top-level directories for self-modification
    ALLOWED_TOP_LEVELS = {
        "core", "api", "agents", "llm", "services", "orchestration", 
        "observability", "db", "tasks", "quality", "improve", "heal", "utils", "webhooks",
        "dashboard"
    }
    
    # Paths that require extra scrutiny or manual approval (Faz 12)
    HIGH_RISK_PATHS = {
        "main.py", "auth/", "db/session.py", "core/self_updater.py", "config.py"
    }

    DISALLOWED_TOP_LEVELS = {
        ".git", ".venv", "venv", "__pycache__", "node_modules", "workspace", "artifacts", "brain", ".gemini"
    }

    def __init__(self, model_orch: ModelOrchestrator, project_root: str | None = None):
        self.model_orch = model_orch
        self.project_root = (
            Path(project_root).resolve()
            if project_root
            else Path(__file__).resolve().parents[1]
        )

        self.registry = SystemUpdateRegistry(
            registry_path=str(self.project_root / "workspace" / "system_state.json")
        )
        self.indexer = SystemIndexer(project_root=str(self.project_root))
        self.shadow_runner = ShadowRunner(project_root=str(self.project_root))
        self.git_ops = GitOps(project_root=str(self.project_root))

    def _resolve_target_path(self, target_file_path: str) -> Path:
        target = Path(target_file_path)
        resolved = (
            target.resolve()
            if target.is_absolute()
            else (self.project_root / target).resolve()
        )

        try:
            relative = resolved.relative_to(self.project_root)
        except ValueError as e:
            raise ValueError("Hedef dosya proje kökü dışında olamaz.") from e

        if resolved.suffix not in (".py", ".html"):
            raise ValueError("Self-updater şimdilik sadece .py ve .html dosyalarını değiştirebilir.")

        if not relative.parts:
            raise ValueError("Geçersiz hedef dosya yolu.")

        top_level = relative.parts[0]
        if top_level in self.DISALLOWED_TOP_LEVELS:
            raise ValueError(f"Bu klasör self-update için bloklanmıştır: {top_level}")

        if top_level not in self.ALLOWED_TOP_LEVELS:
            raise ValueError(f"Bu klasör self-update whitelist içinde değil: {top_level}")

        if not resolved.exists():
            raise FileNotFoundError(f"Hedef dosya bulunamadı: {resolved}")

        return resolved

    def _normalize_llm_output(self, response: Any) -> str:
        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            for key in ("content", "text", "output"):
                value = response.get(key)
                if isinstance(value, str):
                    return value

        content = getattr(response, "content", None)
        if isinstance(content, str):
            return content

        text = getattr(response, "text", None)
        if isinstance(text, str):
            return text

        raise ValueError("LLM çıktısı string formatına normalize edilemedi.")

    def _extract_code(self, raw_response: str) -> str:
        python_block = re.search(r"```python\s*(.*?)```", raw_response, re.DOTALL)
        if python_block:
            return python_block.group(1).strip()

        generic_block = re.search(r"```[\w+-]*\s*(.*?)```", raw_response, re.DOTALL)
        if generic_block:
            return generic_block.group(1).strip()

        stripped = raw_response.strip()
        if stripped:
            return stripped

        raise ValueError("LLM boş çıktı döndürdü veya kod bloğu bulunamadı.")

    def _validate_code(self, code: str, filename: str) -> None:
        suffix = Path(filename).suffix
        if suffix == ".py":
            try:
                ast.parse(code, filename=filename)
                compile(code, filename, "exec")
            except SyntaxError as e:
                raise ValueError(
                    f"Yeni Python kodu sentaks doğrulamasını geçemedi: satır {e.lineno} -> {e.msg}"
                ) from e
        elif suffix == ".html":
            # Basic non-empty and minimal structure check for HTML
            if not code or "<html" not in code.lower():
                 raise ValueError("Yeni HTML kodu eksik veya geçersiz bir yapıya sahip.")
        else:
            raise ValueError(f"Desteklenmeyen dosya türü: {suffix}")

    def _create_backup(self, target_path: Path, original_code: str) -> Path:
        relative = target_path.relative_to(self.project_root)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_dir = self.project_root / "workspace" / "backups" / relative.parent
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_name = (
            f"{target_path.stem}_{timestamp}_{uuid.uuid4().hex[:8]}{target_path.suffix}"
        )
        backup_path = backup_dir / backup_name
        backup_path.write_text(original_code, encoding="utf-8")
        return backup_path

    def _atomic_write_text(self, target_path: Path, content: str) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            prefix=f"{target_path.stem}_",
            suffix=".tmp",
            dir=str(target_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())

            os.replace(temp_path, target_path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _get_top_level_definitions(self, code: str) -> Dict[str, str]:
        """
        Top-level class/function metinlerini çıkartır.
        Değişen sembol analizi için kullanılır.
        """
        tree = ast.parse(code)
        lines = code.splitlines()
        mapping: Dict[str, str] = {}

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = node.lineno - 1
                end = getattr(node, "end_lineno", node.lineno) - 1
                block = "\n".join(lines[start : end + 1]).strip()
                mapping[node.name] = block

        return mapping

    def _detect_changed_symbols(self, original_code: str, new_code: str) -> List[str]:
        try:
            old_defs = self._get_top_level_definitions(original_code)
            new_defs = self._get_top_level_definitions(new_code)

            changed: List[str] = []
            all_names = sorted(set(old_defs) | set(new_defs))

            for name in all_names:
                if name not in old_defs:
                    changed.append(f"+ {name}")
                elif name not in new_defs:
                    changed.append(f"- {name}")
                elif old_defs[name] != new_defs[name]:
                    changed.append(f"~ {name}")

            return changed[:30]
        except Exception as e:
            logger.error(f"Changed symbol tespiti başarısız: {e}")
            return []

    def _summarize_diff(self, original_code: str, new_code: str, max_lines: int = 80) -> str:
        diff = list(
            difflib.unified_diff(
                original_code.splitlines(),
                new_code.splitlines(),
                fromfile="before",
                tofile="after",
                lineterm="",
            )
        )
        if not diff:
            return "No diff."

        return "\n".join(diff[:max_lines])

    async def modify_system_file(self, target_file_path: str, instruction: str) -> str:
        from core.rollback_manager import RollbackManager
        rb_mgr = RollbackManager(str(self.project_root))
        
        snapshot_tag = None
        try:
            full_path = self._resolve_target_path(target_file_path)
            relative_path = full_path.relative_to(self.project_root)

            logger.warning(
                f"⚠️ SELF-UPDATE başlatıldı -> {relative_path.as_posix()}"
            )

            # Faz 12.1: Snapshot before operation
            snapshot_tag = rb_mgr.create_snapshot(f"update_{relative_path.name}")

            original_code = full_path.read_text(encoding="utf-8")

            # Kod hafızasını güncel tut
            self.indexer.build_index()

            recent_history = self.registry.get_recent_updates(limit=10)
            related_context = self.indexer.get_context_for_task(
                query=f"{relative_path.as_posix()} {instruction}",
                limit=6,
                max_chars=7000,
            )

            prompt = f"""
AŞAĞIDAKİ PYTHON DOSYASINI GÜNCELLE: {relative_path.as_posix()}

{recent_history}

{related_context}

GÜNCELLEME İSTEĞİ:
{instruction}

SERT KURALLAR:
- Mevcut davranışı bozma.
- Sadece istenen değişikliği ekle veya düzelt.
- Importları, sınıf yapısını, public API'yi gereksiz yere değiştirme.
- Placeholder bırakma.
- Eksik kod bırakma.
- Sadece TAM ve ÇALIŞIR Python dosyasını döndür.
- Ek açıklama yazma.
- Yalnızca tek bir ```python ... ``` kod bloğu döndür.

MEVCUT DOSYA:
```python
{original_code}
```
"""

            raw_response = await self.model_orch.complete(
                messages=[{"role": "user", "content": prompt}],
                preferred_agent="engineering-system-architect",
            )

            raw_text = self._normalize_llm_output(raw_response)
            new_code = self._extract_code(raw_text)
            self._validate_code(new_code, str(relative_path))

            if new_code.strip() == original_code.strip():
                logger.info(f"Değişiklik yok: {relative_path.as_posix()}")
                return f"Değişiklik yapılmadı. Dosya zaten aynı içerikte: {relative_path.as_posix()}"

            changed_symbols = self._detect_changed_symbols(original_code, new_code)
            diff_summary = self._summarize_diff(original_code, new_code)

            validation = self.shadow_runner.validate_candidate(
                relative_path=str(relative_path.as_posix()),
                candidate_code=new_code,
            )

            test_result = {
                "shadow_root": validation.get("shadow_root"),
                "syntax_ok": validation.get("syntax_ok"),
                "pytest_ok": validation.get("pytest_ok"),
                "pytest_skipped": validation.get("pytest_skipped"),
                "returncode": validation.get("returncode"),
                "stdout_tail": (validation.get("stdout") or "")[-3000:],
                "stderr_tail": (validation.get("stderr") or "")[-3000:],
            }

            if not validation.get("syntax_ok"):
                self.registry.log_update(
                    target_file=relative_path.as_posix(),
                    description=instruction,
                    rationale="Self-Modification Request",
                    status="rejected_syntax",
                    diff_summary=diff_summary,
                    changed_symbols=changed_symbols,
                    test_result=test_result,
                    bump_version=False,
                )
                return (
                    f"Başarısız: Shadow syntax doğrulaması geçilemedi. "
                    f"Dosya yazılmadı. Hedef={relative_path.as_posix()}"
                )

            if validation.get("pytest_ok") is False:
                self.registry.log_update(
                    target_file=relative_path.as_posix(),
                    description=instruction,
                    rationale="Self-Modification Request",
                    status="rejected_tests",
                    diff_summary=diff_summary,
                    changed_symbols=changed_symbols,
                    test_result=test_result,
                    bump_version=False,
                )
                return (
                    f"Başarısız: Shadow pytest başarısız oldu. "
                    f"Dosya yazılmadı. Hedef={relative_path.as_posix()}"
                )

            backup_path = self._create_backup(full_path, original_code)
            self._atomic_write_text(full_path, new_code)

            commit_sha = None
            try:
                commit_sha = self.git_ops.commit_file(
                    relative_path=relative_path.as_posix(),
                    message=f"[AUTO-UPDATE] {relative_path.as_posix()} :: {instruction[:80]}",
                )
            except Exception as git_error:
                logger.error(f"Git commit hatası: {git_error}")

            self.registry.log_update(
                target_file=relative_path.as_posix(),
                description=instruction,
                rationale="Self-Modification Request",
                backup_path=str(backup_path.relative_to(self.project_root).as_posix()),
                status="applied",
                diff_summary=diff_summary,
                changed_symbols=changed_symbols,
                test_result=test_result,
                git_commit=commit_sha,
                bump_version=True,
            )

            logger.info(
                f"✅ SELF-UPDATE başarılı -> {relative_path.as_posix()} | "
                f"backup={backup_path}"
            )

            # Faz 12.1: Verify Health
            import asyncio
            await asyncio.sleep(5) # Wait for reload / reload sequence
            
            if not rb_mgr.verify_health():
                logger.error(f"Post-update health check failed for {relative_path.name}. Rolling back to {snapshot_tag}")
                rb_mgr.rollback_to_tag(snapshot_tag)
                return (
                    f"Başarısız: Güncelleme sonrası sistem sağlığı bozuldu. "
                    f"Geri yükleme (rollback) yapıldı: {snapshot_tag}"
                )

            return (
                f"Başarılı. Dosya güncellendi: {relative_path.as_posix()} | "
                f"Yedek: {backup_path.relative_to(self.project_root).as_posix()} | "
                f"Snapshot: {snapshot_tag} | "
                f"Git: {commit_sha or 'commit_atılmadı'}"
            )

        except Exception as e:
            logger.error(f"Sistem kendini güncellerken hata aldı: {e}")
            if snapshot_tag:
                logger.warning(f"Kritik hata: rollback tetikleniyor -> {snapshot_tag}")
                rb_mgr.rollback_to_tag(snapshot_tag)
            return f"Başarısız: {e}"
