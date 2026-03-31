from sqlalchemy import Column, DateTime, Float, Integer, func

from .database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    selected_skills_count = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    total_correct = Column(Integer, nullable=False)
    accuracy_pct = Column(Float, nullable=False)
    avg_time_sec = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    math_score = Column(Float, nullable=False, default=0)
    logic_score = Column(Float, nullable=False, default=0)
    aptitude_score = Column(Float, nullable=False, default=0)
    problem_score = Column(Float, nullable=False, default=0)
    target_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
