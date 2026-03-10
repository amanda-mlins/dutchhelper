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

        # Add sentence_id FK column to conjunction_game_answers (new in v2)
        try:
            conn.execute(text(
                "ALTER TABLE conjunction_game_answers ADD COLUMN sentence_id INTEGER REFERENCES conjunction_sentences(id)"
            ))
            conn.commit()
        except Exception:
            pass  # Column already exists

        # Add explanation column to conjunction_sentences (new in v3)
        try:
            conn.execute(text(
                "ALTER TABLE conjunction_sentences ADD COLUMN explanation TEXT"
            ))
            conn.commit()
        except Exception:
            pass  # Column already exists

        # Add prep_verb_pairs, prep_verb_stats, prep_verb_game_sessions,
        # prep_verb_game_answers tables — created by Base.metadata.create_all,
        # but ensure reflexive column exists if table was created before it was added.
        try:
            conn.execute(text(
                "ALTER TABLE prep_verb_pairs ADD COLUMN reflexive INTEGER NOT NULL DEFAULT 0"
            ))
            conn.commit()
        except Exception:
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
