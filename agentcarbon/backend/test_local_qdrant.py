import requests
try:
    r = requests.get("http://localhost:6333/collections")
    print(f"Status: {r.status_code}")
    print(f"Collections: {r.json()}")
except Exception as e:
    print(f"Connection Failed: {e}")
