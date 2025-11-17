import requests
from config import get_api_key

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def get_insight(sel_intent, sel_gender, top_segments, median) -> str:
    prompt = (
        f"Provide concise risk guidance. Median ECL={median:.2f}. "
        f"Recommend actions for highest-risk segments."
    )
    parts = [
        {"text": prompt},
        {"text": f"Selected intents={sel_intent}, genders={sel_gender}"},
        {"text": f"Top segments: {top_segments}"},
    ]
    payload = {"contents": [{"parts": parts}]}
    try:
        api_key = get_api_key()
        if not api_key:
            return "No insight available (missing API key)"
        r = requests.post(
            API_URL,
            headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
            json=payload,
            timeout=10,
        )
        if not r.ok:
            return f"No insight available (HTTP {r.status_code})"
        js = r.json()
        return (
            js.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text")
        ) or "No insight available"
    except Exception:
        return "No insight available"
