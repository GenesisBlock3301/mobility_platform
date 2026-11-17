# Test evidence

Recorded on 2026-11-17 against the Docker Compose stack, after a clean rebuild with `docker compose down -v`.

## Automated tests

```sh
cd deployment
docker compose --profile test run --build --rm api-test
```

```
........................................................................ [100%]
85 passed in 2.92s
```

| Suite | Tests | What it covers |
|---|---|---|
| `tests/matching/` | 41 | Required cases, expected ranking for all 12 roles, edge cases, layering rule |
| `tests/api/` | 40 | CRUD, match pagination and filtering (page 2 continues the rank, a page past the end is empty, filter before paging, invalid parameters are 422), validation, 404 resource, 413 (including chunked bodies), 429, 500 and 503 behaviour, rate-limit key trust, shortlist idempotency, CORS, security headers, logs free of profile data |
| `tests/test_seed.py`, `tests/test_rate_limit.py` | 4 | Seed validity; a bad record stops the seed; the limiter's per-client counting and memory cap |

Frontend: `npm run typecheck` and `npm run lint` pass with no errors.

## The three required cases

All three use the sample profile from the brief: a Bachelor's in Business Administration, 2 years of experience, Bengali (native) and English (professional), preferring Germany, Canada and Singapore, with work authorisation unknown. They live in `tests/matching/test_required_cases.py`.

| Case | Role | Score | Band | Eligibility | What the test asserts |
|---|---|---|---|---|---|
| Strong match | Programme Assistant, International NGO (Berlin) | 91 | Strong | Requires verification | 3 of 3 required skills matched; only gap is preferred "budget tracking"; right to work is "verify", not "met" |
| Partial match | Operations Analyst, fintech (Amsterdam) | 73 | Partial | Requires verification | SQL listed as missing; location earns 0 (Netherlands not preferred) |
| Critical requirement gap | German-speaking Client Associate (Munich) | 57 | Partial | **Blocked** | Exactly one blocking check, naming German; score still calculated; explanation says "Blocked:" |

The what-if for the blocked role: adding German at professional level raises the score from 57 to 72 and removes the block.

## Full ranking for the sample profile

| Rank | Role | Score | Band | Eligibility |
|---|---|---|---|---|
| 1 | Business Operations Associate, Singapore | 98 | Strong | Requires verification |
| 2 | Graduate Trainee, Singapore | 91 | Strong | Requires verification (no sponsorship: likely barrier) |
| 3 | Programme Assistant, Berlin | 91 | Strong | Requires verification |
| 4 | Project Coordinator, Toronto | 91 | Strong | Requires verification |
| 5 | Operations Analyst, Amsterdam | 73 | Partial | Requires verification |
| 6 | Research Assistant, Singapore | 72 | Partial | Requires verification |
| 7 | Business Analyst Intern, Vancouver | 69 | Partial | Requires verification (enrolment and right to work) |
| 8 | Junior Project Manager, remote UK | 57 | Partial | No known blockers |
| 9 | Software Engineer, Berlin | 47 | Poor | Requires verification |
| 10 | German-speaking Client Associate, Munich | 57 | Partial | Blocked (German) |
| 11 | Marketing Coordinator, Montréal | 53 | Partial | Blocked (French) |
| 12 | Senior Programme Manager, Geneva | 17 | Poor | Blocked (French, English level) |

Ranks 2 to 4 tie at 91 and are ordered by slug, as the ranking rule says.

## Manual checks

| Check | Result |
|---|---|
| The database's app role tries `DROP TABLE` | `ERROR: must be owner of table shortlist_entries` |
| The database's app role tries `DELETE FROM opportunities` | `ERROR: permission denied for table opportunities` |
| Response headers on the web app | CSP with a per-request nonce, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` |
| Browser console during the journey | No errors and no CSP violations |
| `npm audit --audit-level=high` | 0 vulnerabilities |
| `pip-audit` (backend environment) | No known vulnerabilities |

## Mobile responsiveness

Every page was rendered in headless Chrome with phone emulation (touch, 2× pixel density) at 320, 360, 390, 414, 768 and 1024 px wide. A script checked that the page never scrolls sideways and that no element extends past the screen edge. All seven pages pass at every width.

| Check | Result |
|---|---|
| Horizontal overflow, 320 to 1024 px | None on any page |
| Tap targets | Buttons and form controls are at least 40 px. Chip remove buttons are 32 px, above the 24 px WCAG 2.2 minimum |
| Profile form on a phone | The strength summary shows first; a bar fixed to the bottom keeps "See my matches" in reach, clear of the iPhone home indicator |
| Score breakdown on a phone | Label and points on one line, a full-width bar below, then the note |

Phone screenshots at 390 px: [overview](evidence/mobile-overview.jpg), [welcome](evidence/m1-welcome.jpg), [profile](evidence/m2-profile.jpg), [matches](evidence/m3-matches.jpg), [blocked role](evidence/m4-detail-blocked.jpg), [shortlist](evidence/m5-shortlist.jpg).

## User journey in the browser

I verified the journey in Chrome against the running stack. Screenshots are in [`docs/evidence/`](evidence/).

1. **Welcome page:** [01](evidence/01-welcome.jpg).
2. **Profile form loaded with the sample profile:** [02](evidence/02-profile-sample.jpg).
3. **Invalid input:** years of experience set to -1. The form shows an inline error, keeps every value and moves focus to the field ([03](evidence/03-validation-error.jpg)).
4. **Save:** after correcting the value, saving redirects to 12 ranked matches with summary tiles and the "verify" banner ([04](evidence/04-matches.jpg)).
5. **Shortlist:** saving Programme Assistant updates the button and the header count straight away.
6. **Detail view:** the explanation, a breakdown that adds up to 91, eligibility checks, the checklist and the what-if (91 → 98) ([05](evidence/05-detail-strong.jpg), [06](evidence/06-detail-breakdown.jpg)).
7. **Blocked roles:** the Blocked filter, then the blocked German-speaking role with its reason ([07](evidence/07-blocked-filter.jpg), [08](evidence/08-detail-blocked.jpg)).
8. **Shortlist page:** the saved role persists. Ticking both checks shows "Ready to apply", which survives a reload ([09](evidence/09-shortlist-ready.jpg)).
9. **Database stopped:** the page shows "The service is temporarily unavailable. Nothing you entered was lost." with a retry button ([10](evidence/10-database-down.jpg)).
