from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.services.risk_assessment import assess_assessment_risk


def generate_patient_risk_trends(
    db: Session,
    patient_id: int,
) -> dict[str, Any]:

    assessments = list(
        db.scalars(
            select(AssessmentSession)
            .where(
                AssessmentSession.patient_id == patient_id
            )
            .order_by(
                AssessmentSession.started_at.asc()
            )
        ).all()
    )

    if not assessments:
        return {
            "patient_id": patient_id,
            "assessment_count": 0,
            "latest": None,
            "trend": "no_data",
            "assessments": [],
        }

    history: list[dict[str, Any]] = []

    for assessment in assessments:
        result = assess_assessment_risk(
            db=db,
            assessment_id=assessment.id,
        )

        risk_score = result.get("risk_score", {})

        score = risk_score.get("score", 0)
        risk_level = risk_score.get(
            "risk_level",
            "unknown",
        )

        history.append(
            {
                "assessment_id": assessment.id,
                "assessment_type": assessment.assessment_type,
                "status": assessment.status,
                "started_at": (
                    assessment.started_at.isoformat()
                    if assessment.started_at
                    else None
                ),
                "completed_at": (
                    assessment.completed_at.isoformat()
                    if assessment.completed_at
                    else None
                ),
                "risk_score": score,
                "risk_level": risk_level,
            }
        )

    # ---------------------------------------------------------
    # Calculate changes between assessments
    # ---------------------------------------------------------

    for index, item in enumerate(history):

        if index == 0:
            item["score_change"] = None
            item["direction"] = "baseline"
            continue

        previous = history[index - 1]

        current_score = item["risk_score"]
        previous_score = previous["risk_score"]

        change = current_score - previous_score

        item["score_change"] = change

        if change > 0:
            item["direction"] = "increased"
        elif change < 0:
            item["direction"] = "decreased"
        else:
            item["direction"] = "unchanged"

    latest = history[-1]

    # ---------------------------------------------------------
    # Overall trend
    # ---------------------------------------------------------

    if len(history) < 2:
        overall_trend = "insufficient_data"
    else:
        first_score = history[0]["risk_score"]
        latest_score = latest["risk_score"]

        if latest_score > first_score:
            overall_trend = "increased"
        elif latest_score < first_score:
            overall_trend = "decreased"
        else:
            overall_trend = "unchanged"

    # ---------------------------------------------------------
    # Summary statistics
    # ---------------------------------------------------------

    scores = [
        item["risk_score"]
        for item in history
    ]

    highest_score = max(scores)
    lowest_score = min(scores)

    return {
        "patient_id": patient_id,
        "assessment_count": len(history),
        "latest": latest,
        "trend": overall_trend,
        "highest_risk_score": highest_score,
        "lowest_risk_score": lowest_score,
        "assessments": history,
    }