import socket
from urllib.parse import urlparse

url = "https://c363f2b2-a22a-4a49-af1a-990732e04e7d.europe-west3-0.gcp.cloud.qdrant.io"
print(f"Testing New URL: '{url}'")

try:
    parsed = urlparse(url)
    hostname = parsed.hostname
    print(f"Resolving hostname: '{hostname}'")
    ip = socket.gethostbyname(hostname)
    print(f"Successfully resolved to IP: {ip}")
except Exception as e:
    print(f"DNS Resolution Failed: {e}")
