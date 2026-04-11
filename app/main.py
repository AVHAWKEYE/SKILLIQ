import json
import io
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import or_
from sqlalchemy.orm import Session

load_dotenv()

from . import ml, models, schemas
from .auth import (
    create_access_token, hash_password, verify_password,
    get_current_user, get_current_admin
)
from .database import SessionLocal, engine, get_db
from .cse_career import analyze_cse_profile, build_cse_pdf_report, format_cse_report, parse_uploaded_document
from .insights import InsightsEngine
from .mongo_sync import (
    full_sync_from_sql,
    ping_mongo,
    safe_sync,
    upsert_instance,
    upsert_instances,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkillIQ API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STAFF_ROLES = {"admin"}


def seed_demo_users(db: Session) -> None:
    """Create demo users for admin/user if they do not already exist."""
    demo_users = [
        {
            "username": "admin_demo",
            "email": "admin.demo@skilliq.com",
            "full_name": "Demo Admin",
            "role": "admin",
            "password": "Admin@123",
        },
        {
            "username": "user_demo",
            "email": "user.demo@skilliq.com",
            "full_name": "Demo User",
            "role": "user",
            "password": "User@123",
        },
    ]

    for item in demo_users:
        existing = db.query(models.User).filter(
            or_(models.User.username == item["username"], models.User.email == item["email"])
        ).first()
        if existing:
            continue

        db.add(models.User(
            username=item["username"],
            email=item["email"],
            full_name=item["full_name"],
            role=item["role"],
            password_hash=hash_password(item["password"]),
            is_active=True,
        ))

    db.commit()


@app.on_event("startup")
def startup_mongo_sync() -> None:
    """On startup, mirror SQL data to MongoDB Atlas if reachable."""
    db = SessionLocal()
    try:
        seed_demo_users(db)
        safe_sync(full_sync_from_sql, db)
    finally:
        db.close()


# ========== AUTH ENDPOINTS ==========
@app.post("/api/auth/register", response_model=schemas.UserRead)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing = db.query(models.User).filter(
        (models.User.username == payload.username) | (models.User.email == payload.email)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create user
    user = models.User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role if payload.role in ["user", "admin"] else "user"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    safe_sync(upsert_instance, "users", user)
    return user


@app.post("/api/auth/login")
def login(
    password: str,
    username: Optional[str] = None,
    email: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Login user and return JWT token"""
    identifier = (username or email or "").strip()
    if not identifier:
        raise HTTPException(status_code=400, detail="Username or email is required")

    user = db.query(models.User).filter(
        or_(models.User.username == identifier, models.User.email == identifier)
    ).first()
    
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    
    access_token = create_access_token(user.id, user.username, user.role)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserRead.from_orm(user)
    }


@app.get("/api/auth/demo-users-status")
def demo_users_status(db: Session = Depends(get_db)):
    """Return availability status for seeded demo users (no password exposure)."""
    targets = [
        ("admin", "admin_demo", "admin.demo@skilliq.com"),
        ("user", "user_demo", "user.demo@skilliq.com"),
    ]

    items = []
    for role, username, email in targets:
        row = db.query(models.User).filter(
            or_(models.User.username == username, models.User.email == email)
        ).first()
        items.append(
            {
                "role": role,
                "username": username,
                "email": email,
                "available": row is not None,
            }
        )

    return {"items": items}


@app.get("/api/auth/me", response_model=schemas.UserRead)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@app.patch("/api/auth/update-profile", response_model=schemas.UserRead)
def update_profile(
    payload: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    if payload.full_name:
        current_user.full_name = payload.full_name
    
    if payload.password:
        current_user.password_hash = hash_password(payload.password)
    
    db.commit()
    db.refresh(current_user)
    safe_sync(upsert_instance, "users", current_user)
    return current_user


# ========== ASSESSMENT ENDPOINTS (Original) ==========
@app.get("/api/health")
def health():
    return {"status": "ok", "model_ready": ml.is_model_ready()}


@app.get("/api/mongo/status")
def mongo_status():
    """Check MongoDB Atlas connectivity."""
    return {"connected": ping_mongo()}


@app.post("/api/mongo/sync")
def mongo_full_sync(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
):
    """Manually force a full SQL->Mongo synchronization (admin only)."""
    counts = safe_sync(full_sync_from_sql, db)
    if counts is None:
        raise HTTPException(status_code=503, detail="MongoDB Atlas is not reachable")
    return {"message": "Mongo sync completed", "counts": counts}


@app.post("/api/assessments", response_model=schemas.AssessmentRead)
def create_assessment(
    payload: schemas.AssessmentCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Create assessment record"""
    # Support both authenticated and anonymous submissions
    user_id = current_user.id if current_user else None
    
    item = models.Assessment(
        user_id=user_id,
        **payload.model_dump()
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    safe_sync(upsert_instance, "assessments", item)
    return item


@app.patch("/api/assessments/{assessment_id}/label", response_model=schemas.AssessmentRead)
def update_label(
    assessment_id: int,
    payload: schemas.LabelUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin),
):
    """Label assessment with target score (staff only)"""
    row = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    
    row.target_score = payload.target_score
    db.commit()
    db.refresh(row)
    safe_sync(upsert_instance, "assessments", row)
    return row


@app.get("/api/assessments", response_model=List[schemas.AssessmentRead])
def list_assessments(db: Session = Depends(get_db)):
    """List all assessments (with limit)"""
    return db.query(models.Assessment).order_by(models.Assessment.id.desc()).limit(300).all()


@app.post("/api/train", response_model=schemas.TrainResponse)
def train_model(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Train model (staff only)"""
    try:
        return ml.train(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/predict", response_model=schemas.PredictResponse)
def predict(
    payload: schemas.PredictRequest,
    current_user: models.User = Depends(get_current_admin)
):
    """Predict target score (staff only)"""
    try:
        y_hat = ml.predict_one(payload.model_dump())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"predicted_target_score": round(y_hat, 2)}


# ========== TEST MANAGEMENT ENDPOINTS (Admin) ==========
@app.post("/api/tests", response_model=schemas.TestRead)
def create_test(
    payload: schemas.TestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Create a new test/quiz"""
    test = models.Test(
        created_by=current_user.id,
        title=payload.title,
        description=payload.description,
        test_type=payload.test_type,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        passing_score=payload.passing_score,
        is_live=payload.is_live,
        live_start_time=payload.live_start_time,
        live_end_time=payload.live_end_time,
        total_questions=len(payload.questions)
    )
    
    db.add(test)
    db.flush()  # Get test ID
    
    # Add questions
    for idx, q in enumerate(payload.questions):
        question = models.TestQuestion(
            test_id=test.id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=json.dumps(q.options),
            correct_answer=q.correct_answer,
            explanation=q.explanation,
            difficulty=q.difficulty,
            skill_tag=q.skill_tag,
            points=q.points,
            order=idx
        )
        db.add(question)
    
    db.commit()
    db.refresh(test)
    questions = db.query(models.TestQuestion).filter(models.TestQuestion.test_id == test.id).all()
    safe_sync(upsert_instance, "tests", test)
    safe_sync(upsert_instances, "test_questions", questions)
    return test


@app.get("/api/tests", response_model=List[schemas.TestRead])
def list_tests(
    db: Session = Depends(get_db),
    published_only: bool = False,
    current_user: models.User = Depends(get_current_user)
):
    """List tests (users see published tests, admins see all tests)."""
    query = db.query(models.Test)
    
    if current_user.role == "user":
        query = query.filter(models.Test.is_published == True)
    
    if published_only:
        query = query.filter(models.Test.is_published == True)
    
    return query.order_by(models.Test.created_at.desc()).all()


@app.get("/api/tests/{test_id}", response_model=schemas.TestDetailedRead)
def get_test(test_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Get test details"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Authorization check
    if current_user.role == "user" and not test.is_published:
        raise HTTPException(status_code=403, detail="Test not published")
    
    return test


@app.patch("/api/tests/{test_id}", response_model=schemas.TestRead)
def update_test(
    test_id: int,
    payload: schemas.TestUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Update test (admin only)"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot modify other admin's test")
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(test, field, value)
    
    db.commit()
    db.refresh(test)
    safe_sync(upsert_instance, "tests", test)
    return test


@app.post("/api/tests/{test_id}/publish")
def publish_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Publish test to users"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot publish other admin's test")
    
    test.is_published = True
    db.commit()
    db.refresh(test)
    safe_sync(upsert_instance, "tests", test)
    
    return {"message": "Test published successfully", "test": test}


@app.delete("/api/tests/{test_id}")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Delete test"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete other admin's test")
    
    db.delete(test)
    db.commit()
    safe_sync(full_sync_from_sql, db)
    
    return {"message": "Test deleted successfully"}


# ========== TEST ATTEMPT ENDPOINTS (User) ==========
@app.post("/api/tests/{test_id}/attempt/start", response_model=schemas.TestAttemptRead)
def start_test_attempt(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Start a test attempt"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    
    if not test or not test.is_published:
        raise HTTPException(status_code=404, detail="Test not found or not published")
    
    if current_user.role == "admin":
        raise HTTPException(status_code=403, detail="Admins cannot attempt tests")
    
    # Check if test is available
    if test.is_live:
        now = datetime.utcnow()
        if now < test.live_start_time or now > test.live_end_time:
            raise HTTPException(status_code=403, detail="Test not available at this time")
    
    # Create test attempt
    attempt = models.TestAttempt(
        test_id=test_id,
        student_id=current_user.id,
        status="in_progress",
        max_score=test.total_questions if test.total_questions > 0 else 100
    )
    
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    safe_sync(upsert_instance, "test_attempts", attempt)
    
    return attempt


@app.post("/api/test-attempts/{attempt_id}/submit", response_model=schemas.TestAttemptRead)
def submit_test_attempt(
    attempt_id: int,
    payload: schemas.TestAttemptSubmit,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Submit test attempt"""
    attempt = db.query(models.TestAttempt).filter(models.TestAttempt.id == attempt_id).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot submit other user's attempt")
    
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="Attempt already submitted")
    
    # Score the attempt
    test = db.query(models.Test).filter(models.Test.id == attempt.test_id).first()
    questions = db.query(models.TestQuestion).filter(
        models.TestQuestion.test_id == test.id
    ).all()
    
    score = 0
    answers_dict = {}
    
    for answer in payload.answers:
        question = next((q for q in questions if q.id == answer.question_id), None)
        if question:
            is_correct = answer.answer.lower() == question.correct_answer.lower()
            if is_correct:
                score += question.points
            
            answers_dict[str(answer.question_id)] = {
                "answer": answer.answer,
                "is_correct": is_correct,
                "time_taken_sec": answer.time_taken_sec
            }
    
    attempt.status = "submitted"
    attempt.score = score
    attempt.percentage = (score / attempt.max_score * 100) if attempt.max_score > 0 else 0
    attempt.answers = json.dumps(answers_dict)
    attempt.submit_time = datetime.utcnow()
    
    # Calculate time taken
    if attempt.start_time:
        attempt.time_taken_seconds = int((attempt.submit_time - attempt.start_time).total_seconds())
    
    # Check if passed
    attempt.is_passed = attempt.percentage >= test.passing_score
    
    db.commit()
    db.refresh(attempt)
    
    # Update performance metrics
    engine_insights = InsightsEngine(db)
    engine_insights.update_performance_metrics(current_user.id, test.id)
    safe_sync(upsert_instance, "test_attempts", attempt)
    metric_rows = db.query(models.PerformanceMetric).filter(
        models.PerformanceMetric.user_id == current_user.id
    ).all()
    safe_sync(upsert_instances, "performance_metrics", metric_rows)
    
    return attempt


@app.get("/api/test-attempts/{attempt_id}", response_model=schemas.TestAttemptRead)
def get_test_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get test attempt details"""
    attempt = db.query(models.TestAttempt).filter(models.TestAttempt.id == attempt_id).first()
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    # Authorization
    if current_user.role == "user" and attempt.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access other user's attempt")
    
    return attempt


@app.get("/api/tests/{test_id}/attempts")
def get_test_attempts(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Get all attempts for a test (admin only)"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    if test.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot access other admin's test")
    
    attempts = db.query(models.TestAttempt).filter(
        models.TestAttempt.test_id == test_id
    ).order_by(models.TestAttempt.submit_time.desc()).all()
    
    return attempts


# ========== LEARNING RESOURCES ENDPOINTS ==========
@app.post("/api/learning-resources", response_model=schemas.LearningResourceRead)
def create_learning_resource(
    payload: schemas.LearningResourceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Create learning resource (admin only)"""
    resource = models.LearningResource(**payload.model_dump())
    db.add(resource)
    db.commit()
    db.refresh(resource)
    safe_sync(upsert_instance, "learning_resources", resource)
    return resource


@app.get("/api/learning-resources", response_model=List[schemas.LearningResourceRead])
def list_learning_resources(
    skill_tag: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List learning resources"""
    query = db.query(models.LearningResource)
    
    if skill_tag:
        query = query.filter(models.LearningResource.skill_tag.ilike(f"%{skill_tag}%"))
    
    if resource_type:
        query = query.filter(models.LearningResource.resource_type == resource_type)
    
    return query.order_by(models.LearningResource.rating.desc()).limit(100).all()


@app.patch("/api/learning-resources/{resource_id}", response_model=schemas.LearningResourceRead)
def update_learning_resource(
    resource_id: int,
    payload: schemas.LearningResourceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Update learning resource (admin only)"""
    resource = db.query(models.LearningResource).filter(
        models.LearningResource.id == resource_id
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)
    
    db.commit()
    db.refresh(resource)
    safe_sync(upsert_instance, "learning_resources", resource)
    return resource


@app.post("/api/learning-resources/{resource_id}/view")
def view_learning_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Record resource view"""
    resource = db.query(models.LearningResource).filter(
        models.LearningResource.id == resource_id
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    resource.views += 1
    db.commit()
    db.refresh(resource)
    safe_sync(upsert_instance, "learning_resources", resource)
    
    return {"message": "View recorded"}


# ========== AI INSIGHTS ENDPOINTS ==========
@app.get("/api/insights/analyze")
def analyze_performance(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get AI analysis of user performance"""
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="Users only")
    
    engine = InsightsEngine(db)
    analysis = engine.analyze_student_performance(current_user.id)
    
    return analysis


@app.post("/api/insights/generate")
def generate_insights(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Generate new AI insights for user"""
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="Users only")
    
    # Clear old insights
    db.query(models.AIInsight).filter(models.AIInsight.user_id == current_user.id).delete()
    db.commit()
    
    engine = InsightsEngine(db)
    insights = engine.generate_insights(current_user.id)
    
    for insight in insights:
        db.add(insight)
    
    db.commit()
    safe_sync(full_sync_from_sql, db)
    
    return {"insights_generated": len(insights), "insights": [schemas.AIInsightRead.from_orm(i) for i in insights]}


@app.get("/api/insights", response_model=List[schemas.AIInsightRead])
def get_insights(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get AI insights for user"""
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="Users only")
    
    query = db.query(models.AIInsight).filter(models.AIInsight.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(models.AIInsight.is_read == False)
    
    insights = query.order_by(models.AIInsight.priority_level.desc(), models.AIInsight.created_at.desc()).all()
    
    return insights


@app.patch("/api/insights/{insight_id}/read")
def mark_insight_read(
    insight_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark insight as read"""
    insight = db.query(models.AIInsight).filter(
        models.AIInsight.id == insight_id,
        models.AIInsight.user_id == current_user.id
    ).first()
    
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    
    insight.is_read = True
    db.commit()
    db.refresh(insight)
    safe_sync(upsert_instance, "ai_insights", insight)
    
    return {"message": "Marked as read"}


# ========== PERFORMANCE ANALYTICS ENDPOINTS ==========
@app.get("/api/analytics/student")
def get_student_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user analytics"""
    if current_user.role != "user":
        raise HTTPException(status_code=403, detail="Users only")
    
    assessments = db.query(models.Assessment).filter(
        models.Assessment.user_id == current_user.id
    ).all()
    
    test_attempts = db.query(models.TestAttempt).filter(
        models.TestAttempt.student_id == current_user.id
    ).all()
    
    completed_tests = [t for t in test_attempts if t.status in ["submitted", "graded"]]
    
    avg_assessment = sum(a.overall_score for a in assessments) / len(assessments) if assessments else 0
    avg_test = sum(t.percentage for t in completed_tests if t.percentage) / len(completed_tests) if completed_tests else 0
    
    return {
        "total_assessments": len(assessments),
        "total_tests_attempted": len(test_attempts),
        "average_assessment_score": round(avg_assessment, 2),
        "average_test_score": round(avg_test, 2),
        "tests_passed": sum(1 for t in completed_tests if t.is_passed),
        "recent_insights": len(db.query(models.AIInsight).filter(
            models.AIInsight.user_id == current_user.id
        ).all())
    }


@app.get("/api/analytics/admin/test/{test_id}")
def get_admin_test_analytics(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Get admin analytics for a specific test"""
    test = db.query(models.Test).filter(models.Test.id == test_id).first()
    
    if not test or test.created_by != current_user.id:
        raise HTTPException(status_code=404, detail="Test not found")
    
    attempts = db.query(models.TestAttempt).filter(
        models.TestAttempt.test_id == test_id,
        models.TestAttempt.status.in_(["submitted", "graded"])
    ).all()
    
    if not attempts:
        return {"total_attempts": 0, "message": "No completed attempts"}
    
    scores = [a.percentage for a in attempts if a.percentage is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    pass_count = sum(1 for a in attempts if a.is_passed)
    
    return {
        "total_attempts": len(attempts),
        "average_score": round(avg_score, 2),
        "pass_rate": round(pass_count / len(attempts) * 100, 2),
        "highest_score": max(scores) if scores else 0,
        "lowest_score": min(scores) if scores else 0,
        "students_passed": pass_count,
        "students_failed": len(attempts) - pass_count
    }


# ========== CSE CAREER GAP ANALYZER ==========
@app.post("/api/cse/skill-gap/analyze")
async def analyze_cse_skill_gap(
    career_goal: str = Form(...),
    target_role: Optional[str] = Form(None),
    resume_text: Optional[str] = Form(None),
    document: Optional[UploadFile] = File(None),
):
    """Analyze resume/marksheet/performance sheet and return CSE goal-based skill gaps."""
    content_parts: List[str] = []

    if resume_text and resume_text.strip():
        content_parts.append(resume_text.strip())

    if document:
        raw = await document.read()
        if raw:
            parsed = parse_uploaded_document(document.filename or "uploaded_document", raw)
            if parsed.strip():
                content_parts.append(parsed.strip())

    if not content_parts:
        raise HTTPException(
            status_code=400,
            detail="Provide resume_text or upload a resume/marksheet/performance sheet.",
        )

    combined_text = "\n".join(content_parts)
    try:
        return analyze_cse_profile(combined_text, career_goal, target_role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/cse/skill-gap/report")
async def download_cse_skill_gap_report(
    career_goal: str = Form(...),
    target_role: Optional[str] = Form(None),
    resume_text: Optional[str] = Form(None),
    document: Optional[UploadFile] = File(None),
):
    """Generate downloadable text report for CSE goal-based skill gaps."""
    content_parts: List[str] = []

    if resume_text and resume_text.strip():
        content_parts.append(resume_text.strip())

    if document:
        raw = await document.read()
        if raw:
            parsed = parse_uploaded_document(document.filename or "uploaded_document", raw)
            if parsed.strip():
                content_parts.append(parsed.strip())

    if not content_parts:
        raise HTTPException(
            status_code=400,
            detail="Provide resume_text or upload a resume/marksheet/performance sheet.",
        )

    combined_text = "\n".join(content_parts)
    try:
        analysis = analyze_cse_profile(combined_text, career_goal, target_role)
        report_text = format_cse_report(analysis)
        filename = f"skilliq_{analysis.get('goal', 'career')}_report.txt"
        return StreamingResponse(
            iter([report_text]),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/cse/skill-gap/report-pdf")
async def download_cse_skill_gap_report_pdf(
    career_goal: str = Form(...),
    target_role: Optional[str] = Form(None),
    resume_text: Optional[str] = Form(None),
    document: Optional[UploadFile] = File(None),
):
    """Generate downloadable PDF report for CSE goal-based skill gaps."""
    content_parts: List[str] = []

    if resume_text and resume_text.strip():
        content_parts.append(resume_text.strip())

    if document:
        raw = await document.read()
        if raw:
            parsed = parse_uploaded_document(document.filename or "uploaded_document", raw)
            if parsed.strip():
                content_parts.append(parsed.strip())

    if not content_parts:
        raise HTTPException(
            status_code=400,
            detail="Provide resume_text or upload a resume/marksheet/performance sheet.",
        )

    combined_text = "\n".join(content_parts)
    try:
        analysis = analyze_cse_profile(combined_text, career_goal, target_role)
        pdf_bytes = build_cse_pdf_report(analysis)
        filename = f"skilliq_{analysis.get('goal', 'career')}_report.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ========== LIVE TEST WEBSOCKET ENDPOINT ==========
# Store active live test connections
live_test_connections = {}

@app.websocket("/ws/live-test/{test_id}/{student_id}")
async def websocket_live_test(websocket: WebSocket, test_id: int, student_id: int, db: Session = Depends(get_db)):
    """WebSocket for live testing"""
    await websocket.accept()
    
    key = f"{test_id}_{student_id}"
    live_test_connections[key] = websocket
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Broadcast updates to teacher
            if data.get("type") == "status_update":
                # Handle status updates
                pass
            elif data.get("type") == "submission":
                # Handle submission
                pass
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        del live_test_connections[key]


# ========== STATIC FILES ==========
WEB_ROOT = Path(__file__).resolve().parent.parent / "frontend"
if WEB_ROOT.exists():
    app.mount("/", StaticFiles(directory=str(WEB_ROOT), html=True), name="web")
else:
    @app.get("/")
    def web_root_fallback():
        return {
            "message": "SkillIQ API is running",
            "docs": "/docs",
        }
