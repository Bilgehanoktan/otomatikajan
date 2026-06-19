@echo off
chcp 65001 >nul
title Admin Hesabi Olustur

echo.
echo  [GUVENLiK] E-posta ve parola interaktif sorulacak.
echo  Hardcoded varsayilan kullanilmaz.
echo.

set /p ADMIN_EMAIL=Admin e-posta: 
if "%ADMIN_EMAIL%"=="" ( echo Eposta bos olamaz & pause & exit /b 1 )

set /p ADMIN_PASS=Parola (min 10 karakter): 
if "%ADMIN_PASS%"=="" ( echo Parola bos olamaz & pause & exit /b 1 )

echo Olusturuluyor: %ADMIN_EMAIL%

set "CMD_STR=import asyncio, sys, os; sys.path.insert(0, '.'); \
async def main(): \
    email = os.environ.get('_ADM_EMAIL',''); \
    password = os.environ.get('_ADM_PASS',''); \
    if not email or len(password) < 8: \
        print('HATA: E-posta veya parola gecersiz (min 8 karakter).'); \
        sys.exit(1); \
    from libs.db.session import async_session, init_db; \
    from services.auth.jwt_auth import auth_service; \
    from libs.db.models.auth_models import Operator; \
    from sqlalchemy import update; \
    await init_db(); \
    async with async_session() as db: \
        try: \
            u = await auth_service.register(db, email, password); \
            await db.execute(update(Operator).where(Operator.id==u.id).values(role='SOVEREIGN_PRIME')); \
            await db.commit(); \
            print(f'Admin olusturuldu: {email}'); \
        except Exception as e: \
            if 'kayitli' in str(e).lower() or '409' in str(e): \
                print(f'Zaten kayitli: {email}'); \
            else: \
                print(f'Hata: {e}'); \
                sys.exit(1); \
asyncio.run(main())"

where docker >nul 2>&1
if errorlevel 1 (
    echo [LOKAL] Docker bulunamadi, dogrudan calistiriliyor...
    set "_ADM_EMAIL=%ADMIN_EMAIL%"
    set "_ADM_PASS=%ADMIN_PASS%"
    py -3.13 -c "%CMD_STR%"
) else (
    docker ps >nul 2>&1
    if errorlevel 1 (
        echo [LOKAL] Docker daemon calismiyor, dogrudan calistiriliyor...
        set "_ADM_EMAIL=%ADMIN_EMAIL%"
        set "_ADM_PASS=%ADMIN_PASS%"
        py -3.13 -c "%CMD_STR%"
    ) else (
        echo [DOCKER] Container icinde calistiriliyor...
        docker compose exec -e _ADM_EMAIL=%ADMIN_EMAIL% -e _ADM_PASS=%ADMIN_PASS% app python -c "%CMD_STR%"
    )
)

echo.
echo  Panel: http://localhost:8000
pause
