"""
Repair Report Generator — Faz 11
Her repair job sonunda Markdown/HTML özet raporu üretir.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone


def generate_markdown_report(job, incident, plan=None, validation=None,
                              decision: str = "unknown", feedback_code: str = "",
                              lessons: str = "") -> str:
    now   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    emoji = {"success": "✅", "rejected": "❌", "manual": "🔍", "failed": "💥"}.get(decision, "⏳")

    def _val(v): return v.value if hasattr(v, "value") else str(v)

    lines = [
        f"# {emoji} Self-Repair Raporu",
        f"",
        f"**Oluşturma:** {now}  |  **Job:** `{job.job_id}`  |  **Durum:** `{decision.upper()}`",
        f"",
        f"---",
        f"## 📋 Incident",
        f"| Alan | Değer |",
        f"|------|-------|",
        f"| ID | `{incident.incident_id}` |",
        f"| Modül | `{incident.module}` |",
        f"| Önem | `{_val(incident.severity)}` |",
        f"",
        f"**Semptom:** {incident.symptom}",
        f"",
    ]

    if incident.stack_trace:
        lines += [
            "<details><summary>Stack Trace</summary>\n\n```",
            incident.stack_trace[:1500],
            "```\n</details>\n",
        ]

    if plan:
        lines += [
            f"## 🗺️ Patch Planı",
            f"**Risk:** `{_val(plan.risk)}`  |  **Dosyalar:** {', '.join(f'`{f}`' for f in plan.target_files)}",
            f"",
            f"**Gerekçe:** {plan.rationale}",
            f"",
        ]

    if validation:
        checks = [
            ("Patch Uygulandı", validation.patch_applied),
            ("Syntax",          validation.syntax_ok),
            ("Güvenlik",        validation.security_ok),
            ("Mimari",          validation.architecture_ok),
            ("Unit Test",       validation.unit_tests_ok),
        ]
        rows = "\n".join(
            f"| {name} | {'✅' if ok else '❌'} |" for name, ok in checks
        )
        lines += [
            f"## 🧪 Doğrulama",
            f"| Kontrol | Sonuç |",
            f"|---------|-------|",
            rows,
            f"",
            f"**Güven:** `{validation.confidence}%` · **Risk:** `{validation.regression_risk}` · **Tavsiye:** `{validation.final_recommendation}`",
            f"",
        ]
        if validation.verification_gaps:
            lines += [f"**Boşluklar:** {', '.join(f'`{g}`' for g in validation.verification_gaps)}", f""]

    lines += [
        f"## 📊 Karar: `{decision.upper()}`",
        f"",
    ]
    if feedback_code:
        lines.append(f"**Geri Bildirim:** `{feedback_code}`\n")
    if hasattr(job, "pr_url") and job.pr_url:
        lines.append(f"**PR:** `{job.pr_url}`\n")
    if lessons:
        lines += [f"## 📚 Dersler", f"", lessons, f""]

    lines += [
        f"---",
        f"*Otomatik üretildi · İnsan onayı gereklidir*",
    ]
    return "\n".join(lines)


def generate_html_report(job, incident, plan=None, validation=None,
                         decision="unknown", **kwargs) -> str:
    md   = generate_markdown_report(job, incident, plan, validation, decision, **kwargs)
    html = re.sub(r"^# (.+)$",  r"<h1>\1</h1>",  md, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", html)
    html = re.sub(r"^---$", r"<hr>", html, flags=re.MULTILINE)
    html = html.replace("\n", "<br>\n")
    return f"""<!DOCTYPE html><html lang="tr">
<head><meta charset="UTF-8"><title>Repair — {job.job_id}</title>
<style>body{{font-family:system-ui;max-width:900px;margin:40px auto;padding:0 20px}}
code{{background:#f4f4f4;padding:2px 5px;border-radius:3px}}
h2{{border-bottom:1px solid #eee;padding-bottom:4px}}</style></head>
<body>{html}</body></html>"""
