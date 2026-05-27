# Edge Cases & Exception Handling Guide

This document catalogs edge cases across the restaurant recommendation system. Each entry defines the **scenario**, **expected behavior**, **implementation owner** (layer), and **test priority**.

Use this alongside [`architecture.md`](./architecture.md), [`context.md`](./context.md), and [`implementation-plan.md`](./implementation-plan.md).

---

## Legend

| Priority | Meaning |
|----------|---------|
| **P0** | Must handle in MVP; incorrect behavior breaks core flow |
| **P1** | Should handle in MVP; degraded UX or cost risk if ignored |
| **P2** | Nice-to-have; document and defer or handle with generic fallback |

| Owner | Layer |
|-------|-------|
| ING | Data ingestion |
| REPO | Restaurant repository |
| VAL | Input validation |
| FIL | Filter service |
| PRM | Prompt builder |
| LLM | LLM client |
| PAR | Response parser |
| MRG | Recommendation merger |
| ORCH | Orchestrator |
| API | Application / REST API |
| UI | Presentation layer |
| CFG | Configuration / startup |

---

## Table of Contents

1. [User Input & Validation](#1-user-input--validation)
2. [Data Ingestion](#2-data-ingestion)
3. [Restaurant Repository & Store](#3-restaurant-repository--store)
4. [Filter Service](#4-filter-service)
5. [Prompt Builder](#5-prompt-builder)
6. [LLM Client](#6-llm-client)
7. [Response Parser & Merger](#7-response-parser--merger)
8. [Orchestrator](#8-orchestrator)
9. [API Layer](#9-api-layer)
10. [Presentation Layer (UI)](#10-presentation-layer-ui)
11. [Configuration & Startup](#11-configuration--startup)
12. [Security & Abuse](#12-security--abuse)
13. [Performance & Concurrency](#13-performance--concurrency)
14. [Cross-Cutting Fallback Matrix](#14-cross-cutting-fallback-matrix)
15. [Test Checklist](#15-test-checklist)

---

## 1. User Input & Validation

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| UI-001 | Empty `location` | Reject before filter/LLM; validation error: "Location is required" | VAL | P0 |
| UI-002 | Empty `cuisine` | Reject; validation error: "Cuisine is required" | VAL | P0 |
| UI-003 | Whitespace-only location/cuisine (`"   "`) | Treat as empty after trim; reject | VAL | P0 |
| UI-004 | `min_rating` below 0 or above 5 | Reject with range error | VAL | P0 |
| UI-005 | `min_rating` not a number (UI string) | Reject or coerce with validation error | VAL | P0 |
| UI-006 | Invalid `budget` value (not low/medium/high) | Reject with enum error | VAL | P0 |
| UI-007 | Missing optional `additional_preferences` | Proceed; pass `null`/empty to LLM | VAL | P0 |
| UI-008 | Empty `additional_preferences` | Proceed; omit from prompt or pass empty | VAL | P0 |
| UI-009 | Very long `additional_preferences` (>2000 chars) | Truncate with ellipsis before prompt; log warning | VAL, PRM | P1 |
| UI-010 | Special characters in preferences (`<script>`, emojis, newlines) | Sanitize/escape for prompt; never execute as HTML in UI | VAL, UI | P0 |
| UI-011 | `top_k` = 0 or negative | Reject or default to 5 | VAL | P1 |
| UI-012 | `top_k` very large (e.g., 100) | Cap at `MAX_TOP_K` (e.g., 10) | VAL | P1 |
| UI-013 | Location with alternate spelling ("Bengaluru" vs "Bangalore") | May not match; return empty or partial (see FIL-006); future: alias map | FIL | P1 |
| UI-014 | Cuisine substring vs exact ("Ital" vs "Italian") | Substring/any-match on cuisine list per design | FIL | P1 |
| UI-015 | User selects cuisine not in dataset | Zero candidates after filter; empty state (no LLM) | FIL, ORCH | P0 |
| UI-016 | `min_rating` = 5.0 | Only perfect-rated restaurants; may be empty | FIL | P0 |
| UI-017 | `min_rating` = 0 | No rating filter effect (all ratings pass) | FIL | P1 |
| UI-018 | Conflicting preferences ("vegan" + cuisine "Steakhouse") | Filter still runs; LLM explains poor fit or ranks best available | LLM | P1 |
| UI-019 | Duplicate form submission (double-click) | Debounce submit; ignore in-flight duplicate or idempotent response | UI, API | P1 |
| UI-020 | Non-English preferences | Accept; LLM handles multilingual explanations if model supports | PRM, LLM | P2 |

---

## 2. Data Ingestion

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| ING-001 | Hugging Face download fails (network) | Fail ingest with clear error; do not write partial file | ING | P0 |
| ING-002 | Dataset schema changed (unknown columns) | Fail or skip unmapped columns with warning; document required mapping | ING | P0 |
| ING-003 | Missing `rating` column or all null ratings | Drop rows or set rating=null and exclude from min_rating filter | ING | P0 |
| ING-004 | Missing cost/price field | Drop row or assign `budget_band=unknown` and exclude from budget filter | ING | P0 |
| ING-005 | Rating out of range (e.g., 6.0, -1) | Clamp to [0,5] or drop row; log count | ING | P1 |
| ING-006 | Cost = 0 or negative | Treat as invalid; drop or map to low with flag in metadata | ING | P1 |
| ING-007 | Duplicate (name, location) rows | Dedupe keeping highest rating or first; stable `id` generation | ING | P1 |
| ING-008 | Empty restaurant name | Drop row | ING | P0 |
| ING-009 | Cuisine as comma-separated string | Split, trim, lowercase → `cuisines: list[str]` | ING | P0 |
| ING-010 | Cuisine as single value / list / null | Normalize all variants | ING | P0 |
| ING-011 | Location inconsistent casing ("delhi" vs "Delhi") | Normalize to canonical display form; filter uses case-insensitive match | ING, FIL | P0 |
| ING-012 | Multiple cities in one location field | Keep as-is; substring filter may still match | ING, FIL | P1 |
| ING-013 | Extremely long name/address | Truncate for storage; full text optional in metadata | ING | P2 |
| ING-014 | Special characters in names | Preserve UTF-8; no stripping of legitimate names | ING | P1 |
| ING-015 | Re-run ingest on existing processed file | Overwrite atomically (write temp → rename) | ING | P0 |
| ING-016 | Partial write interrupted | Detect corrupt file on load; require re-ingest | ING, REPO | P1 |
| ING-017 | Empty dataset after cleaning | Fail ingest; app must not start with zero restaurants | ING, CFG | P0 |
| ING-018 | Budget band boundary (cost exactly 500) | Consistent rule: e.g., `low` if cost ≤ 500 | ING | P1 |
| ING-019 | All restaurants in one city | Valid; filter by other cities returns empty | ING | P0 |
| ING-020 | HF dataset version drift | Pin dataset revision in config; log revision on ingest | ING, CFG | P2 |

---

## 3. Restaurant Repository & Store

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| REPO-001 | Processed file missing at startup | Fail fast: "Run ingest first" with exit code / 503 on API | REPO, CFG | P0 |
| REPO-002 | Corrupt Parquet / unreadable file | Log error; fail startup; do not serve partial data | REPO | P0 |
| REPO-003 | Empty in-memory store after load | Fail startup | REPO, CFG | P0 |
| REPO-004 | `get_by_ids` with unknown id | Omit from result; log warning | REPO, MRG | P0 |
| REPO-005 | `get_by_ids` with empty list | Return `[]` | REPO | P1 |
| REPO-006 | Duplicate ids in dataset | Last-wins or dedupe at ingest; repository returns one per id | ING, REPO | P1 |
| REPO-007 | Very large dataset (100k+ rows) | Load once at startup; consider lazy load later (P2) | REPO | P2 |
| REPO-008 | Hot reload of data without restart | Not supported in MVP; require restart after re-ingest | REPO | P2 |

---

## 4. Filter Service

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| FIL-001 | **Zero matches** after all hard filters | Return `candidates=[]`; **do not call LLM** | FIL, ORCH | P0 |
| FIL-002 | **Too many matches** (> MAX_CANDIDATES) | Sort by rating desc; cap to MAX_CANDIDATES | FIL | P0 |
| FIL-003 | Exactly MAX_CANDIDATES matches | Pass all to LLM | FIL | P0 |
| FIL-004 | Single match | Pass 1 candidate; LLM returns rank=1 or fallback works | FIL, LLM | P0 |
| FIL-005 | Location substring false positive ("Del" matches "Model Town, Delhi") | Acceptable for MVP; document behavior | FIL | P2 |
| FIL-006 | Location no match ("Noida" not in data) | Empty candidates; user message: try another city | FIL, UI | P0 |
| FIL-007 | Budget filter eliminates all (medium budget but only low/high in city) | Empty candidates | FIL | P0 |
| FIL-008 | Cuisine case mismatch ("italian" vs "Italian") | Case-insensitive any-match on cuisines | FIL | P0 |
| FIL-009 | Multi-cuisine restaurant ("Italian, Chinese") | Matches if user cuisine in list | FIL | P0 |
| FIL-010 | `min_rating` excludes all in otherwise valid set | Empty candidates | FIL | P0 |
| FIL-011 | Tie ratings on sort | Secondary sort by votes/name for stability | FIL | P1 |
| FIL-012 | `additional_preferences` contains "near airport" | **Not** structurally filtered; passed to LLM only | FIL | P0 |
| FIL-013 | User budget "low" but all low-band have rating < min_rating | Empty after combined filters | FIL | P0 |
| FIL-014 | Relax-one-filter strategy (future) | Not in MVP; return empty with suggestion text | FIL, UI | P2 |
| FIL-015 | Filter with `top_k` > candidate count | LLM asked for top_k; merger returns min(top_k, len) | FIL, MRG | P1 |

---

## 5. Prompt Builder

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| PRM-001 | Zero candidates passed to builder | Orchestrator must not call builder (guard in ORCH) | ORCH | P0 |
| PRM-002 | One candidate | Prompt asks for top 1; valid JSON with single item | PRM | P0 |
| PRM-003 | Candidate list at token limit | Reduce fields per restaurant; never drop ids | PRM | P1 |
| PRM-004 | Missing optional metadata on restaurants | Omit from prompt; core fields required | PRM | P1 |
| PRM-005 | `top_k` > len(candidates) | Instruct "recommend up to N from list" where N = len(candidates) | PRM | P1 |
| PRM-006 | Prompt injection in user fields ("ignore previous instructions") | System prompt: only use provided list; sanitize user block | PRM | P0 |
| PRM-007 | Unicode / emoji in restaurant names | Include as UTF-8 in JSON block | PRM | P1 |
| PRM-008 | Very large candidate JSON | Enforce MAX_CANDIDATES at filter stage first | FIL, PRM | P0 |

---

## 6. LLM Client

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| LLM-001 | Missing `LLM_API_KEY` (hosted provider) | Fail at startup or first call with config error | CFG, LLM | P0 |
| LLM-002 | Invalid API key | 401 from provider; surface "check API key"; no crash | LLM, UI | P0 |
| LLM-003 | Request timeout | Retry once with backoff; then fallback ranking | LLM, ORCH | P0 |
| LLM-004 | Rate limit (429) | Retry after delay once; then fallback or cached response | LLM | P1 |
| LLM-005 | Provider 5xx | Retry once; then fallback | LLM | P0 |
| LLM-006 | Empty model response | Treat as parse failure → fallback | LLM, PAR | P0 |
| LLM-007 | Ollama not running (local dev) | Clear error: start Ollama or switch provider | LLM, CFG | P1 |
| LLM-008 | Model returns markdown-wrapped JSON | Parser strips fences (```json) | PAR | P0 |
| LLM-009 | Model invents restaurant not in list | Merger drops unknown ids; log warning | MRG, PAR | P0 |
| LLM-010 | Model returns fewer than top_k | Return what was parsed; pad with rating fallback if needed | MRG, ORCH | P1 |
| LLM-011 | Model returns duplicate ranks or ids | Dedupe by id; re-rank by first occurrence or rating | PAR, MRG | P1 |
| LLM-012 | Token limit exceeded on request | Reduce candidates or truncate prompt; retry once | PRM, LLM | P1 |
| LLM-013 | Extremely slow response (>60s) | UI timeout message; optional cancel (P2) | UI, LLM | P2 |
| LLM-014 | Concurrent requests (multiple users) | Stateless; each request independent; watch rate limits | LLM | P2 |

---

## 7. Response Parser & Merger

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| PAR-001 | Valid JSON matching schema | Parse; merge; return recommendations | PAR, MRG | P0 |
| PAR-002 | JSON with extra unknown fields | Ignore extras | PAR | P1 |
| PAR-003 | Missing `summary` | `summary=null`; UI hides summary block | PAR, UI | P0 |
| PAR-004 | Missing `explanation` on one item | Use generic: "Matches your preferences based on rating and cuisine." | MRG | P1 |
| PAR-005 | Invalid JSON (prose only) | Regex extract `{...}`; if fail → full fallback | PAR | P0 |
| PAR-006 | Partial JSON (truncated) | Fallback | PAR | P0 |
| PAR-007 | `restaurant_id` not in candidate set | Drop entry; log warning | MRG | P0 |
| PAR-008 | Duplicate `restaurant_id` in response | Keep first rank; drop duplicates | MRG | P1 |
| PAR-009 | Non-integer or duplicate `rank` | Re-number 1..n by sort order in array or by rank field | MRG | P1 |
| PAR-010 | Empty `recommendations` array | Fallback to rating-based top-K | PAR, ORCH | P0 |
| PAR-011 | `rank` gaps (1, 3, 5) | Renumber contiguously for display | MRG, UI | P2 |
| MRG-001 | **Full fallback**: parse fails completely | Top-K by rating from filtered list; generic explanation each | ORCH | P0 |
| MRG-002 | **Partial fallback**: some ids invalid | Return valid merges + fill remainder from rating order | MRG | P1 |
| MRG-003 | LLM returns more than top_k | Truncate to top_k by rank | MRG | P0 |

---

## 8. Orchestrator

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| ORCH-001 | Happy path | validate → filter → prompt → LLM → parse → merge → response | ORCH | P0 |
| ORCH-002 | Empty filter result | Return `{ recommendations: [], summary: null, meta: { candidates_considered: 0 } }`; **no LLM** | ORCH | P0 |
| ORCH-003 | LLM fails after retry | Fallback recommendations + `meta.llm_fallback: true` | ORCH | P0 |
| ORCH-004 | Validation fails before filter | Propagate validation error; no LLM | ORCH, VAL | P0 |
| ORCH-005 | Exception in filter | Log; return 500 with safe message | ORCH, API | P0 |
| ORCH-006 | Exception in merge | Log; attempt full fallback; never return 500 with empty if candidates exist | ORCH | P0 |
| ORCH-007 | `meta` always populated | `candidates_considered`, `filters_applied`, `llm_used`, `fallback_used` | ORCH | P1 |
| ORCH-008 | Idempotent same preferences | Same result (deterministic filter); LLM may vary unless temperature=0 | ORCH | P2 |
| ORCH-009 | Cache hit (optional) | Return cached response; skip LLM | ORCH | P2 |

---

## 9. API Layer

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| API-001 | Malformed JSON body | 400 with validation detail | API | P0 |
| API-002 | Missing required fields | 400 field-level errors | API | P0 |
| API-003 | Wrong Content-Type | 415 or 400 | API | P1 |
| API-004 | GET on POST-only endpoint | 405 | API | P2 |
| API-005 | Store not loaded | 503 "Service unavailable" | API, CFG | P0 |
| API-006 | LLM upstream failure after fallback | 200 with fallback results + warning header (preferred) OR 502 if no candidates | API | P1 |
| API-007 | Request body too large | 413 | API | P1 |
| API-008 | Health check | 200 when repo loaded; 503 otherwise | API | P1 |
| API-009 | Metadata `/locations` empty dataset | 200 with `[]` | API | P1 |
| API-010 | CORS preflight (React) | Allow configured origin | API | P1 |

---

## 10. Presentation Layer (UI)

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| UI-101 | First load before data ingested | Banner: run ingest; disable submit | UI, CFG | P0 |
| UI-102 | Submit with invalid form | Inline field errors; no API call | UI | P0 |
| UI-103 | Loading during LLM (2–15s) | Spinner/skeleton; disable submit | UI | P0 |
| UI-104 | Zero results | Empty state: "No restaurants match. Try relaxing location, cuisine, or rating." | UI | P0 |
| UI-105 | Results with fallback | Show results + subtle notice: "AI ranking unavailable; showing top rated matches." | UI | P1 |
| UI-106 | Partial fields null (no cost in data) | Display "N/A" or hide cost row | UI | P1 |
| UI-107 | Very long explanation text | Wrap text; max-height with expand | UI | P2 |
| UI-108 | Summary present | Render above cards | UI | P0 |
| UI-109 | Network error (FastAPI path) | Retry button + error message | UI | P1 |
| UI-110 | Browser refresh mid-request | Request may complete or fail; user can resubmit | UI | P2 |
| UI-111 | Streamlit session rerun | Preserve or reset form per product choice; document behavior | UI | P2 |

---

## 11. Configuration & Startup

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| CFG-001 | Missing `.env` | Use defaults where safe; fail if API key required | CFG | P0 |
| CFG-002 | Invalid `MAX_CANDIDATES` (non-int) | Fail startup with config error | CFG | P1 |
| CFG-003 | `MAX_CANDIDATES` = 0 | Fail startup or coerce to minimum 1 | CFG | P1 |
| CFG-004 | Budget thresholds misordered (low > medium) | Fail startup validation | CFG | P1 |
| CFG-005 | Wrong `DATA_PATH` | Fail startup with file not found | CFG | P0 |
| CFG-006 | `LLM_PROVIDER` unknown | Fail startup | CFG | P0 |
| CFG-007 | Development without LLM (dry run flag) | Optional: filter-only mode returns rating sort, no API call | CFG, ORCH | P2 |

---

## 12. Security & Abuse

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| SEC-001 | Prompt injection via `additional_preferences` | Hardened system prompt; no tool execution | PRM | P0 |
| SEC-002 | XSS in LLM explanation output | Escape HTML when rendering in web UI | UI | P0 |
| SEC-003 | Oversized request payload | Reject at API/gateway; max length on text fields | API, VAL | P1 |
| SEC-004 | Secrets in logs | Never log API keys; redact prompts in prod | CFG | P0 |
| SEC-005 | SQL injection | N/A for in-memory filter; use parameterized queries if SQLite added | REPO | P0 |
| SEC-006 | High-frequency automated requests | Rate limit (future); MVP: document only | API | P2 |

---

## 13. Performance & Concurrency

| ID | Scenario | Expected behavior | Owner | Priority |
|----|----------|-------------------|-------|----------|
| PERF-001 | Cold start with large Parquet | Acceptable delay once; log load time | REPO | P1 |
| PERF-002 | Filter on 50k rows in memory | Complete <100ms for MVP | FIL | P1 |
| PERF-003 | Repeated identical queries | Optional cache to save LLM cost | ORCH | P2 |
| PERF-004 | Two simultaneous UI submits | Both complete or second waits; no shared mutable state | ORCH | P1 |

---

## 14. Cross-Cutting Fallback Matrix

Decision tree for recommendation outcomes:

```text
                    ┌─────────────────┐
                    │ User submits    │
                    │ preferences     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Valid input?    │
                    └───┬─────────┬───┘
                     no │         │ yes
                        ▼         ▼
                   400 error   ┌──────────────┐
                               │ Filter       │
                               └───┬──────┬───┘
                            empty │      │ candidates > 0
                                  ▼      ▼
                          Empty UI   ┌─────────┐
                          no LLM     │ LLM call│
                                     └───┬──┬──┘
                                  fail  │  │ success
                                        ▼  ▼
                              Fallback   Parse
                              top-K      JSON
                              by rating     │
                                        ┌───┴───┐
                                   fail │       │ ok
                                        ▼       ▼
                                   Fallback   Merge
                                   top-K      + display
```

| Outcome | HTTP (API) | UI message | `meta.fallback_used` |
|---------|------------|------------|----------------------|
| Validation error | 400 | Field errors | — |
| No candidates | 200, `recommendations: []` | Empty state | false |
| LLM success | 200 | Cards + summary | false |
| LLM fail, fallback | 200 (preferred) | Cards + warning banner | true |
| Store missing | 503 | Cannot load data | — |

---

## 15. Test Checklist

Map edge cases to automated or manual tests.

### Unit tests (required for MVP)

- [ ] VAL: UI-001, UI-002, UI-004, UI-006
- [ ] ING: ING-009, ING-011, ING-007 (fixtures)
- [ ] FIL: FIL-001, FIL-002, FIL-004, FIL-008, FIL-010
- [ ] PAR: PAR-001, PAR-005, PAR-007, PAR-010
- [ ] MRG: MRG-001, MRG-003

### Integration tests

- [ ] ORCH-002 (empty filter, no LLM mock called)
- [ ] ORCH-003 (mock LLM raises → fallback results)
- [ ] ORCH-001 (mock LLM returns valid JSON → merged response)

### Manual QA scenarios

| # | Input | Expected |
|---|-------|----------|
| M1 | Valid Bangalore, Italian, medium, 4.0 | ≥1 recommendation with explanation |
| M2 | Valid prefs, impossible combo | Empty state, no LLM charge |
| M3 | Empty location | Validation error |
| M4 | `min_rating` = 5 | Few or zero results |
| M5 | Disconnect LLM / invalid key | Fallback or clear error |
| M6 | `additional_preferences`: "family-friendly" | Explanations mention family-friendly |
| M7 | Very long additional text | Truncated; still returns results |
| M8 | `top_k` = 3 | At most 3 cards |

---

## Implementation Notes by Layer

### Filter before generate (non-negotiable)

- **FIL-001**, **ORCH-002**: Never invoke LLM when `len(candidates) == 0`.
- Saves cost and prevents hallucinated restaurants when there is no ground truth set.

### Grounding (non-negotiable)

- **LLM-009**, **PAR-007**: Output restaurants must ⊆ filtered candidates.
- Merger is the last line of defense; log all dropped ids.

### Degrade gracefully

- **LLM-003–005**, **PAR-005**, **MRG-001**: User always gets *something* when candidates exist, even if generic.

### User trust

- **UI-104**, **UI-105**: Clear empty and fallback messaging; never show blank screen after submit.

---

## Future Edge Cases (Post-MVP)

| ID | Scenario | Direction |
|----|----------|-----------|
| FUT-001 | Ambiguous location ("Springfield") | Disambiguation UI + metadata endpoint |
| FUT-002 | "Relax filters" suggestion | Drop lowest-priority filter until candidates > 0 |
| FUT-003 | Semantic match on `additional_preferences` | Embedding pre-filter before LLM |
| FUT-004 | Multi-turn ("cheaper please") | Session state + follow-up orchestrator |
| FUT-005 | Stale dataset | Version banner + re-ingest job |

---

## References

- [`docs/architecture.md`](./architecture.md) — component edge cases and failure handling
- [`docs/context.md`](./context.md) — success criteria
- [`docs/implementation-plan.md`](./implementation-plan.md) — phase tasks and QA
