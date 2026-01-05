def analyze_issue(description: str):
    description_lower = description.lower()

    if "garbage" in description_lower or "waste" in description_lower:
        issue_type = "Garbage Overflow"
        priority = "Important"
        urgency_score = 85
    else:
        issue_type = "Unknown Issue"
        priority = "Normal"
        urgency_score = 40

    return {
        "issue_type": issue_type,
        "priority": priority,
        "urgency_score": urgency_score
    }
