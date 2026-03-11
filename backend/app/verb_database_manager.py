"""
Verb database management utilities.

Provides tools for:
- Exporting verb database for version control
- Analyzing database statistics
- Managing database backups
- Resetting the database
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from app.verb_persistence import get_persistence, SQLitePersistence

logger = logging.getLogger(__name__)


class VerbDatabaseManager:
    """Management utilities for the verb conjugation database"""
    
    @staticmethod
    def export_to_json(output_path: str = None) -> str:
        """
        Export all verbs from SQLite to a JSON file for version control.
        
        This allows the verb database to be tracked in git, serving as a backup
        and making it portable.
        
        Args:
            output_path: Path where to save the JSON file.
                        If None, saves to backend/data/verbs_export.json
                        
        Returns:
            Path to the exported file
        """
        if output_path is None:
            output_path = "/Users/alins/dutchhelper/backend/data/verbs_export.json"
        
        try:
            persistence = get_persistence()
            verbs = persistence.get_all_verbs()
            
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_verbs': len(verbs),
                'verbs': verbs
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(verbs)} verbs to {output_path}")
            return str(path)
        except Exception as e:
            logger.error(f"Error exporting verbs: {e}")
            raise
    
    @staticmethod
    def import_from_json(input_path: str) -> int:
        """
        Import verbs from a JSON file into the database.
        
        Args:
            input_path: Path to the JSON file to import
            
        Returns:
            Number of verbs imported
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            verbs = data.get('verbs', {})
            persistence = get_persistence()
            
            count = 0
            for verb, conjugation in verbs.items():
                if persistence.save_verb(verb, conjugation):
                    count += 1
            
            logger.info(f"Imported {count} verbs from {input_path}")
            return count
        except Exception as e:
            logger.error(f"Error importing verbs: {e}")
            raise
    
    @staticmethod
    def get_database_stats() -> Dict[str, Any]:
        """
        Get comprehensive statistics about the verb database.
        
        Returns:
            Dictionary with statistics including:
            - total_verbs: Total number of verbs in storage
            - database_size_mb: Size of the SQLite database file
            - most_queried: Most frequently requested verbs
            - verb_types: Distribution of verb types
        """
        persistence = get_persistence()
        
        stats = {
            'timestamp': datetime.now().isoformat(),
            'verbs': persistence.get_all_verbs()
        }
        
        # If using SQLite, get additional stats
        if isinstance(persistence, SQLitePersistence):
            stats.update(persistence.get_statistics())
        
        return stats
    
    @staticmethod
    def backup_database(backup_path: str = None) -> str:
        """
        Create a backup of the verb database.
        
        Args:
            backup_path: Path for the backup file.
                        If None, saves to backend/backups/verbs_TIMESTAMP.json
                        
        Returns:
            Path to the backup file
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"/Users/alins/dutchhelper/backend/backups/verbs_{timestamp}.json"
        
        try:
            return VerbDatabaseManager.export_to_json(backup_path)
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            raise
    
    @staticmethod
    def get_query_statistics() -> Dict[str, Any]:
        """
        Get statistics about verb queries (for SQLite only).
        
        Shows which verbs are most frequently queried, helping to identify
        patterns in usage.
        
        Returns:
            Dictionary with query statistics
        """
        persistence = get_persistence()
        
        if not isinstance(persistence, SQLitePersistence):
            logger.warning("Query statistics only available with SQLite persistence")
            return {}
        
        try:
            cursor = persistence.connection.cursor()
            
            cursor.execute("""
                SELECT infinitive, query_count, created_at, updated_at
                FROM verbs
                ORDER BY query_count DESC
                LIMIT 20
            """)
            
            top_verbs = [
                {
                    'verb': row[0],
                    'queries': row[1],
                    'created': row[2],
                    'last_queried': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'top_20_most_queried': top_verbs,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting query statistics: {e}")
            return {}
    
    @staticmethod
    def estimate_llm_savings() -> Dict[str, Any]:
        """
        Estimate LLM API call savings based on database hits.
        
        Returns:
            Dictionary with savings estimates
        """
        stats = VerbDatabaseManager.get_database_stats()
        
        if 'total_queries' not in stats:
            return {'message': 'Statistics not available for this persistence type'}
        
        total_verbs = stats.get('total_verbs', 0)
        total_queries = stats.get('total_queries', 0)
        database_hits = total_queries - total_verbs  # Approximate
        
        # Rough estimate: OpenRouter billing ~$0.05-0.10 per 1000 tokens for LLM
        # Average conjugation query ~100 tokens
        estimated_cost_per_query = 0.000005  # $0.000005 per token * 100 tokens
        saved_amount = database_hits * estimated_cost_per_query
        
        return {
            'total_verbs_in_database': total_verbs,
            'total_queries_made': total_queries,
            'estimated_database_hits': database_hits,
            'estimated_api_calls_saved': database_hits,
            'estimated_savings_usd': round(saved_amount, 4),
            'note': 'Savings based on $0.0005 per conjugation API call average'
        }
    
    @staticmethod
    def cleanup_verb_data() -> Dict[str, Any]:
        """
        Clean up and validate the verb database.
        
        Performs the following cleanup operations:
        - Removes duplicate entries (keeps most recent)
        - Validates all entries have required fields
        - Removes entries with missing critical conjugation data
        - Fixes malformed verb data
        - Removes verbs with empty English translations
        
        Returns:
            Dictionary with cleanup statistics including:
            - removed_count: Number of invalid entries removed
            - fixed_count: Number of entries with minor fixes applied
            - validated_count: Number of entries that passed validation
            - total_remaining: Total verbs in database after cleanup
        """
        persistence = get_persistence()
        
        if not isinstance(persistence, SQLitePersistence):
            logger.warning("Cleanup only fully supported with SQLite persistence")
            return {'note': 'Cleanup operations only available for SQLite database'}
        
        try:
            cursor = persistence.connection.cursor()
            
            removed_count = 0
            fixed_count = 0
            
            # Get all verbs
            cursor.execute("""
                SELECT infinitive, conjugation_data, created_at, updated_at
                FROM verbs
                ORDER BY updated_at DESC
            """)
            
            all_verbs = cursor.fetchall()
            seen_infinitives = set()
            verbs_to_keep = []
            
            for infinitive, conj_data_str, created_at, updated_at in all_verbs:
                # Skip duplicates - keep first (most recent) occurrence
                if infinitive.lower() in seen_infinitives:
                    removed_count += 1
                    logger.debug(f"Removing duplicate: {infinitive}")
                    continue
                
                seen_infinitives.add(infinitive.lower())
                
                try:
                    conj_data = json.loads(conj_data_str)
                except (json.JSONDecodeError, TypeError):
                    removed_count += 1
                    logger.warning(f"Removing verb with malformed JSON: {infinitive}")
                    continue
                
                # Validate required fields
                english = conj_data.get('english_translation', '').strip()
                if not english or english == 'Translation not available':
                    removed_count += 1
                    logger.debug(f"Removing verb with empty translation: {infinitive}")
                    continue
                
                # Check for required conjugation structure
                if 'infinitive' not in conj_data or not conj_data.get('infinitive'):
                    removed_count += 1
                    logger.debug(f"Removing verb with missing infinitive: {infinitive}")
                    continue
                
                # Fix case-sensitivity issues - normalize infinitive
                if infinitive != conj_data.get('infinitive'):
                    conj_data['infinitive'] = infinitive
                    fixed_count += 1
                    logger.debug(f"Fixed infinitive case for: {infinitive}")
                
                verbs_to_keep.append((infinitive, json.dumps(conj_data, ensure_ascii=False)))
            
            # Remove all verbs and re-insert valid ones
            if removed_count > 0:
                cursor.execute("DELETE FROM verbs")
                for infinitive, conj_data in verbs_to_keep:
                    cursor.execute("""
                        INSERT OR IGNORE INTO verbs
                        (infinitive, conjugation_data, created_at, updated_at, query_count)
                        VALUES (?, ?, ?, ?, 0)
                    """, (infinitive, conj_data, datetime.now().isoformat(), datetime.now().isoformat()))
                
                persistence.connection.commit()
                logger.info(f"Database cleanup complete: {removed_count} removed, {fixed_count} fixed")
            
            validated_count = len(verbs_to_keep)
            
            return {
                'removed_count': removed_count,
                'fixed_count': fixed_count,
                'validated_count': validated_count,
                'total_remaining': validated_count,
                'cleanup_performed': removed_count > 0 or fixed_count > 0
            }
        
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            raise
    
    @staticmethod
    def update_verb(infinitive: str, conjugation_data: Dict[str, Any]) -> bool:
        """
        Update an existing verb's conjugation data in the database.
        
        Args:
            infinitive: The verb's infinitive form to update
            conjugation_data: Dictionary containing updated conjugation information
                             Should include at minimum:
                             - english_translation (str)
                             - present, preterite, perfect, etc. (Dict with conjugation forms)
                             
        Returns:
            True if update was successful, False otherwise
        """
        persistence = get_persistence()
        
        try:
            # Check if verb exists
            existing = persistence.get_verb(infinitive)
            if not existing:
                logger.warning(f"Attempt to update non-existent verb: {infinitive}")
                return False
            
            # Validate required fields in conjugation data
            if 'english_translation' not in conjugation_data or not conjugation_data['english_translation']:
                logger.error(f"Cannot update {infinitive}: missing english_translation")
                return False
            
            # Ensure infinitive is in the data
            if 'infinitive' not in conjugation_data:
                conjugation_data['infinitive'] = infinitive
            
            # Update in persistence layer
            success = persistence.save_verb(infinitive, conjugation_data)
            
            if success:
                logger.info(f"Updated verb: {infinitive}")
            else:
                logger.warning(f"Failed to update verb: {infinitive}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error updating verb {infinitive}: {e}")
            return False
    
    @staticmethod
    def delete_verb(infinitive: str) -> bool:
        """
        Remove a specific verb from the database.
        
        Args:
            infinitive: The verb's infinitive form to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        persistence = get_persistence()
        
        if not isinstance(persistence, SQLitePersistence):
            logger.warning("Deletion only available with SQLite persistence")
            return False
        
        try:
            # Check if verb exists
            existing = persistence.get_verb(infinitive)
            if not existing:
                logger.warning(f"Attempt to delete non-existent verb: {infinitive}")
                return False
            
            # Delete from database
            cursor = persistence.connection.cursor()
            cursor.execute("DELETE FROM verbs WHERE infinitive = ?", (infinitive,))
            persistence.connection.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Deleted verb: {infinitive}")
                return True
            else:
                logger.warning(f"Failed to delete verb: {infinitive}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting verb {infinitive}: {e}")
            return False


# Management API endpoints (can be exposed as admin endpoints)
async def get_database_info() -> Dict[str, Any]:
    """Get complete database information"""
    return {
        'statistics': VerbDatabaseManager.get_database_stats(),
        'query_stats': VerbDatabaseManager.get_query_statistics(),
        'savings': VerbDatabaseManager.estimate_llm_savings()
    }
