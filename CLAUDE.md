# CLAUDE.md

## Codebase Overview

FastAPI analytics API (Portuguese-language project) serving KPIs, correlations, K-Means clusters and AI-generated reports over a local DuckDB file. Real GA4/Search Console collection is disabled; data comes from a synthetic simulator (`tests/simulador_dados.py`), loaded via `POST /api/v1/admin/populate-database`. API deployed on Render; the Next.js frontend is a separate project deployed on Vercel that consumes this API.

**Stack**: Python, FastAPI, DuckDB, pandas, scikit-learn, Agno + NVIDIA API (`NVIDIA_MODEL`, padrão `meta/llama-3.3-70b-instruct`), pytest.
**Structure**: `app/` (all HTTP routes in `app/main.py`, AI report agent), `src/collectors/db_storage.py` (DuckDB storage), `src/ml/` (clustering), `src/cleaning/` (cleaners), `src/ga`, `src/gsc` (disabled stubs), `tests/` (simulator + tests), `docs/` (many stale).

Run from the repo root: `python -m uvicorn app.main:app --reload --port 8000`; tests: `python -m pytest tests/test_api.py -v` (needs a populated DB).

For detailed architecture, see [docs/CODEBASE_MAP.md](docs/CODEBASE_MAP.md).
