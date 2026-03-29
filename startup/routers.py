"""
startup/routers.py — Router kayıtları.

18 API router'ın import ve include_router() çağrıları burada yapılır.
"""

from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    """Tüm API router'larını uygulamaya kaydet."""
    from api.admin_router import router as admin_router
    from api.routes import router as main_router
    from auth.router import router as auth_router
    from webhooks.router import router as webhook_router
    from api.storage_router import router as storage_router
    from api.task_read_router import router as task_read_router
    from api.task_write_router import router as task_write_router
    from api.task_control_router import router as task_control_router
    from api.monitoring_router import router as monitoring_router
    from api.telegram_router import router as telegram_router
    from api.code_router import router as code_router
    from api.repair_router import router as repair_router
    from api.repair_admin_router import router as repair_admin_router
    from api.faz12_router import router as faz12_router
    from api.self_update_router import router as self_update_router
    from api.specialists_router import router as specialists_router
    from api.ceo_router import router as ceo_router
    from api.improvement_router import router as improvement_router
    from api.finance_router import router as finance_router
    from api.skills_router import router as skills_router

    app.include_router(main_router, prefix="/api/v1", tags=["Projeler & Heal"])
    app.include_router(admin_router, prefix="/api/v1", tags=["Admin"])
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(webhook_router, prefix="/api/v1", tags=["Webhooks"])
    app.include_router(task_read_router, prefix="/api/v1", tags=["Görevler - Okuma"])
    app.include_router(task_write_router, prefix="/api/v1", tags=["Görevler - Yazma"])
    app.include_router(task_control_router, prefix="/api/v1", tags=["Görevler - Kontrol"])
    app.include_router(monitoring_router, prefix="/api/v1", tags=["Monitoring"])
    app.include_router(telegram_router, prefix="/api/v1", tags=["Telegram"])
    app.include_router(code_router, prefix="/api/v1", tags=["Code Generation"])
    app.include_router(repair_router, prefix="/api/v1", tags=["Self-Repair"])
    app.include_router(repair_admin_router, prefix="/api/v1", tags=["Self-Repair-Admin"])
    app.include_router(faz12_router, prefix="/api/v1", tags=["Faz12-AI-Engine"])
    app.include_router(self_update_router, prefix="/api/v1", tags=["Self-Update"])
    app.include_router(improvement_router, prefix="/api/v1", tags=["Self-Improvement"])
    app.include_router(specialists_router, prefix="/api/v1", tags=["Agency Specialists"])
    app.include_router(ceo_router, prefix="/api/v1", tags=["CEO Audit"])
    app.include_router(finance_router, prefix="/api/v1", tags=["Financial Control"])
    app.include_router(storage_router, prefix="/api/v1", tags=["System Storage"])
    app.include_router(skills_router, prefix="/api/v1", tags=["Beceriler (Skills)"])
