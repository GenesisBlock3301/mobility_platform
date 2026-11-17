"""Which profile fields are empty, so the interface can say why scores are less reliable."""

from dataclasses import dataclass

from app.matching.types import Profile

FIELD_LABELS: dict[str, str] = {
    "education_level": "Education level",
    "field_of_study": "Field of study",
    "years_experience": "Years of experience",
    "skills": "Skills",
    "languages": "Languages",
    "preferred_countries": "Preferred countries",
    "career_interests": "Career interests",
    "work_authorisations": "Right to work",
    "is_current_student": "Student status",
}


@dataclass(frozen=True, slots=True)
class Completeness:
    percent: int
    missing: tuple[str, ...]


def completeness(profile: Profile) -> Completeness:
    missing = [name for name in FIELD_LABELS if getattr(profile, name) in (None, "", ())]
    filled = len(FIELD_LABELS) - len(missing)
    return Completeness(percent=round(100 * filled / len(FIELD_LABELS)), missing=tuple(missing))
