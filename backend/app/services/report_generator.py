import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment_sessions import AssessmentSession
from app.models.reports import Report
from app.ai.config import get_ai_config
from app.ai.prompts import REPORT_GENERATION_INSTRUCTIONS
from app.ai.provider import (
    AIProviderError,
    AIProviderUnavailable,
    get_ai_provider,
)
from app.services.risk_assessment import assess_assessment_risk


def _generate_ai_report_narrative(
    report_content: dict[str, Any],
) -> tuple[dict[str, str] | None, str | None, str | None]:
    """
    Generate an AI narrative from the already-computed deterministic report.
    """
    config = get_ai_config()
    if not config.enabled:
        return None, None, None

    try:
        provider = get_ai_provider()
        response = provider.generate(
            instructions=REPORT_GENERATION_INSTRUCTIONS,
            input_text=json.dumps(
                report_content,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
        )
    except (AIProviderUnavailable, AIProviderError):
        # Keep the existing deterministic report workflow available when the
        # optional AI layer is unavailable.
        return None, None, None

    raw_output = (response.output or "").strip()
    if not raw_output:
        return None, response.provider, response.model

    try:
        parsed = json.loads(raw_output)
    except (TypeError, ValueError):
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    normalized = {
        "executive_summary": str(parsed.get("executive_summary") or "").strip(),
        "clinical_summary": str(parsed.get("clinical_summary") or "").strip(),
        "recommendations_summary": str(
            parsed.get("recommendations_summary") or ""
        ).strip(),
        "limitations": str(parsed.get("limitations") or "").strip(),
    }

    # If the provider returned non-JSON text, keep it visible as the clinical
    # summary rather than silently losing the model output.
    if not any(normalized.values()) and raw_output:
        normalized["clinical_summary"] = raw_output

    if not any(normalized.values()):
        return None, response.provider, response.model

    return normalized, response.provider, response.model


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
    # Optional AI narrative
    # ---------------------------------------------------------

    ai_content, ai_provider, ai_model = _generate_ai_report_narrative(
        report_content
    )

    if ai_content:
        report_content["ai_generated_content"] = ai_content
        report_content["ai_provider"] = ai_provider
        report_content["ai_model"] = ai_model

    # ---------------------------------------------------------
    # Executive summary
    # ---------------------------------------------------------

    executive_summary = (
        ai_content.get("executive_summary")
        if ai_content and ai_content.get("executive_summary")
        else (
            f"{summary_text} "
            "This report is generated from the "
            "available assessment information and "
            "should be reviewed by an appropriate "
            "clinician."
        )
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

    if ai_content and ai_content.get("limitations"):
        limitations = f"{limitations} AI note: {ai_content['limitations']}"

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
        ai_generated=bool(ai_content),
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