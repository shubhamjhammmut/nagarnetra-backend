from fastapi import APIRouter, UploadFile, File, Form
from ai.mock_ai import analyze_issue

router = APIRouter()

@router.post("/detect")
async def detect_issue(
    image: UploadFile = File(...),
    description: str = Form(...)
):
    ai_result = analyze_issue(description)

    return {
        "success": True,
        "detected_issue": ai_result["issue_type"],
        "priority": ai_result["priority"],
        "urgency_score": ai_result["urgency_score"],
        "message": "AI analysis completed successfully"
    }
