import os
import json

CONFIG_PATH = "config.json"
ENV_PATH = ".env"


def _read_env_file_var(name: str) -> str:
    try:
        if not os.path.exists(ENV_PATH):
            return ""
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == name:
                    return v.strip().strip('"').strip("'")
    except Exception:
        return ""
    return ""


def get_api_key() -> str:
    # Prefer Streamlit Cloud secrets if available
    try:
        import streamlit as st  # local import to avoid hard dep in non-UI contexts
        s = str(st.secrets.get("GEMINI_API_KEY", "")).strip()
        if s:
            return s
    except Exception:
        pass
    # Fallback to environment variable
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key
    # Fallback to .env file (not committed)
    env_key = _read_env_file_var("GEMINI_API_KEY")
    if env_key:
        return env_key
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
