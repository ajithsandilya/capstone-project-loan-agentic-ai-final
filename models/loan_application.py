from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal


class ApplicantProfile(BaseModel):
    age: int = Field(..., ge=18, le=120, description="Applicant age in years")
    income: float = Field(..., ge=0, description="Annual income")
    employment_type: str = Field(..., description="Employment type")


class LoanApplication(BaseModel):
    applicant_id: str = Field(..., description="Unique applicant identifier")
    applicant_profile: ApplicantProfile
    credit_score: int = Field(..., ge=300, le=850, description="Credit score")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    tenure: int = Field(..., ge=1, description="Loan tenure in months")
    existing_liabilities: float = Field(..., ge=0, description="Total existing liabilities")
    location: str = Field(..., description="Applicant location")
    application_timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("applicant_id")
    @classmethod
    def applicant_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("applicant_id must not be empty")
        return v

    @field_validator("location")
    @classmethod
    def location_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("location must not be empty")
        return v
