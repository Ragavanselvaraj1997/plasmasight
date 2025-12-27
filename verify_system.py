import requests
import sys
import asyncio
import websockets
import json

def check_service(name, url, expected_status=200):
    print(f"Checking {name} at {url}...", end=" ")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            print(f"✅ OK ({response.status_code})")
            return True
        else:
            print(f"❌ FAIL (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ FAIL (Error: {e})")
        return False

def check_inference():
    url = "http://localhost:8000/api/v1/predict/etch-depth"
    payload = {"sensor": {}, "image": {}}
    print(f"Checking Inference Prediction at {url}...", end=" ")
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("✅ OK")
            return True
        else:
            print(f"❌ FAIL (Status: {response.status_code}, Body: {response.text})")
            return False
    except Exception as e:
        print(f"❌ FAIL (Error: {e})")
        return False

async def check_websocket():
    uri = "ws://localhost:8001/ws/metrics"
    print(f"Checking Backend WebSocket at {uri}...", end=" ")
    try:
        async with websockets.connect(uri) as websocket:
            msg = await websocket.recv()
            data = json.loads(msg)
            if "predicted_depth" in data:
                print("✅ OK")
                return True
            else:
                print("❌ FAIL (Invalid Data)")
                return False
    except Exception as e:
        print(f"❌ FAIL (Error: {e})")
        return False

async def main_async():
    print("=== System Verification ===")
    
    frontend = check_service("Frontend", "http://localhost:5173")
    backend = check_service("Backend", "http://localhost:8001")
    inference_health = check_service("Inference Health", "http://localhost:8000/docs", 200)
    inference_pred = check_inference()
    ws_health = await check_websocket()

    print("\n=== Summary ===")
    if all([frontend, backend, inference_health, inference_pred, ws_health]):
        print("✅ ALL SYSTEMS OPERATIONAL")
        sys.exit(0)
    else:
        print("❌ SOME SYSTEMS FAILED")
        sys.exit(1)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
