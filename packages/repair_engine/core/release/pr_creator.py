"""
Release Layer — Branch yönetimi ve PR önerisi.

ÖNEMLİ:
- Otomatik merge KAPALI
- Sistem sadece branch açar ve PR hazırlar
- Merge kararını insan verir

PR açmak için Git gerekir. Git yoksa (sandbox):
- PR içeriğini JSON olarak döner
- İnsan bunu manuel kullanabilir
"""

import os
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from packages.repair_engine.generation.patch_generator import GeneratedPatch
from packages.repair_engine.schemas.patch_plan import PatchPlan
from packages.repair_engine.schemas.validation import ValidationReport
from packages.observability.logging import get_logger

_log = get_logger("repair.release")


@dataclass
class PRProposal:
    """Pull Request önerisi — insan onayı bekler."""
    pr_id:          str
    job_id:         str
    branch_name:    str
    title:          str
    body:           str
    incident_id:    str      = ""       # Faz 10.1: ilgili incident
    target_branch:  str      = "main"
    changed_files:  list[str] = field(default_factory=list)
    diff:           str       = ""
    validation_summary: str  = ""
    risk_level:     str       = "low"
    auto_merge:     bool      = False   # Her zaman False — değiştirilemez
    created_at:     datetime  = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "pr_id":               self.pr_id,
            "job_id":              self.job_id,
            "incident_id":         self.incident_id,
            "branch_name":         self.branch_name,
            "title":               self.title,
            "body":                self.body[:3000],
            "target_branch":       self.target_branch,
            "changed_files":       self.changed_files,
            "risk_level":          self.risk_level,
            "auto_merge":          self.auto_merge,
            "validation_summary":  self.validation_summary,
            "created_at":          self.created_at.isoformat(),
        }


def _run_git(args: list[str], cwd: str) -> tuple[bool, str]:
    """Git komutu çalıştır. Git yoksa graceful fail."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, f"Git hatası: {e}"


def _build_pr_body(
    patch:      GeneratedPatch,
    plan:       PatchPlan,
    validation: ValidationReport,
    incident_id: str,
    symptom:    str,
) -> str:
    checks = []
    checks.append(f"- [{'x' if validation.syntax_ok else ' '}] Syntax OK")
    checks.append(f"- [{'x' if validation.lint_ok else ' '}] Lint OK")
    checks.append(f"- [{'x' if validation.unit_tests_ok else ' '}] Unit Tests OK")
    checks.append(f"- [{'x' if validation.security_ok else ' '}] Security OK")
    checks.append(f"- [{'x' if validation.architecture_ok else ' '}] Architecture OK")

    body = f"""## 🔧 Self-Repair Patch

**Incident:** `{incident_id}`
**Symptom:** {symptom[:200]}
**Risk:** {plan.risk.value.upper()}

---

### Yapılan Değişiklikler
{patch.rationale or 'Patch açıklaması mevcut değil.'}

**Hedef Dosyalar:**
{chr(10).join(f'- `{f}`' for f in patch.changed_files)}

---

### Validation Sonuçları
{chr(10).join(checks)}

**Validation Confidence:** {validation.confidence}%
**Regression Risk:** {validation.regression_risk}
**Security Risk:** {validation.security_risk}

---

### Patch Detayı
```diff
{patch.diff[:3000]}
```

---

> ⚠️ **Bu PR otomatik olarak üretilmiştir.**
> Merge etmeden önce lütfen diff'i ve test sonuçlarını inceleyin.
> Auto-merge **KAPALI**. Merge kararını insan verir.

**Üretildi:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
"""
    return body


class BranchManager:
    """Git branch oluşturma ve patch uygulama."""

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)

    def create_repair_branch(self, job_id: str) -> tuple[bool, str]:
        """repair/job_id formatında yeni branch oluştur."""
        branch_name = f"repair/{job_id}"

        # Mevcut branch'i kontrol et
        ok, current = _run_git(["branch", "--show-current"], self.project_root)
        if not ok:
            return False, f"Git repo yok veya erişilemiyor: {current}"

        # Branch oluştur
        ok, out = _run_git(["checkout", "-b", branch_name], self.project_root)
        if not ok:
            # Zaten varsa geç
            if "already exists" in out:
                ok2, _ = _run_git(["checkout", branch_name], self.project_root)
                return ok2, branch_name
            return False, f"Branch oluşturulamadı: {out}"

        return True, branch_name

    def apply_patch_to_branch(self, diff: str, branch_name: str) -> tuple[bool, str]:
        """Patch'i branch'e uygula."""
        import tempfile
        patch_file = os.path.join(self.project_root, "_repair_temp.patch")
        try:
            with open(patch_file, "w", encoding="utf-8") as f:
                f.write(diff)

            ok, out = _run_git(["apply", "--check", "_repair_temp.patch"], self.project_root)
            if not ok:
                return False, f"Patch uygulanamaz: {out}"

            ok, out = _run_git(["apply", "_repair_temp.patch"], self.project_root)
            return ok, out
        finally:
            if os.path.exists(patch_file):
                os.remove(patch_file)

    def commit_patch(self, job_id: str, title: str) -> tuple[bool, str]:
        """Patch'i commit et."""
        ok, _ = _run_git(["add", "-A"], self.project_root)
        if not ok:
            return False, "git add başarısız"

        message = f"repair: {title[:80]}\n\nAuto-generated by Self-Repair System (job={job_id})\nDo NOT merge without human review."
        ok, out = _run_git(["commit", "-m", message], self.project_root)
        return ok, out

    def return_to_main(self) -> None:
        """Ana branch'e geri dön. Default branch'i algıla."""
        # Önce repo default branch'i tespit et
        ok, out = _run_git(
            ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            self.project_root,
        )
        if ok and out.strip():
            default = out.strip().replace("origin/", "")
        else:
            # Fallback: main > master
            ok_main, _ = _run_git(
                ["show-ref", "--verify", "--quiet", "refs/heads/main"],
                self.project_root,
            )
            default = "main" if ok_main else "master"
        _run_git(["checkout", default], self.project_root)
        _log.debug(f"Ana branch'e döndü: {default}")


class PRCreator:
    """
    PR önerisi oluşturur.
    GitHub API bağlantısı opsiyonel — yoksa JSON olarak döner.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.branch_manager = BranchManager(project_root)
        self._proposals: dict[str, PRProposal] = {}

    def create_proposal(
        self,
        job_id:      str,
        patch:       GeneratedPatch,
        plan:        PatchPlan,
        validation:  ValidationReport,
        incident_id: str,
        symptom:     str,
    ) -> PRProposal:
        """PR önerisi oluştur (git push yapmaz). Auto-merge her zaman False."""
        branch_name = f"repair/{job_id}"
        title       = f"[Self-Repair] {symptom[:60]}"
        body        = _build_pr_body(patch, plan, validation, incident_id, symptom)

        proposal = PRProposal(
            pr_id=f"pr_{uuid.uuid4().hex[:8]}",
            job_id=job_id,
            incident_id=incident_id,    # Faz 10.1: ilişki düzeltildi
            branch_name=branch_name,
            title=title,
            body=body,
            changed_files=patch.changed_files,
            diff=patch.diff,
            validation_summary=(
                f"confidence={validation.confidence}% | "
                f"regression_risk={validation.regression_risk} | "
                f"security_risk={validation.security_risk}"
            ),
            risk_level=plan.risk.value,
            auto_merge=False,   # Her zaman False — DEĞİŞTİRİLEMEZ
        )
        self._proposals[proposal.pr_id] = proposal
        _log.info(f"PR önerisi hazırlandı: {proposal.pr_id} — {branch_name}")
        return proposal

    def apply_to_branch(
        self,
        proposal: PRProposal,
        dry_run:  bool = True,   # Varsayılan: sadece rapor, dosya değiştirme
    ) -> dict:
        """
        Branch oluştur ve patch uygula.
        dry_run=True -> dosya sistemi değişmez, sadece rapor
        dry_run=False -> gerçek git işlemleri
        """
        if dry_run:
            return {
                "mode":        "dry_run",
                "branch":      proposal.branch_name,
                "would_apply": proposal.diff[:500],
                "message":     "Dry run — dosya değiştirilmedi. dry_run=False ile gerçek uygula.",
            }

        # Gerçek uygulama
        ok, branch = self.branch_manager.create_repair_branch(proposal.job_id)
        if not ok:
            return {"error": f"Branch oluşturulamadı: {branch}"}

        ok, msg = self.branch_manager.apply_patch_to_branch(proposal.diff, branch)
        if not ok:
            self.branch_manager.return_to_main()
            return {"error": f"Patch uygulanamadı: {msg}"}

        ok, commit_msg = self.branch_manager.commit_patch(proposal.job_id, proposal.title)
        self.branch_manager.return_to_main()

        if not ok:
            return {"error": f"Commit başarısız: {commit_msg}"}

        return {
            "mode":    "applied",
            "branch":  branch,
            "commit":  commit_msg,
            "next":    "git push origin <branch> && GitHub'da PR aç",
            "warning": "Auto-merge kapalı — insan onayı gerekli",
        }

    def get_proposal(self, pr_id: str) -> Optional[PRProposal]:
        return self._proposals.get(pr_id)

    def list_proposals(self) -> list[PRProposal]:
        return list(self._proposals.values())


# Singleton factory
# ── Singleton Registry (proje root başına tek instance) ──────
_PR_CREATORS: dict[str, "PRCreator"] = {}


def get_pr_creator(project_root: str = ".") -> "PRCreator":
    """
    Aynı project_root için her zaman aynı PRCreator instance'ı döndür.
    Bu, proposal'ların in-memory kaybolmamasını garantiler.
    """
    key = os.path.abspath(project_root)
    if key not in _PR_CREATORS:
        _PR_CREATORS[key] = PRCreator(key)
    return _PR_CREATORS[key]
