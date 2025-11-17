import os
import pandas as pd


REPORTS_DIR = "reports"
INSIGHTS_PATH = "insights.csv"


def _ensure_paths():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def save_report(g: pd.DataFrame, med: float) -> str:
    _ensure_paths()
    rid = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = g.copy()
    out["median"] = med
    out["rid"] = rid
    out["saved_at"] = pd.Timestamp.now()
    out.to_csv(os.path.join(REPORTS_DIR, f"report_{rid}.csv"), index=False)
    return rid


def list_reports() -> pd.DataFrame:
    _ensure_paths()
    rows = []
    for fn in os.listdir(REPORTS_DIR):
        if fn.startswith("report_") and fn.endswith(".csv"):
            rid = fn.replace("report_", "").replace(".csv", "")
            rows.append({"rid": rid, "file": fn})
    df = pd.DataFrame(rows, columns=["rid", "file"])  # ensure columns exist
    if df.empty or "rid" not in df.columns:
        return df
    return df.sort_values("rid", ascending=False)


def load_report(rid: str) -> pd.DataFrame:
    path = os.path.join(REPORTS_DIR, f"report_{rid}.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def save_insight(rid: str, note: str, rec: str) -> str:
    _ensure_paths()
    iid = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    row = {
        "iid": iid,
        "rid": rid,
        "note": note,
        "recommendation": rec,
        "saved_at": pd.Timestamp.now(),
        "cro_decision": "pending",
        "cro_note": "",
    }
    df = pd.DataFrame([row])
    if os.path.exists(INSIGHTS_PATH):
        old = pd.read_csv(INSIGHTS_PATH)
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(INSIGHTS_PATH, index=False)
    return iid


def list_insights() -> pd.DataFrame:
    if not os.path.exists(INSIGHTS_PATH):
        return pd.DataFrame()
    return pd.read_csv(INSIGHTS_PATH)


def update_insight(iid: str, decision: str, cro_note: str) -> bool:
    if not os.path.exists(INSIGHTS_PATH):
        return False
    df = pd.read_csv(INSIGHTS_PATH)
    if "iid" not in df.columns:
        return False
    m = df["iid"].astype(str) == str(iid)
    if not m.any():
        return False
    df.loc[m, "cro_decision"] = decision
    df.loc[m, "cro_note"] = cro_note
    df.to_csv(INSIGHTS_PATH, index=False)
    return True
