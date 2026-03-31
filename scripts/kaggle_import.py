import argparse
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "skilliq.db"
MODEL_DIR = ROOT / "model_artifacts"
MODEL_PATH = MODEL_DIR / "linear_model.json"

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

ALL_FIELDS = FEATURES + ["target_score"]


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


def _to_float(raw: str) -> float:
    return float(str(raw).strip())


def _safe_ratio_pct(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return (num / den) * 100.0


def _normalize_payload(payload: dict[str, float]) -> dict[str, float]:
    payload["selected_skills_count"] = int(round(payload["selected_skills_count"]))
    payload["total_questions"] = int(round(payload["total_questions"]))
    payload["total_correct"] = int(round(payload["total_correct"]))
    return payload


def _validate_payload(payload: dict[str, float]) -> tuple[bool, str]:
    for field in FEATURES:
        if field not in payload:
            return False, f"Missing field: {field}"

    if payload["selected_skills_count"] < 1:
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
    for field in bounded_fields:
        if payload[field] < 0 or payload[field] > 100:
            return False, f"{field} must be in [0, 100]"

    if payload["avg_time_sec"] < 0:
        return False, "avg_time_sec must be >= 0"

    if "target_score" in payload and payload["target_score"] is not None:
        if payload["target_score"] < 0 or payload["target_score"] > 100:
            return False, "target_score must be in [0, 100]"

    return True, ""


def load_mapping(mapping_path: Path) -> tuple[dict[str, str], dict[str, float]]:
    config = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping = config.get("fields") or {}
    defaults = config.get("defaults") or {}
    return mapping, defaults


def row_to_payload(
    row: dict[str, str],
    mapping: dict[str, str],
    defaults: dict[str, float],
) -> dict[str, float]:
    payload: dict[str, float] = {}

    for field in ALL_FIELDS:
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

    payload = _normalize_payload(payload)
    valid, error = _validate_payload(payload)
    if not valid:
        raise ValueError(error)

    return payload


def insert_rows(rows: list[dict[str, float]]) -> int:
    conn = get_conn()
    inserted = 0
    for payload in rows:
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
        inserted += 1

    conn.commit()
    conn.close()
    return inserted


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


def _train_gd(X: list[list[float]], y: list[float], lr: float = 0.03, epochs: int = 2500) -> tuple[float, list[float]]:
    n = len(X)
    m = len(X[0])
    b0 = 0.0
    b = [0.0] * m
    for _ in range(epochs):
        preds = [b0 + _dot(row, b) for row in X]
        errors = [preds[i] - y[i] for i in range(n)]
        grad0 = (2 / n) * sum(errors)
        grads = [(2 / n) * sum(errors[i] * X[i][j] for i in range(n)) for j in range(m)]
        b0 -= lr * grad0
        b = [b[j] - lr * grads[j] for j in range(m)]
    return b0, b


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


def train_model() -> dict[str, float | int | str]:
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
        raise ValueError("Need at least 12 labeled assessments to train the model.")

    X = [[float(r[f]) for f in FEATURES] for r in rows]
    y = [float(r["target_score"]) for r in rows]

    split = max(1, int(len(X) * 0.8))
    X_train_raw, y_train = X[:split], y[:split]
    X_test_raw, y_test = X[split:], y[split:]
    if not X_test_raw:
        X_test_raw, y_test = X_train_raw, y_train

    X_train, means, stds = _normalize(X_train_raw)
    X_test = [[(v - means[i]) / stds[i] for i, v in enumerate(row)] for row in X_test_raw]

    b0, b = _train_gd(X_train, y_train)
    preds = [b0 + _dot(row, b) for row in X_test]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.write_text(
        json.dumps(
            {
                "intercept": b0,
                "weights": b,
                "feature_names": FEATURES,
                "means": means,
                "stds": stds,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "trained_rows": len(rows),
        "r2_score": float(_r2(y_test, preds)),
        "rmse": float(_rmse(y_test, preds)),
        "model_path": str(MODEL_PATH),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Kaggle CSV rows into SkillIQ DB.")
    parser.add_argument("--csv", required=True, help="Path to Kaggle CSV file")
    parser.add_argument("--map", required=True, help="Path to JSON field mapping file")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter, default is ','")
    parser.add_argument("--train", action="store_true", help="Train model after successful import")
    parser.add_argument(
        "--fail-on-row-error",
        action="store_true",
        help="Stop immediately when a row cannot be converted",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)
    mapping_path = Path(args.map)

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return 1

    if not mapping_path.exists():
        print(f"Mapping file not found: {mapping_path}")
        return 1

    init_db()
    mapping, defaults = load_mapping(mapping_path)

    converted_rows: list[dict[str, float]] = []
    skipped = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=args.delimiter)
        if reader.fieldnames is None:
            print("CSV file appears to be missing a header row.")
            return 1

        for line_number, row in enumerate(reader, start=2):
            try:
                converted_rows.append(row_to_payload(row, mapping, defaults))
            except Exception as exc:
                skipped += 1
                print(f"Skipping row {line_number}: {exc}")
                if args.fail_on_row_error:
                    return 1

    inserted = insert_rows(converted_rows)
    print(f"Imported rows: {inserted}")
    print(f"Skipped rows: {skipped}")

    if args.train:
        try:
            result = train_model()
            print("Training complete")
            print(json.dumps(result, indent=2))
        except ValueError as exc:
            print(str(exc))
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
