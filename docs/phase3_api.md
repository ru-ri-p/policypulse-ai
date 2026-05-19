# Phase 3 — FastAPI

## Setup

```bash
source .venv/bin/activate
pip install fastapi "uvicorn[standard]" pydantic "python-jose[cryptography]" "passlib[bcrypt]" email-validator
pip freeze > requirements.txt

psql -U ppuser -d policypulse -f ingestion/migrations/005_api_auth.sql

# Add to .env
# SECRET_KEY=your-long-random-secret
```

## Run

```bash
./scripts/run_api.sh
```

Open http://localhost:8000/docs

## Endpoints (11)

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | No |
| GET | `/documents/` | No |
| GET | `/documents/{id}` | No |
| GET | `/search/?q=...` | No |
| GET | `/sources/` | No |
| POST | `/auth/register` | No |
| POST | `/auth/login` | No |
| GET | `/user/profile` | Bearer JWT |
| POST | `/alerts/` | Bearer JWT |
| GET | `/alerts/` | Bearer JWT |

## Test auth in Swagger

1. POST `/auth/register` with email + password (8+ chars)
2. Copy `access_token`
3. Click **Authorize** → `Bearer <token>`
4. Call `/user/profile` and `/alerts/`
