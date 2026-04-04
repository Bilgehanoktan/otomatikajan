"""
Faz 6 Test Paketi — Kod Üretim Motoru & Temiz Kod
══════════════════════════════════════════════════
Çalıştır: python tests/test_faz6.py
"""
import asyncio
import io
import sys
import zipfile

sys.path.insert(0, ".")

PASS = []
FAIL = []


def ok(name):
    PASS.append(name)
    print(f"  ✅ {name}")


def fail(name, err):
    FAIL.append(name)
    print(f"  ❌ {name}: {err}")


# ─── 1. Agent Registry — temiz kod sözleşmesi ─────────────

def test_agent_clean_code_contract():
    from agents.agent_registry import build_agents
    agents = build_agents()
    assert len(agents) == 8, f"8 ajan beklendi, {len(agents)} var"
    for aid, agent in agents.items():
        assert "ZORUNLU" in agent.system_prompt, f"{aid} temiz kod sözleşmesi eksik"
        assert "YASAK" in agent.system_prompt,   f"{aid} yasak listesi eksik"
        assert "eval" in agent.system_prompt,     f"{aid} eval uyarısı eksik"
    ok("agent_registry: 8 ajan + temiz kod sözleşmesi")


# ─── 2. SyntaxValidator ───────────────────────────────────

def test_syntax_validator_python():
    from code_engine import SyntaxValidator, CodeFile, CodeLanguage
    v = SyntaxValidator()

    # Güvenlik sorunları olan kod
    bad = CodeFile(path="bad.py", language=CodeLanguage.PYTHON, content="""
import os
def foo():
    print("debug")
    try:
        x = 1
    except:
        pass
    eval("x+1")
    password = "s3cr3t123"
""")
    result = v.validate(bad)
    assert result.syntax_ok, "syntax geçerli olmalı"
    assert any("eval" in i for i in result.lint_issues), "eval uyarısı beklendi"
    assert any("parola" in i.lower() or "hardcoded" in i.lower() for i in result.lint_issues), "hardcoded parola uyarısı beklendi"
    ok(f"SyntaxValidator Python: {len(result.lint_issues)} sorun tespit edildi")


def test_syntax_validator_broken_python():
    from code_engine import SyntaxValidator, CodeFile, CodeLanguage
    v = SyntaxValidator()
    broken = CodeFile(path="broken.py", language=CodeLanguage.PYTHON, content="def foo(\n  x: int\n  return x")
    result = v.validate(broken)
    assert not result.syntax_ok or len(result.lint_issues) > 0
    ok("SyntaxValidator: bozuk Python tespit edildi")


def test_syntax_validator_typescript():
    from code_engine import SyntaxValidator, CodeFile, CodeLanguage
    v = SyntaxValidator()
    ts = CodeFile(path="app.ts", language=CodeLanguage.TYPESCRIPT, content="""
var x: any = 1;
console.log(x);
// @ts-ignore
const y = x as any;
""")
    result = v.validate(ts)
    assert len(result.lint_issues) >= 3, f"en az 3 uyarı beklendi, {len(result.lint_issues)} var"
    ok(f"SyntaxValidator TypeScript: {len(result.lint_issues)} sorun")


def test_syntax_validator_sql():
    from code_engine import SyntaxValidator, CodeFile, CodeLanguage
    v = SyntaxValidator()
    sql = CodeFile(path="q.sql", language=CodeLanguage.SQL, content="SELECT * FROM users; DELETE FROM orders;")
    result = v.validate(sql)
    assert any("SELECT *" in i or "select" in i.lower() for i in result.lint_issues), "SELECT * uyarısı beklendi"
    assert any("DELETE" in i or "WHERE" in i for i in result.lint_issues), "WHERE koşulsuz DELETE uyarısı beklendi"
    ok(f"SyntaxValidator SQL: {len(result.lint_issues)} sorun")


def test_syntax_validator_clean_code():
    from code_engine import SyntaxValidator, CodeFile, CodeLanguage
    v = SyntaxValidator()
    clean = CodeFile(path="clean.py", language=CodeLanguage.PYTHON, content="""
import logging

logger = logging.getLogger(__name__)

MAX_RETRIES: int = 3


def fetch_user(user_id: int) -> dict:
    \"\"\"Veritabanından kullanıcı çek.\"\"\"
    try:
        return {"id": user_id}
    except ValueError as e:
        logger.error("Kullanıcı bulunamadı: %s", e)
        raise
""")
    result = v.validate(clean)
    assert result.syntax_ok
    critical = [i for i in result.lint_issues if "GÜVENLİK" in i or "CRITICAL" in i.upper()]
    assert len(critical) == 0, f"Temiz kodda kritik uyarı olmamalı: {critical}"
    ok("SyntaxValidator: temiz kod sorunsuz geçti")


# ─── 3. CodeExtractor ─────────────────────────────────────

def test_code_extractor_python():
    from code_engine import CodeExtractor, CodeLanguage
    ex = CodeExtractor()
    text = """
Burada backend kodu:
```python
# filepath: src/api/routes.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root() -> dict:
    return {"status": "ok"}
```
"""
    files = ex.extract(text, agent_id="backend_dev")
    assert len(files) == 1
    assert files[0].language == CodeLanguage.PYTHON
    assert files[0].path == "src/api/routes.py"
    assert "FastAPI" in files[0].content
    ok(f"CodeExtractor Python: path='{files[0].path}' tespit edildi")


def test_code_extractor_multiple():
    from code_engine import CodeExtractor, CodeLanguage
    ex = CodeExtractor()
    text = """
```python
# filepath: backend/main.py
from fastapi import FastAPI
```
```typescript
// filepath: frontend/App.tsx
import React from 'react';
```
```yaml
# filepath: docker-compose.yml
version: '3'
```
"""
    files = ex.extract(text)
    assert len(files) == 3
    langs = {f.language for f in files}
    assert CodeLanguage.PYTHON in langs
    assert CodeLanguage.TYPESCRIPT in langs
    assert CodeLanguage.YAML in langs
    ok(f"CodeExtractor çoklu dil: {len(files)} dosya, {len(langs)} dil")


def test_code_extractor_no_filepath():
    from code_engine import CodeExtractor, CodeLanguage
    ex = CodeExtractor()
    text = "```python\nprint('hello')\n```"
    files = ex.extract(text, agent_id="backend_dev")
    assert len(files) == 1
    assert files[0].path  # path boş olmamalı
    ok(f"CodeExtractor: filepath yoksa varsayılan oluşturuldu: {files[0].path}")


# ─── 4. AutoFixer ─────────────────────────────────────────

def test_auto_fixer_bare_except():
    from agents.code_reviewer import AutoFixer
    fixer = AutoFixer()
    code = """
def foo():
    try:
        pass
    except:
        pass
"""
    fixed, count = fixer.fix_python(code, [])
    assert "except Exception as e:" in fixed, "bare except düzeltilmedi"
    assert count > 0
    ok("AutoFixer: bare except -> except Exception as e:")


def test_auto_fixer_print_to_logger():
    from agents.code_reviewer import AutoFixer
    fixer = AutoFixer()
    code = 'def foo():\n    print("debug msg")\n    return 1\n'
    fixed, count = fixer.fix_python(code, [])
    assert "logger.info" in fixed, "print -> logger.info dönüşümü olmadı"
    assert "import logging" in fixed, "logging import eklenmedi"
    ok("AutoFixer: print() -> logger.info() + import logging")


def test_auto_fixer_typescript_var():
    from agents.code_reviewer import AutoFixer
    fixer = AutoFixer()
    code = "var x = 1;\nvar y = 'hello';\n"
    fixed, count = fixer.fix_python(code, [])  # fix_typescript kullan
    fixed_ts, count_ts = fixer.fix_typescript(code)
    assert "let" in fixed_ts, "var -> let dönüşümü olmadı"
    assert "var" not in fixed_ts
    ok(f"AutoFixer TypeScript: {count_ts} var -> let")


# ─── 5. PythonStaticAnalyzer ──────────────────────────────

def test_static_analyzer_security():
    from agents.code_reviewer import PythonStaticAnalyzer, FindingCategory, FindingSeverity
    from code_engine import CodeFile, CodeLanguage
    analyzer = PythonStaticAnalyzer()
    code = CodeFile(path="s.py", language=CodeLanguage.PYTHON, content="""
import subprocess
subprocess.call("rm -rf /", shell=True)
api_key = "sk-1234567890abcdef"
import hashlib
h = hashlib.md5(b"password")
""")
    result = analyzer.analyze(code)
    critical = [f for f in result.findings if f.severity == FindingSeverity.CRITICAL]
    assert len(critical) >= 1, "kritik bulgu beklendi"
    assert result.score < 0.6, f"düşük skor beklendi, {result.score}"
    ok(f"StaticAnalyzer güvenlik: {len(critical)} kritik, skor={result.score:.2f}")


def test_static_analyzer_function_quality():
    from agents.code_reviewer import PythonStaticAnalyzer, FindingCategory
    from code_engine import CodeFile, CodeLanguage
    analyzer = PythonStaticAnalyzer()
    # Tip annotation eksik, uzun fonksiyon
    long_fn = "\n".join([f"    x_{i} = {i}" for i in range(40)])
    code = CodeFile(path="q.py", language=CodeLanguage.PYTHON, content=f"""
def process_data(x, y):
{long_fn}
    return x
""")
    result = analyzer.analyze(code)
    doc_findings = [f for f in result.findings if f.category == FindingCategory.DOCUMENTATION]
    clean_findings = [f for f in result.findings if f.category == FindingCategory.CLEAN_CODE]
    assert len(doc_findings) + len(clean_findings) > 0
    ok(f"StaticAnalyzer: uzun fonksiyon + eksik annotation tespit edildi ({len(result.findings)} bulgu)")


# ─── 6. CodePlanner ───────────────────────────────────────

def test_code_planner_fastapi():
    from code_engine import CodePlanner, ProjectTemplate
    p = CodePlanner()
    tasks = p.plan("Blog API", "REST API", ProjectTemplate.FASTAPI_REST)
    agent_ids = [t["agent_id"] for t in tasks]
    assert "backend_dev" in agent_ids
    assert "qa_engineer" in agent_ids
    assert "devops" in agent_ids
    for t in tasks:
        assert "filepath" in t["prompt_extra"].lower() or "dosya" in t["prompt_extra"].lower()
    ok(f"CodePlanner FastAPI: {len(tasks)} ajan -> {agent_ids}")


def test_code_planner_custom():
    from code_engine import CodePlanner, ProjectTemplate
    p = CodePlanner()
    tasks = p.plan("Custom Thing", "Some description", ProjectTemplate.CUSTOM)
    assert len(tasks) == 8, f"custom şablonda 8 ajan beklendi, {len(tasks)} var"
    ok(f"CodePlanner custom: {len(tasks)} ajan")


# ─── 7. CodeGenerationResult ──────────────────────────────

def test_code_result_zip():
    from code_engine import CodeGenerationResult, CodeFile, CodeLanguage
    r = CodeGenerationResult(
        project_id="z1",
        title="Test ZIP",
        files=[
            CodeFile(path="src/main.py", language=CodeLanguage.PYTHON,
                     content='"""Main."""\nprint("hi")', agent_id="backend_dev"),
            CodeFile(path="tests/test_main.py", language=CodeLanguage.PYTHON,
                     content='def test_ok(): assert True', agent_id="qa_engineer"),
            CodeFile(path="docker-compose.yml", language=CodeLanguage.YAML,
                     content='version: "3"\nservices:\n  app:\n    image: python', agent_id="devops"),
        ]
    )
    zip_bytes = r.to_zip()
    assert len(zip_bytes) > 200
    buf = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
    assert "src/main.py" in names
    assert "GENERATED_README.md" in names
    ok(f"CodeGenerationResult.to_zip: {len(zip_bytes)} byte, {len(names)} dosya")


def test_code_result_stats():
    from code_engine import CodeGenerationResult, CodeFile, CodeLanguage
    r = CodeGenerationResult(
        project_id="s1",
        title="Stats Test",
        files=[
            CodeFile(path="a.py", language=CodeLanguage.PYTHON, content="x = 1\ny = 2\n"),
            CodeFile(path="b.ts", language=CodeLanguage.TYPESCRIPT, content="const x = 1;\n"),
        ]
    )
    assert r.total_lines == 3
    assert "python" in r.languages
    assert "typescript" in r.languages
    ok(f"CodeGenerationResult stats: {r.total_lines} satır, diller: {r.languages}")


# ─── 8. FileReviewResult skoru ────────────────────────────

def test_file_review_score():
    from agents.code_reviewer import FileReviewResult, Finding, FindingSeverity, FindingCategory
    r = FileReviewResult(path="x.py", language="python")
    r.findings = [
        Finding(FindingCategory.SECURITY, FindingSeverity.CRITICAL, 1, "eval"),
        Finding(FindingCategory.CLEAN_CODE, FindingSeverity.WARNING, 2, "print"),
        Finding(FindingCategory.CLEAN_CODE, FindingSeverity.WARNING, 3, "TODO"),
    ]
    score = r.calculate_score()
    assert score < 0.8, f"critical bulgu varken yüksek skor olmamalı: {score}"
    assert r.critical_count == 1
    assert r.warning_count == 2
    ok(f"FileReviewResult skor: {score:.2f} (1 kritik, 2 uyarı)")


# ─── 9. TEMPLATE_SPECS ────────────────────────────────────

def test_template_specs_complete():
    from code_engine import TEMPLATE_SPECS, ProjectTemplate
    for tmpl in [ProjectTemplate.FASTAPI_REST, ProjectTemplate.REACT_SPA, ProjectTemplate.FULLSTACK]:
        spec = TEMPLATE_SPECS.get(tmpl)
        assert spec, f"{tmpl} spec eksik"
        assert "files" in spec and len(spec["files"]) > 0
        assert "agents" in spec and len(spec["agents"]) > 0
    ok(f"TEMPLATE_SPECS: {len(TEMPLATE_SPECS)} şablon tanımlı")


# ─── Koşucu ───────────────────────────────────────────────

TESTS = [
    test_agent_clean_code_contract,
    test_syntax_validator_python,
    test_syntax_validator_broken_python,
    test_syntax_validator_typescript,
    test_syntax_validator_sql,
    test_syntax_validator_clean_code,
    test_code_extractor_python,
    test_code_extractor_multiple,
    test_code_extractor_no_filepath,
    test_auto_fixer_bare_except,
    test_auto_fixer_print_to_logger,
    test_auto_fixer_typescript_var,
    test_static_analyzer_security,
    test_static_analyzer_function_quality,
    test_code_planner_fastapi,
    test_code_planner_custom,
    test_code_result_zip,
    test_code_result_stats,
    test_file_review_score,
    test_template_specs_complete,
]


if __name__ == "__main__":
    print("\n" + "═" * 55)
    print("  FAZ 6 — Kod Üretim Motoru & Temiz Kod Testleri")
    print("═" * 55 + "\n")

    for test_fn in TESTS:
        try:
            test_fn()
        except Exception as e:
            fail(test_fn.__name__, e)

    print()
    print("═" * 55)
    total = len(PASS) + len(FAIL)
    print(f"  Sonuç: {len(PASS)}/{total} geçti", end="")
    if FAIL:
        print(f"  |  {len(FAIL)} başarısız: {', '.join(FAIL)}")
        sys.exit(1)
    else:
        print("  🎉 Tüm testler geçti!")
    print("═" * 55 + "\n")
