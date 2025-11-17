import os
import json

CONFIG_PATH = "config.json"


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            k = str(data.get("GEMINI_API_KEY", "")).strip()
            return k
        except Exception:
            return ""
    return ""


def set_api_key(key: str) -> bool:
    k = str(key).strip()
    try:
        data = {}
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}
        data["GEMINI_API_KEY"] = k
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.environ["GEMINI_API_KEY"] = k
        return True
    except Exception:
        return False

