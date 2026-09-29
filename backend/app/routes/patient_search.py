from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.security.permissions import require_roles
from app.services.patient_search import search_patients


router = APIRouter(
    prefix="/patients",
    tags=["Patient Search"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/search")
def patient_search(
    search: str | None = None,
    patient_number: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    district: str | None = None,
    sex: str | None = None,
    status: str | None = None,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("administrator", "clinician")),
):
    return search_patients(
        db=db,
        search=search,
        patient_number=patient_number,
        first_name=first_name,
        last_name=last_name,
        district=district,
        sex=sex,
        status=status,
        limit=limit,
        offset=offset,
    )