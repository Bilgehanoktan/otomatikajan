import ast
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List

from observability.logging import get_logger

logger = get_logger("system_indexer")


@dataclass
class FileIndexEntry:
    path: str
    file_type: str
    summary: str
    symbols: List[str]
    imports: List[str]
    mtime_utc: str
    size_bytes: int


class SystemIndexer:
    """
    Kod tabanını tarar, özetler ve basit aranabilir indeks üretir.
    Bu sürüm stdlib tabanlıdır. İleride gerçek embedding/vector DB ile genişletilebilir.
    """

    INCLUDED_TOP_LEVELS = {
        "core",
        "api",
        "agents",
        "llm",
        "services",
        "orchestration",
        "observability",
    }

    EXCLUDED_DIR_NAMES = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        "backups",
        "shadow_workspace",
        ".pytest_cache",
    }

    ALLOWED_SUFFIXES = {".py", ".md"}

    def __init__(
        self,
        project_root: str | None = None,
        index_path: str = "workspace/code_index.json",
    ):
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = Path(__file__).resolve().parents[1]

        self.index_path = (self.project_root / index_path).resolve()

    def _atomic_write_json(self, data: Dict[str, Any]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            prefix="code_index_",
            suffix=".tmp",
            dir=str(self.index_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            os.replace(temp_path, self.index_path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def _is_allowed(self, rel_path: Path) -> bool:
        if not rel_path.parts:
            return False

        top_level = rel_path.parts[0]
        if top_level not in self.INCLUDED_TOP_LEVELS:
            return False

        if rel_path.suffix not in self.ALLOWED_SUFFIXES:
            return False

        if any(part in self.EXCLUDED_DIR_NAMES for part in rel_path.parts):
            return False

        return True

    def _collapse_ws(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _build_python_entry(self, file_path: Path, rel_path: Path) -> FileIndexEntry:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        symbols: List[str] = []
        imports: List[str] = []
        summary = "Python modülü."

        try:
            tree = ast.parse(content)
            module_doc = ast.get_docstring(tree) or ""

            class_names: List[str] = []
            function_names: List[str] = []

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_names.append(node.name)
                    symbols.append(node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_names.append(node.name)
                    symbols.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module or ""
                    imports.append(module_name)

            parts = []
            if module_doc:
                parts.append(self._collapse_ws(module_doc)[:350])
            if class_names:
                parts.append(f"Sınıflar: {', '.join(class_names[:10])}")
            if function_names:
                parts.append(f"Fonksiyonlar: {', '.join(function_names[:15])}")
            if imports:
                parts.append(f"Importlar: {', '.join(imports[:10])}")

            if parts:
                summary = " | ".join(parts)

        except Exception as e:
            summary = f"AST parse edilemedi: {e}"

        stat = file_path.stat()
        return FileIndexEntry(
            path=rel_path.as_posix(),
            file_type="python",
            summary=summary,
            symbols=symbols,
            imports=imports,
            mtime_utc=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            size_bytes=stat.st_size,
        )

    def _build_markdown_entry(self, file_path: Path, rel_path: Path) -> FileIndexEntry:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        content = self._collapse_ws(content)
        summary = content[:500] if content else "Boş markdown dosyası."

        stat = file_path.stat()
        return FileIndexEntry(
            path=rel_path.as_posix(),
            file_type="markdown",
            summary=summary,
            symbols=[],
            imports=[],
            mtime_utc=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            size_bytes=stat.st_size,
        )

    def build_index(self) -> Dict[str, Any]:
        entries: List[Dict[str, Any]] = []

        for file_path in self.project_root.rglob("*"):
            if not file_path.is_file():
                continue

            try:
                rel_path = file_path.relative_to(self.project_root)
            except ValueError:
                continue

            if not self._is_allowed(rel_path):
                continue

            try:
                if file_path.suffix == ".py":
                    entry = self._build_python_entry(file_path, rel_path)
                else:
                    entry = self._build_markdown_entry(file_path, rel_path)

                entries.append(asdict(entry))
            except Exception as e:
                logger.error(f"İndeksleme hatası: {file_path} | {e}")

        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "project_root": str(self.project_root),
            "entry_count": len(entries),
            "entries": entries,
        }

        self._atomic_write_json(payload)
        logger.info(f"Kod indeksi üretildi. entry_count={len(entries)}")
        return payload

    def read_index(self) -> Dict[str, Any]:
        if not self.index_path.exists():
            return self.build_index()

        try:
            with self.index_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.build_index()

    def search_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Finds files containing a specific symbol (class, function name)."""
        data = self.read_index()
        entries = data.get("entries", [])
        symbol_l = symbol.lower().strip()

        if not symbol_l:
            return []

        matches: List[Dict[str, Any]] = []
        for entry in entries:
            symbols = [s.lower() for s in entry.get("symbols", [])]
            if symbol_l in symbols:
                matches.append(entry)

        return matches[:limit]

    def impact_analysis(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Calculates potential impact of a change by finding related files
        via shared symbols and import relationships.
        """
        data = self.read_index()
        entries = data.get("entries", [])
        primary_hits = self.search(query=query, limit=limit)

        if not primary_hits:
            return []

        primary_paths = {e.get("path", "") for e in primary_hits}
        primary_symbols = set()
        primary_imports = set()

        for hit in primary_hits:
            for s in hit.get("symbols", []):
                primary_symbols.add(s.lower())
            for imp in hit.get("imports", []):
                if imp:
                    primary_imports.add(imp.lower())

        scored: List[tuple[float, Dict[str, Any]]] = []
        for entry in entries:
            path = entry.get("path", "")
            if path in primary_paths:
                continue

            score = 0.0
            entry_symbols = [s.lower() for s in entry.get("symbols", [])]
            entry_imports = [i.lower() for i in entry.get("imports", []) if i]
            hay = f"{path} {entry.get('summary', '')}".lower()

            for sym in primary_symbols:
                if sym and sym in entry_symbols:
                    score += 4.0
                elif sym and sym in hay:
                    score += 1.5

            for imp in primary_imports:
                if imp and imp in entry_imports:
                    score += 2.0
                elif imp and imp in hay:
                     score += 1.0

            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z_][a-zA-Z0-9_./-]*", text.lower())

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        data = self.read_index()
        entries = data.get("entries", [])

        if not query.strip():
            return entries[:limit]

        query_tokens = set(self._tokenize(query))
        scored: List[tuple[float, Dict[str, Any]]] = []

        for entry in entries:
            path = entry.get("path", "")
            symbols = entry.get("symbols", [])
            summary = entry.get("summary", "")

            haystack = f"{path} {' '.join(symbols)} {summary}".lower()
            hay_tokens = set(self._tokenize(haystack))

            overlap = len(query_tokens & hay_tokens)
            symbol_bonus = sum(
                2 for token in query_tokens if token in " ".join(symbols).lower()
            )
            path_bonus = sum(2 for token in query_tokens if token in path.lower())
            similarity = SequenceMatcher(None, query.lower(), haystack[:700]).ratio()

            score = (overlap * 5.0) + symbol_bonus + path_bonus + similarity
            
            # Minimum score threshold to be considered a primary hit
            if score > 1.0:
                scored.append((score, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def get_context_for_task(
        self,
        query: str,
        limit: int = 5,
        max_chars: int = 6000,
    ) -> str:
        matches = self.search(query=query, limit=limit)
        if not matches:
            return "İlgili kod tabanı bağlamı bulunamadı."

        lines = ["--- İLGİLİ KOD TABANI BAĞLAMI ---"]
        for item in matches:
            path = item.get("path", "")
            summary = item.get("summary", "")
            symbols = ", ".join(item.get("symbols", [])[:15]) or "yok"
            lines.append(
                f"[{path}]\n"
                f"Semboller: {symbols}\n"
                f"Özet: {summary}\n"
            )

        context = "\n".join(lines)
        return context[:max_chars]
