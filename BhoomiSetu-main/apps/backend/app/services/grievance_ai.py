from app.schemas.intelligence import GrievanceClassification


def classify_grievance(description: str) -> GrievanceClassification:
    text = description.lower()
    rules = [
        (
            ("payment", "compensation", "amount", "bank"),
            "compensation",
            "Compensation & Treasury Cell",
        ),
        (("owner", "title", "inheritance", "name"), "ownership", "Land Records Department"),
        (
            ("area", "boundary", "survey", "measurement"),
            "measurement",
            "Survey & Settlement Department",
        ),
        (
            ("rehabilitation", "resettlement", "house", "livelihood"),
            "rehabilitation",
            "R&R Department",
        ),
    ]
    category, department = "process", "Land Acquisition Office"
    for keywords, candidate, destination in rules:
        if any(keyword in text for keyword in keywords):
            category, department = candidate, destination
            break
    urgent = any(term in text for term in ("urgent", "court", "homeless", "fraud", "deadline"))
    high = urgent or any(term in text for term in ("not received", "months", "wrong", "rejected"))
    priority = "urgent" if urgent else "high" if high else "medium" if len(text) > 120 else "low"
    return GrievanceClassification(
        category=category,
        priority=priority,
        suggested_department=department,
        confidence=0.91 if category != "process" else 0.76,
        rationale=(
            f"Matched {category} grievance indicators; officer confirmation "
            "is required before routing."
        ),
    )
