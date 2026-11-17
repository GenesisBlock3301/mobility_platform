import pytest

from app.matching.convert import opportunity_from_mapping, profile_from_mapping
from app.matching.types import Opportunity, Profile
from tests.sample import SAMPLE_PROFILE, load_opportunity_dicts


@pytest.fixture
def sample_profile() -> Profile:
    return profile_from_mapping(SAMPLE_PROFILE)


@pytest.fixture
def opportunities() -> list[Opportunity]:
    return [opportunity_from_mapping(d) for d in load_opportunity_dicts()]


@pytest.fixture
def by_slug(opportunities: list[Opportunity]) -> dict[str, Opportunity]:
    return {o.slug: o for o in opportunities}
