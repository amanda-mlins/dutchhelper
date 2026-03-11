"""Verb conjugation service for Dutch verbs"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class VerbConjugationService:
    """Service for conjugating Dutch verbs.
    
    This service provides intelligent caching and persistence with LLM fallback:
    1. In-memory cache (fastest - instant responses for frequently used verbs)
    2. Persistent SQLite storage (growing database of all queried verbs)
    3. OpenRouter LLM (for new verbs - automatically saved to storage)
    
    Architecture:
    - Zero external database costs (uses local SQLite)
    - All new verbs automatically saved for future queries
    - Reduced LLM costs over time as database grows
    - No hardcoded database needed (learned from user queries)
    """
    
    @staticmethod
    def _is_valid_conjugation(conjugation_data: Dict[str, Any]) -> bool:
        """
        Validate conjugation data before storing in database.
        
        Checks for:
        - Required fields: infinitive, englishTranslation, tenses, examples
        - Tenses array has at least 6 items
        - Each tense has forms array with conjugations
        - Examples array has at least 1 example
        
        Args:
            conjugation_data: The conjugation data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(conjugation_data, dict):
            logger.warning("[VALIDATION] Conjugation data is not a dictionary")
            return False
        
        # Check required fields exist and are not None
        required_fields = ['infinitive', 'englishTranslation', 'tenses', 'examples']
        for field in required_fields:
            if field not in conjugation_data or conjugation_data[field] is None:
                logger.warning(f"[VALIDATION] Missing required field: {field}")
                return False
        
        # Validate tenses
        tenses = conjugation_data.get('tenses', [])
        if not isinstance(tenses, list) or len(tenses) < 6:
            logger.warning(f"[VALIDATION] Tenses should be array with at least 6 items, got {len(tenses) if isinstance(tenses, list) else 'non-array'}")
            return False
        
        # Validate each tense has forms
        for i, tense in enumerate(tenses):
            if not isinstance(tense, dict):
                logger.warning(f"[VALIDATION] Tense {i} is not a dictionary")
                return False
            
            forms = tense.get('forms', [])
            if not isinstance(forms, list) or len(forms) < 6:
                logger.warning(f"[VALIDATION] Tense {i} should have at least 6 forms, got {len(forms)}")
                return False
            
            # Validate each form has person and conjugation
            for j, form in enumerate(forms):
                if not isinstance(form, dict) or 'person' not in form or 'conjugation' not in form:
                    logger.warning(f"[VALIDATION] Tense {i} form {j} missing person or conjugation")
                    return False
        
        # Validate examples
        examples = conjugation_data.get('examples', [])
        if not isinstance(examples, list) or len(examples) < 1:
            logger.warning(f"[VALIDATION] Examples should be array with at least 1 item, got {len(examples)}")
            return False
        
        logger.debug("[VALIDATION] Conjugation data passed all validations")
        return True
    
    @staticmethod
    async def conjugate_verb_with_llm(verb: str) -> Dict[str, Any]:
        """
        Conjugate a Dutch verb with intelligent caching and persistence.
        
        Lookup order:
        1. Cache (if available and not expired)
        2. Persistent storage (SQLite - growing database of all queried verbs)
        3. OpenRouter LLM (for unknown verbs - automatically saved to persistent storage)
        
        This approach ensures:
        - Instant responses for frequently used verbs
        - Reduced LLM costs over time as the database grows
        - Zero external database costs (uses SQLite)
        - All new verbs are automatically saved for future queries
        
        Args:
            verb: The infinitive form of a Dutch verb
            
        Returns:
            Dictionary with conjugation data including tenses and examples
            
        Raises:
            ProcessingError: If all lookup methods and LLM generation fail
        """
        from app.cache_service import CacheManager
        from app.llm_service import OpenRouterService
        from app.exceptions import ProcessingError
        from app.verb_persistence import get_persistence
        
        verb_lower = verb.lower().strip()
        persistence = get_persistence()
        
        # Step 1: Check memory cache first (fastest)
        cache_key = CacheManager.generate_key("conjugate", verb_lower)
        cached_result = CacheManager.get(cache_key)
        if cached_result:
            logger.info(f"[CACHE HIT] Verb '{verb_lower}' found in memory cache")
            return cached_result
        
        # Step 2: Check persistent storage (SQLite) - growing database
        persistent_result = persistence.get_verb(verb_lower)
        if persistent_result:
            # Cache it for future requests
            CacheManager.set(cache_key, persistent_result)
            logger.info(f"[STORAGE HIT] Verb '{verb_lower}' found in persistent database")
            return persistent_result
        
        # Step 3: Fallback to LLM - this is a new verb
        logger.info(f"[LLM REQUIRED] Verb '{verb_lower}' not found in cache or storage, using LLM to generate conjugation")
        
        try:
            conjugation = await OpenRouterService.conjugate_dutch_verb(verb_lower)
            
            # Validate the conjugation response before storing
            if not VerbConjugationService._is_valid_conjugation(conjugation):
                logger.error(f"[LLM VALIDATION FAILED] Invalid conjugation data for '{verb_lower}': missing critical fields")
                raise ProcessingError(
                    f"Unable to generate conjugation for '{verb}'. Please try again or try a different verb."
                )
            
            # Save the new conjugation to persistent storage for future use
            persistence.save_verb(verb_lower, conjugation)
            logger.info(f"[LLM SUCCESS] Generated and persisted conjugation for '{verb_lower}'")
            logger.info(conjugation)
            
            # Cache the result
            CacheManager.set(cache_key, conjugation)
            
            return conjugation
        except ProcessingError:
            # Re-raise ProcessingError as-is (already has user-friendly message)
            raise
        except Exception as e:
            logger.error(f"[LLM FAILED] Failed to conjugate '{verb_lower}': {str(e)}")
            raise ProcessingError(
                f"I couldn't find or generate the conjugation for '{verb}'. Please check the spelling and try again."
            )
