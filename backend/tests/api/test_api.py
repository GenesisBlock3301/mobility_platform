import logging
import uuid

import pytest

from app.seed import load_seed
from tests.sample import SAMPLE_PROFILE

pytestmark = pytest.mark.usefixtures("clean")

PROBLEM_KEYS = {"type", "title", "status", "detail", "request_id"}


async def _create(client, body=None):
    response = await client.post("/profiles", json=body or SAMPLE_PROFILE)
    assert response.status_code == 201, response.text
    return response.json()


async def _opportunity_id(client, slug: str) -> str:
    opportunities = (await client.get("/opportunities")).json()
    return next(o["id"] for o in opportunities if o["slug"] == slug)


async def test_health(client):
    assert (await client.get("/health/live")).json() == {"status": "ok"}
    ready = await client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["postgres"] == "up"


async def test_profile_create_read_update_delete(client):
    created = await _create(client)
    profile_id = created["id"]
    assert created["completeness"]["missing"] == ["work_authorisations", "is_current_student"]

    fetched = await client.get(f"/profiles/{profile_id}")
    assert fetched.status_code == 200
    assert fetched.json()["skills"] == SAMPLE_PROFILE["skills"]

    updated = await client.put(
        f"/profiles/{profile_id}", json={**SAMPLE_PROFILE, "is_current_student": False}
    )
    assert updated.status_code == 200
    assert updated.json()["is_current_student"] is False

    assert (await client.delete(f"/profiles/{profile_id}")).status_code == 204
    assert (await client.get(f"/profiles/{profile_id}")).status_code == 404


async def test_delete_removes_shortlist_entries(client):
    profile_id = (await _create(client))["id"]
    opp = await _opportunity_id(client, "programme-assistant-ngo-berlin")
    assert (await client.put(f"/profiles/{profile_id}/shortlist/{opp}")).status_code == 204

    assert (await client.delete(f"/profiles/{profile_id}")).status_code == 204
    # The profile is gone, and so is everything hanging off it.
    assert (await client.get(f"/profiles/{profile_id}/shortlist")).status_code == 404


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"years_experience": -1}, "years_experience"),
        ({"field_of_study": "x" * 121}, "field_of_study"),
        ({"favourite_colour": "blue"}, "favourite_colour"),
        ({"preferred_countries": ["XX"]}, "preferred_countries"),
        ({"languages": [{"language": "English", "level": "expert"}]}, "languages.0.level"),
        ({"education_level": None}, "education_level"),
        ({"years_experience": None}, "years_experience"),
        ({"skills": []}, "skills"),
        ({"languages": []}, "languages"),
    ],
)
async def test_validation_errors_use_problem_format(client, body, field):
    response = await client.post("/profiles", json={**SAMPLE_PROFILE, **body})
    assert response.status_code == 422
    problem = response.json()
    assert PROBLEM_KEYS <= problem.keys()
    assert field in {e["field"] for e in problem["errors"]}
    assert response.headers["content-type"].startswith("application/problem+json")


async def test_required_fields_are_named_when_omitted(client):
    response = await client.post("/profiles", json={"preferred_countries": ["DE"]})
    assert response.status_code == 422
    messages = {e["field"]: e["message"] for e in response.json()["errors"]}
    assert messages == {
        "education_level": "Choose your highest education",
        "years_experience": "Enter your years of work experience",
        "skills": "Add at least one skill",
        "languages": "Add at least one language",
    }


async def test_optional_fields_can_be_left_empty(client):
    required_only = {k: SAMPLE_PROFILE[k] for k in ("education_level", "years_experience", "skills", "languages")}
    created = await _create(client, required_only)
    assert created["preferred_countries"] == []
    assert created["is_current_student"] is None


async def test_unknown_profile_returns_404(client):
    response = await client.get(f"/profiles/{uuid.uuid4()}/matches")
    assert response.status_code == 404
    assert response.json()["title"] == "Not found"


async def test_404_says_which_resource_is_missing(client):
    profile_id = (await _create(client))["id"]
    unknown_role = await client.get(f"/profiles/{profile_id}/matches/{uuid.uuid4()}")
    assert unknown_role.json()["resource"] == "opportunity"
    unknown_profile = await client.get(f"/profiles/{uuid.uuid4()}")
    assert unknown_profile.json()["resource"] == "profile"


async def test_no_endpoint_lists_profiles(client):
    assert (await client.get("/profiles")).status_code == 405


async def test_injection_text_round_trips_as_plain_text(client):
    nasty = "'; DROP TABLE profiles; -- <script>alert(1)</script>"
    created = await _create(client, {**SAMPLE_PROFILE, "field_of_study": nasty[:120]})
    fetched = (await client.get(f"/profiles/{created['id']}")).json()
    assert fetched["field_of_study"] == nasty[:120]
    assert (await client.get("/opportunities")).status_code == 200


async def test_shortlist_is_idempotent(client):
    profile_id = (await _create(client))["id"]
    opp = await _opportunity_id(client, "project-coordinator-toronto")

    for _ in range(2):
        assert (await client.put(f"/profiles/{profile_id}/shortlist/{opp}")).status_code == 204
    saved = (await client.get(f"/profiles/{profile_id}/shortlist")).json()
    assert [m["opportunity"]["slug"] for m in saved] == ["project-coordinator-toronto"]

    for _ in range(2):
        assert (await client.delete(f"/profiles/{profile_id}/shortlist/{opp}")).status_code == 204
    assert (await client.get(f"/profiles/{profile_id}/shortlist")).json() == []


async def test_shortlist_unknown_opportunity_is_404(client):
    profile_id = (await _create(client))["id"]
    response = await client.put(f"/profiles/{profile_id}/shortlist/{uuid.uuid4()}")
    assert response.status_code == 404


async def _all_matches(client, profile_id: str) -> list[dict]:
    body = (await client.get(f"/profiles/{profile_id}/matches", params={"page_size": 50})).json()
    return body["items"]


async def test_matches_are_ranked_and_reflect_profile_edits(client):
    profile_id = (await _create(client))["id"]
    matches = await _all_matches(client, profile_id)
    assert len(matches) == len(load_seed())
    assert [m["rank"] for m in matches] == list(range(1, len(matches) + 1))
    assert matches[-1]["eligibility"] == "blocked"
    german = next(m for m in matches if m["opportunity"]["slug"] == "german-speaking-client-associate-munich")
    assert german["eligibility"] == "blocked"

    languages = SAMPLE_PROFILE["languages"] + [{"language": "German", "level": "professional"}]
    await client.put(f"/profiles/{profile_id}", json={**SAMPLE_PROFILE, "languages": languages})
    matches = await _all_matches(client, profile_id)
    german = next(m for m in matches if m["opportunity"]["slug"] == "german-speaking-client-associate-munich")
    assert german["eligibility"] == "requires_verification"


async def test_match_detail(client):
    profile_id = (await _create(client))["id"]
    opp = await _opportunity_id(client, "programme-assistant-ngo-berlin")
    detail = (await client.get(f"/profiles/{profile_id}/matches/{opp}")).json()
    assert detail["score"] == 91
    assert sum(c["points_possible"] for c in detail["criteria"]) == 100
    assert detail["verification_checklist"]
    assert detail["what_if"][0]["new_score"] == 98
    assert "Strong fit (91/100)" in detail["explanation"]


async def test_rate_limit_returns_429(app_factory, client_for):
    app = app_factory(rate_limit_enabled=True, rate_limit_reads_per_minute=3)
    async for client in client_for(app):
        statuses = [(await client.get("/opportunities")).status_code for _ in range(4)]
        assert statuses == [200, 200, 200, 429]
        limited = await client.get("/opportunities")
        assert int(limited.headers["retry-after"]) >= 1


async def test_body_too_large_returns_413(client):
    big = {**SAMPLE_PROFILE, "experience_summary": "x" * 70_000}
    response = await client.post("/profiles", json=big)
    assert response.status_code == 413


async def test_chunked_body_without_content_length_is_capped(client):
    async def chunks():
        for _ in range(100):
            yield b"x" * 1024

    response = await client.post("/profiles", content=chunks(), headers={"content-type": "application/json"})
    assert response.status_code == 413


async def test_duplicate_language_error_names_the_field(client):
    languages = [{"language": "English", "level": "professional"}, {"language": "english", "level": "native"}]
    response = await client.post("/profiles", json={**SAMPLE_PROFILE, "languages": languages})
    assert response.status_code == 422
    assert {"field": "languages", "message": "Each language can be listed only once"} in response.json()[
        "errors"
    ]


async def test_shortlist_ids(client):
    profile_id = (await _create(client))["id"]
    opp = await _opportunity_id(client, "project-coordinator-toronto")
    assert (await client.get(f"/profiles/{profile_id}/shortlist/ids")).json() == []
    await client.put(f"/profiles/{profile_id}/shortlist/{opp}")
    assert (await client.get(f"/profiles/{profile_id}/shortlist/ids")).json() == [opp]


async def test_rate_limit_key_from_web_server_is_trusted_only_with_the_token(app_factory, client_for):
    from tests.api.conftest import INTERNAL_TOKEN

    app = app_factory(rate_limit_enabled=True, rate_limit_reads_per_minute=1)
    async for client in client_for(app):
        web = {"x-internal-token": INTERNAL_TOKEN}
        assert (await client.get("/opportunities", headers={**web, "x-client-key": "a"})).status_code == 200
        assert (await client.get("/opportunities", headers={**web, "x-client-key": "a"})).status_code == 429
        assert (await client.get("/opportunities", headers={**web, "x-client-key": "b"})).status_code == 200
        # Without the token the header is ignored and the socket address is used.
        forged = {"x-internal-token": "wrong-token-000000", "x-client-key": "c"}
        assert (await client.get("/opportunities", headers=forged)).status_code == 200
        assert (await client.get("/opportunities", headers={"x-client-key": "d"})).status_code == 429


async def test_unhandled_error_has_no_stack_trace(app_factory, client_for):
    app = app_factory()

    @app.get("/api/v1/boom")
    async def boom():
        raise RuntimeError("secret internal detail")

    async for client in client_for(app):
        response = await client.get("/boom")
        assert response.status_code == 500
        assert "secret internal detail" not in response.text
        assert "Traceback" not in response.text
        # Handled inside RequestMiddleware, so it is traceable and keeps the headers.
        assert response.json()["request_id"] == response.headers["x-request-id"]
        assert response.headers["x-content-type-options"] == "nosniff"


async def test_database_down_returns_503(client_for):
    from app.main import create_app
    from tests.api.conftest import make_settings

    url = "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/none"
    app = create_app(make_settings(url, db_timeout_seconds=1))
    async for client in client_for(app):
        assert (await client.get("/opportunities")).status_code == 503
        assert (await client.get("/health/ready")).status_code == 503


async def test_security_headers(client):
    response = await client.get("/opportunities")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "x-request-id" in response.headers


async def test_cors_allows_only_the_web_origin(client):
    other = await client.get("/opportunities", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in other.headers
    mine = await client.get("/opportunities", headers={"Origin": "http://localhost:3000"})
    assert mine.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_logs_contain_no_profile_data(client, caplog):
    caplog.set_level(logging.INFO, logger="app.access")
    created = await _create(client, {**SAMPLE_PROFILE, "field_of_study": "Unique Marker Studies"})
    await client.get(f"/profiles/{created['id']}")
    text = " ".join(f"{r.getMessage()} {r.__dict__}" for r in caplog.records)
    assert "Unique Marker Studies" not in text
    assert created["id"] not in text
    assert "/profiles/{profile_id}" in text


async def test_matches_are_paginated_with_stable_global_rank(client):
    profile_id = (await _create(client))["id"]
    total = len(load_seed())
    url = f"/profiles/{profile_id}/matches"

    first = (await client.get(url)).json()
    assert (first["page"], first["page_size"], first["total"]) == (1, 10, total)
    assert first["total_pages"] == -(-total // 10)
    assert [m["rank"] for m in first["items"]] == list(range(1, 11))

    second = (await client.get(url, params={"page": 2})).json()
    # Rank continues from page 1 instead of restarting at 1.
    assert [m["rank"] for m in second["items"]] == list(range(11, total + 1))

    everything = (await client.get(url, params={"page_size": 50})).json()["items"]
    assert first["items"] + second["items"] == everything


async def test_page_past_the_end_is_empty_not_an_error(client):
    profile_id = (await _create(client))["id"]
    response = await client.get(f"/profiles/{profile_id}/matches", params={"page": 99})
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == len(load_seed())


async def test_filter_applies_before_paging_and_counts_cover_everything(client):
    profile_id = (await _create(client))["id"]
    url = f"/profiles/{profile_id}/matches"
    everything = (await client.get(url, params={"page_size": 50})).json()

    blocked = (await client.get(url, params={"filter": "blocked", "page_size": 2})).json()
    expected = [m for m in everything["items"] if m["eligibility"] == "blocked"]
    assert blocked["total"] == len(expected) == blocked["counts"]["blocked"]
    assert blocked["items"] == expected[:2]
    # Counts describe the whole ranking, whatever the filter or page.
    assert blocked["counts"] == everything["counts"]
    assert everything["counts"]["all"] == len(load_seed())


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"page": 0}, "page"),
        ({"page_size": 0}, "page_size"),
        ({"page_size": 51}, "page_size"),
        ({"filter": "nope"}, "filter"),
    ],
)
async def test_invalid_paging_params_are_422(client, params, field):
    profile_id = (await _create(client))["id"]
    response = await client.get(f"/profiles/{profile_id}/matches", params=params)
    assert response.status_code == 422
    assert field in {e["field"] for e in response.json()["errors"]}
