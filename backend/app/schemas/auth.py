from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)
    login_role: str | None = Field(default=None, min_length=1, max_length=50)


class PatientRegistrationRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=200)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    date_of_birth: date | None = None
    sex: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    preferred_language: str | None = None
    residence: str | None = None
    district: str | None = None
    country: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    status: str
    permissions: list[str]
    patient_id: int | None = None


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    user: UserResponse
