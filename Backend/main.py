from __future__ import annotations

import logging
import os
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text

from crud import generate_branch_metric, seed_database
from database import Base, AsyncSessionLocal, engine
from models import Branch
from routers import alerts, branches, incidents, metrics

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("urbanbank-backend")

scheduler = AsyncIOScheduler(timezone="UTC")
METRIC_COLLECTION_INTERVAL_SECONDS = int(os.getenv("METRIC_COLLECTION_INTERVAL_SECONDS", "120"))


async def ensure_performance_indexes() -> None:
    """Create frequently-used indexes for query paths on large datasets."""
    index_statements = (
        "CREATE INDEX IF NOT EXISTS ix_metrics_branch_recorded_at_desc ON metrics (branch_id, recorded_at DESC, id DESC)",
        "CREATE INDEX IF NOT EXISTS ix_alerts_fired_at_desc ON alerts (fired_at DESC)",
        "CREATE INDEX IF NOT EXISTS ix_alerts_branch_fired_at_desc ON alerts (branch_id, fired_at DESC)",
        "CREATE INDEX IF NOT EXISTS ix_incidents_started_at_desc ON incidents (started_at DESC)",
    )

    async with engine.begin() as conn:
        for statement in index_statements:
            await conn.execute(text(statement))


class DashboardUpdateBroker:
    """In-memory pub/sub for dashboard update events."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1)
        async with self._lock:
            self._subscribers.add(queue)
        return queue

    async def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        async with self._lock:
            self._subscribers.discard(queue)

    async def publish(self, payload: dict[str, Any]) -> None:
        async with self._lock:
            subscribers = list(self._subscribers)

        for queue in subscribers:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass


dashboard_updates = DashboardUpdateBroker()


async def collect_branch_metrics() -> None:
    """Background job that simulates live agent metric ingestion."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Branch).order_by(Branch.id.asc()))
        branch_rows = list(result.scalars().all())
        for branch in branch_rows:
            await generate_branch_metric(session, branch)
        logger.info("Generated new metric readings for %s branches", len(branch_rows))
        await dashboard_updates.publish(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "branch_count": len(branch_rows),
            }
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting UrbanBank backend initialization")
    
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await ensure_performance_indexes()
            logger.info("Successfully connected to the database and created tables!")
            break
        except Exception as e:
            logger.warning(f"Database connection failed on attempt {attempt}/{max_retries}. Retrying in 5 seconds...")
            if attempt == max_retries:
                logger.error("Could not connect to the database after maximum retries.")
                raise e
            await asyncio.sleep(5)
            
    async with AsyncSessionLocal() as session:
        await seed_database(session)
    scheduler.add_job(
        collect_branch_metrics,
        "interval",
        seconds=METRIC_COLLECTION_INTERVAL_SECONDS,
        id="branch-metric-collector",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Background scheduler started")
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped")


app = FastAPI(
    title="Automated Self-Healing Infrastructure Pipeline API",
    description="Head Office IT Dashboard backend for Indian cooperative bank branches",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(branches.router)
app.include_router(metrics.router)
app.include_router(alerts.router)
app.include_router(incidents.router)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {
        "message": "Automated Self-Healing Infrastructure Pipeline API",
        "status": "running",
    }


@app.get("/health", tags=["root"])
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/dashboard/stream", tags=["metrics"])
async def dashboard_stream() -> StreamingResponse:
    queue = await dashboard_updates.subscribe()

    async def event_generator() -> AsyncIterator[str]:
        try:
            yield (
                "event: connected\n"
                f"data: {json.dumps({'interval_seconds': METRIC_COLLECTION_INTERVAL_SECONDS})}\n\n"
            )
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=20)
                    yield f"event: metrics_updated\ndata: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    yield "event: keepalive\ndata: {}\n\n"
        finally:
            await dashboard_updates.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
