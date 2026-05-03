import requests
import sys

def check_ollama(url="http://localhost:11434"):
    try:
        print(f"Checking Ollama at {url}...")
        resp = requests.get(url, timeout=2)
        if resp.status_code == 200:
            print("✅ Ollama is running.")
            return True
        else:
            print(f"⚠️ Ollama responded with status code: {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Ollama. Is it running on port 11434?")
        return False
    except Exception as e:
        print(f"❌ Error checking Ollama: {e}")
        return False

def check_model(model_name="llama3.2-vision:11b", url="http://localhost:11434/api/tags"):
    try:
        print(f"Checking for model '{model_name}'...")
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            found = any(m['name'].startswith(model_name) or m['name'] == model_name for m in models)
            if found:
                print(f"✅ Model '{model_name}' found.")
            else:
                print(f"❌ Model '{model_name}' NOT found in installed models.")
                print("Available models:", [m['name'] for m in models])
        else:
            print(f"⚠️ Failed to list models. Status: {resp.status_code}")
    except Exception as e:
        print(f"❌ Error checking models: {e}")

if __name__ == "__main__":
    if check_ollama():
        check_model()
    else:
        sys.exit(1)
