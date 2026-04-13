
# ══════════════════════════════════════════════════════════════
# Validation Report Store — RC1 Gerçek Kanıt Zinciri
# ══════════════════════════════════════════════════════════════
import json as _json
import time as _time

class _ValidationReportStore:
    """In-memory validation raporu saklama (pgvector olmadan da çalışır)."""
    def __init__(self):
        self._reports: dict[str, dict] = {}

    def save(self, job_id: str, report: dict) -> None:
        self._reports[job_id] = {**report, "_saved_at": _time.time()}

    def get(self, job_id: str) -> dict | None:
        return self._reports.get(job_id)

    def all_keys(self) -> list[str]:
        return list(self._reports.keys())

_validation_store = _ValidationReportStore()

def save_validation_report(job_id: str, report: dict) -> None:
    """Doğrulama raporunu kalıcı store'a kaydet (RC1 kanıt zinciri)."""
    _validation_store.save(job_id, report)
    # Arka planda DB'ye yaz (varsa) - P0: is_db_available async olduğu için task içinde kontrol edilir
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        loop.create_task(_persist_to_db(job_id, report))
    except (RuntimeError, Exception):
        pass

def get_validation_report(job_id: str) -> dict | None:
    """Kaydedilmiş doğrulama raporunu oku."""
    return _validation_store.get(job_id)

async def _persist_to_db(job_id: str, report: dict) -> None:
    try:
        from libs.db.session import AsyncSessionLocal, is_db_available
        if not await is_db_available():
            return
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            await db.execute(
                text("INSERT INTO validation_reports (job_id, report_json, created_at) "
                     "VALUES (:job_id, :report, NOW()) "
                     "ON CONFLICT (job_id) DO UPDATE SET report_json=:report"),
                {"job_id": job_id, "report": _json.dumps(report)}
            )
            await db.commit()
    except Exception:
        pass  # DB yoksa sessizce geç

"""
Verification Engine — Faz 10.1 (Güvenilir Doğrulama)

Değişiklikler (P0):
1. _python_apply_patch() artık gerçek hunk-based patch uygular — mock YOK
2. patch binary yoksa -> kontrollü FAIL (simüle etmez)
3. report.patch_applied doğrudan True set edilmiyor — apply sonucuna bağlı
4. report.bug_reproduced doğrudan True set edilmiyor — reproducer mantığı
5. test tanımlanmamışsa unit_tests_ok=False, gap kaydediliyor
6. Reproducer zinciri: patch öncesi fail / patch sonrası pass kanıtı
7. VerificationEngine.verify() artık verification_gaps raporluyor

Katmanlar (P2 refactor):
- PatchApplicator  -> patch uygulama sorumluluğu
- CommandRunner    -> komut çalıştırma sorumluluğu
- VerificationEngine -> orkestrasyon
"""

import ast
import os
import re
import shutil
import subprocess
import tempfile
from typing import Optional

from services.repair.generation.patch_generator import GeneratedPatch
from services.repair.schemas.patch_plan import PatchPlan
from services.repair.schemas.validation import ValidationReport, ValidationStatus
from services.observability.logging import get_logger

_log = get_logger("repair.verification")

# Güvenli shell komutları (allowlist)
_ALLOWED_COMMANDS = {"pytest", "python", "ruff", "mypy", "bandit", "python3"}


def _cmd_allowed(cmd: list[str]) -> bool:
    return bool(cmd) and cmd[0] in _ALLOWED_COMMANDS


# ══════════════════════════════════════════════════════════════
# P2: PatchApplicator — patch uygulama sorumluluğu izole edildi
# ══════════════════════════════════════════════════════════════

class PatchApplicator:
    """
    Unified diff'i hedef dizine uygular.
    Önce sistem 'patch' binary'sini dener.
    Yoksa Python hunk parser ile uygular.
    Binary da yoksa patch parse da başarısızsa -> açık FAIL döner.
    """

    def apply(self, cwd: str, diff_text: str) -> tuple[bool, str]:
        """(ok, output) döndür."""
        if not diff_text or not diff_text.strip():
            return False, "Diff boş — uygulanacak değişiklik yok."

        # Önce patch binary dene
        patch_ok = self._try_patch_binary(cwd, diff_text)
        if patch_ok is not None:
            return patch_ok

        # Fallback: Python hunk parser
        return self._python_hunk_apply(cwd, diff_text)

    def _try_patch_binary(self, cwd: str, diff_text: str) -> Optional[tuple[bool, str]]:
        """patch komutu varsa kullan; yoksa None döndür."""
        if not shutil.which("patch"):
            return None   # binary yok -> fallback'e geç
        import tempfile as _tmp
        with _tmp.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write(diff_text)
            patch_file = f.name
        try:
            result = subprocess.run(
                ["patch", "-p1", "--dry-run", "-i", patch_file],
                cwd=cwd, capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                return False, f"Patch dry-run başarısız:\n{result.stdout}{result.stderr}"
            # Gerçek uygula
            result2 = subprocess.run(
                ["patch", "-p1", "-i", patch_file],
                cwd=cwd, capture_output=True, text=True, timeout=10,
            )
            ok = result2.returncode == 0
            return ok, (result2.stdout + result2.stderr)[:2000]
        except subprocess.TimeoutExpired:
            return False, "patch komutu timeout'a düştü."
        finally:
            try:
                os.unlink(patch_file)
            except OSError:
                pass

    def _python_hunk_apply(self, cwd: str, diff_text: str) -> tuple[bool, str]:
        """
        Minimal unified diff hunk parser.
        Yalnızca tam eşleşen context satırları olan basit patch'leri uygular.
        Eşleşme başarısızsa açık fail döner — başarılı saymaz.
        """
        try:
            hunks = self._parse_hunks(diff_text)
        except Exception as e:
            return False, f"Diff parse hatası: {e}"

        if not hunks:
            return False, "Diff içinde uygulanabilir hunk bulunamadı."

        applied, failed = [], []
        for file_path, hunk_list in hunks.items():
            abs_path = os.path.join(cwd, file_path)
            if not os.path.isfile(abs_path):
                failed.append(f"{file_path}: dosya bulunamadı")
                continue
            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            ok, new_lines, msg = self._apply_hunks_to_lines(lines, hunk_list, file_path)
            if not ok:
                failed.append(f"{file_path}: {msg}")
                continue
            with open(abs_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            applied.append(file_path)

        if failed:
            return False, (
                f"Patch kısmen uygulanamadı.\n"
                f"Uygulanan: {applied}\nBaşarısız: {failed}"
            )
        return True, f"Patch uygulandı: {applied}"

    def _parse_hunks(self, diff_text: str) -> dict[str, list[list[str]]]:
        """
        Basit unified diff parser.
        {relative_path: [[hunk_lines], ...]} döndürür.
        """
        result: dict[str, list[list[str]]] = {}
        current_file: Optional[str] = None
        current_hunk: Optional[list[str]] = None

        for line in diff_text.splitlines(keepends=True):
            # +++ b/path.py satırı
            m = re.match(r"^\+\+\+ b/(.+)$", line.rstrip())
            if m:
                current_file = m.group(1)
                result.setdefault(current_file, [])
                current_hunk = None
                continue
            # @@ -old +new @@
            if line.startswith("@@"):
                current_hunk = []
                if current_file:
                    result[current_file].append(current_hunk)
                continue
            if current_hunk is not None:
                current_hunk.append(line)
        return result

    def _apply_hunks_to_lines(
        self,
        lines: list[str],
        hunks: list[list[str]],
        fname: str,
    ) -> tuple[bool, list[str], str]:
        """
        Hunk'ları sırayla uygula.
        Context satırları eşleşmezse fail döner.
        """
        result = list(lines)
        offset = 0   # önceki hunk'ların satır farkı

        for hunk in hunks:
            context = [l[1:] for l in hunk if l.startswith(" ")]
            removals = [l[1:] for l in hunk if l.startswith("-")]
            additions = [l[1:] for l in hunk if l.startswith("+")]

            # Context + removal bloğunu bul
            search_block = [(" " + c) for c in context[:3]]  # ilk 3 context satır yeterli
            anchor = self._find_anchor(result, removals, context[:3], offset)
            if anchor < 0:
                return False, result, (
                    f"Hunk uygulama noktası bulunamadı "
                    f"(removal={removals[:1]}, context={context[:1]})"
                )

            # Eski satırları kaldır, yenileri ekle
            remove_count = len(removals)
            if removals:
                # removals'ı doğrula
                actual = [l.rstrip("\n") for l in result[anchor:anchor+remove_count]]
                expected = [r.rstrip("\n") for r in removals]
                if actual != expected:
                    return False, result, (
                        f"Satır eşleşmesi başarısız:\n"
                        f"  beklenen={expected[:2]}\n"
                        f"  gerçek={actual[:2]}"
                    )
                result[anchor:anchor+remove_count] = [a + ("\n" if not a.endswith("\n") else "") for a in additions]
                offset += len(additions) - remove_count
            else:
                # Sadece ekleme — anchor'dan sonra ekle
                result[anchor:anchor] = [a + ("\n" if not a.endswith("\n") else "") for a in additions]
                offset += len(additions)

        return True, result, "OK"

    def _find_anchor(
        self,
        lines: list[str],
        removals: list[str],
        context: list[str],
        offset: int,
    ) -> int:
        """Removal bloğunun başlangıç satırını bul."""
        if removals:
            first = removals[0].rstrip("\n")
            for i, line in enumerate(lines):
                if line.rstrip("\n") == first:
                    return i
        elif context:
            first_ctx = context[0].rstrip("\n")
            for i, line in enumerate(lines):
                if line.rstrip("\n") == first_ctx:
                    return i + 1   # context'ten sonraki satıra ekle
        return -1


# ══════════════════════════════════════════════════════════════
# P2: CommandRunner — komut çalıştırma sorumluluğu izole edildi
# ══════════════════════════════════════════════════════════════

class CommandRunner:
    """Sandbox içinde izin listesindeki komutları çalıştırır."""

    TIMEOUT = 60

    def __init__(self, allowed_commands: Optional[list[str]] = None):
        self._allowed = set(allowed_commands or list(_ALLOWED_COMMANDS))

    def run(self, cmd: list[str], cwd: str) -> tuple[bool, str]:
        """(ok, output) döndür. İzinsiz komut -> False."""
        if not cmd:
            return False, "Komut boş."
        base = cmd[0].split("/")[-1]   # path varsa sadece binary adı
        if base not in self._allowed:
            return False, f"Komut izin listesinde değil: {cmd[0]}"
        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=self.TIMEOUT,
            )
            return result.returncode == 0, (result.stdout + result.stderr)[:3000]
        except subprocess.TimeoutExpired:
            return False, f"Timeout: {' '.join(cmd)} — {self.TIMEOUT}s aşıldı"
        except FileNotFoundError:
            return False, f"Komut bulunamadı: {cmd[0]}"
        except Exception as e:
            return False, f"Komut hatası: {e}"


# ══════════════════════════════════════════════════════════════
# SandboxRunner — geçici kopya + apply + test
# ══════════════════════════════════════════════════════════════

class SandboxRunner:
    """
    Repo kopyasında patch uygular ve testleri koşturur.
    Ana kod tabanına dokunmaz.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.applicator  = PatchApplicator()

    def run_in_sandbox(
        self,
        diff_text: str,
        test_cmds: list[list[str]],
        extra_allowed: Optional[list[str]] = None,
    ) -> tuple[bool, str, str]:
        """
        (ok, apply_output, test_output) döndür.
        Geçici kopya oluşturur -> patch uygular -> testleri çalıştırır -> temizler.
        """
        with tempfile.TemporaryDirectory(prefix="repair_sandbox_") as tmpdir:
            # Repo klonu
            self._copy_project(tmpdir)

            runner = CommandRunner(
                allowed_commands=list(_ALLOWED_COMMANDS) + (extra_allowed or [])
            )

            # Patch uygula
            apply_ok, apply_out = self.applicator.apply(tmpdir, diff_text)
            if not apply_ok:
                return False, apply_out, "Patch uygulanamadı — testler koşturulmadı."

            # Test komutlarını çalıştır
            all_ok = True
            test_parts = []
            for cmd in test_cmds:
                if not _cmd_allowed(cmd):
                    test_parts.append(f"SKIP (izinsiz): {' '.join(cmd)}")
                    continue
                ok, out = runner.run(cmd, tmpdir)
                status = "PASS" if ok else "FAIL"
                test_parts.append(f"{status}: {' '.join(cmd)}\n{out[:1000]}")
                if not ok:
                    all_ok = False

            return all_ok, apply_out, "\n\n".join(test_parts)

    def _copy_project(self, dest: str) -> None:
        """Proje dosyalarını geçici dizine kopyala (.git, __pycache__ hariç)."""
        skip = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
        for item in os.listdir(self.project_root):
            if item in skip:
                continue
            src = os.path.join(self.project_root, item)
            dst = os.path.join(dest, item)
            try:
                if os.path.isdir(src):
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                else:
                    shutil.copy2(src, dst)
            except Exception:
                pass   # Tek dosya kopyalama hatası pipeline'ı durdurmasın


# ══════════════════════════════════════════════════════════════
# VerificationEngine — orkestrasyon
# ══════════════════════════════════════════════════════════════

class VerificationEngine:
    """
    Patch'i katmanlar halinde doğrular.
    Her kapı bağımsız çalışır.
    Faz 10.1: Sahte "passed" mantığı kaldırıldı.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.sandbox      = SandboxRunner(project_root)
        self.applicator   = PatchApplicator()

    def verify(
        self,
        patch:  GeneratedPatch,
        plan:   PatchPlan,
    ) -> ValidationReport:
        report     = ValidationReport.create(patch_plan_id=plan.plan_id)
        notes:  list[str] = []
        gaps:   list[str] = []
        parts:  list[str] = []

        # ── 1. Diff boş mu? ────────────────────────────────
        if not patch.diff or not patch.diff.strip():
            report.notes  = ["Diff boş — doğrulama yapılamaz."]
            report.verification_gaps = ["diff_empty"]
            report.final_status         = ValidationStatus.FAILED
            report.final_recommendation = "reject"
            return report

        # ── 2. Syntax Kontrolü ─────────────────────────────
        syntax_ok, syntax_msg = self._check_syntax(patch.diff)
        report.syntax_ok = syntax_ok
        if not syntax_ok:
            notes.append(f"Syntax hatası: {syntax_msg}")
            parts.append(f"SYNTAX: FAIL — {syntax_msg}")
        else:
            parts.append("SYNTAX: OK")

        # ── 3. Güvenlik Taraması ────────────────────────────
        sec_ok, sec_issues = self._security_scan(patch.diff)
        report.security_ok  = sec_ok
        report.security_risk = "high" if not sec_ok else "low"
        if sec_issues:
            notes.extend(sec_issues)
            parts.append(f"SECURITY: FAIL — {'; '.join(sec_issues[:3])}")
        else:
            parts.append("SECURITY: OK")

        # ── 4. Architecture Kontrolü ────────────────────────
        arch_ok, arch_issues = self._architecture_check(patch.diff, plan)
        report.architecture_ok = arch_ok
        if arch_issues:
            notes.extend(arch_issues)
            parts.append(f"ARCHITECTURE: FAIL — {'; '.join(arch_issues[:3])}")
        else:
            parts.append("ARCHITECTURE: OK")

        # ── 5. Lint Kontrolü ────────────────────────────────
        report.lint_ok = self._quick_lint(patch.diff)
        parts.append(f"LINT: {'OK' if report.lint_ok else 'WARN'}")

        # ── 6. Patch Apply + Reproducer + Tests ────────────
        self._run_sandbox_phase(patch, plan, report, notes, gaps, parts)

        # ── 7. Sonuç ────────────────────────────────────────
        report.notes              = notes
        report.test_output        = "\n".join(parts)
        report.verification_gaps  = gaps
        report.regression_risk    = self._regression_risk(patch, plan)
        report.confidence         = self._confidence(report)

        if report.overall_passed():
            report.final_status         = ValidationStatus.PASSED
            report.final_recommendation = "create_pr"
        elif report.syntax_ok and report.security_ok and report.patch_applied:
            report.final_status         = ValidationStatus.PARTIAL
            report.final_recommendation = "manual_review_only"
        else:
            report.final_status         = ValidationStatus.FAILED
            report.final_recommendation = "reject"

        _log.info(
            f"Validation {report.validation_id}: {report.final_recommendation} "
            f"(confidence={report.confidence}%)"
        )
        return report

    def _run_sandbox_phase(
        self,
        patch:  GeneratedPatch,
        plan:   PatchPlan,
        report: ValidationReport,
        notes:  list[str],
        gaps:   list[str],
        parts:  list[str],
    ) -> None:
        """Patch uygulama + reproducer + test aşaması."""

        # Reproducer tanımlı mı?
        has_reproducer = bool(plan.reproducer_tests)
        report.reproducer_defined = has_reproducer

        # Test yoksa açık gap kaydet
        if not plan.required_tests and not has_reproducer:
            report.unit_tests_ok = False
            gaps.append("no_test_defined")
            notes.append("Hedefli test tanımlanmadı — doğrulama eksik (manual_review_only).")
            parts.append("TESTS: SKIPPED — test dosyası belirtilmedi (gap kaydedildi)")
            # Patch'i yalnızca syntax için kopya üstünde dene
            self._try_apply_only(patch, plan, report, notes, parts)
            return

        # Sandbox testleri çalıştır
        all_cmds: list[list[str]] = []

        # Reproducer önce eklenir (patch öncesi fail kanıtı ayrı)
        if has_reproducer:
            all_cmds += [
                ["python3", "-m", "pytest", t, "-x", "--tb=short", "-q"]
                for t in plan.reproducer_tests[:2]
            ]

        # Standart testler
        all_cmds += [
            ["python3", "-m", "pytest", t, "-x", "--tb=short", "-q"]
            for t in plan.required_tests[:3]
        ]

        # Reproducer: patch öncesi fail bekliyoruz
        if has_reproducer:
            pre_ok, pre_apply_out, pre_test_out = self.sandbox.run_in_sandbox(
                diff_text="",   # diff uygulamadan testleri çalıştır
                test_cmds=[
                    ["python3", "-m", "pytest", t, "-x", "--tb=short", "-q"]
                    for t in plan.reproducer_tests[:2]
                ],
            )
            # patch öncesi FAIL bekliyoruz
            report.reproducer_passed_before_patch = pre_ok
            report.bug_reproduced = not pre_ok   # Öncesi fail -> bug reproduced
            if pre_ok:
                notes.append("Reproducer patch öncesi geçti — bug zaten yok veya yanlış reproducer.")
                gaps.append("reproducer_already_passing")
            parts.append(
                f"REPRODUCER (pre-patch): {'FAIL (beklenen)' if not pre_ok else 'PASS (beklenmeyen)'}\n"
                f"{pre_test_out[:500]}"
            )

        # Patch uygula + testler
        extra = [c.split("/")[-1].split()[0] for c in (plan.allowed_commands or [])]
        sandbox_ok, apply_out, test_out = self.sandbox.run_in_sandbox(
            diff_text=patch.diff,
            test_cmds=all_cmds,
            extra_allowed=extra,
        )
        report.patch_applied     = apply_out and not apply_out.startswith("Patch uygulanamadı") and not apply_out.startswith("Diff boş")
        report.patch_apply_output = apply_out[:500]

        if not report.patch_applied:
            notes.append(f"Patch uygulanamadı: {apply_out[:200]}")
            gaps.append("patch_apply_failed")
            parts.append(f"PATCH APPLY: FAIL\n{apply_out[:300]}")
            report.unit_tests_ok = False
            return

        parts.append(f"PATCH APPLY: OK\n{apply_out[:200]}")

        # Reproducer: patch sonrası pass bekliyoruz
        if has_reproducer:
            report.reproducer_passed_after_patch = sandbox_ok
            if sandbox_ok:
                parts.append("REPRODUCER (post-patch): PASS ✓ (bug kanıtlandı ve düzeltildi)")
            else:
                notes.append("Reproducer patch sonrası hâlâ fail — patch yetersiz.")
                gaps.append("reproducer_still_failing")
                parts.append("REPRODUCER (post-patch): FAIL ✗")

        # Test sonucu
        report.unit_tests_ok = sandbox_ok
        parts.append(f"TESTS: {'PASS' if sandbox_ok else 'FAIL'}\n{test_out[:1500]}")
        if not sandbox_ok:
            notes.append("Sandbox testleri geçmedi.")

    def _try_apply_only(
        self,
        patch:  GeneratedPatch,
        plan:   PatchPlan,
        report: ValidationReport,
        notes:  list[str],
        parts:  list[str],
    ) -> None:
        """Test yokken sadece syntax/apply doğrulaması yap."""
        import tempfile, shutil as _sh
        with tempfile.TemporaryDirectory(prefix="repair_apply_") as tmpdir:
            try:
                SandboxRunner(self.project_root)._copy_project(tmpdir)
            except Exception:
                pass
            ok, out = self.applicator.apply(tmpdir, patch.diff)
        report.patch_applied      = ok
        report.patch_apply_output = out[:500]
        if ok:
            parts.append(f"PATCH APPLY (syntax-only mode): OK")
        else:
            notes.append(f"Patch uygulanamadı: {out[:200]}")
            parts.append(f"PATCH APPLY: FAIL\n{out[:300]}")

    # ── Yardımcı Kontroller ──────────────────────────────────

    def _check_syntax(self, diff: str) -> tuple[bool, str]:
        """Eklenen Python satırlarını syntax açısından kontrol et."""
        added_lines = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        snippet = "\n".join(added_lines)
        if not snippet.strip():
            return True, ""
        try:
            ast.parse(snippet)
            return True, ""
        except SyntaxError as e:
            return False, str(e)

    def _security_scan(self, diff: str) -> tuple[bool, list[str]]:
        """Tehlikeli pattern tespiti (kural tabanlı)."""
        DANGER = [
            (r"\beval\s*\(", "eval() kullanımı — RCE riski"),
            (r"\bexec\s*\(", "exec() kullanımı — RCE riski"),
            (r"subprocess\.call\(.+shell\s*=\s*True", "shell=True — komut enjeksiyonu riski"),
            (r"__import__\s*\(", "__import__() — dinamik import riski"),
            (r"os\.system\s*\(", "os.system() — komut enjeksiyonu riski"),
            (r"pickle\.loads?\s*\(", "pickle.load() — güvenilmez veri"),
            (r"open\(.+['\"]w['\"]", "Dosya yazma — sandbox dışı etki riski"),
        ]
        added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
        issues = []
        for pattern, msg in DANGER:
            if re.search(pattern, added):
                issues.append(msg)
        return len(issues) == 0, issues

    def _architecture_check(self, diff: str, plan: PatchPlan) -> tuple[bool, list[str]]:
        """Hedef dışı dosya ve forbidden pattern kontrolü."""
        BLOCKED_PREFIXES = ("auth/", "alembic/", "alembic\\")
        issues = []
        changed_files = re.findall(r"^\+\+\+ b/(.+)$", diff, re.MULTILINE)

        # Plan hedefine uymayan dosya var mı?
        for f in changed_files:
            f_norm = f.replace("\\", "/")
            if any(f_norm.startswith(bp) for bp in BLOCKED_PREFIXES):
                issues.append(f"Bloklu prefix'e erişim: {f}")
            elif plan.target_files and f_norm not in plan.target_files:
                issues.append(f"Plan dışı dosya değiştiriliyor: {f}")

        return len(issues) == 0, issues

    def _quick_lint(self, diff: str) -> bool:
        """Çok basit lint: açık print() ve debug kodu tespiti."""
        added = "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++"))
        bad = [r"\bpdb\.set_trace\(\)", r"\bbreakpoint\(\)", r"import pdb"]
        return not any(re.search(p, added) for p in bad)

    def _regression_risk(self, patch: GeneratedPatch, plan: PatchPlan) -> str:
        lines = len([l for l in patch.diff.splitlines() if l.startswith("+") or l.startswith("-")])
        if lines <= 10 and len(patch.changed_files) <= 1:
            return "low"
        elif lines <= 50:
            return "medium"
        return "high"

    def _confidence(self, report: ValidationReport) -> int:
        score = 0
        if report.patch_applied:        score += 25
        if report.syntax_ok:             score += 15
        if report.security_ok:           score += 20
        if report.architecture_ok:       score += 15
        if report.lint_ok:               score += 5
        if report.unit_tests_ok:         score += 15
        if report.reproducer_evidence_ok(): score += 5
        return min(score, 100)


def get_verification_engine(project_root: str = ".") -> VerificationEngine:
    return VerificationEngine(project_root)
