"""Cache service for storing LLM responses and analysis results with TTL support"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Simple in-memory cache with Time-To-Live (TTL) support.
    
    Caches LLM responses and analysis results to avoid redundant API calls.
    Cached items expire after TTL_SECONDS (default 1 hour).
    
    Thread-safe for use with async/await and httpx.
    """
    
    # In-memory cache: {key: (value, timestamp)}
    _cache: Dict[str, tuple[Any, datetime]] = {}
    
    # Cache expiration time in seconds (1 hour)
    TTL_SECONDS = 3600
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """
        Get a cached value by key.
        
        Args:
            key: The cache key (usually a hash)
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        if key not in cls._cache:
            return None
        
        value, timestamp = cls._cache[key]
        
        # Check if cache entry has expired
        age = datetime.now() - timestamp
        if age > timedelta(seconds=cls.TTL_SECONDS):
            # Expired entry - remove it
            del cls._cache[key]
            logger.debug(f"[Cache] Expired entry removed: {key[:16]}...")
            return None
        
        logger.debug(f"[Cache] Hit for key: {key[:16]}... (age: {age.total_seconds():.1f}s)")
        return value
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """
        Store a value in the cache with current timestamp.
        
        Args:
            key: The cache key (usually a hash)
            value: The value to cache
        """
        cls._cache[key] = (value, datetime.now())
        logger.debug(f"[Cache] Stored key: {key[:16]}... (size: {len(cls._cache)} items)")
    
    @classmethod
    def generate_key(cls, prefix: str, *args) -> str:
        """
        Generate a cache key from a prefix and arguments.
        
        Uses MD5 hash for consistent, short keys.
        
        Args:
            prefix: A namespace prefix (e.g., "conjugate", "sentence")
            args: Arguments to include in the key
            
        Returns:
            A hash string for use as cache key
            
        Example:
            >>> key = CacheManager.generate_key("conjugate", "lopen")
            >>> # key will be something like: "4a5e9f2d1b3c..."
        """
        # Combine prefix and arguments into a single string
        data = f"{prefix}:{'|'.join(str(arg) for arg in args)}"
        
        # Hash it to get a short, consistent key
        hash_obj = hashlib.md5(data.encode())
        key = hash_obj.hexdigest()
        
        logger.debug(f"[Cache] Generated key '{key[:16]}...' for {prefix}({args})")
        return key
    
    @classmethod
    def clear(cls) -> None:
        """
        Clear all cached items.
        
        Useful for testing or cache invalidation.
        """
        count = len(cls._cache)
        cls._cache.clear()
        logger.info(f"[Cache] Cleared {count} cached items")
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        
        Returns:
            Dictionary with cache size, item count, and TTL
        """
        # Calculate total size in bytes (rough estimate)
        total_size = 0
        for value, _ in cls._cache.values():
            try:
                # Simple size estimation - might not be perfect
                if isinstance(value, dict):
                    total_size += len(str(value).encode())
                elif isinstance(value, list):
                    total_size += len(str(value).encode())
                else:
                    total_size += len(str(value).encode())
            except Exception:
                pass
        
        return {
            "item_count": len(cls._cache),
            "estimated_size_kb": round(total_size / 1024, 2),
            "ttl_seconds": cls.TTL_SECONDS,
            "keys": list(cls._cache.keys())[:10]  # First 10 keys for visibility
        }
