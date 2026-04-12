from __future__ import annotations

import logging
import os
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from crud import ensure_branch_state, generate_branch_metric, seed_database
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


async def collect_branch_metrics() -> None:
    """Background job that simulates live agent metric ingestion."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Branch).order_by(Branch.id.asc()))
        branch_rows = list(result.scalars().all())
        for branch in branch_rows:
            await generate_branch_metric(session, branch)
            await ensure_branch_state(session, branch)
        logger.info("Generated new metric readings for %s branches", len(branch_rows))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting UrbanBank backend initialization")
    
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
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
        seconds=30,
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
