import json
import random
from pathlib import Path

from sqlalchemy.orm import Session

from .models import Assessment

MODEL_DIR = Path(__file__).resolve().parent.parent / "model_artifacts"
MODEL_PATH = MODEL_DIR / "score_regressor.json"
MODEL_METADATA_PATH = MODEL_DIR / "score_regressor.metadata.json"

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


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float], mean_value: float) -> float:
    if not values:
        return 1.0
    var = sum((v - mean_value) ** 2 for v in values) / len(values)
    return var**0.5 if var > 0 else 1.0


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


def _normalize(X: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    cols = list(zip(*X))
    means = [_mean(list(c)) for c in cols]
    stds = [_std(list(c), means[i]) for i, c in enumerate(cols)]
    X_norm = [[(v - means[i]) / stds[i] for i, v in enumerate(row)] for row in X]
    return X_norm, means, stds


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


def _to_xy(rows: list[Assessment]) -> tuple[list[list[float]], list[float]]:
    X, y = [], []
    for row in rows:
        X.append([float(getattr(row, name)) for name in FEATURES])
        target_score = getattr(row, "target_score")
        y.append(float(target_score if target_score is not None else 0.0))
    return X, y


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


def train(db: Session) -> dict:
    rows = db.query(Assessment).filter(Assessment.target_score.isnot(None)).all()
    if len(rows) < 12:
        raise ValueError("Need at least 12 labeled assessments to train the model.")

    X, y = _to_xy(rows)
    artifact, metrics = _train_best_regressor(X, y)

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

    return {
        "trained_rows": len(rows),
        "r2_score": metrics["holdout"]["r2"],
        "rmse": metrics["holdout"]["rmse"],
        "model_path": str(MODEL_PATH),
    }


def is_model_ready() -> bool:
    return MODEL_PATH.exists()


def predict_one(payload: dict) -> float:
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model not trained yet.")

    artifact = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    feature_names = artifact.get("feature_names") or FEATURES
    means = artifact["means"]
    stds = artifact["stds"]

    row = [float(payload[name]) for name in feature_names]
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

    return max(0.0, min(100.0, float(pred)))
