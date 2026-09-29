from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_answers import AssessmentAnswer
from app.models.assessment_questions import AssessmentQuestion
from app.models.assessment_sessions import AssessmentSession
from app.models.health_concerns import HealthConcern
from app.models.user import User
from app.schemas.assessment_answer import (
    AssessmentAnswerCreate,
    AssessmentAnswerResponse,
    AssessmentAnswerUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/assessments",
    tags=["Assessment Answers"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/{assessment_id}/answers",
    response_model=AssessmentAnswerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment_answer(
    assessment_id: int,
    answer_data: AssessmentAnswerCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    question = db.get(
        AssessmentQuestion,
        answer_data.question_id,
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment question not found",
        )

    if answer_data.health_concern_id is not None:
        health_concern = db.get(
            HealthConcern,
            answer_data.health_concern_id,
        )

        if health_concern is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health concern not found",
            )

        if health_concern.assessment_id != assessment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Health concern does not belong to this assessment",
            )

    now = datetime.now(timezone.utc)

    answer = AssessmentAnswer(
        assessment_id=assessment_id,
        **answer_data.model_dump(),
        answered_at=now,
        answered_by=current_user.id,
    )

    db.add(answer)
    db.commit()
    db.refresh(answer)

    return answer


@router.get(
    "/{assessment_id}/answers",
    response_model=list[AssessmentAnswerResponse],
)
def list_assessment_answers(
    assessment_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    assessment = db.get(
        AssessmentSession,
        assessment_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment session not found",
        )

    statement = (
        select(AssessmentAnswer)
        .where(
            AssessmentAnswer.assessment_id == assessment_id
        )
        .order_by(AssessmentAnswer.id.asc())
    )

    return db.scalars(statement).all()


@router.put(
    "/answers/{answer_id}",
    response_model=AssessmentAnswerResponse,
)
def update_assessment_answer(
    answer_id: int,
    answer_data: AssessmentAnswerUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    answer = db.get(
        AssessmentAnswer,
        answer_id,
    )

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment answer not found",
        )

    if answer_data.health_concern_id is not None:
        health_concern = db.get(
            HealthConcern,
            answer_data.health_concern_id,
        )

        if health_concern is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Health concern not found",
            )

        if health_concern.assessment_id != answer.assessment_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Health concern does not belong to this assessment",
            )

    update_data = answer_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(answer, field, value)

    answer.answered_at = datetime.now(timezone.utc)
    answer.answered_by = current_user.id

    db.commit()
    db.refresh(answer)

    return answer