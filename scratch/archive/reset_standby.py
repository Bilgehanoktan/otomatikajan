from services.governance.standby_manager import StandbyManager
import asyncio

async def main():
    StandbyManager.reset_to_standby()
    print("System reset to STANDBY MODE.")

if __name__ == "__main__":
    asyncio.run(main())
