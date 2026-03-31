from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import ml, models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

STAFF_ROLES = {"admin", "teacher"}

app = FastAPI(title="SkillIQ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_staff_role(request: Request):
    role = (request.headers.get("X-SkillIQ-Role") or "").strip().lower()
    if role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Forbidden. Staff role required.")


@app.get("/api/health")
def health():
    return {"status": "ok", "model_ready": ml.is_model_ready()}


@app.post("/api/assessments", response_model=schemas.AssessmentRead)
def create_assessment(payload: schemas.AssessmentCreate, db: Session = Depends(get_db)):
    item = models.Assessment(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.patch("/api/assessments/{assessment_id}/label", response_model=schemas.AssessmentRead)
def update_label(
    assessment_id: int,
    payload: schemas.LabelUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_staff_role),
):
    row = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    row.target_score = payload.target_score
    db.commit()
    db.refresh(row)
    return row


@app.get("/api/assessments", response_model=list[schemas.AssessmentRead])
def list_assessments(db: Session = Depends(get_db)):
    return db.query(models.Assessment).order_by(models.Assessment.id.desc()).limit(300).all()


@app.post("/api/train", response_model=schemas.TrainResponse)
def train_model(db: Session = Depends(get_db), _: None = Depends(require_staff_role)):
    try:
        return ml.train(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/predict", response_model=schemas.PredictResponse)
def predict(payload: schemas.PredictRequest, _: None = Depends(require_staff_role)):
    try:
        y_hat = ml.predict_one(payload.model_dump())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"predicted_target_score": round(y_hat, 2)}


WEB_ROOT = Path(__file__).resolve().parent.parent
app.mount("/", StaticFiles(directory=str(WEB_ROOT), html=True), name="web")
