"""
Seed the article_words table from the static dutch_article_words.py list.

Usage (from backend/ directory with venv active):
    python seed_article_words.py

Safe to run multiple times — uses INSERT OR IGNORE (SQLite) / ON CONFLICT DO NOTHING (Postgres).
"""
import os
import sys

# Make sure the app package is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app import models
from app.dutch_article_words import DUTCH_ARTICLE_WORDS
from datetime import datetime, timezone

# Ensure tables exist (no-op if already created by Alembic)
models.Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    try:
        added = 0
        skipped = 0
        for entry in DUTCH_ARTICLE_WORDS:
            existing = db.query(models.ArticleWord).filter_by(word=entry["word"]).first()
            if existing:
                skipped += 1
                continue
            row = models.ArticleWord(
                word=entry["word"],
                article=entry["article"],
                translation=entry.get("translation"),
                difficulty=entry.get("difficulty", "medium"),
                category=entry.get("category"),
                is_active=True,
                created_at=datetime.now(timezone.utc),
            )
            db.add(row)
            added += 1
        db.commit()
        print(f"✅ Seed complete: {added} added, {skipped} already existed.")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
