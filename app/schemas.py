from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AssessmentBase(BaseModel):
    selected_skills_count: int = Field(ge=1, le=10)
    total_questions: int = Field(ge=1, le=500)
    total_correct: int = Field(ge=0, le=500)
    accuracy_pct: float = Field(ge=0, le=100)
    avg_time_sec: float = Field(ge=0, le=120)
    overall_score: float = Field(ge=0, le=100)
    math_score: float = Field(ge=0, le=100)
    logic_score: float = Field(ge=0, le=100)
    aptitude_score: float = Field(ge=0, le=100)
    problem_score: float = Field(ge=0, le=100)


class AssessmentCreate(AssessmentBase):
    target_score: Optional[float] = Field(default=None, ge=0, le=100)


class AssessmentRead(AssessmentBase):
    id: int
    target_score: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class LabelUpdate(BaseModel):
    target_score: float = Field(ge=0, le=100)


class TrainResponse(BaseModel):
    trained_rows: int
    r2_score: float
    rmse: float
    model_path: str


class PredictRequest(AssessmentBase):
    pass


class PredictResponse(BaseModel):
    predicted_target_score: float
