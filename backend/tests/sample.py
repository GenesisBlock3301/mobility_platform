"""The sample candidate from the assessment brief, shared by engine and API tests."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

SAMPLE_PROFILE: dict = {
    "education_level": "bachelor",
    "field_of_study": "Business Administration",
    "years_experience": 2,
    "experience_summary": "Business operations and project support",
    "skills": ["Excel", "Research", "Stakeholder communication", "Reporting", "Project coordination"],
    "languages": [
        {"language": "Bengali", "level": "native"},
        {"language": "English", "level": "professional"},
    ],
    "preferred_countries": ["DE", "CA", "SG"],
    "career_interests": ["Programme support", "Business operations", "Project coordination"],
    "work_authorisations": [],
    "is_current_student": None,
}


def load_opportunity_dicts() -> list[dict]:
    return json.loads((DATA_DIR / "opportunities.json").read_text(encoding="utf-8"))


def load_expected_ranking() -> dict:
    return json.loads((FIXTURES_DIR / "expected_ranking.json").read_text(encoding="utf-8"))
