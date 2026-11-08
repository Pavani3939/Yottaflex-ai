"""
YottaPay AI – Database Connection and Session Management
Uses SQLAlchemy 2.0 with PyMySQL driver for MySQL 8.0+.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from loguru import logger

from app.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# SQLAlchemy Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.database_url,
    pool_size=10,           # number of persistent connections in pool
    max_overflow=20,        # additional connections beyond pool_size
    pool_timeout=30,        # seconds to wait for a connection
    pool_recycle=1800,      # recycle connections every 30 minutes
    pool_pre_ping=True,     # verify connection liveness before use
    echo=settings.DEBUG,    # log SQL statements in debug mode
)


# ---------------------------------------------------------------------------
# Session Factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Declarative Base (shared by all ORM models)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ---------------------------------------------------------------------------
# FastAPI Dependency – yields a DB session per request
# ---------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    The session is automatically closed after the request completes.

    Usage:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Context manager variant (for scripts / services outside FastAPI)
# ---------------------------------------------------------------------------
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager that provides a database session.

    Usage:
        with get_db_context() as db:
            db.query(Vendor).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
def check_database_connection() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error(f"Database connection failed: {exc}")
        return False
