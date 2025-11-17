import os
import json
import hashlib
import pandas as pd

USERS_PATH = "users.csv"


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def _ensure_users_file():
    if not os.path.exists(USERS_PATH):
        df = pd.DataFrame(columns=["username", "password_hash", "role", "segments_json"]) 
        df.to_csv(USERS_PATH, index=False)


def ensure_default_users():
    _ensure_users_file()
    df = pd.read_csv(USERS_PATH) if os.path.exists(USERS_PATH) else pd.DataFrame()
    existing = set(df["username"].astype(str).tolist()) if not df.empty else set()
    rows = []
    if "analyst1" not in existing:
        rows.append({
            "username": "analyst1",
            "password_hash": _hash("Analyst@123"),
            "role": "analyst",
            "segments_json": json.dumps({"*": ["*"]}),
        })
    if "cro1" not in existing:
        rows.append({
            "username": "cro1",
            "password_hash": _hash("CRO@123"),
            "role": "cro",
            "segments_json": json.dumps({"*": ["*"]}),
        })
    if rows:
        add = pd.DataFrame(rows)
        df = pd.concat([df, add], ignore_index=True) if not df.empty else add
        df.to_csv(USERS_PATH, index=False)


def create_user(username: str, password: str, role: str, segments: dict | None = None) -> bool:
    _ensure_users_file()
    username = str(username).strip().lower()
    if not username or not password or role not in {"analyst", "cro"}:
        return False
    df = pd.read_csv(USERS_PATH)
    if (df["username"].astype(str).str.lower() == username).any():
        return False
    seg = segments or {"*": ["*"]}
    row = {
        "username": username,
        "password_hash": _hash(password),
        "role": role,
        "segments_json": json.dumps(seg),
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(USERS_PATH, index=False)
    return True


def verify_login(username: str, password: str) -> dict | None:
    _ensure_users_file()
    df = pd.read_csv(USERS_PATH)
    m = df["username"].astype(str).str.lower() == str(username).strip().lower()
    if not m.any():
        return None
    row = df[m].iloc[0]
    if str(row["password_hash"]) != _hash(password):
        return None
    try:
        seg = json.loads(str(row["segments_json"]))
    except Exception:
        seg = {"*": ["*"]}
    return {"username": row["username"], "role": row["role"], "segments": seg}


def get_user(username: str) -> dict | None:
    if not os.path.exists(USERS_PATH):
        return None
    df = pd.read_csv(USERS_PATH)
    m = df["username"].astype(str).str.lower() == str(username).strip().lower()
    if not m.any():
        return None
    row = df[m].iloc[0]
    try:
        seg = json.loads(str(row["segments_json"]))
    except Exception:
        seg = {"*": ["*"]}
    return {"username": row["username"], "role": row["role"], "segments": seg}


def list_users() -> pd.DataFrame:
    _ensure_users_file()
    return pd.read_csv(USERS_PATH)


def update_segments(username: str, segments: dict) -> bool:
    _ensure_users_file()
    df = pd.read_csv(USERS_PATH)
    m = df["username"].astype(str).str.lower() == str(username).strip().lower()
    if not m.any():
        return False
    df.loc[m, "segments_json"] = json.dumps(segments)
    df.to_csv(USERS_PATH, index=False)
    return True
