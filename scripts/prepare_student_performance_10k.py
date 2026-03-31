import argparse
import csv
import statistics
from pathlib import Path


NUMERIC_COLUMNS = [
    "math_score",
    "reading_score",
    "writing_score",
    "science_score",
    "total_score",
]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def parse_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_binary(raw: str | None, default_value: int = 0) -> int:
    if raw is None:
        return default_value
    text = str(raw).strip().lower()
    if text in {"1", "yes", "true", "y"}:
        return 1
    if text in {"0", "no", "false", "n"}:
        return 0
    return default_value


def grade_to_target(grade: str | None) -> float:
    if grade is None:
        return 50.0
    text = str(grade).strip().upper()
    mapping = {
        "A": 90.0,
        "B": 78.0,
        "C": 65.0,
        "D": 50.0,
        "FAIL": 35.0,
    }
    return mapping.get(text, 50.0)


def build_numeric_medians(rows: list[dict[str, str]]) -> dict[str, float]:
    medians: dict[str, float] = {}
    for col in NUMERIC_COLUMNS:
        values = [v for v in (parse_float(r.get(col)) for r in rows) if v is not None]
        medians[col] = float(statistics.median(values)) if values else 0.0
    return medians


def transform_row(row: dict[str, str], medians: dict[str, float]) -> dict[str, float | int]:
    math_score = parse_float(row.get("math_score"))
    reading_score = parse_float(row.get("reading_score"))
    writing_score = parse_float(row.get("writing_score"))
    science_score = parse_float(row.get("science_score"))
    total_score = parse_float(row.get("total_score"))

    math_score = medians["math_score"] if math_score is None else math_score
    reading_score = medians["reading_score"] if reading_score is None else reading_score
    writing_score = medians["writing_score"] if writing_score is None else writing_score
    science_score = medians["science_score"] if science_score is None else science_score

    subject_avg = (math_score + reading_score + writing_score + science_score) / 4.0
    if total_score is None:
        total_score = subject_avg * 4.0

    # Scale total score from 0-400 to 0-100 for target.
    total_target = clamp(total_score / 4.0, 0.0, 100.0)
    grade_target = grade_to_target(row.get("grade"))

    # Prefer score-based target when present; blend with grade to smooth noisy labels.
    target_score = round(clamp((0.8 * total_target) + (0.2 * grade_target), 0.0, 100.0), 2)

    lunch_flag = parse_binary(row.get("lunch"), default_value=1)
    prep_flag = parse_binary(row.get("test_preparation_course"), default_value=0)

    overall_score = round(clamp(subject_avg, 0.0, 100.0), 2)
    math_skill = round(clamp(math_score, 0.0, 100.0), 2)
    logic_skill = round(clamp((0.6 * reading_score) + (0.4 * science_score), 0.0, 100.0), 2)
    aptitude_skill = round(clamp((0.7 * reading_score) + (0.3 * writing_score), 0.0, 100.0), 2)

    base_problem = (0.5 * science_score) + (0.35 * math_score) + (0.15 * writing_score)
    support_bonus = (lunch_flag * 4.0) + (prep_flag * 6.0)
    problem_skill = round(clamp(base_problem + support_bonus, 0.0, 100.0), 2)

    total_questions = 20
    total_correct = int(round(clamp(overall_score / 5.0, 0.0, 20.0)))
    accuracy_pct = round((total_correct / total_questions) * 100.0, 2)

    # Construct a stable pseudo-time signal using performance and support features.
    avg_time_sec = round(clamp(70.0 - (0.45 * overall_score) - (prep_flag * 8.0) - (lunch_flag * 3.0), 8.0, 120.0), 2)

    return {
        "selected_skills_count": 4,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "accuracy_pct": accuracy_pct,
        "avg_time_sec": avg_time_sec,
        "overall_score": overall_score,
        "math_score": math_skill,
        "logic_score": logic_skill,
        "aptitude_score": aptitude_skill,
        "problem_score": problem_skill,
        "target_score": target_score,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Student_performance_10k.csv to SkillIQ schema CSV.")
    parser.add_argument("--input", required=True, help="Path to Student_performance_10k.csv")
    parser.add_argument("--output", required=True, help="Path for transformed SkillIQ CSV")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    with input_path.open("r", encoding="utf-8-sig", newline="") as in_file:
        reader = csv.DictReader(in_file)
        source_rows = list(reader)

    if not source_rows:
        print("Source CSV has no rows.")
        return 1

    medians = build_numeric_medians(source_rows)
    out_rows = [transform_row(row, medians) for row in source_rows]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(out_rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote transformed rows: {len(out_rows)}")
    print(f"Output file: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
