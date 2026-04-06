import asyncio
import os
from sqlalchemy import select, func
from packages.persistence.session import AsyncSessionLocal, init_db, is_db_available
from packages.persistence.models import User, Project

async def check_persistence():
    print("--- User & Project Persistence Check ---")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        res_u = await packages.persistence.execute(select(func.count(User.id)))
        count_u = res_u.scalar()
        
        res_p = await packages.persistence.execute(select(func.count(Project.id)))
        count_p = res_p.scalar()
        
        print(f"Mevcut Kullanıcı: {count_u}")
        print(f"Mevcut Proje/Task: {count_p}")
        
        if count_p > 0:
            res_p_last = await packages.persistence.execute(select(Project).order_by(Project.created_at.desc()).limit(3))
            ps = res_p_last.scalars().all()
            for p in ps:
                print(f" - [{p.status}] {p.title} (ID: {str(p.id)[:8]}..., Kayıt: {p.created_at})")

if __name__ == "__main__":
    asyncio.run(check_persistence())
