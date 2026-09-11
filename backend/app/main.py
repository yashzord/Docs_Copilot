"""The FastAPI app. Wires the routes together.

Run locally, from backend/:

    uv run uvicorn app.main:app --reload
"""

import logging

from fastapi import FastAPI

from app.chat import router as chat_router
from app.documents import router as documents_router
from app.sessions import router as sessions_router

# ponytail: plain-text logs to the terminal. Ceiling: hard to search once there are
# many services. Upgrade: JSON logs plus OpenTelemetry traces in D7.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Docs Copilot API")
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(sessions_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness check for Docker and load balancers. Touches nothing external on purpose."""
    return {"status": "ok"}
