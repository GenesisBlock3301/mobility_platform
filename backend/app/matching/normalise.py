"""Text normalisation and a small skill synonym map.

Limits: the map is hand-written and covers only the skills in the sample data.
It does exact matching after normalisation, so "Excel" and "Advanced Excel"
are still different skills. A real product would use a managed skills taxonomy.
"""

import re

_SPACES = re.compile(r"\s+")
_PUNCTUATION = re.compile(r"[^\w\s+#]")

SKILL_SYNONYMS: dict[str, str] = {
    "ms excel": "excel",
    "microsoft excel": "excel",
    "excel spreadsheets": "excel",
    "stakeholder management": "stakeholder communication",
    "stakeholder engagement": "stakeholder communication",
    "data analytics": "data analysis",
    "presentations": "presentation",
    "presentation skills": "presentation",
    "powerpoint": "presentation",
    "microsoft project": "ms project",
    "customer service": "customer support",
    "client support": "customer support",
    "budgeting": "budget tracking",
    "budget management": "budget tracking",
    "report writing": "reporting",
    "reports": "reporting",
    "crm": "crm software",
    "aws": "cloud platforms",
    "cloud": "cloud platforms",
}

COUNTRY_NAMES: dict[str, str] = {
    "CA": "Canada",
    "CH": "Switzerland",
    "DE": "Germany",
    "GB": "the United Kingdom",
    "NL": "the Netherlands",
    "SG": "Singapore",
}


def normalise_text(value: str) -> str:
    """Lower-case, strip punctuation and collapse whitespace."""
    text = _PUNCTUATION.sub(" ", value.lower())
    return _SPACES.sub(" ", text).strip()


def normalise_skill(value: str) -> str:
    text = normalise_text(value)
    return SKILL_SYNONYMS.get(text, text)


def same_language(a: str, b: str) -> bool:
    return normalise_text(a) == normalise_text(b)


def country_name(code: str) -> str:
    return COUNTRY_NAMES.get(code.upper(), code.upper())
