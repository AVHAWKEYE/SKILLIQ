from sqlalchemy import Column, DateTime, Float, Integer, String, Text, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    """User model for standard users and admins"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user")  # user, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    assessments = relationship("Assessment", back_populates="user", foreign_keys="Assessment.user_id")
    created_tests = relationship("Test", back_populates="creator", foreign_keys="Test.created_by")
    test_attempts = relationship("TestAttempt", back_populates="student", foreign_keys="TestAttempt.student_id")
    ai_insights = relationship("AIInsight", back_populates="user", foreign_keys="AIInsight.user_id")


class Assessment(Base):
    """Student self-assessment record"""
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
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
    
    user = relationship("User", back_populates="assessments", foreign_keys=[user_id])


class Test(Base):
    """Teacher-created tests/quizzes"""
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(String(20), default="homework")  # homework, quiz, live
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    duration_minutes = Column(Integer, default=30)
    passing_score = Column(Float, default=60.0)
    total_questions = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    is_live = Column(Boolean, default=False)
    live_start_time = Column(DateTime(timezone=True), nullable=True)
    live_end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    creator = relationship("User", back_populates="created_tests", foreign_keys=[created_by])
    questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
    attempts = relationship("TestAttempt", back_populates="test", cascade="all, delete-orphan")


class TestQuestion(Base):
    """Questions within a teacher-created test"""
    __tablename__ = "test_questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default="mcq")  # mcq, short_answer, essay
    options = Column(Text, nullable=False)  # JSON string
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(20), default="medium")
    skill_tag = Column(String(50), nullable=True)
    points = Column(Float, default=1.0)
    order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    test = relationship("Test", back_populates="questions", foreign_keys=[test_id])


class TestAttempt(Base):
    """Student's attempt at a teacher-created test"""
    __tablename__ = "test_attempts"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="in_progress")  # in_progress, submitted, graded
    score = Column(Float, nullable=True)
    max_score = Column(Float, default=100.0)
    percentage = Column(Float, nullable=True)
    answers = Column(Text, nullable=True)  # JSON string storing answers
    start_time = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    submit_time = Column(DateTime(timezone=True), nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)
    teacher_feedback = Column(Text, nullable=True)
    is_passed = Column(Boolean, nullable=True)
    
    test = relationship("Test", back_populates="attempts", foreign_keys=[test_id])
    student = relationship("User", back_populates="test_attempts", foreign_keys=[student_id])


class LearningResource(Base):
    """Learning materials - videos, books, websites"""
    __tablename__ = "learning_resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    resource_type = Column(String(50), default="video")  # video, book, website, article, course
    skill_tag = Column(String(50), nullable=False, index=True)
    difficulty = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    url = Column(String(500), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    instructor = Column(String(100), nullable=True)
    rating = Column(Float, default=0.0)
    views = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    insights = relationship("AIInsight", back_populates="resource", foreign_keys="AIInsight.resource_id")


class AIInsight(Base):
    """AI-generated insights and recommendations for students"""
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    insight_type = Column(String(50), default="skill_gap")  # skill_gap, improvement, strength, weakness
    skill_name = Column(String(100), nullable=False)
    current_score = Column(Float, nullable=True)
    benchmark_score = Column(Float, nullable=True)
    recommendation_text = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.8)
    action_items = Column(Text, nullable=True)  # JSON array
    resource_id = Column(Integer, ForeignKey("learning_resources.id"), nullable=True)
    priority_level = Column(String(20), default="medium")  # low, medium, high
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    user = relationship("User", back_populates="ai_insights", foreign_keys=[user_id])
    resource = relationship("LearningResource", back_populates="insights", foreign_keys=[resource_id])


class PerformanceMetric(Base):
    """Aggregate performance metrics for tracking progress"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=True)
    metric_type = Column(String(50), default="overall")  # overall, skill, topic
    category = Column(String(100), nullable=False)  # skill name or test name
    total_attempts = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    highest_score = Column(Float, default=0.0)
    improvement_rate = Column(Float, default=0.0)  # percentage improvement
    last_attempt_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
