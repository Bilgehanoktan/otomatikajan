import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from services.workflow_api.main import create_app


async def main():
    app = create_app()
    print("--- REGISTERED ROUTES ---")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', [])
            print(f"{list(methods)} {route.path}")
    print("--- END ---")

if __name__ == "__main__":
    asyncio.run(main())
