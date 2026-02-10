"""Unit tests for CacheManager"""
import pytest
import time
from app.cache_service import CacheManager


class TestCacheManager:
    """Test suite for CacheManager class"""
    
    def setup_method(self):
        """Clear cache before each test"""
        CacheManager.clear()
    
    def test_set_and_get(self):
        """Test basic set and get operations"""
        key = "test_key"
        value = {"data": "test"}
        
        CacheManager.set(key, value)
        result = CacheManager.get(key)
        
        assert result == value
    
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist"""
        result = CacheManager.get("nonexistent")
        assert result is None
    
    def test_cache_expiration(self):
        """Test that cache entries expire after TTL"""
        key = "expire_test"
        value = "test_value"
        
        # Temporarily set TTL to 1 second
        original_ttl = CacheManager.TTL_SECONDS
        CacheManager.TTL_SECONDS = 1
        
        try:
            CacheManager.set(key, value)
            result = CacheManager.get(key)
            assert result == value
            
            # Wait for expiration
            time.sleep(1.1)
            result = CacheManager.get(key)
            assert result is None
        finally:
            CacheManager.TTL_SECONDS = original_ttl
    
    def test_generate_key(self):
        """Test cache key generation"""
        key1 = CacheManager.generate_key("conjugate", "zijn")
        key2 = CacheManager.generate_key("conjugate", "zijn")
        key3 = CacheManager.generate_key("conjugate", "gaan")
        
        # Same inputs should produce same key
        assert key1 == key2
        
        # Different inputs should produce different keys
        assert key1 != key3
        
        # Keys should be 32 characters (MD5 hex digest)
        assert len(key1) == 32
    
    def test_generate_key_with_multiple_args(self):
        """Test key generation with multiple arguments"""
        key = CacheManager.generate_key("prefix", "arg1", "arg2", "arg3")
        assert len(key) == 32
        assert isinstance(key, str)
    
    def test_cache_overwrite(self):
        """Test that setting a key again overwrites the old value"""
        key = "overwrite_test"
        
        CacheManager.set(key, "first_value")
        assert CacheManager.get(key) == "first_value"
        
        CacheManager.set(key, "second_value")
        assert CacheManager.get(key) == "second_value"
    
    def test_cache_different_types(self):
        """Test caching different data types"""
        # String
        CacheManager.set("str_key", "string_value")
        assert CacheManager.get("str_key") == "string_value"
        
        # Integer
        CacheManager.set("int_key", 42)
        assert CacheManager.get("int_key") == 42
        
        # List
        CacheManager.set("list_key", [1, 2, 3])
        assert CacheManager.get("list_key") == [1, 2, 3]
        
        # Dictionary
        data = {"nested": {"data": "value"}}
        CacheManager.set("dict_key", data)
        assert CacheManager.get("dict_key") == data
        
        # None
        CacheManager.set("none_key", None)
        assert CacheManager.get("none_key") is None
    
    def test_clear(self):
        """Test clearing the cache"""
        CacheManager.set("key1", "value1")
        CacheManager.set("key2", "value2")
        
        assert CacheManager.get("key1") == "value1"
        
        CacheManager.clear()
        
        assert CacheManager.get("key1") is None
        assert CacheManager.get("key2") is None
    
    def test_cache_stats(self):
        """Test getting cache statistics"""
        CacheManager.clear()
        
        # Add some entries
        CacheManager.set("key1", "value1")
        CacheManager.set("key2", "value2")
        CacheManager.set("key3", "value3")
        
        stats = CacheManager.get_stats()
        
        assert stats["item_count"] == 3
        assert stats["ttl_seconds"] == 3600
        assert "estimated_size_kb" in stats
        assert isinstance(stats["keys"], list)
    
    def test_cache_size_limit(self):
        """Test that cache can store multiple items"""
        CacheManager.clear()
        
        # Add items
        CacheManager.set("key1", "value1")
        CacheManager.set("key2", "value2")
        CacheManager.set("key3", "value3")
        
        stats = CacheManager.get_stats()
        
        assert stats["item_count"] == 3
        
        # Add more items
        CacheManager.set("key4", "value4")
        
        stats = CacheManager.get_stats()
        assert stats["item_count"] == 4
        assert CacheManager.get("key4") == "value4"
    
    def test_delete_expired_on_get(self):
        """Test that expired entries are deleted when accessed"""
        key = "delete_test"
        value = "test_value"
        
        original_ttl = CacheManager.TTL_SECONDS
        CacheManager.TTL_SECONDS = 1
        
        try:
            CacheManager.set(key, value)
            assert key in CacheManager._cache
            
            # Wait for expiration
            time.sleep(1.1)
            
            # Access should return None and delete the key
            result = CacheManager.get(key)
            assert result is None
            assert key not in CacheManager._cache
        finally:
            CacheManager.TTL_SECONDS = original_ttl
    
    def test_key_collision_resistance(self):
        """Test that similar keys produce different cache keys"""
        key1 = CacheManager.generate_key("conjugate", "sein")
        key2 = CacheManager.generate_key("conjugate", "se", "in")
        key3 = CacheManager.generate_key("conjugate", "s", "e", "i", "n")
        
        # All should be different despite similar structure
        assert key1 != key2
        assert key2 != key3
        assert key1 != key3


class TestCacheManagerIntegration:
    """Integration tests for cache usage patterns"""
    
    def setup_method(self):
        """Clear cache before each test"""
        CacheManager.clear()
    
    def test_verb_conjugation_cache_pattern(self):
        """Test typical verb conjugation caching pattern"""
        verb = "lopen"
        cache_key = CacheManager.generate_key("conjugate", verb)
        
        # Simulate LLM response
        llm_result = {
            "infinitive": "lopen",
            "englishTranslation": "to walk",
            "tenses": [{"dutchName": "Tegenwoordige Tijd", "forms": []}]
        }
        
        # Cache the result
        CacheManager.set(cache_key, llm_result)
        
        # Retrieve from cache
        cached_result = CacheManager.get(cache_key)
        assert cached_result == llm_result
    
    def test_sentence_analysis_cache_pattern(self):
        """Test typical sentence analysis caching pattern"""
        sentence = "De kat zit op de tafel"
        normalized = sentence.lower().strip()
        cache_key = CacheManager.generate_key("sentence", normalized)
        
        # Simulate analyzed result
        analysis = {
            "sentence": sentence,
            "sentence_translation": "The cat sits on the table",
            "components": [
                {"word": "De", "type": "article", "translation": "The"},
                {"word": "kat", "type": "noun", "translation": "cat"},
            ]
        }
        
        # Cache the result
        CacheManager.set(cache_key, analysis)
        
        # Retrieve from cache with normalized key
        cached_analysis = CacheManager.get(cache_key)
        assert cached_analysis == analysis
    
    def test_multiple_cache_prefixes(self):
        """Test using different cache prefixes"""
        verb_key = CacheManager.generate_key("conjugate", "zijn")
        sentence_key = CacheManager.generate_key("sentence", "De kat")
        batch_key = CacheManager.generate_key("batch", "zijn|gaan|doen")
        
        # All keys should be different
        assert verb_key != sentence_key
        assert sentence_key != batch_key
        assert batch_key != verb_key
        
        # Can store different data types with different prefixes
        CacheManager.set(verb_key, {"type": "verb"})
        CacheManager.set(sentence_key, {"type": "sentence"})
        CacheManager.set(batch_key, {"type": "batch"})
        
        assert CacheManager.get(verb_key)["type"] == "verb"
        assert CacheManager.get(sentence_key)["type"] == "sentence"
        assert CacheManager.get(batch_key)["type"] == "batch"


class TestCacheEdgeCases:
    """Test edge cases and error conditions"""
    
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
    
    def test_repeated_get_doesnt_modify_cache(self):
        """Test that getting a value multiple times doesn't affect it"""
        CacheManager.set("key", {"data": [1, 2, 3]})
        
        result1 = CacheManager.get("key")
        result2 = CacheManager.get("key")
        result3 = CacheManager.get("key")
        
        assert result1 == result2 == result3
        # Results should be equal
        assert result1 is result2  # Same object reference
    
    def test_cache_with_none_value_vs_missing_key(self):
        """Test distinction between None value and missing key"""
        # Set a key with None value
        CacheManager.set("none_value", None)
        
        # Get the None value
        result1 = CacheManager.get("none_value")
        
        # Get a missing key
        result2 = CacheManager.get("missing_key")
        
        # Both return None, but intention is different
        assert result1 is None
        assert result2 is None
        
        # Check if key exists in cache
        assert "none_value" in CacheManager._cache
        assert "missing_key" not in CacheManager._cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
