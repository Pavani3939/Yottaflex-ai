"""
YottaPay AI – FastAPI Application Entry Point
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import get_settings
from app.database.connection import check_database_connection

settings = get_settings()


# ---------------------------------------------------------------------------
# Application Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} …")

    # Verify DB connectivity on startup
    if check_database_connection():
        logger.success("Database connection: OK")
    else:
        logger.error("Database connection: FAILED — check .env settings")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"Upload directory: {settings.UPLOAD_DIR}")

    yield  # Application runs

    logger.info(f"Shutting down {settings.APP_NAME} …")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Intelligent Invoice Processing and Payment Automation Platform. "
        "Automates invoice intake, three-way matching, exception management, "
        "approval workflows, and payment readiness evaluation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers (imported lazily to avoid circular imports at startup)
# ---------------------------------------------------------------------------
from app.routers import (  # noqa: E402
    vendors,
    purchase_orders,
    goods_receipts,
    invoices,
    matching,
    exceptions,
    approvals,
    payments,
    analytics,
    audit_events,
    auth,
)

API_PREFIX = "/api"

app.include_router(auth.router,            prefix=API_PREFIX, tags=["Authentication"])
app.include_router(vendors.router,         prefix=API_PREFIX, tags=["Vendors"])
app.include_router(purchase_orders.router, prefix=API_PREFIX, tags=["Purchase Orders"])
app.include_router(goods_receipts.router,  prefix=API_PREFIX, tags=["Goods Receipts"])
app.include_router(invoices.router,        prefix=API_PREFIX, tags=["Invoices"])
app.include_router(matching.router,        prefix=API_PREFIX, tags=["Matching"])
app.include_router(exceptions.router,      prefix=API_PREFIX, tags=["Exceptions"])
app.include_router(approvals.router,       prefix=API_PREFIX, tags=["Approvals"])
app.include_router(payments.router,        prefix=API_PREFIX, tags=["Payments"])
app.include_router(analytics.router,       prefix=API_PREFIX, tags=["Analytics"])
app.include_router(audit_events.router,    prefix=API_PREFIX, tags=["Audit Events"])


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    """Quick health check — returns DB connectivity status."""
    db_ok = check_database_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "database": "connected" if db_ok else "disconnected",
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
    }
