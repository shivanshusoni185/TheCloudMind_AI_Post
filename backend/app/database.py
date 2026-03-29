import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

connect_args = {}
if "sslmode" not in DATABASE_URL:
    connect_args["sslmode"] = "require"

engine = create_engine(
    DATABASE_URL,
    # Larger pool to absorb burst image requests without exhaustion.
    # A homepage loads 20-30 images; each image request needs one connection.
    pool_size=15,
    max_overflow=25,      # 40 total connections at peak
    pool_timeout=10,      # fail fast — don't queue forever
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args=connect_args,
)
logger.info("Database engine created (pool_size=15, max_overflow=25)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as exc:
        db.rollback()
        logger.error("Database error: %s", exc)
        raise
    finally:
        db.close()


def db_ping() -> bool:
    """Lightweight connectivity check that does NOT use the session pool.
    Used by the health endpoint so pool exhaustion never blocks health probes."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("DB ping failed: %s", exc)
        return False
