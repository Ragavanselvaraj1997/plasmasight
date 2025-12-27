import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8001/ws/metrics"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            msg = await websocket.recv()
            print(f"Received message: {msg}")
            data = json.loads(msg)
            if "predicted_depth" in data:
                print("✅ Data validation passed")
            else:
                print("❌ Data missing required fields")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
