import os
import socket
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path

# Manually load env just like app does
# Assumes this script is run from backend/ dir
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / ".env"
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

url = os.getenv("QDRANT_URL")
print(f"QDRANT_URL: '{url}'")

if not url:
    print("URL is empty!")
else:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        print(f"Resolving hostname: '{hostname}'")
        ip = socket.gethostbyname(hostname)
        print(f"Successfully resolved to IP: {ip}")
    except Exception as e:
        print(f"DNS Resolution Failed: {e}")
