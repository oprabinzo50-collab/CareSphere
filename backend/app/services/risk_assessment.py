from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.health_concerns import HealthConcern
from app.models.lifestyle import Lifestyle
from app.models.medical_history import MedicalHistory
from app.models.recommendations import Recommendation
from app.models.vital_signs import VitalSign

from app.services.assessment_summary import (
    generate_assessment_summary,
)

from app.services.recommendation_engine import (
    generate_recommendations,
)

from app.services.risk_engine import (
    calculate_risk_factors,
    calculate_risk_score,
)


def assess_assessment_risk(
    db: Session,
    assessment_id: int,
) -> dict[str, Any]:
    """
    Analyze an assessment using the existing patient data.

    This is a transparent rule-based screening/triage
    calculation. It does not make a medical diagnosis.
    """

    # ---------------------------------------------------------
    # Get assessment
    # ---------------------------------------------------------

    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise ValueError("Assessment not found")

    # ---------------------------------------------------------
    # Get latest vital signs for this assessment
    # ---------------------------------------------------------

    vital_sign = db.scalar(
        select(VitalSign)
        .where(
            VitalSign.assessment_id == assessment_id
        )
        .order_by(
            VitalSign.recorded_at.desc()
        )
    )

    # Patient-entered vital signs may not be linked to a
    # clinician assessment yet. In that case, use the latest
    # vital-sign record belonging to the same patient.
    if vital_sign is None:
        vital_sign = db.scalar(
            select(VitalSign)
            .where(
                VitalSign.patient_id == assessment.patient_id
            )
            .order_by(
                VitalSign.recorded_at.desc()
            )
        )

    # ---------------------------------------------------------
    # Get latest lifestyle information for patient
    # ---------------------------------------------------------

    lifestyle = db.scalar(
        select(Lifestyle)
        .where(
            Lifestyle.patient_id == assessment.patient_id
        )
        .order_by(
            Lifestyle.recorded_at.desc()
        )
    )

    # ---------------------------------------------------------
    # Get health concerns
    # ---------------------------------------------------------

    health_concerns = list(
        db.scalars(
            select(HealthConcern)
            .where(
                HealthConcern.assessment_id
                == assessment_id
            )
        ).all()
    )

    # ---------------------------------------------------------
    # Get medical history
    # ---------------------------------------------------------

    medical_history = list(
        db.scalars(
            select(MedicalHistory)
            .where(
                MedicalHistory.patient_id
                == assessment.patient_id
            )
        ).all()
    )

    # ---------------------------------------------------------
    # Convert vital signs to dictionaries
    # ---------------------------------------------------------

    vital_signs_data: dict[str, Any] = {}

    if vital_sign is not None:
        vital_signs_data = {
            "height": vital_sign.height,
            "weight": vital_sign.weight,
            "bmi": vital_sign.bmi,
            "blood_pressure_systolic": (
                vital_sign.blood_pressure_systolic
            ),
            "blood_pressure_diastolic": (
                vital_sign.blood_pressure_diastolic
            ),
            "pulse": vital_sign.pulse,
            "temperature": vital_sign.temperature,
            "oxygen_saturation": (
                vital_sign.oxygen_saturation
            ),
        }

    # ---------------------------------------------------------
    # Convert lifestyle to dictionary
    # ---------------------------------------------------------

    lifestyle_data: dict[str, Any] = {}

    if lifestyle is not None:
        lifestyle_data = {
            "smoking_status": (
                lifestyle.smoking_status
            ),
            "alcohol_use": (
                lifestyle.alcohol_use
            ),
            "physical_activity_level": (
                lifestyle.physical_activity_level
            ),
            "exercise_frequency": (
                lifestyle.exercise_frequency
            ),
            "diet_pattern": (
                lifestyle.diet_pattern
            ),
            "sleep_duration_hours": (
                lifestyle.sleep_duration_hours
            ),
            "sleep_quality": (
                lifestyle.sleep_quality
            ),
            "stress_level": (
                lifestyle.stress_level
            ),
        }

    # ---------------------------------------------------------
    # Convert health concerns to dictionaries
    # ---------------------------------------------------------

    health_concerns_data: list[dict[str, Any]] = []

    for concern in health_concerns:
        health_concerns_data.append(
            {
                "id": concern.id,
                "concern_title": (
                    concern.concern_title
                ),
                "severity": concern.severity,
                "urgent_flag": (
                    concern.urgent_flag
                ),
                "patient_priority": (
                    concern.patient_priority
                ),
            }
        )

    # ---------------------------------------------------------
    # Convert medical history to dictionaries
    # ---------------------------------------------------------

    medical_history_data: list[dict[str, Any]] = []

    for condition in medical_history:
        medical_history_data.append(
            {
                "id": condition.id,
                "condition_name": (
                    condition.condition_name
                ),
                "status": condition.status,
            }
        )

    # ---------------------------------------------------------
    # Calculate risk factors
    # ---------------------------------------------------------

    risk_factors = calculate_risk_factors(
        vital_signs=vital_signs_data,
        lifestyle=lifestyle_data,
        health_concerns=health_concerns_data,
        medical_history=medical_history_data,
    )

    # ---------------------------------------------------------
    # Calculate risk score
    # ---------------------------------------------------------

    risk_score = calculate_risk_score(
        risk_factors
    )

    # ---------------------------------------------------------
    # Generate recommendations
    # ---------------------------------------------------------

    recommendations = generate_recommendations(
        risk_factors=risk_factors
    )

    # ---------------------------------------------------------
    # Prepare assessment information
    # ---------------------------------------------------------

    assessment_data = {
        "id": assessment.id,
        "assessment_type": (
            assessment.assessment_type
        ),
        "status": assessment.status,
        "summary": assessment.summary,
    }

    # ---------------------------------------------------------
    # Generate structured assessment summary
    # ---------------------------------------------------------

    assessment_summary = generate_assessment_summary(
        assessment=assessment_data,
        risk_score=risk_score,
        risk_factors=risk_factors,
        health_concerns=health_concerns_data,
        recommendations=recommendations,
    )

    # ---------------------------------------------------------
    # Return complete assessment intelligence
    # ---------------------------------------------------------

    return {
        "assessment_id": assessment_id,
        "patient_id": assessment.patient_id,
        "risk_factors": risk_factors,
        "risk_score": risk_score,
        "recommendations": recommendations,
        "assessment_summary": assessment_summary,
    }


def generate_and_save_recommendations(
    db: Session,
    assessment_id: int,
    user_id: int,
) -> list[Recommendation]:
    """
    Generate rule-based recommendations and save them.

    Existing recommendations with the same title and
    rule-based source are reused instead of duplicated.
    """

    result = assess_assessment_risk(
        db=db,
        assessment_id=assessment_id,
    )

    recommendations_data = result.get(
        "recommendations",
        [],
    )

    saved_recommendations: list[Recommendation] = []

    for recommendation_data in recommendations_data:

        title = recommendation_data.get("title")

        if not title:
            continue

        # -----------------------------------------------------
        # Check for existing recommendation
        # -----------------------------------------------------

        existing = db.scalar(
            select(Recommendation)
            .where(
                Recommendation.assessment_id
                == assessment_id,
                Recommendation.title == title,
                Recommendation.source_type
                == "rule_based",
            )
        )

        if existing is not None:
            saved_recommendations.append(
                existing
            )
            continue

        # -----------------------------------------------------
        # Create recommendation
        # -----------------------------------------------------

        recommendation = Recommendation(
            assessment_id=assessment_id,
            recommendation_type=(
                recommendation_data.get(
                    "recommendation_type"
                )
            ),
            title=title,
            recommendation_text=(
                recommendation_data.get(
                    "recommendation_text"
                )
            ),
            priority=(
                recommendation_data.get(
                    "priority"
                )
            ),
            source_type="rule_based",
            ai_generated=False,
            clinician_review_required=True,
            status="pending",
            created_at=datetime.now(
                timezone.utc
            ),
            updated_at=datetime.now(
                timezone.utc
            ),
            created_by=user_id,
        )

        db.add(recommendation)

        saved_recommendations.append(
            recommendation
        )

    # ---------------------------------------------------------
    # Save changes
    # ---------------------------------------------------------

    db.commit()

    # ---------------------------------------------------------
    # Refresh records
    # ---------------------------------------------------------

    for recommendation in saved_recommendations:
        db.refresh(recommendation)

    return saved_recommendations