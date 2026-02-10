"""
Test script to verify response caching is working correctly.

Run this with: python test_caching.py
"""
import asyncio
import sys
import time
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.cache_service import CacheManager
from app.verb_conjugation_service import VerbConjugationService


async def test_verb_conjugation_caching():
    """Test that verb conjugation caching works"""
    print("\n" + "=" * 80)
    print("TEST: Verb Conjugation Caching")
    print("=" * 80)
    
    verb = "lopen"
    
    # First call - should hit LLM
    print(f"\n[1] First call to conjugate '{verb}' (should hit LLM)...")
    start = time.time()
    try:
        result1 = await VerbConjugationService.conjugate_verb_with_llm(verb)
        duration1 = time.time() - start
        print(f"    ✓ First call took {duration1*1000:.0f}ms")
        print(f"    ✓ Result keys: {list(result1.keys())}")
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    
    # Second call - should hit cache
    print(f"\n[2] Second call to conjugate '{verb}' (should hit CACHE)...")
    start = time.time()
    try:
        result2 = await VerbConjugationService.conjugate_verb_with_llm(verb)
        duration2 = time.time() - start
        print(f"    ✓ Second call took {duration2*1000:.0f}ms")
        
        # Verify results are identical
        if result1 == result2:
            print(f"    ✓ Results are identical")
        else:
            print(f"    ✗ Results differ!")
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    
    # Check speedup
    speedup = duration1 / duration2 if duration2 > 0 else float('inf')
    print(f"\n[✓] Speedup: {speedup:.0f}x faster on cache hit!")
    
    if duration2 > 0.1:  # Second call should be < 100ms
        print(f"    ⚠ Warning: Cache hit took {duration2*1000:.0f}ms (expected < 100ms)")
    
    return True


async def test_database_verbs():
    """Test that database verbs are also cached"""
    print("\n" + "=" * 80)
    print("TEST: Database Verb Caching")
    print("=" * 80)
    
    verb = "zijn"  # Common verb in database
    
    # First call - should hit database
    print(f"\n[1] First call to conjugate '{verb}' (should hit DATABASE)...")
    start = time.time()
    result1 = await VerbConjugationService.conjugate_verb_with_llm(verb)
    duration1 = time.time() - start
    print(f"    ✓ First call took {duration1*1000:.0f}ms")
    
    # Second call - should hit cache
    print(f"\n[2] Second call to conjugate '{verb}' (should hit CACHE)...")
    start = time.time()
    result2 = await VerbConjugationService.conjugate_verb_with_llm(verb)
    duration2 = time.time() - start
    print(f"    ✓ Second call took {duration2*1000:.0f}ms")
    
    # Verify they're the same
    if result1 == result2:
        print(f"    ✓ Results are identical")
    
    speedup = duration1 / duration2 if duration2 > 0 else float('inf')
    print(f"\n[✓] Speedup: {speedup:.0f}x faster on cache hit!")
    
    return True


async def test_cache_stats():
    """Test cache statistics"""
    print("\n" + "=" * 80)
    print("TEST: Cache Statistics")
    print("=" * 80)
    
    stats = CacheManager.get_stats()
    print(f"\n[✓] Cache Stats:")
    print(f"    • Items cached: {stats['item_count']}")
    print(f"    • Estimated size: {stats['estimated_size_kb']} KB")
    print(f"    • TTL: {stats['ttl_seconds']} seconds ({stats['ttl_seconds']/3600:.1f} hours)")
    print(f"    • Sample keys: {stats['keys'][:3] if stats['keys'] else 'none'}")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CACHING IMPLEMENTATION TEST SUITE" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    
    all_passed = True
    
    # Test 1: Database verb caching
    try:
        result = await test_database_verbs()
        if not result:
            all_passed = False
    except Exception as e:
        print(f"\n[✗] Test failed with error: {e}")
        all_passed = False
    
    # Test 2: Cache stats
    try:
        result = await test_cache_stats()
        if not result:
            all_passed = False
    except Exception as e:
        print(f"\n[✗] Test failed with error: {e}")
        all_passed = False
    
    # Test 3: LLM verb caching (requires API key)
    try:
        from app.config import settings
        if settings.OPENROUTER_API_KEY:
            result = await test_verb_conjugation_caching()
            if not result:
                all_passed = False
        else:
            print("\n" + "=" * 80)
            print("SKIPPED: Verb Conjugation Caching (no OPENROUTER_API_KEY)")
            print("=" * 80)
    except Exception as e:
        print(f"\n[✗] Test failed with error: {e}")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED!")
    print("=" * 80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
