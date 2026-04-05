# 🚀 PC'de Çalıştırma — Hızlı Başlangıç

## Docker ile (Önerilen — En Kolay)

### 1. Kurulum
```bash
# Repo'yu klonla / ZIP'i aç
cp .env.example .env
```

### 2. .env dosyasını düzenle (minimum gerekli)
```env
APP_ENV=development
JWT_SECRET=<python -c "import secrets; print(secrets.token_hex(64))">
ADMIN_SECRET=gizli-admin-sifresi
OPENAI_API_KEY=sk-...   # veya ANTHROPIC_API_KEY veya GEMINI_API_KEY
```

### 3. Başlat
```bash
docker compose up --build
```

### 4. Admin hesabı oluştur
```bash
# Yeni terminal'de:
docker compose exec app python -c "
import asyncio, sys; sys.path.insert(0,'.')
async def main():
    from db.session import AsyncSessionLocal, init_db
    from auth.jwt_auth import AuthService
    from db.models import User
    from sqlalchemy import update
    await init_db()
    async with AsyncSessionLocal() as db:
        u = await AuthService().register(db, 'admin@local.dev', 'admin1234')
        await db.execute(update(User).where(User.id==u.id).values(is_admin=True))
        await db.commit()
        print('✅ Admin: admin@local.dev / admin1234')
asyncio.run(main())
"
```

### 5. Panel'e eriş
- **Dashboard:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- Giriş: admin@local.dev / admin1234

---

## Docker Olmadan (Local Python)

### Gereksinimler
- Python 3.12+
- PostgreSQL 15+ (pgvector opsiyonel)
- Redis (opsiyonel — sadece Celery kullanılıyorsa)

### Kurulum
```bash
pip install -e ".[dev]"
cp .env.example .env
# .env'i düzenle (DATABASE_URL, JWT_SECRET, ADMIN_SECRET, en az 1 LLM key)
```

### Veritabanı
```bash
# PostgreSQL başlat ve veritabanı oluştur:
createdb ai_company

# Admin hesabı oluştur:
make create-admin
```

### Çalıştır
```bash
make run
# veya
uvicorn main:app --reload --port 8000
```

### Panel: http://localhost:8000

---

## Özet Komutlar

| Komut | Açıklama |
|-------|----------|
| `make setup` | .env oluştur |
| `make secret` | Güvenli JWT_SECRET üret |
| `make create-admin` | Admin kullanıcı oluştur |
| `make run` | Local development server |
| `make test` | Tüm testleri çalıştır |
| `docker compose up --build` | Docker ile tam sistem |
| `alembic upgrade head` | Production migration |

---

## Telegram Bot (Opsiyonel)

1. @BotFather'dan token al
2. `.env`'e ekle: `TELEGRAM_BOT_TOKEN=...`
3. Dashboard > Telegram > Setup'tan webhook kur
