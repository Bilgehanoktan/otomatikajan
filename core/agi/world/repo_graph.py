import os
import re
import json
from typing import Dict, List, Any, Set
from dataclasses import dataclass, field
from datetime import datetime

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
    World Model (Katman 9): Repositories, modules and dependency mapping.
    Sistemin kendi çalışma alanını anlamasını sağlayan içsel temsil.
    """
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.nodes: Dict[str, Node] = {}
        self.ignored_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.deer-flow'}
        self.supported_exts = {'.py', '.js', '.html', '.css', '.md'}

    def scan(self) -> Dict[str, Node]:
        """Tüm repoyu tarar ve grafı oluşturur."""
        self.nodes = {}
        for root, dirs, files in os.walk(self.root_dir):
            # Ignore hidden/excluded dirs
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in self.supported_exts:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_dir)
                    
                    stats = os.stat(full_path)
                    node = Node(
                        path=rel_path,
                        file_type=ext[1:],
                        size_bytes=stats.st_size,
                        last_modified=stats.st_mtime
                    )
                    
                    if ext == '.py':
                        node.imports = self._extract_py_imports(full_path)
                    
                    self.nodes[rel_path] = node

        # Inverse dependencies (Who depends on whom?)
        self._build_reverse_links()

        # --- Otonom Yetenek Keşfi (Phase 12.4) ---
        self._scan_autonomous_tools()

        return self.nodes

    def _scan_autonomous_tools(self):
        """Otonom üretilen araçları haritaya ekler."""
        reg_path = os.path.join(self.root_dir, "tools/autonomous/registry.json")
        if os.path.exists(reg_path):
            try:
                with open(reg_path, "r") as f:
                    tools = json.load(f)
                    for name, meta in tools.items():
                        # Otonom araçları sanal düğümler olarak ekle
                        node = Node(
                            path=meta["path"],
                            file_type="autonomous_tool",
                            size_bytes=0,
                            last_modified=float(meta.get("created_at", 0))
                        )
                        self.nodes[f"capability:{name}"] = node
            except:
                pass

    def _extract_py_imports(self, file_path: str) -> List[str]:
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Basic regex for 'import x' and 'from x import y'
                matches = re.finditer(r'^(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))', content, re.MULTILINE)
                for m in matches:
                    imp = m.group(1) or m.group(2)
                    if imp:
                        imports.append(imp)
        except Exception:
            pass
        return list(set(imports))

    def _build_reverse_links(self):
        """B bağımlılıklarının tersini oluşturur."""
        for path, node in self.nodes.items():
            for imp in node.imports:
                # Try to resolve import to a local file path
                # Example: 'core.agi.schemas' -> 'core/agi/schemas.py'
                potential_path = imp.replace('.', '/') + '.py'
                if potential_path in self.nodes:
                    self.nodes[potential_path].dependents.append(path)

    def get_summary(self) -> Dict[str, Any]:
        """Grafın özetini çıkarır."""
        return {
            "total_files": len(self.nodes),
            "hubs": self._find_hubs(limit=5),
            "critical_files": self._find_critical_files()
        }

    def _find_hubs(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Çok fazla bağımlılığı olan (merkezi) dosyaları bulur."""
        sorted_nodes = sorted(self.nodes.values(), key=lambda x: len(x.dependents), reverse=True)
        return [{"path": n.path, "dependents_count": len(n.dependents)} for n in sorted_nodes[:limit]]

    def _find_critical_files(self) -> List[str]:
        """Tüm sistemin bağlı olduğu kritik dosyaları tespit eder."""
        # Top-level dependencies or cores
        critical = []
        for path in self.nodes:
            if 'schemas' in path or 'orchestrator' in path or 'main' in path:
                critical.append(path)
        return critical

# --- Singleton for AGI Usage ---
repo_world_model = RepoGraph(os.getcwd())
