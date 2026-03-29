"""
Kod Üretim Motoru — Faz 6
════════════════════════════════════════════════════════
Her ajan metin analizi değil, GERÇEK KOD üretir:
  - Syntax-doğrulanmış Python / TypeScript / SQL / YAML
  - Otomatik lint + format (ast.parse, ruff-style checks)
  - Proje şablonlarına göre bağlamlı üretim
  - ZIP olarak indirilebilir çıktı
  - Code review ajan entegrasyonu

Akış:
  Görev -> CodePlanner -> [8 ajan paralel kod üretir]
         -> SyntaxValidator -> CodeReviewAgent
         -> CodeAssembler -> ZIP çıktısı
"""

import ast
import asyncio
import io
import os
import re
import textwrap
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from observability.logging import get_logger
logger = get_logger("code_engine")


# ════════════════════════════════════════════════════════
# Veri Yapıları
# ════════════════════════════════════════════════════════

class CodeLanguage(str, Enum):
    PYTHON     = "python"
    TYPESCRIPT = "typescript"
    SQL        = "sql"
    YAML       = "yaml"
    MARKDOWN   = "markdown"
    BASH       = "bash"
    DOCKERFILE = "dockerfile"
    JSON       = "json"


@dataclass
class CodeFile:
    path:        str           # örn: "src/api/routes.py"
    language:    CodeLanguage
    content:     str
    description: str = ""
    agent_id:    str = ""

    # Doğrulama sonuçları
    syntax_ok:   bool = True
    lint_issues: list[str] = field(default_factory=list)
    review_notes:list[str] = field(default_factory=list)

    @property
    def filename(self) -> str:
        return os.path.basename(self.path)

    @property
    def extension(self) -> str:
        return {
            CodeLanguage.PYTHON:     ".py",
            CodeLanguage.TYPESCRIPT: ".ts",
            CodeLanguage.SQL:        ".sql",
            CodeLanguage.YAML:       ".yaml",
            CodeLanguage.MARKDOWN:   ".md",
            CodeLanguage.BASH:       ".sh",
            CodeLanguage.DOCKERFILE: "Dockerfile",
            CodeLanguage.JSON:       ".json",
        }.get(self.language, ".txt")

    def line_count(self) -> int:
        return len(self.content.splitlines())


@dataclass
class CodeGenerationResult:
    project_id:  str
    title:       str
    files:       list[CodeFile]
    status:      str = "running" # "running" | "completed" | "failed"
    error:       str = ""
    created_at:  str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_lines: int = 0
    languages:   list[str] = field(default_factory=list)
    review_summary: str = ""
    quality_score:  float = 0.0

    def __post_init__(self):
        self.total_lines = sum(f.line_count() for f in self.files)
        self.languages   = list({f.language.value for f in self.files})

    def to_zip(self) -> bytes:
        """Tüm dosyaları ZIP olarak döndür."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for cf in self.files:
                zf.writestr(cf.path, cf.content)
            # Özet README ekle
            readme = self._build_readme()
            zf.writestr("GENERATED_README.md", readme)
        return buf.getvalue()

    def _build_readme(self) -> str:
        lines = [
            f"# {self.title}",
            f"",
            f"> Otonom AI Şirketi tarafından üretildi — {self.created_at[:10]}",
            f"",
            f"## Dosyalar ({len(self.files)} adet, {self.total_lines} satır)",
            f"",
        ]
        for f in self.files:
            lines.append(f"- `{f.path}` — {f.description or f.language.value} ({f.line_count()} satır)")
            if f.lint_issues:
                for issue in f.lint_issues[:3]:
                    lines.append(f"  - ⚠️ {issue}")
        lines += ["", f"**Kalite skoru:** {self.quality_score:.0%}", ""]
        if self.review_summary:
            lines += ["## Code Review Özeti", "", self.review_summary]
        return "\n".join(lines)


# ════════════════════════════════════════════════════════
# Proje Şablonları
# ════════════════════════════════════════════════════════

class ProjectTemplate(str, Enum):
    FASTAPI_REST  = "fastapi_rest"
    REACT_SPA     = "react_spa"
    CLI_TOOL      = "cli_tool"
    DATA_PIPELINE = "data_pipeline"
    MICROSERVICE  = "microservice"
    FULLSTACK     = "fullstack"
    CUSTOM        = "custom"


TEMPLATE_SPECS: dict[ProjectTemplate, dict] = {
    ProjectTemplate.FASTAPI_REST: {
        "description": "FastAPI REST API — Router, Model, Repository, Test",
        "files": [
            ("src/main.py",          CodeLanguage.PYTHON),
            ("src/api/routes.py",    CodeLanguage.PYTHON),
            ("src/db/models.py",     CodeLanguage.PYTHON),
            ("src/db/repository.py", CodeLanguage.PYTHON),
            ("src/schemas.py",       CodeLanguage.PYTHON),
            ("tests/test_api.py",    CodeLanguage.PYTHON),
            ("docker-compose.yml",   CodeLanguage.YAML),
            ("README.md",            CodeLanguage.MARKDOWN),
        ],
        "agents": ["architect", "backend_dev", "data_eng", "qa_engineer", "devops", "tech_writer"],
    },
    ProjectTemplate.REACT_SPA: {
        "description": "React + TypeScript SPA — Component, Hook, Store, Test",
        "files": [
            ("src/App.tsx",             CodeLanguage.TYPESCRIPT),
            ("src/components/Main.tsx", CodeLanguage.TYPESCRIPT),
            ("src/hooks/useApi.ts",     CodeLanguage.TYPESCRIPT),
            ("src/store/index.ts",      CodeLanguage.TYPESCRIPT),
            ("src/types/index.ts",      CodeLanguage.TYPESCRIPT),
            ("tests/App.test.tsx",      CodeLanguage.TYPESCRIPT),
            ("package.json",            CodeLanguage.JSON),
            ("README.md",               CodeLanguage.MARKDOWN),
        ],
        "agents": ["architect", "frontend_dev", "qa_engineer", "tech_writer"],
    },
    ProjectTemplate.CLI_TOOL: {
        "description": "Python CLI Aracı — argparse, config, testler",
        "files": [
            ("cli/main.py",      CodeLanguage.PYTHON),
            ("cli/commands.py",  CodeLanguage.PYTHON),
            ("cli/config.py",    CodeLanguage.PYTHON),
            ("cli/utils.py",     CodeLanguage.PYTHON),
            ("tests/test_cli.py",CodeLanguage.PYTHON),
            ("pyproject.toml",   CodeLanguage.TOML if hasattr(CodeLanguage, 'TOML') else CodeLanguage.YAML),
        ],
        "agents": ["architect", "backend_dev", "qa_engineer"],
    },
    ProjectTemplate.DATA_PIPELINE: {
        "description": "Veri Pipeline — ETL, validasyon, raporlama",
        "files": [
            ("pipeline/extract.py",   CodeLanguage.PYTHON),
            ("pipeline/transform.py", CodeLanguage.PYTHON),
            ("pipeline/load.py",      CodeLanguage.PYTHON),
            ("pipeline/validate.py",  CodeLanguage.PYTHON),
            ("pipeline/models.py",    CodeLanguage.PYTHON),
            ("tests/test_pipeline.py",CodeLanguage.PYTHON),
            ("queries/schema.sql",    CodeLanguage.SQL),
        ],
        "agents": ["architect", "data_eng", "backend_dev", "qa_engineer"],
    },
    ProjectTemplate.FULLSTACK: {
        "description": "Full-Stack — FastAPI backend + React frontend",
        "files": [
            ("backend/main.py",          CodeLanguage.PYTHON),
            ("backend/api/routes.py",    CodeLanguage.PYTHON),
            ("backend/db/models.py",     CodeLanguage.PYTHON),
            ("frontend/src/App.tsx",     CodeLanguage.TYPESCRIPT),
            ("frontend/src/api.ts",      CodeLanguage.TYPESCRIPT),
            ("tests/test_backend.py",    CodeLanguage.PYTHON),
            ("docker-compose.yml",       CodeLanguage.YAML),
            ("README.md",               CodeLanguage.MARKDOWN),
        ],
        "agents": ["architect", "backend_dev", "frontend_dev", "data_eng", "qa_engineer", "devops"],
    },
}


# ════════════════════════════════════════════════════════
# Syntax Validator
# ════════════════════════════════════════════════════════

class SyntaxValidator:
    """Üretilen kodu syntax + temel lint kontrolünden geçirir."""

    def validate(self, code_file: CodeFile) -> CodeFile:
        if code_file.language == CodeLanguage.PYTHON:
            self._validate_python(code_file)
        elif code_file.language == CodeLanguage.TYPESCRIPT:
            self._validate_typescript(code_file)
        elif code_file.language == CodeLanguage.SQL:
            self._validate_sql(code_file)
        elif code_file.language == CodeLanguage.JSON:
            self._validate_json(code_file)
        return code_file

    def _validate_python(self, cf: CodeFile):
        # 1. Syntax kontrolü
        try:
            tree = ast.parse(cf.content)
            cf.syntax_ok = True
        except SyntaxError as e:
            cf.syntax_ok = False
            cf.lint_issues.append(f"SyntaxError satır {e.lineno}: {e.msg}")
            # Otomatik düzeltme dene
            cf.content = self._auto_fix_python(cf.content)
            try:
                ast.parse(cf.content)
                cf.syntax_ok = True
                cf.lint_issues.append("⚡ Otomatik düzeltme uygulandı")
            except SyntaxError:
                pass
            return

        # 2. Lint kontrolleri (AST tabanlı)
        issues = []
        for node in ast.walk(tree):
            # bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(f"Satır {node.lineno}: bare 'except:' kullanımı — spesifik exception yakala")
            # print() production'da uyarı
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "print":
                    issues.append(f"Satır {func.lineno}: print() yerine logging kullan")
            # TODO yorumları
        for i, line in enumerate(cf.content.splitlines(), 1):
            if "TODO" in line or "FIXME" in line or "HACK" in line:
                issues.append(f"Satır {i}: '{line.strip()[:60]}' — tamamlanmamış kod")
            # Çok uzun satır
            if len(line) > 120:
                issues.append(f"Satır {i}: {len(line)} karakter (max 120)")

        # 3. Güvenlik kontrolleri
        content_lower = cf.content.lower()
        if "eval(" in content_lower:
            issues.append("🔴 GÜVENLİK: eval() kullanımı tespit edildi")
        if "exec(" in content_lower:
            issues.append("🔴 GÜVENLİK: exec() kullanımı tespit edildi")
        if re.search(r'password\s*=\s*["\'][^"\']+["\']', cf.content, re.I):
            issues.append("🔴 GÜVENLİK: Hardcoded parola tespit edildi — env variable kullan")
        if re.search(r'(api_key|secret)\s*=\s*["\'][a-zA-Z0-9\-_]{16,}["\']', cf.content, re.I):
            issues.append("🔴 GÜVENLİK: Hardcoded API anahtarı — .env kullan")

        cf.lint_issues.extend(issues[:10])  # max 10 uyarı

    def _auto_fix_python(self, code: str) -> str:
        """Basit otomatik düzeltmeler."""
        # Trailing whitespace
        lines = [line.rstrip() for line in code.splitlines()]
        # Eksik newline
        if lines and lines[-1] != "":
            lines.append("")
        return "\n".join(lines)

    def _validate_typescript(self, cf: CodeFile):
        issues = []
        for i, line in enumerate(cf.content.splitlines(), 1):
            if "any" in line and ":" in line and "//" not in line.split(":")[0]:
                issues.append(f"Satır {i}: 'any' tipi kullanımı — spesifik tip tanımla")
            if "console.log" in line:
                issues.append(f"Satır {i}: console.log() — production'da kaldır")
            if len(line) > 120:
                issues.append(f"Satır {i}: {len(line)} karakter (max 120)")
        # var kullanımı
        if re.search(r'\bvar\b', cf.content):
            issues.append("'var' yerine 'const'/'let' kullan (ES6+)")
        cf.lint_issues.extend(issues[:10])

    def _validate_sql(self, cf: CodeFile):
        issues = []
        content_upper = cf.content.upper()
        if "SELECT *" in content_upper:
            issues.append("SELECT * yerine sütun listesi kullan (performans)")
        if "DROP TABLE" in content_upper and "IF EXISTS" not in content_upper:
            issues.append("🔴 DROP TABLE IF EXISTS kullan")
        if "DELETE FROM" in content_upper and "WHERE" not in content_upper:
            issues.append("🔴 WHERE koşulsuz DELETE — tüm tabloyu siler!")
        cf.lint_issues.extend(issues)

    def _validate_json(self, cf: CodeFile):
        import json
        try:
            json.loads(cf.content)
        except json.JSONDecodeError as e:
            cf.syntax_ok = False
            cf.lint_issues.append(f"JSON hata: {e}")


# ════════════════════════════════════════════════════════
# Kod Çıkarıcı — LLM çıktısından kod bloklarını ayır
# ════════════════════════════════════════════════════════

class CodeExtractor:
    """LLM yanıtından ```lang ... ``` bloklarını çıkarır."""

    FENCE_RE = re.compile(
        r'```(\w+)?\s*\n(.*?)```',
        re.DOTALL
    )

    LANG_MAP = {
        "py": CodeLanguage.PYTHON, "python": CodeLanguage.PYTHON,
        "ts": CodeLanguage.TYPESCRIPT, "typescript": CodeLanguage.TYPESCRIPT,
        "tsx": CodeLanguage.TYPESCRIPT, "js": CodeLanguage.TYPESCRIPT,
        "sql": CodeLanguage.SQL, "yml": CodeLanguage.YAML, "yaml": CodeLanguage.YAML,
        "json": CodeLanguage.JSON, "sh": CodeLanguage.BASH, "bash": CodeLanguage.BASH,
        "md": CodeLanguage.MARKDOWN, "markdown": CodeLanguage.MARKDOWN,
        "dockerfile": CodeLanguage.DOCKERFILE,
    }

    def extract(self, text: str, agent_id: str = "", file_path: str = "") -> list[CodeFile]:
        files = []
        for match in self.FENCE_RE.finditer(text):
            lang_hint = (match.group(1) or "").lower()
            code      = match.group(2).strip()

            if not code or len(code) < 10:
                continue

            lang = self.LANG_MAP.get(lang_hint, CodeLanguage.PYTHON)

            # Dosya yolunu tespit et (yorum veya verilen path'den)
            path = file_path or self._detect_path(code, lang, agent_id)

            files.append(CodeFile(
                path=path,
                language=lang,
                content=code,
                agent_id=agent_id,
            ))

        # Kod bloğu yoksa tüm metni Python olarak al (backend_dev için)
        if not files and agent_id in ("backend_dev", "qa_engineer"):
            files.append(CodeFile(
                path=f"generated/{agent_id}.py",
                language=CodeLanguage.PYTHON,
                content=self._clean_as_code(text),
                agent_id=agent_id,
            ))

        return files

    def _detect_path(self, code: str, lang: CodeLanguage, agent_id: str) -> str:
        """Kodun ilk satırından veya agent_id'den dosya yolu çıkar."""
        first_line = code.splitlines()[0] if code else ""

        # # filepath: xxx.py gibi yorum var mı?
        m = re.search(r'#\s*(?:filepath|file|path):\s*(\S+)', first_line, re.I)
        if m:
            return m.group(1)

        # Agent'a göre varsayılan yollar
        defaults = {
            "architect":    f"docs/architecture.md",
            "backend_dev":  f"src/api.py",
            "frontend_dev": f"src/App.tsx",
            "qa_engineer":  f"tests/test_main.py",
            "devops":       f"docker-compose.yml",
            "security":     f"docs/security.md",
            "data_eng":     f"db/schema.sql",
            "tech_writer":  f"README.md",
        }
        ext_default = {
            CodeLanguage.PYTHON:     ".py",
            CodeLanguage.TYPESCRIPT: ".ts",
            CodeLanguage.SQL:        ".sql",
            CodeLanguage.YAML:       ".yml",
            CodeLanguage.JSON:       ".json",
            CodeLanguage.MARKDOWN:   ".md",
            CodeLanguage.BASH:       ".sh",
        }
        base = defaults.get(agent_id, f"generated/{agent_id}")
        if "." not in os.path.basename(base):
            base += ext_default.get(lang, ".txt")
        return base

    def _clean_as_code(self, text: str) -> str:
        """Metin içindeki Markdown işaretlerini temizle."""
        text = re.sub(r'^#{1,6}\s+', '# ', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        return text


# ════════════════════════════════════════════════════════
# Code Planner — hangi dosyalar üretilecek
# ════════════════════════════════════════════════════════

class CodePlanner:
    """Görev + şablona göre ajan-dosya eşlemesi oluşturur."""

    def plan(
        self,
        title: str,
        description: str,
        template: ProjectTemplate = ProjectTemplate.CUSTOM,
    ) -> list[dict]:
        """Her ajan için yapılacak iş döndür."""
        spec = TEMPLATE_SPECS.get(template)
        if not spec:
            return self._custom_plan(title, description)

        tasks = []
        for agent_id in spec["agents"]:
            # Bu ajandan hangi dosyaları üretmesini istiyoruz?
            agent_files = [
                (path, lang) for path, lang in spec["files"]
                if self._agent_owns(agent_id, path, lang)
            ]
            if not agent_files:
                continue

            file_list = "\n".join(f"- {p} ({l.value})" for p, l in agent_files)
            tasks.append({
                "agent_id":   agent_id,
                "files":      agent_files,
                "prompt_extra": (
                    f"Şablon: {template.value}\n"
                    f"Üretmen gereken dosyalar:\n{file_list}\n\n"
                    f"Her dosya için tam, çalışır, production-ready kod yaz. "
                    f"Her dosyayı ``` bloğu içinde, dosya yolunu ilk yorum satırında belirt. "
                    f"Örnek: # filepath: src/api/routes.py\n"
                    f"Kod gereksiz yorum içermemeli, DRY/SOLID prensiplerine uymalı, "
                    f"type annotation kullanmalı ve hata yönetimi eksiksiz olmalı."
                ),
            })
        return tasks

    def _custom_plan(self, title: str, description: str) -> list[dict]:
        """Şablon seçilmemişse tüm ajanları serbest bırak."""
        return [{"agent_id": aid, "files": [], "prompt_extra": (
            "Görev için uygun dosyaları sen belirle ve tam kod üret. "
            "Her dosyayı ``` bloğu içinde, ilk satırda # filepath: yolu/dosya.ext şeklinde belirt. "
            "Kod gereksiz yorum içermemeli, çalışır ve test edilebilir olmalı."
        )} for aid in ["architect", "backend_dev", "frontend_dev", "qa_engineer",
                       "devops", "security", "data_eng", "tech_writer"]]

    def _agent_owns(self, agent_id: str, path: str, lang: CodeLanguage) -> bool:
        ownership = {
            "architect":    lambda p, l: l == CodeLanguage.MARKDOWN or "architecture" in p,
            "backend_dev":  lambda p, l: l == CodeLanguage.PYTHON and "test" not in p,
            "frontend_dev": lambda p, l: l == CodeLanguage.TYPESCRIPT,
            "qa_engineer":  lambda p, l: "test" in p,
            "devops":       lambda p, l: l in (CodeLanguage.YAML, CodeLanguage.DOCKERFILE) or "docker" in p,
            "security":     lambda p, l: "security" in p or "auth" in p,
            "data_eng":     lambda p, l: l == CodeLanguage.SQL or "model" in p,
            "tech_writer":  lambda p, l: l == CodeLanguage.MARKDOWN,
        }
        fn = ownership.get(agent_id)
        return fn(path, lang) if fn else False


# ════════════════════════════════════════════════════════
# Code Review Ajan (9. Ajan)
# ════════════════════════════════════════════════════════

class CodeReviewAgent:
    """
    Üretilen kodu inceleyen 9. ajan.
    - Güvenlik açıkları
    - Performans sorunları
    - Best practice ihlalleri
    - Test coverage değerlendirmesi
    """

    SYSTEM_PROMPT = """Sen kıdemli bir kod inceleme uzmanısın.
Verilen kodu şu açılardan değerlendir:
1. GÜVENLİK: SQL injection, XSS, hardcoded secret, güvensiz deserialization
2. PERFORMANS: N+1 query, gereksiz döngü, bellek sızıntısı
3. BEST PRACTICE: SOLID, DRY, hata yönetimi, loglama
4. TEST: Test kapsamı yeterli mi, edge case'ler var mı
5. DOKÜMANTASyon: Type hint, docstring, açıklamalar yeterli mi

Her sorun için: [SORUN_TIPI] Satır/Bölüm: Açıklama -> Öneri formatını kullan.
En sonda 0-10 arası puan ver: PUAN: X/10"""

    def __init__(self, model_orch):
        self.model_orch = model_orch

    async def review(self, result: CodeGenerationResult) -> CodeGenerationResult:
        """Üretilen tüm dosyaları toplu incele."""
        if not result.files:
            return result

        # Önemli dosyaları seç (max 4, Python/TS öncelikli)
        priority = [f for f in result.files
                    if f.language in (CodeLanguage.PYTHON, CodeLanguage.TYPESCRIPT)
                    and f.syntax_ok][:4]

        if not priority:
            return result

        # Toplu review prompt'u oluştur
        code_blocks = "\n\n".join([
            f"### {f.path}\n```{f.language.value}\n{f.content[:2000]}\n```"
            for f in priority
        ])

        prompt = (
            f"Proje: {result.title}\n\n"
            f"İncelenecek dosyalar:\n\n{code_blocks}\n\n"
            f"Kapsamlı kod incelemesi yap."
        )

        try:
            review_text = await self.model_orch.complete(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=1200,
            )

            # Puanı parse et
            score_match = re.search(r'PUAN:\s*(\d+(?:\.\d+)?)\s*/\s*10', review_text)
            if score_match:
                result.quality_score = float(score_match.group(1)) / 10.0

            result.review_summary = review_text

            # Dosya bazlı yorumları dağıt
            for cf in priority:
                cf.review_notes = self._extract_notes_for_file(review_text, cf.filename)

        except Exception as e:
            result.review_summary = f"Code review başarısız: {e}"

        return result

    def _extract_notes_for_file(self, review_text: str, filename: str) -> list[str]:
        """Review metninden bu dosyaya ait notları çıkar."""
        notes = []
        lines = review_text.splitlines()
        in_section = False
        for line in lines:
            if filename in line:
                in_section = True
            elif in_section and line.startswith("###"):
                break
            elif in_section and line.strip().startswith("["):
                notes.append(line.strip())
        return notes[:5]


# ════════════════════════════════════════════════════════
# Ana Kod Üretim Motoru
# ════════════════════════════════════════════════════════

class CodeGenerationEngine:
    """
    Tüm pipeline'ı yönetir:
    plan -> generate -> validate -> review -> assemble
    """

    def __init__(self, model_orch):
        self.model_orch  = model_orch
        self.planner     = CodePlanner()
        self.extractor   = CodeExtractor()
        self.validator   = SyntaxValidator()
        self.reviewer    = CodeReviewAgent(model_orch)

        # In-memory sonuç deposu (DB'ye de yazılır)
        self._results: dict[str, CodeGenerationResult] = {}

    async def generate(
        self,
        title:       str,
        description: str,
        template:    ProjectTemplate = ProjectTemplate.CUSTOM,
        agents:      dict | None = None,  # agent_id -> Agent map
        event_bus=None,
        project_id:  str | None = None,
    ) -> CodeGenerationResult:
        """Ana üretim pipeline'ı."""
        result_id = project_id or str(uuid.uuid4())[:8]
        result = CodeGenerationResult(
            project_id=result_id,
            title=title,
            files=[],
        )

        # 1. Plan
        tasks = self.planner.plan(title, description, template)

        if event_bus:
            await event_bus.emit(
                "code.started",
                project_id=result_id, title=title, template=template.value,
                agent_count=len(tasks), severity="info",
                phase="codegen", message=f"Kod üretimi başladı: {title}",
            )

        # 1.5. Hemen listeye ekle (takip edilebilmesi için)
        self._results[result_id] = result

        try:
            # 2. Paralel kod üretimi
            semaphore = asyncio.Semaphore(4)  # max 4 eş zamanlı

            async def generate_for_agent(task: dict):
                async with semaphore:
                    return await self._generate_agent_code(
                        task, title, description, agents, event_bus, result_id
                    )

            agent_results = await asyncio.gather(
                *[generate_for_agent(t) for t in tasks],
                return_exceptions=True,
            )

            # 3. Tüm dosyaları topla
            seen_paths = set()
            error_msgs = []
            for res in agent_results:
                if isinstance(res, list):
                    for cf in res:
                        # Çakışan path'leri çöz
                        if cf.path in seen_paths:
                            base, ext = os.path.splitext(cf.path)
                            cf.path = f"{base}_{cf.agent_id}{ext}"
                        seen_paths.add(cf.path)
                        result.files.append(cf)
                elif isinstance(res, Exception):
                    msg = str(res)
                    error_msgs.append(msg)
                    logger.error(f"Ajan üretim hatası: {msg}")

            # Kritik Kontrol: Eğer hiç dosya üretilmediyse ve hatalar varsa "failed" işaretle
            if not result.files and error_msgs:
                raise RuntimeError(f"Hiçbir ajan kod üretemedi. Sonuç 0 dosya. Hatalar: {'; '.join(set(error_msgs))[:500]}")

            # 4. Syntax validation
            result.files = [self.validator.validate(cf) for cf in result.files]

            # 5. Code review
            try:
                result = await self.reviewer.review(result)
            except Exception:
                pass

            # 6. Sonuçları güncelle
            result.status = "completed"
            result.__post_init__()

            if event_bus:
                await event_bus.emit(
                    "code.completed",
                    project_id=result_id, title=title,
                    file_count=len(result.files),
                    total_lines=result.total_lines,
                    quality_score=result.quality_score,
                    severity="resolved", phase="codegen",
                    message=f"Kod üretimi tamamlandı: {len(result.files)} dosya, {result.total_lines} satır",
                )

        except Exception as e:
            logger.error(f"Kod üretiminde kritik hata: {e}")
            result.status = "failed"
            result.error  = str(e)
            if event_bus:
                await event_bus.emit(
                    "code.failed",
                    project_id=result_id, title=title,
                    error=str(e), severity="critical", phase="codegen",
                    message=f"Kod üretimi başarısız: {e}",
                )

        return result

    async def _generate_agent_code(
        self,
        task: dict,
        title: str,
        description: str,
        agents: dict | None,
        event_bus,
        result_id: str,
    ) -> list[CodeFile]:
        """Tek ajan için kod üret."""
        agent_id   = task["agent_id"]
        agent      = agents.get(agent_id) if agents else None
        system_msg = agent.system_prompt if agent else f"Sen {agent_id} rolünde bir uzman geliştiricisisin."

        prompt = (
            f"Proje: {title}\n"
            f"Açıklama: {description}\n\n"
            f"{task.get('prompt_extra', '')}\n\n"
            f"Önemli kurallar:\n"
            f"- Her dosyayı ``` bloğu içinde yaz\n"
            f"- İlk satır: # filepath: klasör/dosya.uzantı\n"
            f"- Sadece kod yaz, uzun açıklama ekleme\n"
            f"- Type annotation kullan\n"
            f"- Hata yönetimi ekle\n"
            f"- TODO bırakma, tamamlanmış kod üret"
        )

        if event_bus:
            await event_bus.emit(
                "code.agent_start",
                project_id=result_id, agent_id=agent_id,
                severity="info", phase="codegen",
                message=f"{agent_id} kod üretiyor...",
            )

        raw = await self.model_orch.complete(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=2000,
            preferred_agent=agent_id,
        )

        files = self.extractor.extract(raw, agent_id=agent_id)

        if event_bus:
            await event_bus.emit(
                "code.agent_done",
                project_id=result_id, agent_id=agent_id,
                file_count=len(files),
                severity="info", phase="codegen",
                message=f"{agent_id} tamamlandı: {len(files)} dosya",
            )

        return files

    def get_result(self, project_id: str) -> CodeGenerationResult | None:
        return self._results.get(project_id)

    def list_results(self) -> list[dict]:
        return [
            {
                "project_id": r.project_id,
                "title":      r.title,
                "files":      len(r.files),
                "lines":      r.total_lines,
                "languages":  r.languages,
                "quality":    r.quality_score,
                "created_at": r.created_at,
            }
            for r in sorted(
                self._results.values(),
                key=lambda x: x.created_at,
                reverse=True,
            )
        ]


# ── Singleton ─────────────────────────────────────────────
_engine: CodeGenerationEngine | None = None


def get_code_engine() -> CodeGenerationEngine | None:
    """Kod motoruna eriş. Eğer başlatılmadıysa lazily ve agresif bir şekilde oluştur."""
    global _engine
    if _engine is None:
        try:
            # 1. Yol: Ana orkestratörden almayı dene
            try:
                from core.context import orchestrator
                if orchestrator and hasattr(orchestrator, 'model_orch'):
                    return init_code_engine(orchestrator.model_orch)
            except Exception:
                pass

            # 2. Yol: Kendi ModelOrchestrator'ını oluştur (Bağımsız çalışabilsin)
            from llm.model_orchestrator import ModelOrchestrator
            return init_code_engine(ModelOrchestrator())
        except Exception as e:
            logger.error(f"Kod motoru otomatik başlatılamadı: {e}")
    return _engine


def init_code_engine(model_orch) -> CodeGenerationEngine:
    global _engine
    if _engine is None:
        _engine = CodeGenerationEngine(model_orch)
        logger.info("CodeGenerationEngine initialized successfully.")
    return _engine
