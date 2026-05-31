# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    alerts,
    auth_routes,
    documents,
    playbooks,
    search,
    sources,
    stats,
    users,
)

app = FastAPI(
    title="PolicyPulse AI API",
    description="Real-time AI policy monitoring and compliance intelligence.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(sources.router, prefix="/sources", tags=["Sources"])
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/user", tags=["User"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(stats.router, prefix="/stats", tags=["Stats"])
app.include_router(playbooks.router, prefix="/playbooks", tags=["Playbooks"])


@app.get("/health", tags=["System"])
def health_check():
    """Returns API status. Used by deployment platforms to verify the app is alive."""
    return {"status": "healthy", "version": "0.4.0"}
