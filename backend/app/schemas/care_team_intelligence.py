from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CareTeamMember(BaseModel):
    assignment_id: int
    clinician_id: int
    clinician_name: str
    clinician_role: str
    care_role: str
    assigned_at: datetime


class PatientCareTeamSummary(BaseModel):
    patient_id: int
    active_clinician_count: int
    has_primary_clinician: bool
    primary_clinician: CareTeamMember | None
    secondary_clinicians: list[CareTeamMember]
    care_coverage_status: str


class CareCoverageGap(BaseModel):
    patient_id: int
    patient_number: str
    patient_name: str
    patient_status: str
    active_clinician_count: int
    has_primary_clinician: bool
    gap_type: str


class CareCoverageOverview(BaseModel):
    total_active_patients: int
    covered_patients: int
    partially_covered_patients: int
    uncovered_patients: int
    coverage_rate: float
    gaps: list[CareCoverageGap]


class ClinicianWorkloadSummary(BaseModel):
    clinician_id: int
    clinician_name: str
    clinician_role: str
    active_patient_count: int
    primary_patient_count: int
    secondary_patient_count: int


class CareTeamActivity(BaseModel):
    assignment_id: int
    patient_id: int
    patient_name: str
    clinician_id: int
    clinician_name: str
    care_role: str
    status: str
    assigned_at: datetime
    ended_at: datetime | None
    updated_at: datetime


class ClinicianDirectoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clinician_id: int
    clinician_name: str
    role: str
    status: str
    active_patient_count: int
    primary_patient_count: int
    secondary_patient_count: int


class AssignmentRoleUpdate(BaseModel):
    care_role: str = Field(
        min_length=1,
        max_length=30,
    )


class PrimaryClinicianReplacement(BaseModel):
    clinician_id: int


class CareTeamOperationalStatus(BaseModel):
    patient_id: int
    active_clinician_count: int
    has_primary_clinician: bool
    has_secondary_clinicians: bool
    care_coverage_status: str
    operational_status: str
    action_required: bool