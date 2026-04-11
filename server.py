import json
import sqlite3
import csv
import random
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "skilliq.db"
MODEL_DIR = ROOT / "model_artifacts"
MODEL_PATH = MODEL_DIR / "score_regressor.json"
MODEL_METADATA_PATH = MODEL_DIR / "score_regressor.metadata.json"
EXTERNAL_MODEL_DIR = MODEL_DIR / "external_models"

FEATURES = [
    "selected_skills_count",
    "total_questions",
    "total_correct",
    "accuracy_pct",
    "avg_time_sec",
    "overall_score",
    "math_score",
    "logic_score",
    "aptitude_score",
    "problem_score",
]

EXTERNAL_FEATURES = [
    "attendance_percentage",
    "quiz_average",
    "assignment_average",
    "midterm_score",
    "participation_score",
    "study_hours_per_week",
    "previous_gpa",
]

STAFF_ROLES = {"admin"}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            selected_skills_count INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            total_correct INTEGER NOT NULL,
            accuracy_pct REAL NOT NULL,
            avg_time_sec REAL NOT NULL,
            overall_score REAL NOT NULL,
            math_score REAL NOT NULL,
            logic_score REAL NOT NULL,
            aptitude_score REAL NOT NULL,
            problem_score REAL NOT NULL,
            target_score REAL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def to_assessment_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "selected_skills_count": row["selected_skills_count"],
        "total_questions": row["total_questions"],
        "total_correct": row["total_correct"],
        "accuracy_pct": row["accuracy_pct"],
        "avg_time_sec": row["avg_time_sec"],
        "overall_score": row["overall_score"],
        "math_score": row["math_score"],
        "logic_score": row["logic_score"],
        "aptitude_score": row["aptitude_score"],
        "problem_score": row["problem_score"],
        "target_score": row["target_score"],
        "created_at": row["created_at"],
    }


def validate_payload(payload: dict, allow_missing_target: bool = True) -> tuple[bool, str]:
    for field in FEATURES:
        if field not in payload:
            return False, f"Missing field: {field}"

    if not isinstance(payload["selected_skills_count"], (int, float)) or payload["selected_skills_count"] < 1:
        return False, "selected_skills_count must be >= 1"
    if payload["total_questions"] < 1 or payload["total_correct"] < 0:
        return False, "Invalid total_questions/total_correct"
    if payload["total_correct"] > payload["total_questions"]:
        return False, "total_correct cannot exceed total_questions"

    bounded_fields = [
        "accuracy_pct",
        "overall_score",
        "math_score",
        "logic_score",
        "aptitude_score",
        "problem_score",
    ]
    for f in bounded_fields:
        if payload[f] < 0 or payload[f] > 100:
            return False, f"{f} must be in [0, 100]"

    if payload["avg_time_sec"] < 0:
        return False, "avg_time_sec must be >= 0"

    if not allow_missing_target:
        if "target_score" not in payload or payload["target_score"] is None:
            return False, "target_score is required"

    if "target_score" in payload and payload["target_score"] is not None:
        if payload["target_score"] < 0 or payload["target_score"] > 100:
            return False, "target_score must be in [0, 100]"

    return True, ""


def _get_request_role() -> str:
    return (request.headers.get("X-SkillIQ-Role") or "").strip().lower()


def _require_staff_access():
    role = _get_request_role()
    if role not in STAFF_ROLES:
        return jsonify({"detail": "Forbidden. Staff role required."}), 403
    return None


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float], mean_value: float) -> float:
    var = sum((v - mean_value) ** 2 for v in values) / len(values) if values else 0.0
    return var**0.5 if var > 0 else 1.0


def _normalize(X: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    cols = list(zip(*X))
    means = [_mean(list(c)) for c in cols]
    stds = [_std(list(c), means[i]) for i, c in enumerate(cols)]
    X_norm = [[(v - means[i]) / stds[i] for i, v in enumerate(row)] for row in X]
    return X_norm, means, stds


def _rmse(actual: list[float], pred: list[float]) -> float:
    mse = sum((a - p) ** 2 for a, p in zip(actual, pred)) / len(actual)
    return mse**0.5


def _r2(actual: list[float], pred: list[float]) -> float:
    y_bar = _mean(actual)
    ss_res = sum((a - p) ** 2 for a, p in zip(actual, pred))
    ss_tot = sum((a - y_bar) ** 2 for a in actual)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = 1.0 / (1.0 + (2.718281828459045 ** (-x)))
        return z
    ex = 2.718281828459045 ** x
    return ex / (1.0 + ex)


def _softmax(values: list[float]) -> list[float]:
    if not values:
        return []
    max_v = max(values)
    exps = [2.718281828459045 ** (v - max_v) for v in values]
    s = sum(exps)
    if s == 0:
        return [0.0 for _ in values]
    return [v / s for v in exps]


def _linear_predict(coefficients: list[float], intercept: float, features: list[float]) -> float:
    return float(intercept) + _dot(coefficients, features)


def _load_external_model_json(filename: str) -> dict:
    path = EXTERNAL_MODEL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"External model file not found: {filename}")
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_external_feature_payload(payload: dict) -> tuple[bool, str]:
    for field in EXTERNAL_FEATURES:
        if field not in payload:
            return False, f"Missing external feature: {field}"
        try:
            float(payload[field])
        except Exception:
            return False, f"{field} must be numeric"
    return True, ""


def _to_external_feature_payload_from_skilliq(payload: dict) -> dict:
    valid, error = validate_payload(payload, allow_missing_target=True)
    if not valid:
        raise ValueError(error)

    accuracy_pct = float(payload["accuracy_pct"])
    avg_time_sec = float(payload["avg_time_sec"])
    overall_score = float(payload["overall_score"])
    math_score = float(payload["math_score"])
    logic_score = float(payload["logic_score"])
    aptitude_score = float(payload["aptitude_score"])
    problem_score = float(payload["problem_score"])
    selected_skills_count = float(payload["selected_skills_count"])

    attendance_percentage = clamp(58.0 + (0.42 * accuracy_pct) + (0.08 * (100.0 - avg_time_sec)), 0.0, 100.0)
    quiz_average = clamp(overall_score, 0.0, 100.0)
    assignment_average = clamp((0.7 * aptitude_score) + (0.3 * logic_score), 0.0, 100.0)
    midterm_score = clamp((0.55 * math_score) + (0.45 * logic_score), 0.0, 100.0)
    participation_score = clamp((0.6 * problem_score) + (0.4 * aptitude_score), 0.0, 100.0)
    study_hours_per_week = clamp(3.0 + (selected_skills_count * 1.4) + (accuracy_pct / 20.0) + ((100.0 - avg_time_sec) / 18.0), 1.0, 40.0)
    previous_gpa = clamp(5.0 + (overall_score / 20.0), 0.0, 10.0)

    return {
        "attendance_percentage": round(attendance_percentage, 4),
        "quiz_average": round(quiz_average, 4),
        "assignment_average": round(assignment_average, 4),
        "midterm_score": round(midterm_score, 4),
        "participation_score": round(participation_score, 4),
        "study_hours_per_week": round(study_hours_per_week, 4),
        "previous_gpa": round(previous_gpa, 4),
    }


def _external_predict_all(external_payload: dict) -> dict:
    score_model = _load_external_model_json("score_predictor.json")
    risk_model = _load_external_model_json("risk_assessor.json")
    grade_model = _load_external_model_json("grade_classifier.json")

    # Use feature order from model files where possible.
    score_features = score_model.get("features") or EXTERNAL_FEATURES
    risk_features = risk_model.get("features") or EXTERNAL_FEATURES
    grade_features = grade_model.get("features") or EXTERNAL_FEATURES

    score_x = [float(external_payload[f]) for f in score_features]
    risk_x = [float(external_payload[f]) for f in risk_features]
    grade_x = [float(external_payload[f]) for f in grade_features]

    score_raw = _linear_predict(score_model["coefficients"], score_model["intercept"], score_x)
    score_pred = round(clamp(float(score_raw), 0.0, 100.0), 2)

    risk_logits = [
        float(risk_model["intercept"][i]) + _dot([float(v) for v in risk_model["coefficients"][i]], risk_x)
        for i in range(len(risk_model["classes"]))
    ]
    risk_probs = _softmax(risk_logits)
    risk_pairs = [
        {"label": risk_model["classes"][i], "probability": round(float(risk_probs[i]), 6)}
        for i in range(len(risk_model["classes"]))
    ]
    risk_top_idx = max(range(len(risk_probs)), key=lambda i: risk_probs[i])

    grade_logits = [
        float(grade_model["intercept"][i]) + _dot([float(v) for v in grade_model["coefficients"][i]], grade_x)
        for i in range(len(grade_model["classes"]))
    ]
    grade_probs = _softmax(grade_logits)
    grade_pairs = [
        {"label": grade_model["classes"][i], "probability": round(float(grade_probs[i]), 6)}
        for i in range(len(grade_model["classes"]))
    ]
    grade_top_idx = max(range(len(grade_probs)), key=lambda i: grade_probs[i])

    return {
        "predicted_score": score_pred,
        "risk_assessment": {
            "predicted_label": risk_model["classes"][risk_top_idx],
            "class_probabilities": risk_pairs,
        },
        "grade_classification": {
            "predicted_grade": grade_model["classes"][grade_top_idx],
            "class_probabilities": grade_pairs,
        },
    }


def _to_float(raw: str) -> float:
    return float(str(raw).strip())


def _safe_ratio_pct(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return (num / den) * 100.0


def _normalize_import_payload(payload: dict) -> dict:
    payload["selected_skills_count"] = int(round(float(payload["selected_skills_count"])))
    payload["total_questions"] = int(round(float(payload["total_questions"])))
    payload["total_correct"] = int(round(float(payload["total_correct"])))
    return payload


def _row_to_import_payload(row: dict, mapping: dict, defaults: dict) -> dict:
    payload = {}

    for field in FEATURES + ["target_score"]:
        source_column = mapping.get(field)

        if source_column:
            raw = row.get(source_column)
            if raw is None or str(raw).strip() == "":
                if field in defaults:
                    payload[field] = float(defaults[field])
                elif field == "target_score":
                    payload[field] = None
                else:
                    raise ValueError(f"Row missing value for field '{field}' from column '{source_column}'")
            else:
                payload[field] = _to_float(raw)
        elif field in defaults:
            payload[field] = float(defaults[field])
        elif field == "target_score":
            payload[field] = None

    if "accuracy_pct" not in payload:
        if "total_correct" in payload and "total_questions" in payload:
            payload["accuracy_pct"] = _safe_ratio_pct(payload["total_correct"], payload["total_questions"])
        else:
            raise ValueError("Missing accuracy_pct and cannot derive it")

    if "target_score" not in payload:
        payload["target_score"] = None

    payload = _normalize_import_payload(payload)
    valid, error = validate_payload(payload, allow_missing_target=True)
    if not valid:
        raise ValueError(error)
    return payload


def _insert_assessment_payload(payload: dict) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO assessments (
            selected_skills_count, total_questions, total_correct,
            accuracy_pct, avg_time_sec, overall_score,
            math_score, logic_score, aptitude_score, problem_score, target_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(payload["selected_skills_count"]),
            int(payload["total_questions"]),
            int(payload["total_correct"]),
            float(payload["accuracy_pct"]),
            float(payload["avg_time_sec"]),
            float(payload["overall_score"]),
            float(payload["math_score"]),
            float(payload["logic_score"]),
            float(payload["aptitude_score"]),
            float(payload["problem_score"]),
            payload.get("target_score"),
        ),
    )
    conn.commit()
    conn.close()


def _train_gd(
    X: list[list[float]],
    y: list[float],
    lr: float = 0.03,
    epochs: int = 2500,
    l2_alpha: float = 0.0,
) -> tuple[float, list[float]]:
    n = len(X)
    m = len(X[0])
    b0 = 0.0
    b = [0.0] * m
    for _ in range(epochs):
        preds = [b0 + _dot(row, b) for row in X]
        errors = [preds[i] - y[i] for i in range(n)]
        grad0 = (2.0 / n) * sum(errors)
        grads = []
        for j in range(m):
            grad = (2.0 / n) * sum(errors[i] * X[i][j] for i in range(n))
            grad += (2.0 * l2_alpha / n) * b[j]
            grads.append(grad)
        b0 -= lr * grad0
        b = [b[j] - lr * grads[j] for j in range(m)]
    return b0, b


def _shuffle_split(X: list[list[float]], y: list[float], test_ratio: float = 0.2):
    idx = list(range(len(X)))
    random.Random(42).shuffle(idx)
    Xs = [X[i] for i in idx]
    ys = [y[i] for i in idx]

    test_size = max(1, int(len(Xs) * test_ratio))
    if test_size >= len(Xs):
        test_size = len(Xs) - 1
    split = len(Xs) - test_size
    return Xs[:split], ys[:split], Xs[split:], ys[split:]


def _kfold_indices(n: int, folds: int) -> list[tuple[list[int], list[int]]]:
    idx = list(range(n))
    random.Random(42).shuffle(idx)
    fold_sizes = [n // folds] * folds
    for i in range(n % folds):
        fold_sizes[i] += 1

    split_idx = []
    start = 0
    for size in fold_sizes:
        split_idx.append(idx[start : start + size])
        start += size

    out = []
    for i in range(folds):
        val_idx = split_idx[i]
        train_idx = [j for k, part in enumerate(split_idx) if k != i for j in part]
        out.append((train_idx, val_idx))
    return out


def _subset_rows(X: list[list[float]], y: list[float], idx: list[int]) -> tuple[list[list[float]], list[float]]:
    return [X[i] for i in idx], [y[i] for i in idx]


def _predict_knn(train_X: list[list[float]], train_y: list[float], row: list[float], k: int) -> float:
    dists = []
    for i, tr in enumerate(train_X):
        dist = sum((row[j] - tr[j]) ** 2 for j in range(len(row))) ** 0.5
        dists.append((dist, train_y[i]))
    dists.sort(key=lambda t: t[0])
    top = [v for _, v in dists[:k]]
    return _mean(top)


def _evaluate_predictions(actual: list[float], pred: list[float]) -> dict:
    return {
        "rmse": float(_rmse(actual, pred)),
        "mae": float(sum(abs(a - p) for a, p in zip(actual, pred)) / len(actual)),
        "r2": float(_r2(actual, pred)),
    }


def _train_best_regressor(X: list[list[float]], y: list[float]) -> tuple[dict, dict]:
    X_train, y_train, X_test, y_test = _shuffle_split(X, y, test_ratio=0.2)
    folds = min(5, len(X_train))
    if folds < 2:
        raise ValueError("Need at least 2 train rows after split for cross-validation.")

    candidates = [
        {"model": "ridge", "alpha": 0.0},
        {"model": "ridge", "alpha": 0.1},
        {"model": "ridge", "alpha": 1.0},
        {"model": "ridge", "alpha": 5.0},
        {"model": "knn", "k": 3},
        {"model": "knn", "k": 5},
    ]

    cv_results = []
    fold_pairs = _kfold_indices(len(X_train), folds)

    for cand in candidates:
        fold_metrics = []
        for train_idx, val_idx in fold_pairs:
            Xtr_raw, ytr = _subset_rows(X_train, y_train, train_idx)
            Xval_raw, yval = _subset_rows(X_train, y_train, val_idx)

            Xtr, means, stds = _normalize(Xtr_raw)
            Xval = [[(v - means[i]) / stds[i] for i, v in enumerate(row)] for row in Xval_raw]

            if cand["model"] == "ridge":
                b0, b = _train_gd(Xtr, ytr, lr=0.03, epochs=3500, l2_alpha=float(cand["alpha"]))
                preds = [b0 + _dot(row, b) for row in Xval]
            else:
                k = min(int(cand["k"]), len(Xtr))
                preds = [_predict_knn(Xtr, ytr, row, k) for row in Xval]

            fold_metrics.append(_evaluate_predictions(yval, preds))

        avg = {
            "cv_rmse": _mean([m["rmse"] for m in fold_metrics]),
            "cv_mae": _mean([m["mae"] for m in fold_metrics]),
            "cv_r2": _mean([m["r2"] for m in fold_metrics]),
        }
        cv_results.append({**cand, **avg})

    cv_results.sort(key=lambda r: r["cv_rmse"])
    best = cv_results[0]

    Xtr_all, means, stds = _normalize(X_train)
    Xte_all = [[(v - means[i]) / stds[i] for i, v in enumerate(row)] for row in X_test]

    if best["model"] == "ridge":
        b0, b = _train_gd(Xtr_all, y_train, lr=0.03, epochs=3500, l2_alpha=float(best["alpha"]))
        holdout_preds = [b0 + _dot(row, b) for row in Xte_all]
        artifact = {
            "model_type": "ridge",
            "feature_names": FEATURES,
            "means": means,
            "stds": stds,
            "intercept": b0,
            "weights": b,
            "alpha": float(best["alpha"]),
        }
    else:
        k = min(int(best["k"]), len(Xtr_all))
        holdout_preds = [_predict_knn(Xtr_all, y_train, row, k) for row in Xte_all]
        artifact = {
            "model_type": "knn",
            "feature_names": FEATURES,
            "means": means,
            "stds": stds,
            "k": k,
            "train_X": Xtr_all,
            "train_y": y_train,
        }

    holdout = _evaluate_predictions(y_test, holdout_preds)
    holdout["rows"] = len(X_test)

    metrics = {
        "selected_model": f"{best['model']}" + (f"(alpha={best['alpha']})" if best["model"] == "ridge" else f"(k={best['k']})"),
        "cv": cv_results,
        "holdout": holdout,
    }
    return artifact, metrics


app = Flask(__name__, static_folder=str(ROOT), static_url_path="")
# init_db()  # Disabled: using FastAPI app.main instead


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "model_ready": MODEL_PATH.exists()})


@app.get("/api/external-models")
def list_external_models():
    denied = _require_staff_access()
    if denied:
        return denied

    if not EXTERNAL_MODEL_DIR.exists():
        return jsonify({"available": False, "models": []})

    models = []
    for path in sorted(EXTERNAL_MODEL_DIR.glob("*")):
        if not path.is_file():
            continue
        model_info = {
            "name": path.name,
            "size_bytes": path.stat().st_size,
            "extension": path.suffix.lower(),
        }
        if path.suffix.lower() == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    model_info["keys"] = sorted(list(data.keys()))[:12]
            except Exception:
                model_info["keys"] = []
        models.append(model_info)

    return jsonify({"available": True, "models": models})


@app.post("/api/external/predict")
def external_predict():
    denied = _require_staff_access()
    if denied:
        return denied

    payload = request.get_json(force=True, silent=True) or {}

    # Accept either direct external features or SkillIQ payload and convert.
    use_external = all(field in payload for field in EXTERNAL_FEATURES)
    if use_external:
        valid, error = _validate_external_feature_payload(payload)
        if not valid:
            return jsonify({"detail": error}), 400
        external_payload = {field: float(payload[field]) for field in EXTERNAL_FEATURES}
        source = "external_features"
    else:
        try:
            external_payload = _to_external_feature_payload_from_skilliq(payload)
            source = "skilliq_payload"
        except (ValueError, KeyError) as exc:
            return jsonify({"detail": str(exc)}), 400

    try:
        result = _external_predict_all(external_payload)
    except FileNotFoundError as exc:
        return jsonify({"detail": str(exc)}), 400
    except Exception as exc:
        return jsonify({"detail": f"External prediction failed: {exc}"}), 500

    return jsonify(
        {
            "source": source,
            "external_features_used": external_payload,
            **result,
        }
    )


@app.post("/api/assessments")
def create_assessment():
    payload = request.get_json(force=True, silent=True) or {}
    valid, error = validate_payload(payload, allow_missing_target=True)
    if not valid:
        return jsonify({"detail": error}), 400

    conn = get_conn()
    cursor = conn.execute(
        """
        INSERT INTO assessments (
            selected_skills_count, total_questions, total_correct,
            accuracy_pct, avg_time_sec, overall_score,
            math_score, logic_score, aptitude_score, problem_score, target_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(payload["selected_skills_count"]),
            int(payload["total_questions"]),
            int(payload["total_correct"]),
            float(payload["accuracy_pct"]),
            float(payload["avg_time_sec"]),
            float(payload["overall_score"]),
            float(payload["math_score"]),
            float(payload["logic_score"]),
            float(payload["aptitude_score"]),
            float(payload["problem_score"]),
            payload.get("target_score"),
        ),
    )
    assessment_id = cursor.lastrowid
    conn.commit()
    row = conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
    conn.close()
    return jsonify(to_assessment_dict(row)), 201


@app.get("/api/assessments")
def list_assessments():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM assessments ORDER BY id DESC LIMIT 300").fetchall()
    conn.close()
    return jsonify([to_assessment_dict(r) for r in rows])


@app.patch("/api/assessments/<int:assessment_id>/label")
def label_assessment(assessment_id: int):
    denied = _require_staff_access()
    if denied:
        return denied

    payload = request.get_json(force=True, silent=True) or {}
    target = payload.get("target_score")
    if target is None or target < 0 or target > 100:
        return jsonify({"detail": "target_score must be in [0, 100]"}), 400

    conn = get_conn()
    existing = conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
    if existing is None:
        conn.close()
        return jsonify({"detail": "Assessment not found"}), 404

    conn.execute("UPDATE assessments SET target_score = ? WHERE id = ?", (float(target), assessment_id))
    conn.commit()
    row = conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
    conn.close()
    return jsonify(to_assessment_dict(row))


@app.post("/api/train")
def train_model():
    denied = _require_staff_access()
    if denied:
        return denied

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT * FROM assessments
        WHERE target_score IS NOT NULL
        ORDER BY id ASC
        """
    ).fetchall()
    conn.close()

    if len(rows) < 12:
        return jsonify({"detail": "Need at least 12 labeled assessments to train the model."}), 400

    X = [[float(r[f]) for f in FEATURES] for r in rows]
    y = [float(r["target_score"]) for r in rows]

    try:
        artifact, metrics = _train_best_regressor(X, y)
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    MODEL_METADATA_PATH.write_text(
        json.dumps(
            {
                "feature_names": FEATURES,
                "selected_model": metrics["selected_model"],
                "cv": metrics["cv"],
                "holdout": metrics["holdout"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return jsonify(
        {
            "trained_rows": len(rows),
            "r2_score": metrics["holdout"]["r2"],
            "rmse": metrics["holdout"]["rmse"],
            "mae": metrics["holdout"]["mae"],
            "selected_model": metrics["selected_model"],
            "cv": metrics["cv"],
            "model_path": str(MODEL_PATH),
        }
    )


@app.post("/api/predict")
def predict():
    denied = _require_staff_access()
    if denied:
        return denied

    if not MODEL_PATH.exists():
        return jsonify({"detail": "Model not trained yet."}), 400

    payload = request.get_json(force=True, silent=True) or {}
    valid, error = validate_payload(payload, allow_missing_target=True)
    if not valid:
        return jsonify({"detail": error}), 400

    artifact = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    feature_names = artifact.get("feature_names") or FEATURES
    means = artifact["means"]
    stds = artifact["stds"]
    row = [float(payload[f]) for f in feature_names]
    row_norm = [(v - means[i]) / stds[i] for i, v in enumerate(row)]

    if artifact.get("model_type") == "knn":
        train_X = artifact["train_X"]
        train_y = artifact["train_y"]
        k = int(artifact.get("k", 3))
        pred = _predict_knn(train_X, train_y, row_norm, k)
    else:
        b0 = float(artifact["intercept"])
        b = [float(x) for x in artifact["weights"]]
        pred = b0 + _dot(row_norm, b)

    return jsonify({"predicted_target_score": round(clamp(pred, 0.0, 100.0), 2)})


@app.get("/")
def home():
    return send_from_directory(ROOT, "index.html")


@app.get("/skilliq")
@app.get("/skilliq/")
@app.get("/SkillIQ")
@app.get("/SkillIQ/")
def home_alias():
    return send_from_directory(ROOT, "index.html")


@app.get("/<path:path>")
def static_files(path: str):
    candidate = ROOT / path
    if candidate.exists() and candidate.is_file():
        return send_from_directory(ROOT, path)
    return send_from_directory(ROOT, "index.html")


@app.post("/api/import-kaggle")
def import_kaggle_csv():
    denied = _require_staff_access()
    if denied:
        return denied

    csv_file = request.files.get("csv_file")
    map_file = request.files.get("mapping_file")
    if csv_file is None or map_file is None:
        return jsonify({"detail": "Provide csv_file and mapping_file as multipart form data."}), 400

    delimiter = request.form.get("delimiter", ",")
    train_after = request.form.get("train", "false").lower() in {"true", "1", "yes", "on"}
    fail_on_row_error = request.form.get("fail_on_row_error", "false").lower() in {"true", "1", "yes", "on"}

    try:
        mapping_config = json.loads(map_file.stream.read().decode("utf-8"))
    except Exception:
        return jsonify({"detail": "mapping_file must contain valid JSON."}), 400

    mapping = mapping_config.get("fields") or {}
    defaults = mapping_config.get("defaults") or {}

    try:
        csv_text = csv_file.stream.read().decode("utf-8-sig")
    except Exception:
        return jsonify({"detail": "Could not decode csv_file as UTF-8."}), 400

    reader = csv.DictReader(csv_text.splitlines(), delimiter=delimiter)
    if reader.fieldnames is None:
        return jsonify({"detail": "CSV appears to be missing a header row."}), 400

    inserted = 0
    skipped = 0
    errors = []

    for line_number, row in enumerate(reader, start=2):
        try:
            payload = _row_to_import_payload(row, mapping, defaults)
            _insert_assessment_payload(payload)
            inserted += 1
        except Exception as exc:
            skipped += 1
            errors.append(f"row {line_number}: {exc}")
            if fail_on_row_error:
                return jsonify(
                    {
                        "imported_rows": inserted,
                        "skipped_rows": skipped,
                        "detail": errors[-1],
                    }
                ), 400

    response = {
        "imported_rows": inserted,
        "skipped_rows": skipped,
    }

    if errors:
        response["errors"] = errors[:15]

    if train_after:
        conn = get_conn()
        rows = conn.execute(
            """
            SELECT * FROM assessments
            WHERE target_score IS NOT NULL
            ORDER BY id ASC
            """
        ).fetchall()
        conn.close()

        if len(rows) < 12:
            response["training"] = {
                "status": "skipped",
                "detail": "Need at least 12 labeled assessments to train the model.",
            }
            return jsonify(response), 200

        X = [[float(r[f]) for f in FEATURES] for r in rows]
        y = [float(r["target_score"]) for r in rows]

        try:
            artifact, metrics = _train_best_regressor(X, y)
        except ValueError as exc:
            response["training"] = {
                "status": "skipped",
                "detail": str(exc),
            }
            return jsonify(response), 200

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        MODEL_PATH.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

        MODEL_METADATA_PATH.write_text(
            json.dumps(
                {
                    "feature_names": FEATURES,
                    "selected_model": metrics["selected_model"],
                    "cv": metrics["cv"],
                    "holdout": metrics["holdout"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        response["training"] = {
            "status": "trained",
            "trained_rows": len(rows),
            "r2_score": metrics["holdout"]["r2"],
            "rmse": metrics["holdout"]["rmse"],
            "mae": metrics["holdout"]["mae"],
            "selected_model": metrics["selected_model"],
            "model_path": str(MODEL_PATH),
        }

    return jsonify(response), 200


if __name__ == "__main__":
    # Keep backward compatibility with `python server.py` by launching FastAPI.
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)