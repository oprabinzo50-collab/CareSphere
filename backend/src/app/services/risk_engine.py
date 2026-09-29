from typing import Any


def calculate_risk_factors(
    *,
    vital_signs: dict[str, Any] | None = None,
    lifestyle: dict[str, Any] | None = None,
    health_concerns: list[dict[str, Any]] | None = None,
    medical_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Calculate structured risk factors from patient assessment data.

    This first version is intentionally rule-based and transparent.
    It does not make a medical diagnosis.
    """

    vital_signs = vital_signs or {}
    lifestyle = lifestyle or {}
    health_concerns = health_concerns or []
    medical_history = medical_history or []

    factors: list[dict[str, Any]] = []

    # Blood pressure
    systolic = vital_signs.get("blood_pressure_systolic")
    diastolic = vital_signs.get("blood_pressure_diastolic")

    if systolic is not None and systolic >= 140:
        factors.append(
            {
                "factor": "elevated_systolic_blood_pressure",
                "severity": "high",
                "value": systolic,
            }
        )

    if diastolic is not None and diastolic >= 90:
        factors.append(
            {
                "factor": "elevated_diastolic_blood_pressure",
                "severity": "high",
                "value": diastolic,
            }
        )

    # BMI
    bmi = vital_signs.get("bmi")

    if bmi is not None:
        if bmi >= 30:
            factors.append(
                {
                    "factor": "high_bmi",
                    "severity": "moderate",
                    "value": bmi,
                }
            )
        elif bmi < 18.5:
            factors.append(
                {
                    "factor": "low_bmi",
                    "severity": "moderate",
                    "value": bmi,
                }
            )

    # Smoking
    smoking_status = lifestyle.get("smoking_status")

    if smoking_status:
        normalized_smoking = str(smoking_status).lower()

        if normalized_smoking not in {
            "never",
            "none",
            "non_smoker",
            "non-smoker",
        }:
            factors.append(
                {
                    "factor": "smoking",
                    "severity": "high",
                    "value": smoking_status,
                }
            )

    # Physical activity
    activity_level = lifestyle.get("physical_activity_level")

    if activity_level:
        normalized_activity = str(activity_level).lower()

        if normalized_activity in {
            "low",
            "sedentary",
            "inactive",
        }:
            factors.append(
                {
                    "factor": "low_physical_activity",
                    "severity": "moderate",
                    "value": activity_level,
                }
            )

    # Health concerns
    urgent_concerns = [
        concern
        for concern in health_concerns
        if concern.get("urgent_flag") is True
    ]

    if urgent_concerns:
        factors.append(
            {
                "factor": "urgent_health_concern",
                "severity": "high",
                "value": len(urgent_concerns),
            }
        )

    # Medical history
    active_conditions = [
        condition
        for condition in medical_history
        if str(condition.get("status", "")).lower()
        in {"active", "ongoing", "chronic"}
    ]

    if active_conditions:
        factors.append(
            {
                "factor": "active_medical_history",
                "severity": "moderate",
                "value": len(active_conditions),
            }
        )

    return {
        "factor_count": len(factors),
        "factors": factors,
    }


def calculate_risk_score(
    risk_factors: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert identified risk factors into a transparent score.

    This is a screening/triage-oriented score, not a medical diagnosis.
    """

    severity_points = {
        "low": 1,
        "moderate": 2,
        "high": 3,
    }

    score = 0

    for factor in risk_factors.get("factors", []):
        severity = factor.get("severity", "low")
        score += severity_points.get(severity, 0)

    if score >= 7:
        risk_level = "high"
    elif score >= 4:
        risk_level = "moderate"
    elif score >= 1:
        risk_level = "low"
    else:
        risk_level = "minimal"

    return {
        "score": score,
        "risk_level": risk_level,
        "factor_count": len(risk_factors.get("factors", [])),
    }