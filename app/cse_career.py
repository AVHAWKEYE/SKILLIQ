import csv
import io
import re
from typing import Any, Dict, List, Optional, Set

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    Document = None


SKILL_ALIASES: Dict[str, List[str]] = {
    "python": ["python", "py"],
    "java": ["java", "spring boot"],
    "c++": ["c++", "cpp"],
    "data structures": ["data structures", "dsa"],
    "algorithms": ["algorithms", "algorithm design"],
    "dbms": ["dbms", "database management", "database systems"],
    "sql": ["sql", "mysql", "postgresql", "postgres"],
    "operating systems": ["operating systems", "os"],
    "computer networks": ["computer networks", "cn", "networking"],
    "oop": ["oop", "object oriented", "object-oriented"],
    "git": ["git", "github", "gitlab"],
    "debugging": ["debugging", "debug"],
    "testing": ["testing", "unit testing", "pytest", "junit"],
    "web development": ["web development", "html", "css", "javascript", "react", "node"],
    "api development": ["api", "rest", "restful", "fastapi", "flask", "django"],
    "system design": ["system design", "scalability", "distributed systems"],
    "cloud fundamentals": ["aws", "azure", "gcp", "cloud"],
    "linux": ["linux", "unix", "bash"],
    "quantitative aptitude": ["quantitative aptitude", "quant", "aptitude"],
    "reasoning": ["reasoning", "logical reasoning"],
    "english communication": ["english", "communication", "spoken english", "writing"],
    "current affairs": ["current affairs", "general awareness", "gk"],
    "research methodology": ["research", "research methodology", "literature review"],
    "sop writing": ["statement of purpose", "sop"],
    "ielts/toefl": ["ielts", "toefl", "gre", "duolingo english test"],
    "team collaboration": ["teamwork", "collaboration", "agile", "scrum"],
}


CAREER_SKILL_MAP: Dict[str, Dict[str, Any]] = {
    "government_jobs": {
        "label": "Government Jobs (CSE)",
        "mandatory": [
            "data structures",
            "algorithms",
            "dbms",
            "operating systems",
            "computer networks",
            "quantitative aptitude",
            "reasoning",
            "english communication",
            "current affairs",
        ],
        "good_to_have": ["c++", "python", "linux", "debugging"],
        "roles": {
            "gate_cse": ["data structures", "algorithms", "dbms", "operating systems", "computer networks"],
            "isro_drdo_technical": ["c++", "data structures", "algorithms", "operating systems", "reasoning"],
            "ssc_cgl_it": ["quantitative aptitude", "reasoning", "english communication", "current affairs", "dbms"],
        },
    },
    "study_abroad": {
        "label": "Study Abroad (CSE)",
        "mandatory": [
            "ielts/toefl",
            "english communication",
            "sop writing",
            "research methodology",
            "data structures",
            "algorithms",
            "dbms",
            "operating systems",
        ],
        "good_to_have": ["python", "java", "team collaboration", "api development"],
        "roles": {
            "ms_cs": ["ielts/toefl", "sop writing", "research methodology", "data structures", "algorithms"],
            "ms_data_science": ["ielts/toefl", "sop writing", "python", "algorithms", "sql"],
            "research_track": ["research methodology", "english communication", "algorithms", "system design", "python"],
        },
    },
    "it_job": {
        "label": "IT Job",
        "mandatory": [
            "data structures",
            "algorithms",
            "oop",
            "dbms",
            "sql",
            "operating systems",
            "computer networks",
            "git",
            "debugging",
            "testing",
        ],
        "good_to_have": ["python", "java", "api development", "system design", "cloud fundamentals"],
        "roles": {
            "software_engineer": ["data structures", "algorithms", "oop", "dbms", "git", "testing"],
            "backend_developer": ["python", "java", "dbms", "sql", "api development", "system design"],
            "qa_automation": ["testing", "debugging", "python", "sql", "git", "team collaboration"],
        },
    },
}

SUBJECT_TO_SKILLS: Dict[str, List[str]] = {
    "data structures": ["data structures", "algorithms"],
    "algorithms": ["algorithms"],
    "dbms": ["dbms", "sql"],
    "database": ["dbms", "sql"],
    "operating systems": ["operating systems", "linux"],
    "computer networks": ["computer networks"],
    "network": ["computer networks"],
    "oops": ["oop"],
    "oop": ["oop"],
    "software engineering": ["testing", "team collaboration"],
    "web": ["web development", "api development"],
    "python": ["python"],
    "java": ["java"],
    "communication": ["english communication"],
}


def _normalize_goal(goal: str) -> str:
    g = (goal or "").strip().lower()
    aliases = {
        "govt": "government_jobs",
        "government": "government_jobs",
        "government_jobs": "government_jobs",
        "government job": "government_jobs",
        "abroad": "study_abroad",
        "study abroad": "study_abroad",
        "study_abroad": "study_abroad",
        "higher studies": "study_abroad",
        "it": "it_job",
        "it job": "it_job",
        "it_job": "it_job",
        "software job": "it_job",
    }
    return aliases.get(g, g)


def detect_skills_from_text(text: str) -> Set[str]:
    clean = f" {re.sub(r'[^a-z0-9+/# ]+', ' ', text.lower())} "
    detected: Set[str] = set()
    for skill, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            token = f" {alias.lower()} "
            if token in clean:
                detected.add(skill)
                break
    return detected


def extract_subject_scores(text: str) -> Dict[str, float]:
    score_map: Dict[str, float] = {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for line in lines:
        match = re.search(r"([A-Za-z+\- /&]+?)\s*[:=-]\s*(\d{1,3}(?:\.\d+)?)\b", line)
        if not match:
            continue

        subject = match.group(1).strip().lower()
        score = float(match.group(2))
        if score > 100:
            continue
        score_map[subject] = score

    return score_map


def infer_skills_from_scores(subject_scores: Dict[str, float], threshold: float = 65.0) -> Set[str]:
    inferred: Set[str] = set()
    for subject, score in subject_scores.items():
        if score < threshold:
            continue
        for key, skills in SUBJECT_TO_SKILLS.items():
            if key in subject:
                inferred.update(skills)
    return inferred


def build_recommendations(missing_skills: List[str], goal_key: str) -> List[str]:
    if not missing_skills:
        return [
            "You already match the mandatory baseline for this goal.",
            "Build portfolio depth with 2 advanced projects and weekly mock interviews/tests.",
        ]

    recs = []
    for skill in missing_skills[:5]:
        recs.append(f"Focus on {skill}: 30-45 minutes daily practice for 4 weeks.")

    if goal_key == "government_jobs":
        recs.append("Add a weekly mock test for aptitude, reasoning, and CSE core subjects.")
    elif goal_key == "study_abroad":
        recs.append("Start SOP draft and IELTS/TOEFL preparation with weekly speaking practice.")
    else:
        recs.append("Solve 3 coding interview problems daily and do 1 project sprint each week.")

    return recs


def _estimate_proficiency(
    skill: str,
    raw_text: str,
    subject_scores: Dict[str, float],
    mandatory_skills: List[str],
) -> Dict[str, Any]:
    text_l = raw_text.lower()
    aliases = SKILL_ALIASES.get(skill, [skill])
    mention_hits = sum(text_l.count(alias.lower()) for alias in aliases)

    related_scores = []
    for subject, score in subject_scores.items():
        for subject_key, mapped_skills in SUBJECT_TO_SKILLS.items():
            if subject_key in subject and skill in mapped_skills:
                related_scores.append(score)

    avg_score = round(sum(related_scores) / len(related_scores), 2) if related_scores else None

    if avg_score is not None and avg_score >= 80:
        level = "advanced"
    elif avg_score is not None and avg_score >= 65:
        level = "intermediate"
    elif mention_hits >= 2:
        level = "intermediate"
    else:
        level = "beginner"

    confidence = min(100, 25 + mention_hits * 12 + int((avg_score or 0) * 0.6))
    return {
        "level": level,
        "confidence": confidence,
        "mentions": mention_hits,
        "avg_related_score": avg_score,
        "mandatory": skill in mandatory_skills,
    }


def _normalize_role(goal_key: str, role: Optional[str]) -> Optional[str]:
    if not role:
        return None
    r = role.strip().lower().replace(" ", "_")
    roles = CAREER_SKILL_MAP.get(goal_key, {}).get("roles", {})
    return r if r in roles else None


def format_cse_report(analysis: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("SkillIQ - CSE Career Skill Gap Report")
    lines.append("=" * 44)
    lines.append(f"Goal: {analysis.get('goal_label', '-')}")
    if analysis.get("target_role"):
        lines.append(f"Target Role: {analysis['target_role']}")
    lines.append(f"Readiness: {analysis.get('readiness_percentage', 0)}%")
    lines.append("")

    lines.append("Mandatory Skills")
    for item in analysis.get("required_mandatory_skills", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("Detected Skills")
    for item in analysis.get("skills_detected", []):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("Missing Mandatory Skills")
    missing = analysis.get("missing_mandatory_skills", [])
    if not missing:
        lines.append("- None")
    else:
        for item in missing:
            lines.append(f"- {item}")
    lines.append("")

    lines.append("Skill Proficiency")
    for skill, pdata in analysis.get("skill_proficiency", {}).items():
        lvl = pdata.get("level", "beginner")
        conf = pdata.get("confidence", 0)
        lines.append(f"- {skill}: {lvl} (confidence {conf}%)")
    lines.append("")

    lines.append("Recommendations")
    for rec in analysis.get("recommendations", []):
        lines.append(f"- {rec}")

    return "\n".join(lines)


def build_cse_pdf_report(analysis: Dict[str, Any]) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4  # type: ignore[import-not-found]
        from reportlab.pdfgen import canvas  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover
        raise ValueError("PDF export dependency missing. Install reportlab.") from exc

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    _, height = A4

    y = height - 50
    left = 45
    line_h = 16

    def write_line(text: str, bold: bool = False, spacing: int = line_h) -> None:
        nonlocal y
        if y < 55:
            pdf.showPage()
            y = height - 50
        pdf.setFont("Helvetica-Bold" if bold else "Helvetica", 11)
        pdf.drawString(left, y, text[:115])
        y -= spacing

    write_line("SkillIQ - CSE Career Skill Gap Report", bold=True, spacing=20)
    write_line(f"Goal: {analysis.get('goal_label', '-')}")
    if analysis.get("target_role"):
        write_line(f"Target Role: {analysis['target_role']}")
    write_line(f"Readiness: {analysis.get('readiness_percentage', 0)}%")
    y -= 4

    write_line("Mandatory Skills", bold=True)
    for skill in analysis.get("required_mandatory_skills", []):
        write_line(f"- {skill}")
    y -= 4

    write_line("Detected Skills", bold=True)
    for skill in analysis.get("skills_detected", []):
        write_line(f"- {skill}")
    y -= 4

    write_line("Missing Mandatory Skills", bold=True)
    missing = analysis.get("missing_mandatory_skills", [])
    if not missing:
        write_line("- None")
    else:
        for skill in missing:
            write_line(f"- {skill}")
    y -= 4

    write_line("Skill Proficiency", bold=True)
    for skill, pdata in analysis.get("skill_proficiency", {}).items():
        lvl = pdata.get("level", "beginner")
        conf = pdata.get("confidence", 0)
        write_line(f"- {skill}: {lvl} (confidence {conf}%)")
    y -= 4

    write_line("Recommendations", bold=True)
    for rec in analysis.get("recommendations", []):
        write_line(f"- {rec}")

    pdf.save()
    out = buffer.getvalue()
    buffer.close()
    return out


def parse_uploaded_document(filename: str, content: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext in {"txt", "md"}:
        return content.decode("utf-8", errors="ignore")

    if ext == "csv":
        text = content.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        return "\n".join([", ".join(row) for row in reader])

    if ext == "pdf" and PdfReader is not None:
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == "docx" and Document is not None:
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)

    # Best-effort text fallback for unknown or unsupported formats.
    return content.decode("utf-8", errors="ignore")


def analyze_cse_profile(raw_text: str, goal: str, target_role: Optional[str] = None) -> Dict:
    goal_key = _normalize_goal(goal)
    profile = CAREER_SKILL_MAP.get(goal_key)
    if not profile:
        raise ValueError("Unsupported goal. Use: government_jobs, study_abroad, or it_job.")

    role_key = _normalize_role(goal_key, target_role)
    if target_role and not role_key:
        valid_roles = sorted(list(profile.get("roles", {}).keys()))
        if valid_roles:
            raise ValueError(
                "Unsupported target_role for selected goal. "
                f"Valid roles: {', '.join(valid_roles)}"
            )

    detected_direct = detect_skills_from_text(raw_text)
    subject_scores = extract_subject_scores(raw_text)
    detected_from_scores = infer_skills_from_scores(subject_scores)
    all_detected = sorted(detected_direct.union(detected_from_scores))

    mandatory = list(profile["mandatory"])
    if role_key:
        for role_skill in profile.get("roles", {}).get(role_key, []):
            if role_skill not in mandatory:
                mandatory.append(role_skill)

    good_to_have = profile["good_to_have"]
    missing_mandatory = [s for s in mandatory if s not in all_detected]
    matched_mandatory = [s for s in mandatory if s in all_detected]

    readiness = round((len(matched_mandatory) / len(mandatory)) * 100, 2) if mandatory else 0.0
    proficiency = {
        skill: _estimate_proficiency(skill, raw_text, subject_scores, mandatory)
        for skill in all_detected
    }
    role_options = sorted(list(profile.get("roles", {}).keys()))

    return {
        "goal": goal_key,
        "goal_label": profile["label"],
        "target_role": role_key,
        "available_role_profiles": role_options,
        "required_mandatory_skills": mandatory,
        "good_to_have_skills": good_to_have,
        "skills_detected": all_detected,
        "matched_mandatory_skills": matched_mandatory,
        "missing_mandatory_skills": missing_mandatory,
        "readiness_percentage": readiness,
        "detected_subject_scores": subject_scores,
        "skill_proficiency": proficiency,
        "recommendations": build_recommendations(missing_mandatory, goal_key),
    }
