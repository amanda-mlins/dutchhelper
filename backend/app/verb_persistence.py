"""
Verb conjugation persistence layer.

Implementations:
1. PostgresPersistence  – Uses the app's SQLAlchemy session / PostgreSQL (production default)
2. SQLitePersistence    – Standalone SQLite file (local dev fallback)
3. JSONPersistence      – Plain JSON file (last-resort fallback)

Selection logic (get_persistence):
  - DATABASE_URL starts with "postgresql" → PostgresPersistence
  - USE_JSON_PERSISTENCE=true             → JSONPersistence
  - otherwise                             → SQLitePersistence
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class VerbPersistenceBase(ABC):
    @abstractmethod
    def get_verb(self, verb: str) -> Optional[Dict[str, Any]]: pass
    @abstractmethod
    def save_verb(self, verb: str, conjugation: Dict[str, Any]) -> bool: pass
    @abstractmethod
    def verb_exists(self, verb: str) -> bool: pass
    @abstractmethod
    def get_all_verbs(self) -> Dict[str, Dict[str, Any]]: pass
    @abstractmethod
    def close(self): pass


class PostgresPersistence(VerbPersistenceBase):
    """PostgreSQL-backed verb persistence using the app's SQLAlchemy engine."""

    def _session(self):
        from app.database import SessionLocal
        return SessionLocal()

    def get_verb(self, verb: str) -> Optional[Dict[str, Any]]:
        from app.models import VerbConjugation
        db = self._session()
        try:
            row = db.query(VerbConjugation).filter(
                VerbConjugation.infinitive == verb.strip().lower()
            ).first()
            if row:
                row.query_count += 1
                row.updated_at = datetime.now(timezone.utc)
                db.commit()
                return json.loads(row.conjugation_data)
            return None
        except Exception as e:
            logger.error(f"[PG] Error retrieving verb '{verb}': {e}")
            db.rollback()
            return None
        finally:
            db.close()

    def save_verb(self, verb: str, conjugation: Dict[str, Any]) -> bool:
        from app.models import VerbConjugation
        db = self._session()
        try:
            infinitive = verb.strip().lower()
            row = db.query(VerbConjugation).filter(
                VerbConjugation.infinitive == infinitive
            ).first()
            if row:
                row.conjugation_data = json.dumps(conjugation)
                row.english_translation = conjugation.get('englishTranslation', '')
                row.verb_type = conjugation.get('verbType', 'regular')
                row.updated_at = datetime.now(timezone.utc)
            else:
                row = VerbConjugation(
                    infinitive=infinitive,
                    english_translation=conjugation.get('englishTranslation', ''),
                    verb_type=conjugation.get('verbType', 'regular'),
                    conjugation_data=json.dumps(conjugation),
                )
                db.add(row)
            db.commit()
            logger.info(f"[PG] Saved verb '{verb}'")
            return True
        except Exception as e:
            logger.error(f"[PG] Error saving verb '{verb}': {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def verb_exists(self, verb: str) -> bool:
        from app.models import VerbConjugation
        db = self._session()
        try:
            return db.query(VerbConjugation.id).filter(
                VerbConjugation.infinitive == verb.strip().lower()
            ).first() is not None
        except Exception as e:
            logger.error(f"[PG] Error checking verb existence: {e}")
            return False
        finally:
            db.close()

    def get_all_verbs(self) -> Dict[str, Dict[str, Any]]:
        from app.models import VerbConjugation
        db = self._session()
        try:
            rows = db.query(VerbConjugation).order_by(
                VerbConjugation.query_count.desc()
            ).all()
            return {r.infinitive: json.loads(r.conjugation_data) for r in rows}
        except Exception as e:
            logger.error(f"[PG] Error retrieving all verbs: {e}")
            return {}
        finally:
            db.close()

    def close(self):
        pass  # Sessions are closed per-operation


class SQLitePersistence(VerbPersistenceBase):
    """SQLite-based verb persistence (local development only)."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            import os
            db_path = os.environ.get(
                'VERBS_DB_PATH',
                str(Path(__file__).parent.parent / 'verbs.db')
            )
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _initialize_db(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS verbs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    infinitive TEXT UNIQUE NOT NULL,
                    english_translation TEXT,
                    verb_type TEXT,
                    conjugation_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    query_count INTEGER DEFAULT 1
                )
            """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_infinitive ON verbs(infinitive)"
            )
            self.connection.commit()
            logger.info(f"[SQLite] Database initialised at {self.db_path}")
        except Exception as e:
            logger.error(f"[SQLite] Failed to initialise database: {e}")
            raise

    def get_verb(self, verb: str) -> Optional[Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT conjugation_data FROM verbs WHERE LOWER(infinitive) = LOWER(?)",
                (verb.strip(),)
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE verbs SET query_count = query_count + 1, "
                    "updated_at = CURRENT_TIMESTAMP WHERE LOWER(infinitive) = LOWER(?)",
                    (verb.strip(),)
                )
                self.connection.commit()
                return json.loads(row['conjugation_data'])
            return None
        except Exception as e:
            logger.error(f"[SQLite] Error retrieving verb '{verb}': {e}")
            return None

    def save_verb(self, verb: str, conjugation: Dict[str, Any]) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO verbs (infinitive, english_translation, verb_type, conjugation_data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(infinitive) DO UPDATE SET
                    conjugation_data = excluded.conjugation_data,
                    english_translation = excluded.english_translation,
                    verb_type = excluded.verb_type,
                    updated_at = CURRENT_TIMESTAMP
            """, (verb.strip().lower(), conjugation.get('englishTranslation', ''),
                  conjugation.get('verbType', 'regular'), json.dumps(conjugation)))
            self.connection.commit()
            logger.info(f"[SQLite] Saved verb '{verb}'")
            return True
        except Exception as e:
            logger.error(f"[SQLite] Error saving verb '{verb}': {e}")
            return False

    def verb_exists(self, verb: str) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT 1 FROM verbs WHERE LOWER(infinitive) = LOWER(?) LIMIT 1",
                (verb.strip(),)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"[SQLite] Error checking verb existence: {e}")
            return False

    def get_all_verbs(self) -> Dict[str, Dict[str, Any]]:
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT infinitive, conjugation_data FROM verbs ORDER BY query_count DESC"
            )
            return {row['infinitive']: json.loads(row['conjugation_data'])
                    for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"[SQLite] Error retrieving all verbs: {e}")
            return {}

    def close(self):
        if self.connection:
            self.connection.close()


class JSONPersistence(VerbPersistenceBase):
    """Plain JSON file persistence (last-resort fallback)."""

    def __init__(self, json_path: str = None):
        if json_path is None:
            import os
            json_path = os.environ.get(
                'VERBS_JSON_PATH',
                str(Path(__file__).parent.parent / 'verbs.json')
            )
        self.json_path = json_path
        self.verbs: Dict[str, Dict[str, Any]] = {}
        self._load_from_file()

    def _load_from_file(self):
        try:
            path = Path(self.json_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.verbs = json.load(f)
                logger.info(f"[JSON] Loaded {len(self.verbs)} verbs")
        except Exception as e:
            logger.error(f"[JSON] Error loading file: {e}")
            self.verbs = {}

    def _save_to_file(self):
        try:
            path = Path(self.json_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.verbs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[JSON] Error saving file: {e}")

    def get_verb(self, verb: str) -> Optional[Dict[str, Any]]:
        return self.verbs.get(verb.strip().lower())

    def save_verb(self, verb: str, conjugation: Dict[str, Any]) -> bool:
        try:
            self.verbs[verb.strip().lower()] = conjugation
            self._save_to_file()
            return True
        except Exception as e:
            logger.error(f"[JSON] Error saving verb '{verb}': {e}")
            return False

    def verb_exists(self, verb: str) -> bool:
        return verb.strip().lower() in self.verbs

    def get_all_verbs(self) -> Dict[str, Dict[str, Any]]:
        return self.verbs.copy()

    def close(self):
        pass


# ── Singleton factory ─────────────────────────────────────────────────────────

_persistence_instance: Optional[VerbPersistenceBase] = None


def get_persistence() -> VerbPersistenceBase:
    """
    Return the global persistence singleton.

    Selection order:
    1. DATABASE_URL starts with "postgresql" → PostgresPersistence  (production)
    2. USE_JSON_PERSISTENCE=true             → JSONPersistence
    3. otherwise                             → SQLitePersistence    (local dev)
    """
    global _persistence_instance
    if _persistence_instance is None:
        import os
        db_url = os.environ.get('DATABASE_URL', '')
        if db_url.startswith('postgresql'):
            logger.info("[Persistence] Using PostgreSQL for verb conjugations")
            _persistence_instance = PostgresPersistence()
        elif os.getenv('USE_JSON_PERSISTENCE', 'false').lower() == 'true':
            logger.info("[Persistence] Using JSON for verb conjugations")
            _persistence_instance = JSONPersistence()
        else:
            logger.info("[Persistence] Using SQLite for verb conjugations")
            _persistence_instance = SQLitePersistence()
    return _persistence_instance


def initialize_persistence(use_json: bool = False) -> VerbPersistenceBase:
    """Force-initialise the persistence layer (used in tests)."""
    global _persistence_instance
    _persistence_instance = JSONPersistence() if use_json else SQLitePersistence()
    return _persistence_instance
