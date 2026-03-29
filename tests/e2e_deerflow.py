
import asyncio
import os
import httpx
from db.session import AsyncSessionLocal
from db.repository import ProjectRepository
from db.models import ProjectStatus

async def main():
    base_url = "http://localhost:8000/api/v1"
    
    # 1. Login
    async with httpx.AsyncClient() as client:
        print("Logging in...")
        resp = await client.post(
            f"{base_url}/auth/login",
            json={"email": "admin@example.com", "password": "admin12345678"}
        )
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} - {resp.text}")
            return
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create Task
        print("Creating DeerFlow task...")
        task_data = {
            "title": "E2E DeerFlow Prompt",
            "description": "Lutfen bana 1'den 5'e kadar say. Her sayi yeni satirda olsun.",
            "assigned_agent": "deerflow"
        }
        resp = await client.post(f"{base_url}/tasks", json=task_data, headers=headers)
        if resp.status_code != 201:
            print(f"Task creation failed: {resp.status_code} - {resp.text}")
            return
        
        job_id = resp.json()["job_id"]
        task_id = resp.json()["id"]
        print(f"Task created! Task ID: {task_id}, Job ID: {job_id}")
        
        # 3. Wait for result
        print("Waiting for task completion (polling for 60s)...")
        for i in range(60):
            await asyncio.sleep(2)
            resp = await client.get(f"{base_url}/tasks/{task_id}", headers=headers)
            if resp.status_code != 200:
                print(f"Poll failed: {resp.text}")
                continue
            
            data = resp.json()
            status = data.get("status")
            print(f"Iteration {i}: Status={status}")
            
            if status == "completed":
                print("\nSUCCESS! Task completed!")
                print(f"Report:\n{data.get('report')}")
                return
            elif status in ["error", "failed", "cancelled"]:
                print(f"\nFAILED! Task status: {status}")
                print(f"Error detail: {data.get('error_detail')}")
                return
                
        print("\nTIMEOUT! Task didn't complete in time.")

if __name__ == "__main__":
    asyncio.run(main())
