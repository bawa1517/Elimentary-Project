import os
import requests

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
API_KEY = os.environ.get("GEMINI_API_KEY", "")


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
        if not API_KEY:
            return "No insight available"
        r = requests.post(
            API_URL,
            headers={"Content-Type": "application/json", "X-goog-api-key": API_KEY},
            json=payload,
            timeout=10,
        )
        if not r.ok:
            return "No insight available"
        js = r.json()
        return (
            js.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text")
        ) or "No insight available"
    except Exception:
        return "No insight available"
