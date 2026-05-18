import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "gemma3:4b"


def get_model() -> str:
    return os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)


def parse_json_response(raw: str) -> dict | None:
    try:
        first = raw.index("{")
        last = raw.rindex("}")
        clean = raw[first:last+1]
        return json.loads(clean)
    except (ValueError, json.JSONDecodeError):
        return None


def call_ollama(model: str, user_message: str, timeout: int = 60) -> str | None:
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "stream": False,
        "options": {"temperature": 0}
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("message", {}).get("content", "")
    except requests.exceptions.ConnectionError:
        print(f"[OLLAMA] No se pudo conectar a {OLLAMA_URL}")
        return None
    except Exception as e:
        print(f"[OLLAMA] Error: {e}")
        return None


def call_ollama_json(model: str, user_message: str, timeout: int = 60) -> dict:
    raw = call_ollama(model, user_message, timeout)
    if raw is None:
        return {}
    parsed = parse_json_response(raw)
    if parsed is None:
        print(f"[OLLAMA] No se pudo parsear JSON. Raw: {raw[:200]}")
        return {}
    return parsed
