from google.generativeai import GenerativeModel

model = GenerativeModel("gemini-1.5-flash")

def explain_severity(detections):
    if not detections:
        return {
            "severity": "None",
            "summary": "No civic issue detected."
        }

    issues = ", ".join(
        [f"{d['label']} (confidence {round(d['confidence']*100)}%)"
         for d in detections]
    )

    prompt = f"""
You are an urban governance expert in India.

Detected issues:
{issues}

Explain:
1. Overall severity (Low / Medium / High)
2. Why it matters to public health/safety
3. Recommended municipal action

Keep it concise and official.
"""

    response = model.generate_content(prompt)

    return {
        "severity": "Medium",  # can be inferred or parsed later
        "summary": response.text
    }
