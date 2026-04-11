import asyncio
import websockets
import json
import jwt
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from config import JWT_SECRET

async def test_ws_auth():
    uri = "ws://localhost:8000/ws/logs"
    
    # 1. Test Unauthorized (No token)
    print("--- Testing Unauthorized (No Token) ---")
    try:
        async with websockets.connect(uri) as websocket:
            msg = await websocket.recv()
            print(f"Received: {msg}")
            data = json.loads(msg)
            if data.get("error") == "Unauthorized":
                print("PASSED: Correctly received Unauthorized error.")
            else:
                print(f"FAILED: Received unexpected message: {msg}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed as expected. Code: {e.code}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test Authorized (Valid Token)
    print("\n--- Testing Authorized (Valid Token) ---")
    payload = {
        "sub": "00000000-0000-0000-0000-000000000000", 
        "email": "test@sovereign.agi",
        "type": "access",
        "roles": ["admin"]
    }
    token = jwt.encode(
        {**payload, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)},
        JWT_SECRET,
        algorithm="HS256"
    )
    
    try:
        async with websockets.connect(f"{uri}?token={token}") as websocket:
            print("Connected successfully with token!")
            await websocket.send("ping")
            response = await websocket.recv()
            print(f"Received: {response}")
            if "pong" in response or "event_bus" in response or "type" in response:
                 # It might receive recent events first
                 print("PASSED: Received data from server.")
            else:
                print(f"FAILED: Unexpected reply: {response}")
            
    except Exception as e:
        print(f"FAILED: Could not connect with valid token: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws_auth())
