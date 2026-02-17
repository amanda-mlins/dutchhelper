"""
Verb conjugation persistence layer for cost-effective database storage.

This module provides two implementations:
1. SQLitePersistence - Lightweight, zero-cost database (SQLite)
2. JSONPersistence - Simple JSON file storage (fallback)

Both automatically save new verb conjugations when queried and add them to the
growing database, reducing LLM costs over time.
"""

import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VerbPersistenceBase(ABC):
    """Abstract base class for verb persistence implementations"""
    
    @abstractmethod
    def get_verb(self, verb: str) -> Optional[Dict[str, Any]]:
        """Retrieve a verb conjugation from storage"""
        pass
    
    @abstractmethod
    def save_verb(self, verb: str, conjugation: Dict[str, Any]) -> bool:
        """Save a verb conjugation to storage"""
        pass
    
    @abstractmethod
    def verb_exists(self, verb: str) -> bool:
        """Check if a verb exists in storage"""
        pass
    
    @abstractmethod
    def get_all_verbs(self) -> Dict[str, Dict[str, Any]]:
        """Get all verbs from storage"""
        pass
    
    @abstractmethod
    def close(self):
        """Close any open connections or resources"""
        pass


class SQLitePersistence(VerbPersistenceBase):
    """
    SQLite-based verb persistence.
    
    Benefits:
    - Zero hosting/database costs
    - Can be stored in version control (git)
    - Efficient for thousands of verbs
    - Supports full-text search
    - Can be deployed directly with the application
    """
    
    def __init__(self, db_path: str = "/Users/alins/dutchhelper/backend/verbs.db"):
        """
        Initialize SQLite persistence.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Create database schema if it doesn't exist"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            cursor = self.connection.cursor()
            
            # Create verbs table
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
            
            # Create index for fast lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_infinitive 
                ON verbs(infinitive)
            """)
            
            self.connection.commit()
            logger.info(f"SQLite database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            raise
    
    def get_verb(self, verb: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a verb conjugation from the database.
        
        Args:
            verb: The infinitive form of the verb (case-insensitive)
            
        Returns:
            Dictionary with conjugation data or None if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT conjugation_data, query_count FROM verbs WHERE LOWER(infinitive) = LOWER(?)",
                (verb.strip(),)
            )
            row = cursor.fetchone()
            
            if row:
                # Increment query count for analytics
                cursor.execute(
                    "UPDATE verbs SET query_count = query_count + 1, updated_at = CURRENT_TIMESTAMP WHERE LOWER(infinitive) = LOWER(?)",
                    (verb.strip(),)
                )
                self.connection.commit()
                
                return json.loads(row['conjugation_data'])
            return None
        except Exception as e:
            logger.error(f"Error retrieving verb '{verb}' from SQLite: {e}")
            return None
    
    def save_verb(self, verb: str, conjugation: Dict[str, Any]) -> bool:
        """
        Save a verb conjugation to the database.
        
        If the verb already exists, it will be updated.
        
        Args:
            verb: The infinitive form of the verb
            conjugation: Dictionary with conjugation data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            
            # Extract metadata if available
            english_translation = conjugation.get('englishTranslation', '')
            verb_type = conjugation.get('verbType', 'regular')
            conjugation_json = json.dumps(conjugation)
            
            # Upsert (update if exists, insert if not)
            cursor.execute("""
                INSERT INTO verbs (infinitive, english_translation, verb_type, conjugation_data)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(infinitive) DO UPDATE SET
                    conjugation_data = excluded.conjugation_data,
                    english_translation = excluded.english_translation,
                    verb_type = excluded.verb_type,
                    updated_at = CURRENT_TIMESTAMP
            """, (verb.strip().lower(), english_translation, verb_type, conjugation_json))
            
            self.connection.commit()
            logger.info(f"Saved verb '{verb}' to SQLite database")
            return True
        except Exception as e:
            logger.error(f"Error saving verb '{verb}' to SQLite: {e}")
            return False
    
    def verb_exists(self, verb: str) -> bool:
        """Check if a verb exists in the database"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT 1 FROM verbs WHERE LOWER(infinitive) = LOWER(?) LIMIT 1",
                (verb.strip(),)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking verb existence: {e}")
            return False
    
    def get_all_verbs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all verbs from the database.
        
        Returns:
            Dictionary mapping verb infinitives to their conjugation data
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT infinitive, conjugation_data FROM verbs ORDER BY query_count DESC")
            
            verbs = {}
            for row in cursor.fetchall():
                verbs[row['infinitive']] = json.loads(row['conjugation_data'])
            
            return verbs
        except Exception as e:
            logger.error(f"Error retrieving all verbs: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics for monitoring"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM verbs")
            total_verbs = cursor.fetchone()['count']
            
            cursor.execute("SELECT SUM(query_count) as total FROM verbs")
            total_queries = cursor.fetchone()['total'] or 0
            
            cursor.execute("""
                SELECT verb_type, COUNT(*) as count 
                FROM verbs 
                GROUP BY verb_type
            """)
            by_type = {row['verb_type']: row['count'] for row in cursor.fetchall()}
            
            return {
                'total_verbs': total_verbs,
                'total_queries': total_queries,
                'by_type': by_type,
                'database_size_mb': Path(self.db_path).stat().st_size / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def close(self):
        """Close the database connection"""
        if self.connection:
            self.connection.close()
            logger.info("SQLite connection closed")


class JSONPersistence(VerbPersistenceBase):
    """
    JSON file-based verb persistence (lighter alternative to SQLite).
    
    Benefits:
    - No external dependencies (SQLite is built-in, but this uses just JSON)
    - Can be stored in version control
    - Human-readable format
    
    Note: Not recommended for >10k verbs due to performance
    """
    
    def __init__(self, json_path: str = "/Users/alins/dutchhelper/backend/verbs.json"):
        """
        Initialize JSON file persistence.
        
        Args:
            json_path: Path to the JSON file
        """
        self.json_path = json_path
        self.verbs: Dict[str, Dict[str, Any]] = {}
        self._load_from_file()
    
    def _load_from_file(self):
        """Load verbs from JSON file if it exists"""
        try:
            path = Path(self.json_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.verbs = json.load(f)
                logger.info(f"Loaded {len(self.verbs)} verbs from {self.json_path}")
            else:
                logger.info(f"JSON file not found, starting with empty database")
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            self.verbs = {}
    
    def _save_to_file(self):
        """Save verbs to JSON file"""
        try:
            path = Path(self.json_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.verbs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving to JSON file: {e}")
    
    def get_verb(self, verb: str) -> Optional[Dict[str, Any]]:
        """Retrieve a verb conjugation from the JSON storage"""
        verb_lower = verb.strip().lower()
        return self.verbs.get(verb_lower)
    
    def save_verb(self, verb: str, conjugation: Dict[str, Any]) -> bool:
        """Save a verb conjugation to the JSON storage"""
        try:
            verb_lower = verb.strip().lower()
            self.verbs[verb_lower] = conjugation
            self._save_to_file()
            logger.info(f"Saved verb '{verb}' to JSON database")
            return True
        except Exception as e:
            logger.error(f"Error saving verb '{verb}' to JSON: {e}")
            return False
    
    def verb_exists(self, verb: str) -> bool:
        """Check if a verb exists in the JSON storage"""
        return verb.strip().lower() in self.verbs
    
    def get_all_verbs(self) -> Dict[str, Dict[str, Any]]:
        """Get all verbs from the JSON storage"""
        return self.verbs.copy()
    
    def close(self):
        """Close resources (JSON doesn't need cleanup, but keep for interface compliance)"""
        pass


# Global persistence instance (singleton pattern)
_persistence_instance: Optional[VerbPersistenceBase] = None


def get_persistence() -> VerbPersistenceBase:
    """
    Get the global persistence instance.
    
    Uses SQLite by default for better performance and features.
    To use JSON instead, set environment variable: USE_JSON_PERSISTENCE=true
    
    Returns:
        A VerbPersistenceBase implementation (SQLite or JSON)
    """
    global _persistence_instance
    
    if _persistence_instance is None:
        import os
        
        if os.getenv('USE_JSON_PERSISTENCE', 'false').lower() == 'true':
            logger.info("Using JSON persistence for verbs")
            _persistence_instance = JSONPersistence()
        else:
            logger.info("Using SQLite persistence for verbs")
            _persistence_instance = SQLitePersistence()
    
    return _persistence_instance


def initialize_persistence(use_json: bool = False) -> VerbPersistenceBase:
    """
    Initialize the persistence layer.
    
    Args:
        use_json: If True, use JSON persistence. Otherwise use SQLite.
        
    Returns:
        The initialized persistence instance
    """
    global _persistence_instance
    
    if use_json:
        _persistence_instance = JSONPersistence()
    else:
        _persistence_instance = SQLitePersistence()
    
    return _persistence_instance
