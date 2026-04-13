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

docker compose exec -e _ADM_EMAIL=%ADMIN_EMAIL% -e _ADM_PASS=%ADMIN_PASS% app python -c "
import asyncio, sys, os
sys.path.insert(0, '.')
async def main():
    email    = os.environ.get('_ADM_EMAIL','')
    password = os.environ.get('_ADM_PASS','')
    if not email or len(password) < 10:
        print('HATA: E-posta veya parola gecersiz (min 10 karakter).')
        sys.exit(1)
    from hub_infra.persistence.session import AsyncSessionLocal, init_db
    from hub_infra.api.routers.auth.jwt_auth import AuthService
    from hub_infra.persistence.models import User
    from sqlalchemy import update
    await init_db()
    async with AsyncSessionLocal() as db:
        try:
            u = await AuthService().register(db, email, password)
            await db.execute(update(User).where(User.id==u.id).values(is_admin=True))
            await db.commit()
            print(f'Admin olusturuldu: {email}')
        except Exception as e:
            if 'already' in str(e).lower() or '409' in str(e):
                print(f'Zaten kayitli: {email}')
            else:
                print(f'Hata: {e}')
                sys.exit(1)
asyncio.run(main())
"

echo.
echo  Panel: http://localhost:8000
pause
