from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple


@dataclass
class Node:
    path: str
    file_type: str
    size_bytes: int
    last_modified: float
    imports: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)


class RepoGraph:
    """
    World Model (Katman 9): repository, module and dependency mapping.
    AGI planner için hafif ama pratik bir iç dünya modeli sunar.
    """

    def __init__(self, root_dir: str | None = None):
        self.root_dir = self._resolve_root_dir(root_dir)
        self.nodes: Dict[str, Node] = {}
        self.local_edges: Dict[str, Set[str]] = {}
        self.unresolved_local_imports: Dict[str, List[str]] = {}
        self.cycles: List[List[str]] = []
        self.ignored_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            "venv",
            ".venv",
            ".deer-flow",
            ".pytest_cache",
            "dist",
            "build",
        }
        self.supported_exts = {".py", ".js", ".ts", ".html", ".css", ".md"}

    @staticmethod
    def _resolve_root_dir(root_dir: str | None = None) -> str:
        if root_dir:
            return os.path.abspath(root_dir)

        cwd = Path.cwd()
        for candidate in [cwd, *cwd.parents]:
            if (candidate / "pyproject.toml").exists() or (candidate / "README.md").exists() or (candidate / "main.py").exists():
                return str(candidate)

        module_dir = Path(__file__).resolve().parents[3]
        return str(module_dir)

    def scan(self) -> Dict[str, Node]:
        """Repoyu tarar ve grafı üretir."""
        self.nodes = {}
        self.local_edges = {}
        self.unresolved_local_imports = {}
        self.cycles = []

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs and not d.startswith(".")]

            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in self.supported_exts:
                    continue

                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, self.root_dir).replace("\\", "/")
                stats = os.stat(full_path)
                node = Node(
                    path=rel_path,
                    file_type=ext[1:],
                    size_bytes=stats.st_size,
                    last_modified=stats.st_mtime,
                )
                if ext == ".py":
                    node.imports = self._extract_py_imports(full_path)

                self.nodes[rel_path] = node

        self._build_reverse_links()
        self._scan_autonomous_tools()
        self.cycles = self._find_cycles(limit=8)
        return self.nodes

    def _scan_autonomous_tools(self) -> None:
        reg_path = os.path.join(self.root_dir, "tools/autonomous/registry.json")
        if not os.path.exists(reg_path):
            return
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                tools = json.load(f)
            for name, meta in tools.items():
                node = Node(
                    path=meta["path"],
                    file_type="autonomous_tool",
                    size_bytes=0,
                    last_modified=float(meta.get("created_at", 0)),
                )
                self.nodes[f"capability:{name}"] = node
        except Exception:
            pass

    def _extract_py_imports(self, file_path: str) -> List[str]:
        imports: Set[str] = set()
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            matches = re.finditer(
                r"^(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))",
                content,
                re.MULTILINE,
            )
            for match in matches:
                imp = match.group(1) or match.group(2)
                if imp:
                    imports.add(imp)
        except Exception:
            pass
        return sorted(imports)

    def _build_reverse_links(self) -> None:
        for node in self.nodes.values():
            node.dependents = []

        self.local_edges = {path: set() for path in self.nodes}
        self.unresolved_local_imports = {}

        for path, node in self.nodes.items():
            for imp in node.imports:
                resolved = self._resolve_local_import(imp)
                if resolved:
                    self.local_edges[path].add(resolved)
                    self.nodes[resolved].dependents.append(path)
                elif self._looks_like_local_import(imp):
                    self.unresolved_local_imports.setdefault(path, []).append(imp)

    def _resolve_local_import(self, import_path: str) -> str | None:
        candidates = [
            import_path.replace(".", "/") + ".py",
            import_path.replace(".", "/") + "/__init__.py",
        ]
        for candidate in candidates:
            if candidate in self.nodes:
                return candidate
        return None

    def _looks_like_local_import(self, import_path: str) -> bool:
        head = import_path.split(".", 1)[0]
        if head in {"core", "api", "db", "auth", "memory", "agents", "tasks", "quality", "repair", "llm", "dashboard", "skills", "tools", "heal", "observability", "integrations"}:
            return True
        return (Path(self.root_dir) / head).exists()

    def get_summary(self) -> Dict[str, Any]:
        language_breakdown: Dict[str, int] = {}
        for node in self.nodes.values():
            language_breakdown[node.file_type] = language_breakdown.get(node.file_type, 0) + 1

        unresolved_flat = [
            {"path": path, "imports": imports}
            for path, imports in sorted(self.unresolved_local_imports.items())[:8]
        ]
        entrypoints = self._find_entrypoints(limit=8)
        return {
            "root_dir": self.root_dir,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "total_files": len(self.nodes),
            "total_edges": sum(len(edges) for edges in self.local_edges.values()),
            "language_breakdown": language_breakdown,
            "hubs": self._find_hubs(limit=5),
            "critical_files": self._find_critical_files(),
            "entrypoints": entrypoints,
            "unresolved_local_imports": unresolved_flat,
            "cycles": self.cycles,
            "context_pack": self.export_context_pack(limit=6),
        }

    def export_context_pack(self, limit: int = 6) -> str:
        summary = {
            "hubs": self._find_hubs(limit=min(limit, 5)),
            "critical_files": self._find_critical_files()[:limit],
            "entrypoints": self._find_entrypoints(limit=limit),
            "unresolved_local_imports": [
                {"path": path, "imports": imports}
                for path, imports in list(self.unresolved_local_imports.items())[:limit]
            ],
            "cycles": self.cycles[: min(limit, len(self.cycles))],
        }
        lines = ["[WORLD_MODEL]"]
        lines.append(f"root={self.root_dir}")
        lines.append(f"files={len(self.nodes)} edges={sum(len(edges) for edges in self.local_edges.values())}")
        lines.append(f"hubs={summary['hubs']}")
        lines.append(f"critical_files={summary['critical_files']}")
        lines.append(f"entrypoints={summary['entrypoints']}")
        lines.append(f"unresolved_local_imports={summary['unresolved_local_imports']}")
        lines.append(f"cycles={summary['cycles']}")
        return "\n".join(lines)

    def _find_hubs(self, limit: int = 5) -> List[Dict[str, Any]]:
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: len(n.dependents), reverse=True)
        return [
            {"path": node.path, "dependents_count": len(node.dependents)}
            for node in sorted_nodes[:limit]
        ]

    def _find_critical_files(self) -> List[str]:
        critical: List[Tuple[int, str]] = []
        for path, node in self.nodes.items():
            score = 0
            if any(token in path for token in ("main.py", "orchestrator", "schemas", "router", "session", "model_orchestrator")):
                score += 3
            score += len(node.dependents)
            if path in self._find_entrypoints(limit=50):
                score += 2
            if score > 0:
                critical.append((score, path))
        critical.sort(reverse=True)
        return [path for _, path in critical[:10]]

    def _find_entrypoints(self, limit: int = 8) -> List[str]:
        preferred = []
        for path in self.nodes:
            name = Path(path).name
            if name in {"main.py", "app.py", "manage.py"} or path.startswith("api/") or path.startswith("dashboard/"):
                preferred.append(path)
        preferred = sorted(dict.fromkeys(preferred))
        return preferred[:limit]

    def _find_cycles(self, limit: int = 8) -> List[List[str]]:
        cycles: List[List[str]] = []
        seen: Set[Tuple[str, ...]] = set()

        def dfs(node: str, path: List[str], active: Set[str]) -> None:
            if len(cycles) >= limit:
                return
            active.add(node)
            path.append(node)
            for nxt in self.local_edges.get(node, set()):
                if nxt in active:
                    idx = path.index(nxt)
                    cycle = path[idx:] + [nxt]
                    key = tuple(sorted(set(cycle)))
                    if key not in seen:
                        seen.add(key)
                        cycles.append(cycle)
                elif nxt not in path:
                    dfs(nxt, path.copy(), set(active))
            active.discard(node)

        for node in self.local_edges:
            if len(cycles) >= limit:
                break
            dfs(node, [], set())
        return cycles


repo_world_model = RepoGraph()
