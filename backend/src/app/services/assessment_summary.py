from typing import Any


def generate_assessment_summary(
    *,
    assessment: dict[str, Any],
    risk_score: dict[str, Any],
    risk_factors: dict[str, Any],
    health_concerns: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate a structured assessment summary.

    This function summarizes existing assessment data.
    It does not diagnose conditions or replace clinical judgment.
    """

    concern_count = len(health_concerns)
    recommendation_count = len(recommendations)

    high_risk_factors = [
        factor
        for factor in risk_factors.get("factors", [])
        if factor.get("severity") == "high"
    ]

    urgent_concerns = [
        concern
        for concern in health_concerns
        if concern.get("urgent_flag") is True
    ]

    summary_parts: list[str] = []

    assessment_type = assessment.get("assessment_type")

    if assessment_type:
        summary_parts.append(
            f"Assessment type: {assessment_type}."
        )

    summary_parts.append(
        f"Risk level: {risk_score.get('risk_level', 'unknown')}."
    )

    summary_parts.append(
        f"Risk score: {risk_score.get('score', 0)}."
    )

    summary_parts.append(
        f"Health concerns identified: {concern_count}."
    )

    summary_parts.append(
        f"Risk factors identified: "
        f"{risk_factors.get('factor_count', 0)}."
    )

    summary_parts.append(
        f"Recommendations generated: "
        f"{recommendation_count}."
    )

    if high_risk_factors:
        summary_parts.append(
            f"High-severity risk factors identified: "
            f"{len(high_risk_factors)}."
        )

    if urgent_concerns:
        summary_parts.append(
            f"Urgent health concerns recorded: "
            f"{len(urgent_concerns)}."
        )

    return {
        "assessment_id": assessment.get("id"),
        "assessment_type": assessment_type,
        "risk_level": risk_score.get("risk_level"),
        "risk_score": risk_score.get("score", 0),
        "risk_factor_count": risk_factors.get(
            "factor_count",
            0,
        ),
        "health_concern_count": concern_count,
        "urgent_concern_count": len(urgent_concerns),
        "recommendation_count": recommendation_count,
        "high_risk_factor_count": len(high_risk_factors),
        "summary": " ".join(summary_parts),
        "high_risk_factors": high_risk_factors,
        "urgent_concerns": urgent_concerns,
        "recommendations": recommendations,
    }