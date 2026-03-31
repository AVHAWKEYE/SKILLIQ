import argparse
import csv
from pathlib import Path


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def to_float(row: dict[str, str], key: str) -> float:
    return float(str(row.get(key, "0")).strip())


def transform_row(row: dict[str, str]) -> dict[str, float | int]:
    g1 = to_float(row, "G1")
    g2 = to_float(row, "G2")
    g3 = to_float(row, "G3")
    studytime = to_float(row, "studytime")
    failures = to_float(row, "failures")
    absences = to_float(row, "absences")
    goout = to_float(row, "goout")
    freetime = to_float(row, "freetime")
    health = to_float(row, "health")

    # UCI scores are 0-20, scale to 0-100 for SkillIQ features.
    math_score = clamp(g1 * 5.0, 0.0, 100.0)
    logic_score = clamp(g2 * 5.0, 0.0, 100.0)
    target_score = clamp(g3 * 5.0, 0.0, 100.0)

    study_component = (studytime / 4.0) * 70.0
    attendance_component = (1.0 - min(absences / 30.0, 1.0)) * 30.0
    aptitude_score = clamp(study_component + attendance_component, 0.0, 100.0)

    behavior_penalty = ((goout - 1.0) / 4.0) * 20.0
    health_bonus = ((health - 1.0) / 4.0) * 15.0
    free_bonus = ((freetime - 1.0) / 4.0) * 10.0
    failure_penalty = failures * 12.0
    problem_score = clamp(70.0 + health_bonus + free_bonus - behavior_penalty - failure_penalty, 0.0, 100.0)

    overall_score = clamp(
        (0.35 * target_score) + (0.25 * math_score) + (0.2 * logic_score) + (0.1 * aptitude_score) + (0.1 * problem_score),
        0.0,
        100.0,
    )

    total_questions = 20
    total_correct = int(round(clamp(overall_score / 5.0, 0.0, 20.0)))
    accuracy_pct = round((total_correct / total_questions) * 100.0, 2)
    avg_time_sec = round(clamp(65.0 - (studytime * 7.0) + (failures * 6.0) + (absences * 0.2), 8.0, 120.0), 2)

    return {
        "selected_skills_count": 4,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "accuracy_pct": accuracy_pct,
        "avg_time_sec": avg_time_sec,
        "overall_score": round(overall_score, 2),
        "math_score": round(math_score, 2),
        "logic_score": round(logic_score, 2),
        "aptitude_score": round(aptitude_score, 2),
        "problem_score": round(problem_score, 2),
        "target_score": round(target_score, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert student-mat.csv to SkillIQ schema CSV.")
    parser.add_argument("--input", required=True, help="Path to student-mat.csv")
    parser.add_argument("--output", required=True, help="Path for transformed CSV")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as in_file:
        reader = csv.DictReader(in_file)
        rows = [transform_row(row) for row in reader]

    if not rows:
        print("No rows found in source dataset.")
        return 1

    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote transformed rows: {len(rows)}")
    print(f"Output file: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
