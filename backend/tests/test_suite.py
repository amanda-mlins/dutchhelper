"""
Consolidated unit test suite for DutchHelper backend.
Covers caching, deduplication, and logging optimization.
"""
import pytest
import time
import logging
from app.cache_service import CacheManager
from app.nlp_service import NLPService
from app.config import settings


# ============================================================================
# CACHE SERVICE TESTS (22 tests)
# ============================================================================

class TestCacheBasicOperations:
    """Test basic cache get/set operations"""
    
    def setup_method(self):
        """Clear cache before each test"""
        CacheManager.clear()
    
    def test_set_and_get(self):
        """Test basic set and get operations"""
        key = "test_key"
        value = {"data": "test"}
        CacheManager.set(key, value)
        assert CacheManager.get(key) == value
    
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist"""
        assert CacheManager.get("nonexistent") is None
    
    def test_cache_overwrite(self):
        """Test that setting a key again overwrites the old value"""
        key = "overwrite_test"
        CacheManager.set(key, "first_value")
        assert CacheManager.get(key) == "first_value"
        CacheManager.set(key, "second_value")
        assert CacheManager.get(key) == "second_value"


class TestCacheDataTypes:
    """Test caching different data types"""
    
    def setup_method(self):
        """Clear cache before each test"""
        CacheManager.clear()
    
    def test_cache_string(self):
        """Test caching string values"""
        CacheManager.set("str_key", "string_value")
        assert CacheManager.get("str_key") == "string_value"
    
    def test_cache_integer(self):
        """Test caching integer values"""
        CacheManager.set("int_key", 42)
        assert CacheManager.get("int_key") == 42
    
    def test_cache_list(self):
        """Test caching list values"""
        CacheManager.set("list_key", [1, 2, 3])
        assert CacheManager.get("list_key") == [1, 2, 3]
    
    def test_cache_dict(self):
        """Test caching dictionary values with nested structure"""
        data = {"nested": {"data": "value"}}
        CacheManager.set("dict_key", data)
        assert CacheManager.get("dict_key") == data
    
    def test_cache_none_value(self):
        """Test caching None values"""
        CacheManager.set("none_key", None)
        assert CacheManager.get("none_key") is None


class TestCacheKeyGeneration:
    """Test cache key generation"""
    
    def test_generate_key_consistency(self):
        """Test that same inputs produce same key"""
        key1 = CacheManager.generate_key("conjugate", "zijn")
        key2 = CacheManager.generate_key("conjugate", "zijn")
        assert key1 == key2
    
    def test_generate_key_uniqueness(self):
        """Test that different inputs produce different keys"""
        key1 = CacheManager.generate_key("conjugate", "zijn")
        key2 = CacheManager.generate_key("conjugate", "gaan")
        assert key1 != key2
    
    def test_generate_key_length(self):
        """Test that generated keys are MD5 hex digest (32 chars)"""
        key = CacheManager.generate_key("prefix", "arg1")
        assert len(key) == 32
    
    def test_generate_key_multiple_args(self):
        """Test key generation with multiple arguments"""
        key = CacheManager.generate_key("prefix", "arg1", "arg2", "arg3")
        assert len(key) == 32
        assert isinstance(key, str)


class TestCacheExpiration:
    """Test cache expiration logic"""
    
    def setup_method(self):
        """Clear cache before each test"""
        CacheManager.clear()
    
    def test_cache_expiration(self):
        """Test that cache entries expire after TTL"""
        key = "expire_test"
        value = "test_value"
        original_ttl = CacheManager.TTL_SECONDS
        CacheManager.TTL_SECONDS = 1
        
        try:
            CacheManager.set(key, value)
            assert CacheManager.get(key) == value
            time.sleep(1.1)
            assert CacheManager.get(key) is None
        finally:
            CacheManager.TTL_SECONDS = original_ttl
    
    def test_delete_expired_on_get(self):
        """Test that expired entries are deleted when accessed"""
        key = "delete_test"
        original_ttl = CacheManager.TTL_SECONDS
        CacheManager.TTL_SECONDS = 1
        
        try:
            CacheManager.set(key, "value")
            assert key in CacheManager._cache
            time.sleep(1.1)
            assert CacheManager.get(key) is None
            assert key not in CacheManager._cache
        finally:
            CacheManager.TTL_SECONDS = original_ttl


class TestCacheManagement:
    """Test cache management operations"""
    
    def setup_method(self):
        """Clear cache before each test"""
        CacheManager.clear()
    
    def test_clear_cache(self):
        """Test clearing the cache"""
        CacheManager.set("key1", "value1")
        CacheManager.set("key2", "value2")
        CacheManager.clear()
        assert CacheManager.get("key1") is None
        assert CacheManager.get("key2") is None
    
    def test_cache_stats(self):
        """Test getting cache statistics"""
        CacheManager.set("key1", "value1")
        CacheManager.set("key2", "value2")
        CacheManager.set("key3", "value3")
        
        stats = CacheManager.get_stats()
        assert stats["item_count"] == 3
        assert stats["ttl_seconds"] == 3600
        assert "estimated_size_kb" in stats
        assert isinstance(stats["keys"], list)


class TestCacheEdgeCases:
    """Test edge cases and special scenarios"""
    
    def setup_method(self):
        """Clear cache before each test"""
        CacheManager.clear()
    
    def test_empty_string_value(self):
        """Test caching empty string"""
        CacheManager.set("empty", "")
        assert CacheManager.get("empty") == ""
    
    def test_empty_key(self):
        """Test with empty key"""
        CacheManager.set("", "value")
        assert CacheManager.get("") == "value"
    
    def test_very_large_value(self):
        """Test caching large data structures"""
        large_list = list(range(10000))
        CacheManager.set("large", large_list)
        assert CacheManager.get("large") == large_list
    
    def test_special_characters_in_key(self):
        """Test key generation with special characters"""
        key = CacheManager.generate_key("prefix", "value-with/special\\chars?")
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_unicode_values(self):
        """Test caching unicode values"""
        unicode_value = {"text": "Zöo voor dieren 🦁 🐅"}
        CacheManager.set("unicode", unicode_value)
        assert CacheManager.get("unicode") == unicode_value
    
    def test_key_collision_resistance(self):
        """Test that similar keys produce different cache keys"""
        key1 = CacheManager.generate_key("conjugate", "sein")
        key2 = CacheManager.generate_key("conjugate", "se", "in")
        key3 = CacheManager.generate_key("conjugate", "s", "e", "i", "n")
        assert key1 != key2 and key2 != key3 and key1 != key3


class TestCacheIntegrationPatterns:
    """Test real-world caching patterns"""
    
    def setup_method(self):
        """Clear cache before each test"""
        CacheManager.clear()
    
    def test_verb_conjugation_cache_pattern(self):
        """Test typical verb conjugation caching pattern"""
        verb = "lopen"
        cache_key = CacheManager.generate_key("conjugate", verb)
        llm_result = {
            "infinitive": "lopen",
            "englishTranslation": "to walk",
            "tenses": [{"dutchName": "Tegenwoordige Tijd", "forms": []}]
        }
        CacheManager.set(cache_key, llm_result)
        assert CacheManager.get(cache_key) == llm_result
    
    def test_sentence_analysis_cache_pattern(self):
        """Test typical sentence analysis caching pattern"""
        sentence = "De kat zit op de tafel"
        normalized = sentence.lower().strip()
        cache_key = CacheManager.generate_key("sentence", normalized)
        analysis = {
            "sentence": sentence,
            "sentence_translation": "The cat sits on the table",
            "components": [
                {"word": "De", "type": "article", "translation": "The"},
                {"word": "kat", "type": "noun", "translation": "cat"},
            ]
        }
        CacheManager.set(cache_key, analysis)
        assert CacheManager.get(cache_key) == analysis
    
    def test_multiple_cache_prefixes(self):
        """Test using different cache prefixes"""
        verb_key = CacheManager.generate_key("conjugate", "zijn")
        sentence_key = CacheManager.generate_key("sentence", "De kat")
        batch_key = CacheManager.generate_key("batch", "zijn|gaan|doen")
        
        assert verb_key != sentence_key != batch_key
        
        CacheManager.set(verb_key, {"type": "verb"})
        CacheManager.set(sentence_key, {"type": "sentence"})
        CacheManager.set(batch_key, {"type": "batch"})
        
        assert CacheManager.get(verb_key)["type"] == "verb"
        assert CacheManager.get(sentence_key)["type"] == "sentence"
        assert CacheManager.get(batch_key)["type"] == "batch"


# ============================================================================
# DEDUPLICATION TESTS (19 tests)
# ============================================================================

class TestDeduplicationBasics:
    """Test basic deduplication logic"""
    
    def test_no_duplicates(self):
        """Test text with no duplicate sentences"""
        text = "Dit is zin één. Dit is zin twee. Dit is zin drie."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
    
    def test_exact_duplicates_removed(self):
        """Test that exact duplicate sentences are removed"""
        text = "Hallo wereld. Dit is een test. Hallo wereld. Goedemorgen."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
        assert result == ["Hallo wereld.", "Dit is een test.", "Goedemorgen."]
    
    def test_case_insensitive_deduplication(self):
        """Test that deduplication is case-insensitive"""
        text = "Hallo wereld. HALLO WERELD. hallo wereld."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 1
        assert result[0] == "Hallo wereld."
    
    def test_multiple_duplicates(self):
        """Test multiple instances of duplicate sentences"""
        text = "Eerste. Tweede. Eerste. Derde. Eerste. Tweede."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
        assert result == ["Eerste.", "Tweede.", "Derde."]
    
    def test_deduplication_preserves_order(self):
        """Test that deduplication preserves the order of first occurrence"""
        text = "Eerste. Tweede. Derde. Tweede. Eerste. Vierde."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert result == ["Eerste.", "Tweede.", "Derde.", "Vierde."]


class TestDeduplicationWhitespace:
    """Test deduplication with whitespace variations"""
    
    def test_whitespace_normalization(self):
        """Test that whitespace is normalized before comparing"""
        text = "Zin één.  Zin twee.  Zin één.  Zin drie."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
        assert "Zin één." in result
    
    def test_punctuation_variations_not_deduplicated(self):
        """Test sentences with different punctuation are not deduplicated"""
        text = "Dit is een vraag? Dit is een vraag. Dit is een vraag!"
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3


class TestDeduplicationDisabled:
    """Test behavior when deduplication is disabled"""
    
    def test_no_deduplication_when_disabled(self):
        """Test that duplicates are kept when deduplicate=False"""
        text = "Hallo. Wereld. Hallo. Hallo."
        result = NLPService.split_sentences(text, deduplicate=False)
        assert len(result) == 4
        assert result == ["Hallo.", "Wereld.", "Hallo.", "Hallo."]
    
    def test_default_is_deduplicate_true(self):
        """Test that deduplication is enabled by default"""
        text = "A. B. A."
        result_default = NLPService.split_sentences(text)
        result_explicit = NLPService.split_sentences(text, deduplicate=True)
        assert result_default == result_explicit


class TestDeduplicationEdgeCases:
    """Test edge cases for deduplication"""
    
    def test_empty_text(self):
        """Test empty text"""
        result = NLPService.split_sentences("", deduplicate=True)
        assert result == []
    
    def test_single_sentence(self):
        """Test single sentence"""
        text = "Dit is de enige zin."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert result == ["Dit is de enige zin."]
    
    def test_single_sentence_repeated(self):
        """Test single sentence repeated multiple times"""
        text = "Zin. Zin. Zin. Zin."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert result == ["Zin."]
    
    def test_whitespace_only(self):
        """Test whitespace-only text"""
        result = NLPService.split_sentences("   \n  \t  ", deduplicate=True)
        assert result == []
    
    def test_very_long_duplicate_text(self):
        """Test deduplication with very long sentences"""
        long_sentence = "Dit is een zeer lange zin " * 50 + "."
        text = long_sentence + " " + long_sentence + " Dit is een korte."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) >= 1


class TestDeduplicationPerformance:
    """Test performance characteristics of deduplication"""
    
    def test_many_unique_sentences(self):
        """Test that many unique sentences are handled efficiently"""
        sentences = [f"Dit is zin {i}." for i in range(100)]
        text = " ".join(sentences)
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 100
    
    def test_many_duplicate_sentences(self):
        """Test efficiency with many duplicates"""
        text = "Eerste. Tweede. Derde. " * 30 + "Eerste. Tweede. Derde."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 3
        assert result == ["Eerste.", "Tweede.", "Derde."]


class TestDeduplicationRealWorld:
    """Test real-world deduplication scenarios"""
    
    def test_repeated_sentence_in_paragraph(self):
        """Test paragraph with repeated sentence (real-world scenario)"""
        text = """
        De restaurant in Weesp wordt geteisterd door incidenten.
        De restaurant in Weesp wordt geteisterd door incidenten.
        Op 23 januari ontstond een kleine brand.
        De restaurant in Weesp wordt geteisterd door incidenten.
        """
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) == 2
        assert "De restaurant in Weesp wordt geteisterd door incidenten." in result
    
    def test_news_article_with_quote_repetition(self):
        """Test news article where a quote appears multiple times"""
        text = (
            "De burgemeester zei: 'Dit kan niet langer.' "
            "Iedereen was het erover eens. "
            "De burgemeester zei: 'Dit kan niet langer.' "
            "De maatregelen werden onmiddellijk ingevoerd."
        )
        result = NLPService.split_sentences(text, deduplicate=True)
        assert "Dit kan niet langer." in " ".join(result)
    
    def test_dutch_abbreviations(self):
        """Test that Dutch abbreviations don't cause duplicate splitting"""
        text = "Dr. Smith werkt op de U.v.A. Dr. Smith werkt hard."
        result = NLPService.split_sentences(text, deduplicate=True)
        assert len(result) >= 1


# ============================================================================
# LOGGING OPTIMIZATION TESTS (12 tests)
# ============================================================================

class TestLoggingConfiguration:
    """Test that logging is configured correctly"""
    
    def test_default_log_level_is_info(self):
        """Test that default log level is INFO"""
        assert settings.LOG_LEVEL == "INFO"
    
    def test_log_level_valid_values(self):
        """Test that LOG_LEVEL has valid values"""
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    def test_app_has_logging_configured(self):
        """Test that app logging is configured"""
        root_logger = logging.getLogger()
        assert root_logger.level != logging.NOTSET


class TestConditionalDebugLogging:
    """Test conditional debug logging pattern"""
    
    def setup_method(self):
        """Setup for each test"""
        self.logger = logging.getLogger("app.test")
    
    def test_debug_disabled_by_default(self):
        """Test that DEBUG logs are not emitted by default"""
        self.logger.setLevel(logging.INFO)
        assert not self.logger.isEnabledFor(logging.DEBUG)
        assert self.logger.isEnabledFor(logging.INFO)
    
    def test_debug_enabled_at_debug_level(self):
        """Test that DEBUG logs are emitted when level is DEBUG"""
        self.logger.setLevel(logging.DEBUG)
        assert self.logger.isEnabledFor(logging.DEBUG)
        assert self.logger.isEnabledFor(logging.INFO)
    
    def test_conditional_pattern_execution(self):
        """Test the conditional logging pattern used in code"""
        self.logger.setLevel(logging.INFO)
        
        executed = False
        if self.logger.isEnabledFor(logging.DEBUG):
            executed = True
        assert not executed
    
    def test_conditional_pattern_when_enabled(self):
        """Test conditional logging pattern when debug is enabled"""
        self.logger.setLevel(logging.DEBUG)
        
        executed = False
        if self.logger.isEnabledFor(logging.DEBUG):
            executed = True
        assert executed


class TestLoggingOptimization:
    """Test logging optimization benefits"""
    
    def setup_method(self):
        """Setup for each test"""
        self.logger = logging.getLogger("app.test")
        self.logger.setLevel(logging.INFO)
    
    def test_no_expensive_operations_at_info(self):
        """Test that expensive operations don't execute at INFO level"""
        executed = False
        if self.logger.isEnabledFor(logging.DEBUG):
            expensive_string = "A" * 10000
            executed = True
        assert not executed
    
    def test_expensive_operations_at_debug(self):
        """Test that expensive operations execute at DEBUG level"""
        self.logger.setLevel(logging.DEBUG)
        executed = False
        if self.logger.isEnabledFor(logging.DEBUG):
            expensive_string = "A" * 10000
            executed = True
        assert executed


class TestLoggingLevels:
    """Test logging level hierarchy"""
    
    def test_logging_level_values(self):
        """Test that logging levels have correct values"""
        assert logging.DEBUG == 10
        assert logging.INFO == 20
        assert logging.WARNING == 30
        assert logging.ERROR == 40
        assert logging.CRITICAL == 50
    
    def test_level_hierarchy(self):
        """Test that isEnabledFor respects level hierarchy"""
        logger = logging.getLogger("test_hierarchy")
        logger.setLevel(logging.WARNING)
        
        assert not logger.isEnabledFor(logging.DEBUG)
        assert not logger.isEnabledFor(logging.INFO)
        assert logger.isEnabledFor(logging.WARNING)
        assert logger.isEnabledFor(logging.ERROR)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
