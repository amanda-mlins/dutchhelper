#!/usr/bin/env python
"""
Bootstrap script to populate the verb database from hardcoded verbs.

Run this once to seed the persistent database with all common verbs,
then the system will automatically add new verbs as they're queried.

Usage:
    cd backend
    python bootstrap_verbs.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.verb_persistence import get_persistence
from app.verb_conjugation_service import VerbConjugationService


async def bootstrap_verb_database():
    """Populate SQLite database with all hardcoded verbs"""
    
    persistence = get_persistence()
    
    # Get all verbs from the hardcoded database
    hardcoded_verbs = VerbConjugationService.VERB_DATABASE
    
    print(f"\n📚 Bootstrapping verb database with {len(hardcoded_verbs)} common verbs...\n")
    
    saved_count = 0
    existing_count = 0
    failed_count = 0
    
    for verb, conjugation in sorted(hardcoded_verbs.items()):
        if persistence.verb_exists(verb):
            existing_count += 1
            print(f"  ✓ {verb:20} (already in database)")
        else:
            try:
                if persistence.save_verb(verb, conjugation):
                    saved_count += 1
                    print(f"  ✅ {verb:20} (saved)")
                else:
                    failed_count += 1
                    print(f"  ❌ {verb:20} (save failed)")
            except Exception as e:
                failed_count += 1
                print(f"  ❌ {verb:20} (error: {e})")
    
    print(f"\n" + "="*60)
    print(f"Bootstrap complete!")
    print(f"="*60)
    print(f"  New verbs saved:    {saved_count}")
    print(f"  Already in DB:      {existing_count}")
    print(f"  Failed saves:       {failed_count}")
    print(f"  Total in database:  {saved_count + existing_count}")
    print(f"="*60 + "\n")
    
    # Show database statistics
    from app.verb_database_manager import VerbDatabaseManager
    stats = VerbDatabaseManager.get_database_stats()
    
    if 'database_size_mb' in stats:
        print(f"Database size: {stats.get('database_size_mb', 0):.2f} MB")
    print(f"Total verbs: {stats.get('total_verbs', saved_count + existing_count)}\n")


if __name__ == "__main__":
    print("\n🚀 DutchHelper Verb Database Bootstrap")
    print("=" * 60)
    
    try:
        asyncio.run(bootstrap_verb_database())
        print("✅ Bootstrap successful! Verb database is ready.\n")
    except Exception as e:
        print(f"\n❌ Bootstrap failed: {e}\n")
        sys.exit(1)
