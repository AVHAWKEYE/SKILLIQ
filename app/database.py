import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _default_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/skilliq.db"
    return "sqlite:///./skilliq.db"


DATABASE_URL = _default_database_url()


def _create_engine_with_fallback(url: str):
    """Create SQLAlchemy engine with Vercel-safe fallbacks.

    - Uses sqlite-specific connect args only for sqlite URLs.
    - Falls back to sqlite in /tmp on Vercel if provided DATABASE_URL is invalid
      or missing required driver.
    """
    try:
        if url.startswith("sqlite"):
            return create_engine(url, connect_args={"check_same_thread": False})
        return create_engine(url)
    except Exception as exc:
        if os.getenv("VERCEL"):
            fallback_url = "sqlite:////tmp/skilliq.db"
            print(f"Database init warning: {exc}. Falling back to {fallback_url}")
            return create_engine(fallback_url, connect_args={"check_same_thread": False})
        raise


engine = _create_engine_with_fallback(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
