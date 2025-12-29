import os
import json
from dotenv import load_dotenv
from google import genai

# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY environment variable not set")

# --------------------------------------------------
# Configure Gemini Client (NEW SDK)
# --------------------------------------------------
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-flash"

# --------------------------------------------------
# Helper: Severity mapping
# --------------------------------------------------
def map_severity(score: int) -> str:
    if score >= 8:
        return "Critical"
    if score >= 6:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"

# --------------------------------------------------
# Generate AI insights for civic issue
# --------------------------------------------------
def generate_ai_insights(issue_label: str, severity_score: int):
    """
    Returns:
    - description_en
    - description_hi (Hinglish)
    - why_it_matters
    - severity_level
    """

    prompt = f"""
You are an AI assistant for an Indian civic issue reporting platform.

Issue detected: "{issue_label}"
Severity score (1–10): {severity_score}

Generate a JSON object with EXACTLY these keys:

description_en:
- Short English description (1–2 lines)
- Simple, citizen-friendly

description_hi:
- Hinglish (Hindi in English letters)
- Simple language

why_it_matters:
- Why this issue matters for safety, health, or daily life
- 1–2 lines

severity_level:
- One of: Low, Medium, High, Critical

RULES:
- Output ONLY valid JSON
- No markdown
- No emojis
- No explanations outside JSON
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        raw_text = response.text.strip()
        ai_data = json.loads(raw_text)

        return {
            "description_en": ai_data.get(
                "description_en",
                f"{issue_label} detected in the area."
            ),
            "description_hi": ai_data.get(
                "description_hi",
                f"{issue_label} yahan dekha gaya hai."
            ),
            "why_it_matters": ai_data.get(
                "why_it_matters",
                "This issue can impact public health and daily life."
            ),
            "severity_level": ai_data.get(
                "severity_level",
                map_severity(severity_score)
            ),
        }

    except Exception as e:
        print("⚠️ Gemini error:", e)

        # 🔒 Safe fallback
        return {
            "description_en": f"{issue_label} detected in the area.",
            "description_hi": f"{issue_label} yahan dekha gaya hai.",
            "why_it_matters": "This issue may cause inconvenience or safety risks.",
            "severity_level": map_severity(severity_score),
        }
