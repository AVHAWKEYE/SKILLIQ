from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


# ========== USER SCHEMAS ==========
class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    role: str = Field(default="user")  # user, admin


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None


# ========== ASSESSMENT SCHEMAS ==========
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
    user_id: Optional[int]
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


# ========== TEST SCHEMAS ==========
class TestQuestionCreate(BaseModel):
    question_text: str
    question_type: str = "mcq"  # mcq, short_answer, essay
    options: List[str]  # List of options for MCQ
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str = "medium"
    skill_tag: Optional[str] = None
    points: float = 1.0


class TestQuestionRead(TestQuestionCreate):
    id: int
    test_id: int
    order: int
    created_at: datetime

    class Config:
        from_attributes = True


class TestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    test_type: str = Field(default="homework")  # homework, quiz, live
    difficulty: str = Field(default="medium")
    duration_minutes: int = Field(default=30, ge=5, le=480)
    passing_score: float = Field(default=60.0, ge=0, le=100)
    is_live: bool = False
    live_start_time: Optional[datetime] = None
    live_end_time: Optional[datetime] = None
    questions: List[TestQuestionCreate] = []


class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    duration_minutes: Optional[int] = None
    passing_score: Optional[float] = None
    is_published: Optional[bool] = None
    is_live: Optional[bool] = None
    live_start_time: Optional[datetime] = None
    live_end_time: Optional[datetime] = None


class TestRead(BaseModel):
    id: int
    created_by: int
    title: str
    description: Optional[str]
    test_type: str
    difficulty: str
    duration_minutes: int
    passing_score: float
    total_questions: int
    is_published: bool
    is_live: bool
    live_start_time: Optional[datetime]
    live_end_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestDetailedRead(TestRead):
    questions: List[TestQuestionRead] = []
    creator: UserRead


# ========== TEST ATTEMPT SCHEMAS ==========
class TestAnswerSubmit(BaseModel):
    question_id: int
    answer: str
    time_taken_sec: int


class TestAttemptStart(BaseModel):
    test_id: int


class TestAttemptSubmit(BaseModel):
    answers: List[TestAnswerSubmit]


class TestAttemptRead(BaseModel):
    id: int
    test_id: int
    student_id: int
    status: str
    score: Optional[float]
    max_score: float
    percentage: Optional[float]
    start_time: datetime
    submit_time: Optional[datetime]
    time_taken_seconds: Optional[int]
    teacher_feedback: Optional[str]
    is_passed: Optional[bool]

    class Config:
        from_attributes = True


# ========== LEARNING RESOURCE SCHEMAS ==========
class LearningResourceCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    resource_type: str  # video, book, website, article, course
    skill_tag: str
    difficulty: str = "intermediate"
    url: str
    duration_minutes: Optional[int] = None
    instructor: Optional[str] = None
    rating: float = Field(default=0.0, ge=0, le=5)


class LearningResourceRead(LearningResourceCreate):
    id: int
    views: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LearningResourceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    is_verified: Optional[bool] = None


# ========== AI INSIGHT SCHEMAS ==========
class AIInsightCreate(BaseModel):
    user_id: int
    insight_type: str  # skill_gap, improvement, strength, weakness
    skill_name: str
    current_score: Optional[float] = None
    benchmark_score: Optional[float] = None
    recommendation_text: str
    confidence_score: float = 0.8
    action_items: Optional[List[str]] = None
    resource_id: Optional[int] = None
    priority_level: str = "medium"


class AIInsightRead(BaseModel):
    id: int
    user_id: int
    insight_type: str
    skill_name: str
    current_score: Optional[float]
    benchmark_score: Optional[float]
    recommendation_text: str
    confidence_score: float
    action_items: Optional[List[str]]
    resource_id: Optional[int]
    priority_level: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ========== PERFORMANCE METRIC SCHEMAS ==========
class PerformanceMetricRead(BaseModel):
    id: int
    user_id: int
    test_id: Optional[int]
    metric_type: str
    category: str
    total_attempts: int
    successful_attempts: int
    average_score: float
    highest_score: float
    improvement_rate: float
    last_attempt_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== ANALYTICS SCHEMAS ==========
class StudentAnalyticsResponse(BaseModel):
    total_assessments: int
    total_tests_attempted: int
    average_assessment_score: float
    average_test_score: float
    strongest_skill: str
    weakest_skill: str
    improvement_percentage: float
    insights: List[AIInsightRead]
    performance_trends: dict


class TeacherAnalyticsResponse(BaseModel):
    total_tests_created: int
    total_student_attempts: int
    average_class_score: float
    class_pass_rate: float
    student_performance_breakdown: dict
    most_challenging_questions: List[dict]
    recent_test_results: List[TestAttemptRead]
