"""
YottaPay AI – Database Initialisation
Creates all tables in the correct order respecting FK dependencies.
Run this script once after setting up the MySQL database.

Usage:
    cd backend
    python -m app.database.init_db
"""
import sys
from pathlib import Path

# Allow running directly: python -m app.database.init_db
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from loguru import logger
from sqlalchemy import text

from app.database.connection import Base, engine, check_database_connection

# Import ALL models so SQLAlchemy knows about them before create_all()
from app.models import (  # noqa: F401
    vendor,
    purchase_order,
    purchase_order_line,
    goods_receipt,
    goods_receipt_line,
    invoice,
    invoice_line,
    invoice_match,
    invoice_exception,
    approval,
    approval_history,
    payment,
    audit_event,
    invoice_document,
)


def create_database_if_not_exists() -> None:
    """Create the yottapay schema if it does not exist."""
    from sqlalchemy import create_engine as _ce
    from app.config import get_settings

    s = get_settings()
    # Connect without specifying the database name
    root_url = (
        f"mysql+pymysql://{s.DB_USER}:{s.DB_PASSWORD}"
        f"@{s.DB_HOST}:{s.DB_PORT}/?charset=utf8mb4"
    )
    temp_engine = _ce(root_url, echo=False)
    with temp_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{s.DB_NAME}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
        conn.commit()
    temp_engine.dispose()
    logger.info(f"Database '{s.DB_NAME}' is ready.")


def init_db() -> None:
    """Create all tables in dependency order."""
    logger.info("Checking database connection …")
    if not check_database_connection():
        logger.error("Cannot connect to MySQL. Check .env settings and try again.")
        sys.exit(1)

    logger.info("Creating all tables …")
    Base.metadata.create_all(bind=engine)
    logger.success("All tables created successfully.")


if __name__ == "__main__":
    logger.info("=== YottaPay AI – Database Initialisation ===")
    create_database_if_not_exists()
    init_db()
    logger.success("Database initialisation complete.")
