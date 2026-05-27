# Zomato AI Restaurant Recommendation

AI-powered restaurant recommendations using the Zomato Hugging Face dataset and an LLM.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # ingest, API, tests
cp .env.example .env
```

## Phase 1: Data Ingestion

Load and preprocess the dataset from Hugging Face:

```bash
python scripts/ingest.py
```

Output: `data/processed/restaurants.parquet`

### Column mapping (raw → canonical)

| Hugging Face column | Canonical field |
|---------------------|-----------------|
| `name` | `name` |
| `address` + `location` + `listed_in(city)` | `location` (city + locality) |
| `cuisines` | `cuisines` (list) |
| `rate` | `rating` (parsed from e.g. `4.1/5`; `NEW` dropped) |
| `approx_cost(for two people)` | `estimated_cost` |
| derived | `budget_band` (`low` / `medium` / `high`) |
| derived | `id` (stable hash of name + location) |

Rows are dropped if: empty name, unrated (`NEW`/missing), missing cost, or empty cuisines.

## Phase 2: Restaurant Repository

Load preprocessed data at runtime:

```python
from app.data import get_repository

repo = get_repository()
restaurants = repo.get_all()
by_ids = repo.get_by_ids(["abc123", "def456"])
```

Models: `UserPreferences`, `FilterCriteria`, `Recommendation`, `RecommendationResponse`.

## Phase 3: Filter Service

Deterministic filtering before LLM (no API calls):

```python
from app.data import get_repository
from app.models import UserPreferences, BudgetBand
from app.services import FilterService

prefs = UserPreferences(
    location="Bangalore", budget=BudgetBand.MEDIUM,
    cuisine="Italian", min_rating=4.0,
)
result = FilterService().filter(prefs, get_repository())
print(len(result.candidates), result.total_before_cap)
```

Debug CLI:

```bash
PYTHONPATH=src python scripts/filter_debug.py --location Bangalore --cuisine Italian --budget medium --min-rating 4.0
```

## Phase 4: LLM Integration (Groq)

Configure Groq in `.env` (see `.env.example`):

```bash
LLM_PROVIDER=groq
LLM_API_KEY=<your-key>   # or GROQ_API_KEY
LLM_MODEL=llama-3.3-70b-versatile
```

## Phase 5: Orchestrator

Single entry point for UI/API:

```python
from app.models import UserPreferences, BudgetBand
from app.services import RecommendRestaurantsUseCase

prefs = UserPreferences(
    location="Bangalore", budget=BudgetBand.MEDIUM,
    cuisine="Italian", min_rating=4.0, top_k=5,
)
response = RecommendRestaurantsUseCase().execute(prefs)
```

CLI:

```bash
PYTHONPATH=src python scripts/recommend.py --location Bangalore --cuisine Italian --top-k 3
```

## Phase 6: UI

### Next.js frontend + FastAPI backend (recommended)

**Terminal 1 — API** (from project root):

```bash
pip install -r requirements-dev.txt
cp .env.example .env   # set LLM_API_KEY
python scripts/ingest.py
PYTHONPATH=src uvicorn api.main:app --reload --port 8000
```

**Terminal 2 — Frontend**:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The TasteTrail AI UI matches the designs in `design/image1.png` (preference form) and `design/image2.png` (results grid).

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Liveness |
| `GET /api/v1/metadata/locations` | Area dropdown options |
| `POST /api/v1/recommendations` | Generate recommendations |

### Streamlit UI

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
# or: PYTHONPATH=src streamlit run src/app/main.py
```

Deploy to Streamlit Community Cloud: see [`docs/deployment-plan.md`](docs/deployment-plan.md).

## Tests

```bash
PYTHONPATH=src pytest tests/ -v
# Include integration test (requires ingested data):
PYTHONPATH=src pytest tests/ -v -m integration
```

## Production deploy (Railway + Vercel)

| Service | Platform | Config |
|---------|----------|--------|
| **API** | [Railway](https://railway.com) | `railway.toml` + `requirements-api.txt` |
| **UI** | [Vercel](https://vercel.com) | Root directory `frontend`, `frontend/vercel.json` |

1. Push repo with `data/processed/restaurants.parquet` committed.
2. **Railway**: deploy from GitHub; set `LLM_API_KEY`, `CORS_ALLOWED_ORIGINS` (include your Vercel URL and `https://*.vercel.app` for previews).
3. **Vercel**: import repo, set root to `frontend`, set `NEXT_PUBLIC_API_URL` to your Railway HTTPS URL.
4. Full steps: [`docs/deployment-plan.md`](docs/deployment-plan.md).

Optional Docker deploy on Railway: use root `Dockerfile`.

## Documentation

See [`docs/`](docs/) for architecture, implementation plan, and edge cases.
