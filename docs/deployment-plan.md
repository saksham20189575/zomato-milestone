# Streamlit Deployment Plan

Deploy **TasteTrail AI** (the Streamlit UI in `src/app/main.py`) to [Streamlit Community Cloud](https://streamlit.io/cloud) or a self-hosted Streamlit server. This plan covers repository prep, secrets, data files, and verification.

**Related docs**: [`architecture.md`](./architecture.md#deployment-topology), [`implementation-plan.md`](./implementation-plan.md) (Phase 7 — ship).

---

## Overview

| Item | Value |
|------|--------|
| **App entry** | `src/app/main.py` |
| **Runtime** | Python 3.11+ |
| **Dependencies** | Root `requirements.txt` → `requirements-streamlit.txt` (Cloud default) |
| **Alt. entry** | `streamlit_app.py` at repo root (optional; same as `src/app/main.py`) |
| **LLM** | Groq (`LLM_API_KEY` / `GROQ_API_KEY`) |
| **Data** | `data/processed/restaurants.parquet` (~3.6 MB after ingest) |
| **Import path** | Handled in `main.py` (`sys.path` inserts `src/`); no `PYTHONPATH` required on Cloud |

The Streamlit app calls the orchestrator in-process (no FastAPI/Next.js required for this deployment path).

---

## Prerequisites

Before deploying:

1. **Groq API key** — [Groq Console](https://console.groq.com) → create key with chat/completions access.
2. **Processed dataset** — Run locally once:
   ```bash
   python scripts/ingest.py
   ```
   Output: `data/processed/restaurants.parquet`.
3. **Git remote** — Streamlit Community Cloud deploys from GitHub (or GitLab; see Streamlit docs for supported hosts).
4. **Passing smoke test** (recommended):
   ```bash
   PYTHONPATH=src streamlit run src/app/main.py
   ```
   Submit a recommendation and confirm results render.

---

## Pre-deployment checklist

| # | Task | Status |
|---|------|--------|
| 1 | `requirements.txt` / `requirements-streamlit.txt` at repo root (runtime deps only) | |
| 2 | `restaurants.parquet` available in the deployed environment (see [Data on Cloud](#data-on-cloud)) | |
| 3 | Groq secrets configured in Streamlit Cloud (not committed to git) | |
| 4 | Main file path set to `src/app/main.py` | |
| 5 | Python 3.11+ selected in Cloud settings | |
| 6 | `.env` remains gitignored; use Cloud secrets only | |

---

## Data on Cloud

`data/processed/restaurants.parquet` is **tracked in git** for deploy (other `*.parquet` files remain gitignored). The app shows a data-missing banner if the file is absent. Choose one strategy:

### Option A — Commit parquet for deploy (simplest)

1. Generate data locally: `python scripts/ingest.py`.
2. Commit the file: `git add data/processed/restaurants.parquet` (allowed via `.gitignore` exception).
3. Push to the branch Streamlit Cloud watches.

**Pros**: Fast cold start, no Hugging Face access at runtime.  
**Cons**: ~3.6 MB in repo; dataset updates require re-ingest + commit.

### Option B — Run ingest at build time (advanced)

Add a Streamlit Cloud **Advanced settings** custom dependency or a small shell bootstrap that runs ingest before the app starts. This requires network access to Hugging Face during deploy and adds several minutes to first deploy.

Example pattern (not included in repo by default):

```bash
# Only if you add a custom startup script on Cloud
pip install -r requirements.txt
PYTHONPATH=src python scripts/ingest.py
```

**Pros**: Repo stays small; always fresh data from HF.  
**Cons**: Slower deploys; HF/datasets must be available at build time.

### Option C — External artifact URL

Host `restaurants.parquet` on S3/GCS/GitHub Release and download to `data/processed/` in a `streamlit` startup hook or one-time script. Use when parquet must not live in git but Option B is too slow.

**Recommendation for milestone demos**: **Option A** on `main` or a `streamlit-deploy` branch.

---

## Streamlit Community Cloud (step-by-step)

### 1. Push code to GitHub

Ensure the branch you deploy includes:

- `src/app/main.py`
- `requirements.txt`
- `data/processed/restaurants.parquet` (if using Option A)
- Do **not** push `.env` or API keys.

### 2. Create the app

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → select repository and branch.
3. **Main file path**: `src/app/main.py`
4. **App URL**: choose a subdomain (e.g. `tastetrail-zomato`).

### 3. Python version

In app **Settings → General**:

- Set **Python version** to **3.11** (matches `requires-python` in `pyproject.toml`).

### 4. Secrets (Groq + optional overrides)

In **Settings → Secrets**, add TOML that maps to environment variables read by `app.config.Settings`:

```toml
# Streamlit Cloud secrets.toml (paste in UI — do not commit)

LLM_PROVIDER = "groq"
LLM_API_KEY = "gsk_xxxxxxxxxxxxxxxx"   # or use GROQ_API_KEY
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxxxx"
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = "0.3"
LLM_MAX_RETRIES = "1"

# Optional — defaults are fine if parquet is at default path
DATA_PATH = "data/processed/restaurants.parquet"
MAX_CANDIDATES = "30"
BUDGET_LOW_MAX = "500"
BUDGET_MEDIUM_MAX = "1500"
```

`pydantic-settings` loads these from the environment on Cloud (no `.env` file needed). `LLM_API_KEY` and `GROQ_API_KEY` are both supported via `resolved_llm_api_key` in `config.py`.

### 5. Deploy

Click **Deploy**. First build installs `requirements.txt` and starts Streamlit.

### 6. Post-deploy verification

| Check | Expected |
|-------|----------|
| App loads | Hero + preference form visible |
| Area dropdown | Populated (e.g. Bellandur, Indiranagar) |
| Submit recommendations | Loading state → result cards with explanations |
| Missing data | Red banner with ingest instructions (only if parquet missing) |
| Invalid/missing API key | User-friendly error on submit (check Cloud logs for details) |

Manual test: location **Bellandur**, budget **Medium**, cuisine **Italian**, min rating **4.0**, top **5** → **Get AI Recommendations**.

---

## Optional repository files

These are not required but improve operability:

### `.streamlit/config.toml`

```toml
[server]
headless = true

[browser]
gatherUsageStats = false
```

Page title, layout, and theme are already set in `src/app/main.py` and `src/app/ui/theme.py`.

### Root wrapper `streamlit_app.py` (alternative entry)

If your team prefers a root-level entry for documentation clarity:

```python
# streamlit_app.py (optional — Cloud can still use src/app/main.py)
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).parent / "src/app/main.py"), run_name="__main__")
```

Then set main file to `streamlit_app.py` on Cloud.

---

## Configuration reference

Environment variables (local `.env` or Streamlit secrets):

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LLM_API_KEY` or `GROQ_API_KEY` | **Yes** (prod) | — | Groq authentication |
| `LLM_PROVIDER` | No | `groq` | Provider id |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` | Model name |
| `LLM_TEMPERATURE` | No | `0.3` | Sampling temperature |
| `LLM_MAX_RETRIES` | No | `1` | Retry count on LLM errors |
| `DATA_PATH` | No | `data/processed/restaurants.parquet` | Parquet location (relative to repo root) |
| `MAX_CANDIDATES` | No | `30` | Max restaurants sent to LLM |
| `BUDGET_LOW_MAX` | No | `500` | Low band max (INR for two) |
| `BUDGET_MEDIUM_MAX` | No | `1500` | Medium band max |

See [`.env.example`](../.env.example) for the full local template.

---

## Self-hosted Streamlit (Docker / VM)

For a private server or container:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY scripts/ scripts/
COPY data/processed/restaurants.parquet data/processed/

ENV LLM_API_KEY=""
ENV DATA_PATH=data/processed/restaurants.parquet

EXPOSE 8501
CMD ["streamlit", "run", "src/app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Run with secrets via `-e` or orchestrator secret store:

```bash
docker build -t tastetrail-streamlit .
docker run -p 8501:8501 -e LLM_API_KEY="gsk_..." tastetrail-streamlit
```

Place a reverse proxy (nginx, Caddy) with TLS in front for production.

---

## Security and operations

| Topic | Guidance |
|-------|----------|
| **Secrets** | Never commit `.env` or keys; use Streamlit Secrets or host env vars only |
| **Logs** | Do not log full prompts or API keys (see `docs/edge-cases.md` SEC-004) |
| **Rate limits** | Groq free tier has quotas; expect throttling under heavy public demo traffic |
| **Cold start** | `@st.cache_resource` caches orchestrator; first LLM call may be slower |
| **Updates** | Re-deploy from Git push; restart app in Cloud UI after secret changes |
| **Branch strategy** | Use `main` for prod demo or a dedicated `streamlit-deploy` branch with parquet committed |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|----------------|-----|
| `ModuleNotFoundError: app` | Wrong main file or broken `src/` layout | Use `src/app/main.py`; confirm `src/app/` exists on branch |
| Data missing banner | Parquet not in repo / wrong `DATA_PATH` | Commit parquet (Option A) or fix `DATA_PATH` secret |
| Empty location dropdown | Corrupt or empty parquet | Re-run `python scripts/ingest.py` locally and redeploy data |
| LLM error on submit | Missing/invalid Groq key | Set `LLM_API_KEY` in Streamlit Secrets; redeploy |
| Build fails on `datasets` | Heavy HF dependency if ingest runs on Cloud | Prefer Option A (commit parquet); trim unused deps if you fork `requirements.txt` for Streamlit-only deploy |
| App sleeps / 502 | Free tier idle | Wake app with a visit; upgrade plan if needed |
| Works locally, fails on Cloud | Secrets only in local `.env` | Mirror variables in Cloud Secrets TOML |

**Logs**: Streamlit Cloud → app → **Manage app** → **Logs** (build + runtime).

---

## Deployment timeline (suggested)

| Step | Effort |
|------|--------|
| Local ingest + smoke test | 15–30 min |
| Commit parquet (Option A) + push | 10 min |
| Create Cloud app + secrets | 15 min |
| QA on public URL | 15 min |
| **Total** | ~1 hour |

---

## Out of scope (this plan)

- Deploying the **FastAPI + Next.js** stack (see `README.md` Phase 6 Path B).
- CI/CD beyond Streamlit’s native Git deploy.
- Custom domains, auth, and multi-tenant scaling.

For architecture context, see [Deployment Topology](./architecture.md#deployment-topology).
