from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import Base
from .config import settings

_url = settings.DATABASE_URL

# SQLite needs check_same_thread=False; Postgres does not (and rejects it).
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

engine = create_engine(_url, connect_args=_connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes the database and creates tables.

    In production, use Alembic migrations instead of relying on this.
    This is kept for SQLite dev convenience and for the test suite.
    """
    Base.metadata.create_all(bind=engine)
    _run_migrations()

def _run_migrations():
    """Apply lightweight schema migrations for columns added after initial deploy."""
    with engine.connect() as conn:
        # Add category column to user_words if it doesn't exist yet
        try:
            conn.execute(text("ALTER TABLE user_words ADD COLUMN category VARCHAR"))
            conn.commit()
        except Exception:
            # Column already exists — ignore
            pass

def get_db():
    """
    Dependency to get a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db() -> bool:
    """Run a cheap query to verify the database is reachable. Used by /health."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
