import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.reports import Report
from app.services.risk_assessment import assess_assessment_risk


def generate_assessment_report(
    db: Session,
    assessment_id: int,
    user_id: int,
) -> Report:
    """
    Generate and save a structured assessment report.

    The report summarizes existing assessment information.
    It does not provide an autonomous medical diagnosis.
    """

    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise ValueError("Assessment not found")

    result = assess_assessment_risk(
        db=db,
        assessment_id=assessment_id,
    )

    assessment_summary = result.get(
        "assessment_summary",
        {},
    )

    risk_score = result.get(
        "risk_score",
        {},
    )

    risk_factors = result.get(
        "risk_factors",
        {},
    )

    recommendations = result.get(
        "recommendations",
        [],
    )

    summary_text = assessment_summary.get(
        "summary",
        "No assessment summary available.",
    )

    # ---------------------------------------------------------
    # Build report content
    # ---------------------------------------------------------

    report_content = {
        "assessment_id": assessment_id,
        "patient_id": assessment.patient_id,
        "assessment_type": assessment.assessment_type,
        "risk_assessment": {
            "score": risk_score.get("score"),
            "risk_level": risk_score.get(
                "risk_level"
            ),
        },
        "risk_factors": risk_factors.get(
            "factors",
            [],
        ),
        "health_concerns": assessment_summary.get(
            "urgent_concerns",
            [],
        ),
        "recommendations": recommendations,
        "summary": summary_text,
    }

    # ---------------------------------------------------------
    # Executive summary
    # ---------------------------------------------------------

    executive_summary = (
        f"{summary_text} "
        "This report is generated from the "
        "available assessment information and "
        "should be reviewed by an appropriate "
        "clinician."
    )

    # ---------------------------------------------------------
    # Recommendations summary
    # ---------------------------------------------------------

    if recommendations:
        recommendations_summary = "\n".join(
            [
                (
                    f"- {item.get('title')}: "
                    f"{item.get('recommendation_text')}"
                )
                for item in recommendations
            ]
        )
    else:
        recommendations_summary = (
            "No recommendations were generated."
        )

    # ---------------------------------------------------------
    # Limitations
    # ---------------------------------------------------------

    limitations = (
        "This report is generated from the data "
        "available in the CareSphere assessment. "
        "It is intended to support clinical review "
        "and does not constitute an independent "
        "medical diagnosis or treatment decision."
    )

    # ---------------------------------------------------------
    # Determine next version
    # ---------------------------------------------------------

    latest_report = db.scalar(
        select(Report)
        .where(
            Report.assessment_id == assessment_id,
            Report.report_type == "assessment_summary",
        )
        .order_by(
            Report.version.desc()
        )
    )

    if latest_report is None:
        next_version = 1
    else:
        next_version = latest_report.version + 1

    # ---------------------------------------------------------
    # Create report
    # ---------------------------------------------------------

    report = Report(
        assessment_id=assessment_id,
        report_type="assessment_summary",
        report_title=(
            f"Assessment Summary Report "
            f"- Assessment {assessment_id}"
        ),
        report_content=json.dumps(
            report_content,
            ensure_ascii=False,
            indent=2,
        ),
        executive_summary=executive_summary,
        recommendations_summary=(
            recommendations_summary
        ),
        limitations=limitations,
        generated_by=str(user_id),
        ai_generated=False,
        version=next_version,
        status="draft",
        generated_at=datetime.now(
            timezone.utc
        ),
        created_by=user_id,
        updated_at=datetime.now(
            timezone.utc
        ),
    )

    db.add(report)

    db.commit()

    db.refresh(report)

    return report