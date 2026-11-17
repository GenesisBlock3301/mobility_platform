import pytest

from app.matching import rank, score_match
from app.matching.types import OverallEligibility
from tests.sample import load_expected_ranking

EXPECTED = {k: v for k, v in load_expected_ranking().items() if not k.startswith("_")}


def test_fixture_covers_every_seed_opportunity(opportunities):
    assert set(EXPECTED) == {o.slug for o in opportunities}
    assert len(EXPECTED) >= 10


@pytest.mark.parametrize("slug", sorted(EXPECTED))
def test_band_and_eligibility(slug, sample_profile, by_slug):
    result = score_match(sample_profile, by_slug[slug])
    assert result.band.value == EXPECTED[slug]["band"]
    assert result.eligibility.value == EXPECTED[slug]["eligibility"]


def test_blocked_roles_rank_below_every_open_role(sample_profile, opportunities):
    ranked = rank(sample_profile, opportunities)
    blocked = [r.eligibility is OverallEligibility.BLOCKED for r in ranked]
    first_blocked = blocked.index(True)
    assert all(blocked[first_blocked:])
    assert not any(blocked[:first_blocked])


def test_open_roles_are_sorted_by_score(sample_profile, opportunities):
    ranked = [
        r for r in rank(sample_profile, opportunities) if r.eligibility is not OverallEligibility.BLOCKED
    ]
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)
