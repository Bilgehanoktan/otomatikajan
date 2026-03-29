"""
Code Review Ajan (9. Ajan) — Faz 6
════════════════════════════════════════════════════════
Üretilen kodu sadece analiz etmez — DÜZELTIR de.

Pipeline:
  1. Statik analiz (AST + regex tabanlı, offline)
  2. LLM destekli derin inceleme
  3. Otomatik yeniden yazma (auto-fix modu)
  4. Kalite skoru & detaylı rapor

Kullanım:
  engine = CodeReviewEngine(model_orch)
  report = await engine.review_project(code_result)
  fixed  = await engine.auto_fix(code_file)
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from code_engine import CodeGenerationResult, CodeFile


# ════════════════════════════════════════════════════════
# Bulgu Tipleri
# ════════════════════════════════════════════════════════

class FindingSeverity(str, Enum):
    INFO     = "info"
    WARNING  = "warning"
    ERROR    = "error"
    CRITICAL = "critical"


class FindingCategory(str, Enum):
    SECURITY      = "security"
    PERFORMANCE   = "performance"
    CLEAN_CODE    = "clean_code"
    TESTABILITY   = "testability"
    DOCUMENTATION = "documentation"
    LOGIC         = "logic"


@dataclass
class Finding:
    category: FindingCategory
    severity: FindingSeverity
    line:     int | None
    message:  str
    fix:      str = ""          # Önerilen düzeltme
    auto_fixable: bool = False  # Otomatik düzeltildi mi

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "line":     self.line,
            "message":  self.message,
            "fix":      self.fix,
            "auto_fixable": self.auto_fixable,
        }

    def __str__(self) -> str:
        loc = f" [satır {self.line}]" if self.line else ""
        return f"[{self.severity.value.upper()}] {self.category.value}{loc}: {self.message}"


@dataclass
class FileReviewResult:
    path:       str
    language:   str
    findings:   list[Finding]  = field(default_factory=list)
    score:      float          = 1.0    # 0.0 - 1.0
    fixed:      bool           = False
    original:   str            = ""
    fixed_code: str            = ""

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.CRITICAL)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == FindingSeverity.WARNING)

    def calculate_score(self) -> float:
        """Bulgulara göre 0-1 skor hesapla."""
        penalty = (
            self.critical_count * 0.25 +
            self.error_count    * 0.10 +
            self.warning_count  * 0.03
        )
        self.score = max(0.0, 1.0 - penalty)
        return self.score

    def to_dict(self) -> dict:
        return {
            "path":          self.path,
            "language":      self.language,
            "score":         round(self.score, 3),
            "fixed":         self.fixed,
            "critical":      self.critical_count,
            "errors":        self.error_count,
            "warnings":      self.warning_count,
            "findings":      [f.to_dict() for f in self.findings],
        }


@dataclass
class ProjectReviewReport:
    project_id:    str
    title:         str
    file_results:  list[FileReviewResult] = field(default_factory=list)
    overall_score: float = 0.0
    llm_summary:   str   = ""
    auto_fixed:    int   = 0

    def calculate_overall(self) -> float:
        if not self.file_results:
            return 0.0
        self.overall_score = sum(r.score for r in self.file_results) / len(self.file_results)
        return self.overall_score

    def to_dict(self) -> dict:
        return {
            "project_id":    self.project_id,
            "title":         self.title,
            "overall_score": round(self.overall_score, 3),
            "file_count":    len(self.file_results),
            "auto_fixed":    self.auto_fixed,
            "llm_summary":   self.llm_summary,
            "files":         [r.to_dict() for r in self.file_results],
        }


# ════════════════════════════════════════════════════════
# Statik Analizörler
# ════════════════════════════════════════════════════════

class PythonStaticAnalyzer:
    """AST + regex tabanlı Python analizi — LLM gerektirmez."""

    # Güvenlik desenleri
    SECURITY_PATTERNS = [
        (r'\beval\s*\(',         "eval() RCE riski — safeliterals veya ast.literal_eval kullan",  FindingSeverity.CRITICAL),
        (r'\bexec\s*\(',         "exec() RCE riski — kaldır",                                    FindingSeverity.CRITICAL),
        (r'subprocess\.call\(.+shell\s*=\s*True',  "shell=True komut injection riski",           FindingSeverity.CRITICAL),
        (r'password\s*=\s*["\'][^"\']{3,}["\']',   "Hardcoded parola — os.getenv() kullan",      FindingSeverity.CRITICAL),
        (r'(api_key|secret|token)\s*=\s*["\'][a-zA-Z0-9\-_]{10,}["\']',
                                 "Hardcoded gizli anahtar — .env kullan",                         FindingSeverity.CRITICAL),
        (r'pickle\.loads?\(',    "pickle.load() arbitrary code execution riski",                  FindingSeverity.ERROR),
        (r'hashlib\.md5\(',      "MD5 kırılabilir — SHA-256 kullan",                              FindingSeverity.WARNING),
        (r'random\.random\(',    "random kriptografik olarak güvensiz — secrets modülü kullan",   FindingSeverity.WARNING),
        (r'http://',             "HTTP yerine HTTPS kullan",                                       FindingSeverity.WARNING),
    ]

    # Temiz kod desenleri
    CLEAN_CODE_PATTERNS = [
        (r'\bprint\s*\(',        "print() yerine logging kullan",          FindingSeverity.WARNING),
        (r'#\s*TODO',            "TODO tamamlanmamış — bitir veya issue aç", FindingSeverity.WARNING),
        (r'#\s*FIXME',           "FIXME düzeltilmemiş kod",                FindingSeverity.ERROR),
        (r'#\s*HACK',            "HACK geçici çözüm — düzgün yap",         FindingSeverity.WARNING),
        (r'\btime\.sleep\(',     "sync sleep — asyncio.sleep kullan",       FindingSeverity.WARNING),
    ]

    def analyze(self, cf: "CodeFile") -> FileReviewResult:
        from code_engine import CodeLanguage
        result = FileReviewResult(
            path=cf.path,
            language=cf.language.value,
            original=cf.content,
        )

        lines = cf.content.splitlines()

        # 1. Regex tabanlı kontroller
        for pattern, message, severity in self.SECURITY_PATTERNS + self.CLEAN_CODE_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.I):
                    cat = (FindingCategory.SECURITY
                           if (pattern, message, severity) in self.SECURITY_PATTERNS
                           else FindingCategory.CLEAN_CODE)
                    result.findings.append(Finding(
                        category=cat,
                        severity=severity,
                        line=i,
                        message=message,
                    ))

        # 2. Satır uzunluğu
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                result.findings.append(Finding(
                    category=FindingCategory.CLEAN_CODE,
                    severity=FindingSeverity.WARNING,
                    line=i,
                    message=f"Satır {len(line)} karakter (max 100)",
                    fix="Satırı bol — parantez içi wrap kullan",
                    auto_fixable=False,
                ))

        # 3. AST tabanlı kontroller
        try:
            tree = ast.parse(cf.content)
            self._ast_checks(tree, result)
        except SyntaxError as e:
            result.findings.append(Finding(
                category=FindingCategory.LOGIC,
                severity=FindingSeverity.CRITICAL,
                line=e.lineno,
                message=f"Syntax hatası: {e.msg}",
                fix="Kodu düzelt",
            ))

        result.calculate_score()
        return result

    def _ast_checks(self, tree: ast.AST, result: FileReviewResult):
        """AST düğümlerini gez, anti-pattern tespit et."""
        for node in ast.walk(tree):

            # bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                result.findings.append(Finding(
                    category=FindingCategory.CLEAN_CODE,
                    severity=FindingSeverity.ERROR,
                    line=node.lineno,
                    message="bare 'except:' — spesifik exception belirt (except ValueError as e:)",
                    fix="except Exception as e:",
                    auto_fixable=True,
                ))

            # Çok uzun fonksiyon (>35 satır)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_lines = (node.end_lineno or node.lineno) - node.lineno
                if body_lines > 35:
                    result.findings.append(Finding(
                        category=FindingCategory.CLEAN_CODE,
                        severity=FindingSeverity.WARNING,
                        line=node.lineno,
                        message=f"'{node.name}' fonksiyonu {body_lines} satır (max 35) — parçala",
                        fix="Single Responsibility: her fonksiyon tek iş yapmalı",
                    ))

                # Type annotation eksikliği
                missing_return = node.returns is None
                missing_args   = any(
                    a.annotation is None
                    for a in node.args.args
                    if a.arg != "self"
                )
                if missing_return or missing_args:
                    result.findings.append(Finding(
                        category=FindingCategory.DOCUMENTATION,
                        severity=FindingSeverity.WARNING,
                        line=node.lineno,
                        message=f"'{node.name}' tip annotation eksik",
                        fix="def foo(x: int, y: str) -> bool: şeklinde ekle",
                        auto_fixable=False,
                    ))

                # Docstring eksikliği
                has_docstring = (
                    node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                )
                if not has_docstring and body_lines > 5:
                    result.findings.append(Finding(
                        category=FindingCategory.DOCUMENTATION,
                        severity=FindingSeverity.INFO,
                        line=node.lineno,
                        message=f"'{node.name}' docstring yok",
                        fix='"""Kısa açıklama.""" ekle',
                    ))

            # Magic number
            if isinstance(node, ast.Constant) and isinstance(node.value, int):
                if node.value not in (0, 1, -1, 2, 100, 200, 404, 500):
                    if hasattr(node, 'lineno') and node.value > 9:
                        result.findings.append(Finding(
                            category=FindingCategory.CLEAN_CODE,
                            severity=FindingSeverity.INFO,
                            line=node.lineno,
                            message=f"Magic number {node.value} — sabit tanımla",
                            fix=f"MAX_VALUE = {node.value}  # dosya başında",
                            auto_fixable=False,
                        ))


class TypeScriptStaticAnalyzer:
    """TypeScript/TSX statik analizi."""

    PATTERNS = [
        (r':\s*any\b',           "any tipi — spesifik tip tanımla",          FindingSeverity.WARNING,  FindingCategory.CLEAN_CODE),
        (r'\bvar\s+\w',          "var yerine const/let kullan (ES6+)",        FindingSeverity.ERROR,    FindingCategory.CLEAN_CODE),
        (r'console\.(log|warn)', "console.log kaldır — logger kullan",        FindingSeverity.WARNING,  FindingCategory.CLEAN_CODE),
        (r'@ts-ignore',          "@ts-ignore — tipi düzelt",                  FindingSeverity.ERROR,    FindingCategory.CLEAN_CODE),
        (r'as any',              "as any tip güvenliğini kırar",              FindingSeverity.WARNING,  FindingCategory.CLEAN_CODE),
        (r'localStorage\.',      "localStorage XSS riski — httpOnly cookie",  FindingSeverity.WARNING,  FindingCategory.SECURITY),
        (r'dangerouslySetInnerHTML', "XSS riski — sanitize et",               FindingSeverity.CRITICAL, FindingCategory.SECURITY),
        (r'#\s*TODO',            "TODO tamamlanmamış",                        FindingSeverity.WARNING,  FindingCategory.CLEAN_CODE),
    ]

    def analyze(self, cf: "CodeFile") -> FileReviewResult:
        result = FileReviewResult(path=cf.path, language=cf.language.value, original=cf.content)
        lines  = cf.content.splitlines()

        for pattern, message, severity, category in self.PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    result.findings.append(Finding(
                        category=category, severity=severity, line=i, message=message,
                    ))

        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                result.findings.append(Finding(
                    category=FindingCategory.CLEAN_CODE,
                    severity=FindingSeverity.WARNING,
                    line=i,
                    message=f"Satır {len(line)} karakter (max 120)",
                ))

        result.calculate_score()
        return result


# ════════════════════════════════════════════════════════
# Otomatik Düzeltici
# ════════════════════════════════════════════════════════

class AutoFixer:
    """Tespit edilen sorunları otomatik düzeltir."""

    def fix_python(self, code: str, findings: list[Finding]) -> tuple[str, int]:
        """Python kodunu otomatik düzelt. (fixed_code, fix_count) döndür."""
        fixed = code
        count = 0

        # 1. bare except -> except Exception as e:
        bare_except_re = re.compile(r'^(\s*)except\s*:', re.MULTILINE)
        if bare_except_re.search(fixed):
            fixed = bare_except_re.sub(r'\1except Exception as e:', fixed)
            count += bare_except_re.subn(r'\1except Exception as e:', code)[1]

        # 2. print( -> logger.info( (en yaygın form)
        print_re = re.compile(r'\bprint\((.+?)\)', re.DOTALL)
        if print_re.search(fixed):
            # logging import ekle (yoksa)
            if "import logging" not in fixed and "from logging" not in fixed:
                fixed = "import logging\nlogger = logging.getLogger(__name__)\n\n" + fixed
            fixed = print_re.sub(r'logger.info(\1)', fixed)
            count += 1

        # 3. Trailing whitespace kaldır
        lines = [line.rstrip() for line in fixed.splitlines()]
        fixed = "\n".join(lines)

        # 4. Dosya sonu newline
        if fixed and not fixed.endswith("\n"):
            fixed += "\n"
            count += 1

        # 5. Çok fazla boş satır (3+) -> 2'ye indir
        fixed = re.sub(r'\n{4,}', '\n\n\n', fixed)

        return fixed, count

    def fix_typescript(self, code: str) -> tuple[str, int]:
        fixed = code
        count = 0

        # var -> let (const daha güvenli ama mevcut koda dokunmayalım)
        var_re = re.compile(r'\bvar\b')
        if var_re.search(fixed):
            fixed = var_re.sub('let', fixed)
            count += var_re.subn('let', code)[1]

        # Trailing whitespace
        lines = [line.rstrip() for line in fixed.splitlines()]
        fixed = "\n".join(lines)
        if fixed and not fixed.endswith("\n"):
            fixed += "\n"

        return fixed, count


# ════════════════════════════════════════════════════════
# LLM Destekli Derin İnceleme
# ════════════════════════════════════════════════════════

_REVIEW_SYSTEM = """Sen kıdemli bir kod inceleme uzmanısın. 
Verilen kodu derinlemesine incele:
1. GÜVENLİK: SQL injection, XSS, SSRF, hardcoded secret, güvensiz deserialization
2. PERFORMANS: N+1 query, senkron I/O, gereksiz bellek kullanımı, önbellekleme fırsatı  
3. MANTIK HATASI: Yanlış koşullar, off-by-one, null kontrolü eksikliği
4. OKUNABILIRLIK: İsim kalitesi, karmaşıklık, tekrar eden kod

Format: Her bulgu için ->
[KATEGORİ] Satır X: Problem açıklaması | Düzeltme önerisi

Sonunda: GENEL PUAN: X/10 (sadece sayı)"""


class LLMReviewer:
    """LLM ile derin kod incelemesi."""

    def __init__(self, model_orch):
        self.model_orch = model_orch

    async def review_file(self, cf: "CodeFile") -> str:
        """Tek dosya için LLM review — ham metin döndür."""
        snippet = cf.content[:3000]  # token limit
        prompt  = f"Dosya: {cf.path}\n\n```{cf.language.value}\n{snippet}\n```"

        try:
            return await self.model_orch.complete(
                messages=[
                    {"role": "system", "content": _REVIEW_SYSTEM},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=1000,
            )
        except Exception as e:
            return f"LLM review başarısız: {e}"

    async def review_project_summary(
        self,
        title: str,
        file_results: list[FileReviewResult],
    ) -> str:
        """Tüm proje için özet inceleme."""
        critical = sum(r.critical_count for r in file_results)
        errors   = sum(r.error_count    for r in file_results)
        avg      = sum(r.score          for r in file_results) / max(len(file_results), 1)

        summary = (
            f"Proje: {title}\n"
            f"Dosya sayısı: {len(file_results)}\n"
            f"Ortalama skor: {avg:.0%}\n"
            f"Kritik bulgu: {critical}, Hata: {errors}\n\n"
            f"En düşük skorlu dosyalar:\n"
        )
        for r in sorted(file_results, key=lambda x: x.score)[:3]:
            summary += f"- {r.path} ({r.score:.0%}): {r.critical_count} kritik\n"

        try:
            return await self.model_orch.complete(
                messages=[
                    {"role": "system", "content": "Sen kod kalitesi danışmanısın. Özet ve aksiyonlar üret."},
                    {"role": "user",   "content": summary + "\nBu projenin güçlü/zayıf yanları ve öncelikli düzeltmeler?"},
                ],
                max_tokens=600,
            )
        except Exception as e:
            return f"Özet oluşturulamadı: {e}"


# ════════════════════════════════════════════════════════
# Ana Code Review Engine
# ════════════════════════════════════════════════════════

class CodeReviewEngine:
    """
    9. Ajan — Kod inceleme ve otomatik düzeltme.
    Statik analiz (hızlı, offline) + LLM (derin).
    """

    def __init__(self, model_orch):
        self.py_analyzer  = PythonStaticAnalyzer()
        self.ts_analyzer  = TypeScriptStaticAnalyzer()
        self.auto_fixer   = AutoFixer()
        self.llm_reviewer = LLMReviewer(model_orch)

    async def review_project(
        self,
        code_result: "CodeGenerationResult",
        auto_fix:    bool = True,
        llm_depth:   bool = True,
    ) -> ProjectReviewReport:
        """Tüm projeyi incele + isteğe bağlı otomatik düzelt."""
        from code_engine import CodeLanguage

        report = ProjectReviewReport(
            project_id=code_result.project_id,
            title=code_result.title,
        )

        for cf in code_result.files:
            # 1. Statik analiz
            if cf.language == CodeLanguage.PYTHON:
                file_result = self.py_analyzer.analyze(cf)
            elif cf.language == CodeLanguage.TYPESCRIPT:
                file_result = self.ts_analyzer.analyze(cf)
            else:
                file_result = FileReviewResult(
                    path=cf.path, language=cf.language.value, score=1.0
                )

            # 2. Otomatik düzeltme
            if auto_fix and cf.language == CodeLanguage.PYTHON:
                fixed_code, n = self.auto_fixer.fix_python(cf.content, file_result.findings)
                if n > 0 and fixed_code != cf.content:
                    file_result.fixed      = True
                    file_result.fixed_code = fixed_code
                    cf.content             = fixed_code  # orijinali güncelle
                    report.auto_fixed     += 1

            elif auto_fix and cf.language == CodeLanguage.TYPESCRIPT:
                fixed_code, n = self.auto_fixer.fix_typescript(cf.content)
                if n > 0:
                    file_result.fixed      = True
                    file_result.fixed_code = fixed_code
                    cf.content             = fixed_code
                    report.auto_fixed     += 1

            report.file_results.append(file_result)

        # 3. LLM derin inceleme (sadece en kritik dosyalar)
        if llm_depth:
            priority = sorted(report.file_results, key=lambda r: r.score)[:2]
            for fr in priority:
                cf = next((f for f in code_result.files if f.path == fr.path), None)
                if cf:
                    llm_text = await self.llm_reviewer.review_file(cf)
                    # LLM bulgularını parse et
                    llm_findings = self._parse_llm_findings(llm_text)
                    fr.findings.extend(llm_findings)
                    fr.calculate_score()

            report.llm_summary = await self.llm_reviewer.review_project_summary(
                code_result.title, report.file_results
            )

        report.calculate_overall()
        # code_result'a skoru yansıt
        code_result.quality_score  = report.overall_score
        code_result.review_summary = report.llm_summary

        return report

    def _parse_llm_findings(self, text: str) -> list[Finding]:
        """LLM çıktısından bulguları parse et."""
        findings = []
        line_re  = re.compile(
            r'\[(GÜVENLİK|PERFORMANS|MANTIK|OKUNAB|SECURITY|PERF|LOGIC|CLEAN)\]'
            r'\s*(?:Satır\s*(\d+))?[:\s]*(.+?)(?:\|(.+))?$',
            re.I
        )
        cat_map = {
            "güvenlik": FindingCategory.SECURITY, "security": FindingCategory.SECURITY,
            "performans": FindingCategory.PERFORMANCE, "perf": FindingCategory.PERFORMANCE,
            "mantik": FindingCategory.LOGIC, "logic": FindingCategory.LOGIC,
            "okunab": FindingCategory.CLEAN_CODE, "clean": FindingCategory.CLEAN_CODE,
        }

        for line in text.splitlines():
            m = line_re.search(line)
            if m:
                cat_key = m.group(1).lower()
                cat     = cat_map.get(cat_key, FindingCategory.CLEAN_CODE)
                lineno  = int(m.group(2)) if m.group(2) else None
                message = m.group(3).strip() if m.group(3) else line[:120]
                fix_sug = m.group(4).strip() if m.group(4) else ""

                severity = FindingSeverity.WARNING
                if any(w in message.lower() for w in ("kritik", "critical", "injection", "rce")):
                    severity = FindingSeverity.CRITICAL
                elif any(w in message.lower() for w in ("hata", "error", "yasak")):
                    severity = FindingSeverity.ERROR

                findings.append(Finding(
                    category=cat, severity=severity, line=lineno,
                    message=message, fix=fix_sug,
                ))

        return findings[:15]  # max 15 LLM bulgusu
