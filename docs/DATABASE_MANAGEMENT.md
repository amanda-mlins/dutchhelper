# Database Cleanup and Update Methods

## New Methods Added to `verb_database_manager.py`

### 1. `cleanup_verb_data()` - Database Validation and Cleanup

**Purpose:** Clean up and validate the verb database to maintain data integrity.

**Functionality:**

- Removes duplicate entries (keeps the most recent version)
- Validates all entries have required fields
- Removes entries with missing critical conjugation data
- Removes verbs with empty English translations
- Fixes case-sensitivity issues in infinitive forms
- Defragments the database by rebuilding it without invalid entries

**Usage:**

```python
from app.verb_database_manager import VerbDatabaseManager

result = VerbDatabaseManager.cleanup_verb_data()
```

**Returns:**

```python
{
    'removed_count': 0,           # Number of invalid entries removed
    'fixed_count': 0,             # Number of entries with minor fixes applied
    'validated_count': 150,       # Number of entries that passed validation
    'total_remaining': 150,       # Total verbs in database after cleanup
    'cleanup_performed': False    # Whether any cleanup was actually needed
}
```

**When to Use:**

- Periodically to maintain database quality
- After bulk imports from external sources
- To remove malformed entries from development/testing
- As part of database maintenance routine

---

### 2. `update_verb()` - Update Existing Verb Data

**Purpose:** Update an existing verb's conjugation data in the database.

**Usage:**

```python
from app.verb_database_manager import VerbDatabaseManager

conjugation_data = {
    'infinitive': 'eten',
    'english_translation': 'to eat',
    'verb_type': 'irregular',
    'separable': 'no',
    'synonyms': ['consumeren'],
    'present': {
        'ik': 'eet',
        'jij': 'eet',
        'hij/zij/het': 'eet',
        'wij': 'eten',
        'jullie': 'eten',
        'zij': 'eten'
    },
    'preterite': {
        'ik': 'at',
        'jij': 'at',
        'hij/zij/het': 'at',
        'wij': 'aten',
        'jullie': 'aten',
        'zij': 'aten'
    },
    'perfect': {
        'ik': 'heb gegeten',
        'jij': 'hebt gegeten',
        'hij/zij/het': 'heeft gegeten',
        'wij': 'hebben gegeten',
        'jullie': 'hebben gegeten',
        'zij': 'hebben gegeten'
    }
}

success = VerbDatabaseManager.update_verb('eten', conjugation_data)
```

**Parameters:**

- `infinitive` (str): The verb's infinitive form to update (e.g., 'eten', 'lopen')
- `conjugation_data` (Dict[str, Any]): Updated conjugation information

**Returns:**

- `True` if update was successful
- `False` if update failed (verb doesn't exist, missing required fields, or error occurred)

**Required Fields in `conjugation_data`:**

- `english_translation` (str): English meaning of the verb (cannot be empty)
- `infinitive` (str): Will be set automatically if not provided

**Optional Fields:**

- `verb_type` (str): 'regular', 'irregular', or 'modal'
- `separable` (str): 'yes' or 'no' - whether verb is separable
- `separation` (str): How the verb separates (e.g., "mee + nemen")
- `preposition` (str): Associated preposition if applicable
- `synonyms` (list): Array of synonym verbs
- `antonyms` (list): Array of antonym verbs
- `present` (dict): Present tense conjugations by pronoun
- `preterite` (dict): Preterite/past tense conjugations
- `perfect` (dict): Perfect tense conjugations
- `future` (dict): Future tense conjugations
- `conditional` (dict): Conditional conjugations
- Any other conjugation tenses

**When to Use:**

- Correcting incorrect conjugations
- Adding new metadata (separable status, synonyms, antonyms)
- Updating English translations
- Enriching verb data after LLM generation

**Logging:**

- ✓ Successful updates: INFO level logged
- ✗ Failed updates: WARNING/ERROR level logged
- ✗ Non-existent verb: WARNING level logged
- ✗ Missing translation: ERROR level logged

---

## Integration Examples

### Admin API Endpoints

These methods can be exposed through FastAPI endpoints for admin use:

```python
from fastapi import APIRouter, HTTPException
from app.verb_database_manager import VerbDatabaseManager

admin_router = APIRouter()

@admin_router.post("/api/admin/cleanup")
async def cleanup_database():
    """Cleanup and validate the database"""
    try:
        result = VerbDatabaseManager.cleanup_verb_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.put("/api/admin/verbs/{infinitive}")
async def update_verb_endpoint(infinitive: str, data: dict):
    """Update a verb's conjugation data"""
    success = VerbDatabaseManager.update_verb(infinitive, data)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to update {infinitive}")
    return {"status": "success", "infinitive": infinitive}

@admin_router.delete("/api/admin/verbs/{infinitive}")
async def delete_verb_endpoint(infinitive: str):
    """Delete a verb from the database"""
    success = VerbDatabaseManager.delete_verb(infinitive)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to delete {infinitive}")
    return {"status": "deleted", "infinitive": infinitive}
```

### Scheduled Maintenance

In a production environment, schedule cleanup periodically:

```python
# In your main app initialization
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def scheduled_cleanup():
    result = VerbDatabaseManager.cleanup_verb_data()
    logger.info(f"Scheduled cleanup: {result}")

# Run cleanup every week
scheduler.add_job(scheduled_cleanup, 'cron', day_of_week='sunday', hour=2)
scheduler.start()
```

### Direct Management Script

```bash
# Create an admin management script
python -c "
from app.verb_database_manager import VerbDatabaseManager
result = VerbDatabaseManager.cleanup_verb_data()
print(f'Cleanup: {result}')

stats = VerbDatabaseManager.get_database_stats()
print(f'Database now has {stats[\"total_verbs\"]} verbs')
"
```

---

## Data Integrity Notes

### Cleanup Safety

- **Non-destructive (mostly):** Cleanup only removes clearly invalid entries
- **Preserves quality data:** Valid conjugations are always kept
- **Single infinitive**: Duplicate entries keep only the most recently updated version
- **Rollback protection:** Backup database before running cleanup in production

### Update Validation

- **English translation required:** Updates fail if translation is missing or empty
- **Field preservation:** Existing fields not mentioned in update are preserved
- **Atomic operation:** Update either succeeds completely or fails completely
- **Timestamp updated:** `updated_at` is set to current time on successful update

### Examples of What Gets Removed

- ✗ Entries with malformed JSON
- ✗ Verbs with missing English translation
- ✗ Duplicate infinitive forms (keeps latest)
- ✗ Entries with missing 'infinitive' field

### Examples of What Gets Fixed

- ✓ Infinitive case-sensitivity (normalized to stored case)
- ✓ Minor data structure inconsistencies
- ✓ Missing but inferrable fields

---

## Performance Considerations

**`cleanup_verb_data()`:**

- Time: O(n) where n = number of verbs in database
- Memory: O(n) - loads all verbs into memory during cleanup
- I/O: Multiple database operations (SELECT, DELETE, INSERT)
- Best time to run: During low-traffic periods or scheduled maintenance windows

**`update_verb()`:**

- Time: O(1) - single verb update
- Memory: O(1) - minimal overhead
- I/O: Single persistence operation
- Can run anytime without performance impact

---

## Complete Code Example

```python
from app.verb_database_manager import VerbDatabaseManager

# Get current database state
stats_before = VerbDatabaseManager.get_database_stats()
print(f"Before cleanup: {stats_before['total_verbs']} verbs")

# Clean up the database
cleanup_result = VerbDatabaseManager.cleanup_verb_data()
print(f"Cleanup result: {cleanup_result}")

# Update a specific verb with richer metadata
new_data = {
    'infinitive': 'eten',
    'english_translation': 'to eat',
    'verb_type': 'irregular',
    'separable': 'no',
    'synonyms': ['consumeren', 'nuttigen'],
    'antonyms': [],
    'present': {
        'ik': 'eet',
        'jij': 'eet',
        'hij/zij/het': 'eet',
        'wij': 'eten',
        'jullie': 'eten',
        'zij': 'eten'
    }
}

update_success = VerbDatabaseManager.update_verb('eten', new_data)
print(f"Update success: {update_success}")

# Delete a verb from the database
delete_success = VerbDatabaseManager.delete_verb('loopen')
print(f"Delete success: {delete_success}")

# Check final database state
stats_after = VerbDatabaseManager.get_database_stats()
print(f"After operations: {stats_after['total_verbs']} verbs")
```
