import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load .env
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

print(f"Testing connection to: {QDRANT_URL}")

if not QDRANT_URL:
    print("❌ QDRANT_URL is not set.")
    sys.exit(1)

try:
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    collections = client.get_collections()
    print("✅ Connection successful!")
    print(f"Collections: {collections}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    # Inspect URL for common issues
    if "getaddrinfo failed" in str(e):
        print("\nPossible causes:")
        print("1. The hostname is incorrect.")
        print("2. DNS resolution failed.")
        print("3. Check for trailing slashes or protocol mismatches.")
