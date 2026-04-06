from __future__ import annotations

import json
import asyncio
import uuid as _uuid
from celery import Task
from celery.utils.log import get_task_logger

from packages.persistence.models import ProjectStatus  # type: ignore
from packages.persistence.session import AsyncSessionLocal  # type: ignore
from packages.persistence.repositories.repository import ProjectRepository, TaskLogRepository, SubTaskRepository  # type: ignore
from tasks.celery_app import celery_app  # type: ignore
from integrations.deerflow_bridge import DeerFlowBridgeClient  # type: ignore
from schemas import DeerFlowEventType  # type: ignore
from packages.orchestration.heal_engine import heal_engine  # type: ignore

# ── DeerFlow Stream Event Normalizer ─────────────────────
_EVENT_TYPE_MAP: dict[str, DeerFlowEventType] = {
    "messages-tuple": DeerFlowEventType.THOUGHT,
    "thought":        DeerFlowEventType.THOUGHT,
    "message":        DeerFlowEventType.THOUGHT,
    "info":           DeerFlowEventType.THOUGHT,
    "answer":         DeerFlowEventType.FINAL_ANSWER,
    "final_answer":   DeerFlowEventType.FINAL_ANSWER,
    "tool_call":      DeerFlowEventType.TOOL_CALL,
    "tool_result":    DeerFlowEventType.TOOL_RESULT,
    "plan":           DeerFlowEventType.PLAN_STEP,
    "plan_step":      DeerFlowEventType.PLAN_STEP,
    "artifact":       DeerFlowEventType.ARTIFACT_CREATED,
    "error":          DeerFlowEventType.ERROR,
    "usage":          DeerFlowEventType.USAGE,
    "warning":        DeerFlowEventType.WARNING,
}


def _extract_content(ev_type: str, data) -> str:
    """Event verisinden okunabilir içerik çıkarır."""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return data.get("content", "") or data.get("message", "") or data.get("text", "")
    if isinstance(data, list):
        parts = []
        for item in data:
            if isinstance(item, list) and len(item) > 0:
                msg = item[0]
                if isinstance(msg, dict):
                    parts.append(msg.get("content", ""))
                elif isinstance(msg, str):
                    parts.append(msg)
            elif isinstance(item, dict):
                parts.append(item.get("content", ""))
        return "\n".join(p for p in parts if p)
    return ""

logger = get_task_logger(__name__)


def _normalize_status(status) -> str:
    """Enum veya string durumu güvenli bir şekilde normallestirir."""
    if hasattr(status, "value"):
        return str(status.value)
    return str(status) if status else ""


def run_async(coro):
    """Celery worker içinde asenkron kod çalıştırmak için yardımcı (Hardened for loop-reuse)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Eğer zaten bir loop varsa ve çalışıyorsa, Celery sync worker'da bu beklenmez.
        import nest_asyncio  # type: ignore
        nest_asyncio.apply()
        return asyncio.get_event_loop().run_until_complete(coro)

    # Yeni loop oluştur ve çalıştır
    new_loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(new_loop)
        return new_loop.run_until_complete(coro)
    finally:
        try:
            new_loop.close()
        except Exception:
            pass
        asyncio.set_event_loop(None)


def to_uuid(val):
    """Değeri güvenli bir şekilde UUID nesnesine dönüştürür."""
    if isinstance(val, _uuid.UUID) or val is None:
        return val
    try:
        return _uuid.UUID(str(val))
    except (ValueError, TypeError):
        return None


@celery_app.task(
    name="tasks.deerflow_tasks.run_deerflow_task",
    bind=True,
    max_retries=2,
    acks_late=True,
    default_retry_delay=15,
    soft_time_limit=1800,
    time_limit=1900,
)
def run_deerflow_task(
    self: Task,
    db_project_id: str,
    title: str,
    description: str,
    job_id: str = "",
    user_id: str = "",
):
    """
    DeerFlow Bridge üzerinden ağır ajan görevlerini yürüten Celery task.
    """
    async def _execute():
        from packages.persistence.session import AsyncSessionLocal
        from packages.persistence.repositories.repository import ProjectRepository
        from integrations.deerflow_bridge import DeerFlowBridgeClient

        async with AsyncSessionLocal() as db:
            p = await ProjectRepository.get(db, to_uuid(db_project_id))
            if not p:
                return {"status": "error", "reason": "not_found"}

            # V2 Durum Kontrolü (Enum-safe)
            current_status = _normalize_status(p.status)
            terminal_states = {
                _normalize_status(ProjectStatus.RUNNING),
                _normalize_status(ProjectStatus.COMPLETED),
                _normalize_status(getattr(ProjectStatus, "FAILED", "failed")),
                _normalize_status(getattr(ProjectStatus, "CANCELLED", "cancelled")),
            }
            if current_status in terminal_states:
                return {"status": "skipped", "reason": "already_processed"}

            await ProjectRepository.mark_started(db, p.id)
            await packages.persistence.commit()

        # Prompt hazırlığı
        prompt = (
            f"Project title: {title}\n\n"
            f"Project description:\n{description}\n\n"
            "Produce a structured result with summary first."
        )

        # Bridge client ile çalıştır
        bridge = DeerFlowBridgeClient()
        deerflow_result = await bridge.run(
            thread_id=f"project-{db_project_id}",
            prompt=prompt,
            file_paths=None,
        )

        if deerflow_result.get("status") == "error":
            return deerflow_result

        # DB Güncelleme
        async with AsyncSessionLocal() as db:
            p = await ProjectRepository.get(db, to_uuid(db_project_id))
            if p:
                await ProjectRepository.mark_completed(
                    db,
                    p.id,
                    report=deerflow_result.get("result", ""),
                    status=ProjectStatus.COMPLETED.value,
                )
                await packages.persistence.commit()

        return {"status": "success", "result": deerflow_result}

    try:
        result = run_async(_execute())
        if result is None:
            raise Exception("DeerFlow task execution failed: No outcome from _execute()")
        if result.get("status") == "error":
            raise Exception(result.get("reason") or result.get("message") or "deerflow_error")
        return result
    except Exception as exc:
        async def _set_failed():
            from packages.persistence.session import AsyncSessionLocal
            from packages.persistence.repositories.repository import ProjectRepository
            async with AsyncSessionLocal() as db:
                p = await ProjectRepository.get(db, to_uuid(db_project_id))
                if p:
                    if hasattr(ProjectRepository, "set_error"):
                        await ProjectRepository.set_error(db, p.id, str(exc))
                    else:
                        await ProjectRepository.mark_completed(db, p.id, report=f"Error: {exc}", status="error")
                    await packages.persistence.commit()

        run_async(_set_failed())
        raise self.retry(exc=exc)


@celery_app.task(
    name="tasks.deerflow_tasks.run_deerflow_streaming_task",
    bind=True,
    max_retries=1,
    acks_late=True,
    soft_time_limit=1800,
)
def run_deerflow_streaming_task(
    self: Task,
    db_project_id: str,
    title: str,
    description: str,
    user_id: str = "",
    job_id: str = "",
    deerflow_role: str = "deerflow_run",
    workflow_template: str = "default",
    quality_profile: str = "standard",
    acceptance_criteria: list | None = None,
    **kwargs
):
    """
    DeerFlow Bridge üzerinden AKIŞ (Streaming) ile ajan görevini yürüten Celery task.
    Normalize edilmiş olay tipleri ve yapılandırılmış payload ile loglama yapar.
    """
    async def _execute():
        async with AsyncSessionLocal() as db:
            p = await ProjectRepository.get(db, to_uuid(db_project_id))
            if not p or _normalize_status(p.status) == _normalize_status(ProjectStatus.COMPLETED):
                return {"status": "skipped"}

            await ProjectRepository.mark_started(db, p.id)
            await TaskLogRepository.write(
                db, p.id, "deerflow.start",
                f"Streaming task başlatıldı (rol: {deerflow_role}).",
                payload={"deerflow_role": deerflow_role},
            )
            await packages.persistence.commit()

        # Prompt builder: görev tipine göre prompt oluştur
        try:
            from packages.orchestration.task_templates import render_task_payload
            rendered = render_task_payload(
                original_prompt=f"Goal: {description}",
                template_id=workflow_template,
                profile_id=quality_profile,
                acceptance_criteria=acceptance_criteria
            )
            
            from packages.orchestration.deerflow_prompts import build_deerflow_prompt  # type: ignore
            prompt = build_deerflow_prompt(deerflow_role, title, rendered["augmented_prompt"])
        except ImportError:
            prompt = (
                f"Project: {title}\n\n"
                f"Goal: {description}\n\n"
                "Work step-by-step. Provide your thought process."
            )

        # Provider Rotation Logic (Faz 12 Hardening)
        providers_to_try = [None, "groq", "anthropic", "gemini", "openai"] # None uses bridge default
        last_error = "Unknown error"
        
        for provider in providers_to_try:
            bridge = DeerFlowBridgeClient()
            final_result = ""
            has_error = False
            event_counts: dict[str, int] = {}
            error_msg = ""
            
            if provider:
                logger.info(f"Retrying DeerFlow task with provider: {provider}")
            
            async for event in bridge.stream_run(
                thread_id=f"stream-{db_project_id}", 
                prompt=prompt,
                provider=provider
            ):
                raw_ev_type = event.get("event", "")
                data = event.get("data", {})

                # Normalize event type
                normalized = _EVENT_TYPE_MAP.get(raw_ev_type, DeerFlowEventType.THOUGHT)
                event_counts[normalized.value] = event_counts.get(normalized.value, 0) + 1

                # İçerik çıkar
                content = _extract_content(raw_ev_type, data)

                # Yapılandırılmış payload
                structured_payload = {
                    "event_type": normalized.value,
                    "raw_event": raw_ev_type,
                    "deerflow_role": deerflow_role,
                    "provider": provider or "default",
                    "tool_name": data.get("tool_name", "") if isinstance(data, dict) else "",
                    "duration_ms": data.get("duration_ms", 0) if isinstance(data, dict) else 0,
                    "token_usage": data.get("usage", {}) if isinstance(data, dict) else {},
                }

                async with AsyncSessionLocal() as db:
                    if normalized == DeerFlowEventType.ERROR:
                        has_error = True
                        error_msg = content or (data.get("message", "Unknown error") if isinstance(data, dict) else "Unknown error")
                        
                        # Sağlık sistemine raporla
                        try:
                            await heal_engine.on_subtask_error(deerflow_role, error_msg)
                        except Exception as e:
                            logger.warning(f"Heal engine reporting failed: {e}")

                        await TaskLogRepository.write(
                            db, to_uuid(db_project_id),
                            f"deerflow.{normalized.value}",
                            f"[{provider or 'default'}] {error_msg}",
                            level="error",
                            payload=structured_payload,
                        )
                    elif normalized == DeerFlowEventType.USAGE:
                        await TaskLogRepository.write(
                            db, to_uuid(db_project_id),
                            f"deerflow.{normalized.value}",
                            "Token usage event",
                            payload=structured_payload,
                        )
                    elif content:
                        truncated = content[:500] + ("..." if len(content) > 500 else "")
                        await TaskLogRepository.write(
                            db, to_uuid(db_project_id),
                            f"deerflow.{normalized.value}",
                            truncated,
                            payload=structured_payload,
                        )
                        final_result += content + "\n"

                    await packages.persistence.commit()

            # Eğer hata kodu 401, 429 veya "Invalid API Key" ise ve başka provider varsa dön
            if has_error:
                lower_err = error_msg.lower()
                is_auth_or_quota = any(x in lower_err for x in ["401", "429", "invalid api key", "quota", "limit exceeded"])
                
                if is_auth_or_quota and provider != providers_to_try[-1]:
                    logger.warning(f"Provider {provider or 'default'} failed ({error_msg}). Rotating...")
                    continue # Diğer provider'ı dene
                else:
                    last_error = error_msg
                    break # Fatal hata veya son provider
            else:
                break # Başarılı!

        # Final Update
        async with AsyncSessionLocal() as db:
            completion_payload = {
                "deerflow_role": deerflow_role,
                "event_counts": event_counts,
                "result_length": len(final_result),
                "final_provider": provider or "default"
            }
            if has_error:
                await ProjectRepository.mark_completed(
                    db, to_uuid(db_project_id),
                    report=f"Error occurred during streaming. Final Provider: {provider}. Error: {last_error}",
                    status="error",
                )
            else:
                await ProjectRepository.mark_completed(db, to_uuid(db_project_id), report=final_result)
                
                # SPECIAL: Planner JSON Parsing
                if deerflow_role == "deerflow_plan":
                    try:
                        # Extract JSON from potential markdown tags
                        clean_json = final_result.strip()
                        if "```json" in clean_json:
                            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                        elif "```" in clean_json:
                            clean_json = clean_json.split("```")[1].split("```")[0].strip()
                        
                        plan_data = json.loads(clean_json)
                        subtasks = plan_data.get("subtasks", []) or plan_data.get("tasks", [])
                        
                        if subtasks:
                            await SubTaskRepository.bulk_create(db, to_uuid(db_project_id), subtasks)
                            await TaskLogRepository.write(
                                db, to_uuid(db_project_id),
                                "deerflow.plan_extracted",
                                f"{len(subtasks)} alt görev başarıyla oluşturuldu.",
                                payload={"subtask_count": len(subtasks)}
                            )
                    except Exception as e:
                        logger.warning(f"Planner JSON parse failed: {e}")
                        await TaskLogRepository.write(
                            db, to_uuid(db_project_id),
                            "deerflow.plan_error",
                            f"Plan JSON formatı okunamadı: {str(e)}",
                            level="warning"
                        )

                await TaskLogRepository.write(
                    db, to_uuid(db_project_id),
                    "deerflow.completed",
                    "Görev tamamlandı.",
                    payload=completion_payload,
                )
            await packages.persistence.commit()

        return {
            "status": "error" if has_error else "success",
            "result_len": len(final_result),
            "event_counts": event_counts,
            "deerflow_role": deerflow_role,
        }

    try:
        return run_async(_execute())
    except Exception as exc:
        logger.error(f"Streaming task failed (role={deerflow_role}): {exc}")
        raise self.retry(exc=exc)
