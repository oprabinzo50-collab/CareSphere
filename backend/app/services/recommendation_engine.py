from typing import Any


def generate_recommendations(
    risk_factors: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Generate transparent rule-based recommendations
    from identified risk factors.

    These recommendations are informational and require
    appropriate clinical review.
    """

    recommendations: list[dict[str, Any]] = []

    factors = risk_factors.get("factors", [])

    for factor in factors:

        factor_name = factor.get("factor")

        if factor_name in {
            "elevated_systolic_blood_pressure",
            "elevated_diastolic_blood_pressure",
        }:
            recommendations.append(
                {
                    "recommendation_type": "clinical_follow_up",
                    "title": "Blood pressure follow-up",
                    "recommendation_text": (
                        "Consider reviewing the blood pressure "
                        "reading and repeating measurements as "
                        "clinically appropriate."
                    ),
                    "priority": "high",
                    "source_type": "rule_based",
                    "ai_generated": False,
                    "clinician_review_required": True,
                }
            )

        elif factor_name == "high_bmi":
            recommendations.append(
                {
                    "recommendation_type": "lifestyle",
                    "title": "Weight and lifestyle review",
                    "recommendation_text": (
                        "Consider reviewing nutrition, physical "
                        "activity, and other relevant lifestyle "
                        "factors."
                    ),
                    "priority": "moderate",
                    "source_type": "rule_based",
                    "ai_generated": False,
                    "clinician_review_required": True,
                }
            )

        elif factor_name == "low_bmi":
            recommendations.append(
                {
                    "recommendation_type": "lifestyle",
                    "title": "Nutrition review",
                    "recommendation_text": (
                        "Consider reviewing nutritional status "
                        "and relevant dietary factors."
                    ),
                    "priority": "moderate",
                    "source_type": "rule_based",
                    "ai_generated": False,
                    "clinician_review_required": True,
                }
            )

        elif factor_name == "smoking":
            recommendations.append(
                {
                    "recommendation_type": "lifestyle",
                    "title": "Smoking cessation support",
                    "recommendation_text": (
                        "Consider discussing smoking cessation "
                        "and appropriate support options."
                    ),
                    "priority": "high",
                    "source_type": "rule_based",
                    "ai_generated": False,
                    "clinician_review_required": True,
                }
            )

        elif factor_name == "low_physical_activity":
            recommendations.append(
                {
                    "recommendation_type": "lifestyle",
                    "title": "Physical activity review",
                    "recommendation_text": (
                        "Consider reviewing physical activity "
                        "habits and appropriate activity goals."
                    ),
                    "priority": "moderate",
                    "source_type": "rule_based",
                    "ai_generated": False,
                    "clinician_review_required": True,
                }
            )

        elif factor_name == "urgent_health_concern":
            recommendations.append(
                {
                    "recommendation_type": "clinical_follow_up",
                    "title": "Review urgent health concern",
                    "recommendation_text": (
                        "An urgent health concern was recorded. "
                        "Review the concern promptly according "
                        "to clinical workflow."
                    ),
                    "priority": "high",
                    "source_type": "rule_based",
                    "ai_generated": False,
                    "clinician_review_required": True,
                }
            )

        elif factor_name == "active_medical_history":
            recommendations.append(
                {
                    "recommendation_type": "clinical_review",
                    "title": "Review active medical history",
                    "recommendation_text": (
                        "Consider reviewing active medical "
                        "conditions when interpreting the "
                        "current assessment."
                    ),
                    "priority": "moderate",
                    "source_type": "rule_based",
                    "ai_generated": False,
                    "clinician_review_required": True,
                }
            )

    return recommendations