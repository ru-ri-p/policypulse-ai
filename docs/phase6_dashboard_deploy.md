# Phase 6 — Dashboard + Docker

## Local dashboard (Week 17)

Terminal 1 — API:

```bash
./scripts/run_api.sh
```

Terminal 2 — Dashboard:

```bash
pip install streamlit plotly altair
./scripts/run_dashboard.sh
```

Open http://localhost:8501

**Done when:** Feed shows documents, search returns results (needs embeddings).

## Docker (Weeks 18–20)

```bash
# Ensure .env exists (DB_* overridden in compose for `db` service)
docker compose up --build
```

- API docs: http://localhost:8000/docs  
- Dashboard: http://localhost:8501  

**Note:** First `docker compose up` creates an empty DB. Run migrations and seed inside the api container or from host against localhost:5432.

```bash
docker compose exec api psql -h db -U ppuser -d policypulse -f ingestion/migrations/002_ml_columns.sql
# ... run other migrations, seed, embedders as needed
```

## Railway / Render

1. Push repo to GitHub (already done).
2. Connect repo on [railway.app](https://railway.app) or [render.com](https://render.com).
3. Add managed Postgres + Redis plugins (Railway) or use Render PostgreSQL.
4. Set environment variables from `.env.example` (`DB_*`, `SECRET_KEY`, etc.).
5. Deploy **Dockerfile** service on port 8000.
6. Optional second service for Streamlit with start command:
   `streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0`
7. Set `API_BASE_URL` to your public API URL on the dashboard service.

Add live URLs to README for portfolio.

## Milestone

```bash
git tag v0.6.0
```
