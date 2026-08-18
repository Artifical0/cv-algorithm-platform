import json
import os
import urllib.request


base_url = os.getenv("ALGORITHM_BASE_URL", "http://127.0.0.1:8000")
asset_uri = os.getenv("ALGORITHM_TEST_ASSET", "/data/test/000000000285.jpg")

with urllib.request.urlopen(f"{base_url}/health", timeout=30) as response:
    print(response.read().decode())

payload = json.dumps(
    {
        "request_id": "direct-gpu-smoke",
        "input": {"asset_uri": asset_uri},
        "parameters": {"confidence": 0.5},
    }
).encode()
request = urllib.request.Request(
    f"{base_url}/predict",
    payload,
    {"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=180) as response:
    print(response.read().decode())
