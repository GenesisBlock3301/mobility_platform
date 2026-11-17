# AI and tool disclosure

## AI tools

| Tool | Used for | My review |
|---|---|---|
| Claude Code (Anthropic) | Reading the brief, drafting `PLAN.md`, choosing the stack and checking current package versions, the OWASP Top 10:2025 mapping | Read the brief and the plan; went through the data model and how profile, opportunities, matches and shortlist relate, so I can explain them myself |
| Claude Code, Design canvas | The clickable prototype of the six screens (screenshots in `docs/design/`) | Used as the visual reference for the pages |
| Claude Code | Generating the backend: matching engine, API, migrations, seed data, Docker setup | Recalculated the Programme Assistant score (91) by hand from `criteria.py`; asked for pagination on matches and reviewed its logic and tests |
| Claude Code | Generating the frontend: pages, components, Server Actions, CSP proxy | Tested every screen manually; changed the profile form to mark required and optional fields, and removed explanatory text I found unnecessary |
| Claude Code | Writing the tests, then running them and fixing failures | Ran the full suite myself: 85 passed, 0 failed |
| Claude Code with Claude in Chrome | Driving the browser through the user journey and taking the evidence screenshots | Walked through the same journey manually in my own browser |
| Claude Code | Drafting the README, technical note and test evidence | Directed the changes: a plain-language README with one-step start scripts for non-technical reviewers, run files moved to `deployment/`, a settings guide, and the technical note restructured to the brief's sections and cut to 2 pages |

## Libraries and services

| Library | Version | Purpose |
|---|---|---|
| Next.js, React | 16.4.6, 19.3.1 | Web framework and UI |
| TypeScript | 6.0.3 | Type checking |
| Tailwind CSS | 4.3.5 | Styling |
| Zod | 4.6.7 | Form validation |
| ESLint, eslint-config-next | 10.15.0, 16.4.6 | Linting |
| FastAPI, Uvicorn | 0.163.1, 0.54.0 | API framework and server |
| Pydantic, pydantic-settings | 2.14.3, 2.16.3 | Validation and configuration |
| SQLAlchemy, asyncpg, Alembic | 2.1.8, 0.32.0, 1.20.1 | Database access and migrations |
| pytest, pytest-asyncio, httpx | 9.2.0, 1.5.0, 0.28.1 | Tests |
| Ruff, pip-audit | 0.17.5, 2.10.1 | Lint and vulnerability scanning |
| Google Fonts via `next/font` | | Inter, Space Grotesk and JetBrains Mono, self-hosted at build time |

**External APIs:** none. The matching is rule-based and runs offline. All data is fictional.

## What I changed or verified by hand

Most of the code was generated with Claude Code. I directed the work, reviewed it, and made the changes below myself or asked for them as product decisions.

### Verified by hand

- **Scores checked manually.** I recalculated the score for the Programme Assistant role (International NGO, Berlin) from the weights in `backend/app/matching/criteria.py` (skills 35, experience 20, education 15, language 15, location 10, career interests 5): skills 28 (all 3 required skills, but not the preferred "budget tracking"), experience 20, education 15, language 15, location 10, career interests 3.3 (2 of 3). That is 91.3, which rounds to 91/100, the same score the app shows.
- **Full user journey, tested manually.** I went through it myself in the browser: load the sample profile → ranked matches → detail view → save to shortlist → edit the profile and check that the ranking updates.
- **Tests.** I ran the backend test suite myself through Docker (`docker compose --profile test run --build --rm api-test` in `deployment/`): 85 passed, 0 failed.

### Changed or added

- **Profile form: required and optional fields.** The form now marks education, years of experience, skills and languages as required (red asterisk, announced as "required" to screen readers), and every other field as optional, and I removed explanatory text that the markers made unnecessary. This makes it clear that matching needs a minimum profile, while still not forcing users to state things like their work authorisation. (`frontend/components/FieldMarker.tsx`, `ProfileForm.tsx`, `TagInput.tsx`)
- **Pagination on matches.** I asked for pagination on `GET /profiles/{id}/matches` (`page`, `page_size`, `filter`). Claude Code implemented it and I reviewed the design: filtering happens in the API before paging, so a filtered page is never half empty; summary counts still cover all roles; and `rank` stays the position in the full ranking instead of restarting on each page. I checked the logic in `backend/app/services/mobility.py` and the new API tests, and the trade-off is recorded in the technical note.
- **Setup for non-technical reviewers.** I moved the run files into `deployment/` and asked for one-step start and stop scripts and a plain-language README, so someone without development experience can run the app.

### What I am less sure about

- The skill synonym map is small, so some differently worded skills may not match.
- The Windows start script has not been tested on a Windows machine.
