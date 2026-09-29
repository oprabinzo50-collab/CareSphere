from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.assessment_questions import AssessmentQuestion
from app.models.user import User
from app.schemas.assessment_question import (
    AssessmentQuestionCreate,
    AssessmentQuestionResponse,
    AssessmentQuestionUpdate,
)
from app.security.permissions import require_roles


router = APIRouter(
    prefix="/assessment-questions",
    tags=["Assessment Questions"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "",
    response_model=AssessmentQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment_question(
    question_data: AssessmentQuestionCreate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    existing_question = db.scalar(
        select(AssessmentQuestion).where(
            AssessmentQuestion.question_code
            == question_data.question_code
        )
    )

    if existing_question is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Question code already exists",
        )

    now = datetime.now(timezone.utc)

    question = AssessmentQuestion(
        **question_data.model_dump(),
        created_at=now,
        updated_at=now,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


@router.get(
    "",
    response_model=list[AssessmentQuestionResponse],
)
def list_assessment_questions(
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    statement = (
        select(AssessmentQuestion)
        .where(AssessmentQuestion.active.is_(True))
        .order_by(
            AssessmentQuestion.display_order.asc(),
            AssessmentQuestion.id.asc(),
        )
    )

    return db.scalars(statement).all()


@router.get(
    "/{question_id}",
    response_model=AssessmentQuestionResponse,
)
def get_assessment_question(
    question_id: int,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    question = db.get(
        AssessmentQuestion,
        question_id,
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment question not found",
        )

    return question


@router.put(
    "/{question_id}",
    response_model=AssessmentQuestionResponse,
)
def update_assessment_question(
    question_id: int,
    question_data: AssessmentQuestionUpdate,
    current_user: User = Depends(require_roles("administrator", "clinician")),
    db: Session = Depends(get_db),
):
    question = db.get(
        AssessmentQuestion,
        question_id,
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment question not found",
        )

    update_data = question_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(question, field, value)

    question.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(question)

    return question