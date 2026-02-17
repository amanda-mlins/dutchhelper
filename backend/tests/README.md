# Backend Unit Tests

Consolidated test suite for DutchHelper backend. All tests located in `/backend/tests/`.

## Test Summary

**Total: 172 tests** - All passing ✅

### Test Organization

#### Core NLP Tests (64 tests)
- **test_nlp_service.py** (27 tests): Sentence splitting with pysbd
  - Simple/multiple sentence splitting
  - Dutch abbreviation handling (a.u.b., dr., drs.)
  - Edge cases, unicode, singleton pattern

- **test_schemas.py** (28 tests): Pydantic validation
  - Message, SentenceComponent, SentenceAnalysis
  - TextAnalysisRequest, TextAnalysisResponse
  - AnalyzeSentenceRequest schema validation

- **test_exceptions.py** (9 tests): Custom exception classes
  - ValidationError, ProcessingError
  - Error message formatting

#### Optimization Tests (108 tests)
- **test_cache_service.py** (22 tests): Response caching
  - Basic operations, data types, expiration
  - Key generation, edge cases, integration patterns

- **test_deduplication.py** (19 tests): Sentence deduplication
  - Basic dedup, case-insensitive, order preservation
  - Whitespace handling, disabled behavior, real-world scenarios

- **test_logging_optimization.py** (12 tests): Logging configuration
  - Log level hierarchy, conditional logging
  - Performance verification at different levels

- **test_suite.py** (55 tests): Consolidated deduplicated suite
  - Organized cache, dedup, and logging tests in one file
  - Quick reference for all optimization features

## Running Tests

### All tests
```bash
cd /Users/alins/dutchhelper/backend
pytest tests/ -v
```

### Specific test file
```bash
pytest tests/test_suite.py -v           # Consolidated suite
pytest tests/test_nlp_service.py -v     # NLP tests only
pytest tests/test_cache_service.py -v   # Cache tests only
```

### Specific test class or method
```bash
pytest tests/test_suite.py::TestCacheBasicOperations -v
pytest tests/test_suite.py::TestCacheBasicOperations::test_set_and_get -v
```

### With coverage report
```bash
pytest tests/ --cov=app --cov-report=html
# Then open htmlcov/index.html
```

### Quick test (consolidated suite only)
```bash
pytest tests/test_suite.py -v  # ~2.4 seconds, 55 tests
```

### Full test suite
```bash
pytest tests/ -v  # ~5 seconds, 172 tests
```

## Test Files Reference

| File | Tests | Focus | Runtime |
|------|-------|-------|---------|
| test_nlp_service.py | 27 | NLP/sentence splitting | ~1s |
| test_schemas.py | 28 | Pydantic validation | ~0.5s |
| test_exceptions.py | 9 | Error handling | ~0.1s |
| test_cache_service.py | 22 | Response caching | ~1s |
| test_deduplication.py | 19 | Sentence dedup | ~0.5s |
| test_logging_optimization.py | 12 | Logging config | ~0.3s |
| test_suite.py | 55 | Consolidated suite | ~2.4s |
| **TOTAL** | **172** | **All features** | **~5s** |

## Key Testing Principles

- **Isolation**: Each test is independent with setup/teardown
- **Clarity**: Test names describe what is being tested
- **Coverage**: Happy path, edge cases, and error conditions
- **Speed**: All tests complete in ~5 seconds
- **Organization**: Tests grouped by feature/responsibility

## Pytest Configuration

Configuration is in `conftest.py`:
- Adds backend directory to Python path
- Session-scoped fixtures available to all tests
- Can add markers, hooks, or additional fixtures

## Performance Metrics

- Cache hits: **360x faster** than LLM calls
- Logging overhead: **5-10% reduction** at INFO level
- Deduplication: **5-10% improvement** for duplicate-heavy texts
- Full test suite: **~5 seconds** total execution

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run backend tests
  run: |
    cd backend
    python -m pytest tests/ -v --tb=short
```

### Coverage Threshold
Recommend maintaining >90% code coverage. Run:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Adding New Tests

1. Create test file in `/backend/tests/` with `test_` prefix
2. Follow naming: `test_<feature>.py` with `Test<Feature>` classes
3. Use descriptive test names: `test_<what_is_being_tested>`
4. Add docstrings to test classes and complex tests
5. Run `pytest` to verify before committing

## Troubleshooting

**Import errors?**
- Ensure conftest.py is in `/backend/tests/`
- Check sys.path manipulation in conftest.py
- Run from `/backend` directory: `cd backend && pytest`

**Tests failing unexpectedly?**
- Check if app dependencies are installed: `pip install -r requirements.txt`
- Clear pytest cache: `pytest --cache-clear tests/`
- Run with more verbosity: `pytest tests/ -vv`

**Slow tests?**
- Profile with: `pytest tests/ --durations=10`
- Consider using markers for slow tests
- Run fast tests first for quick feedback
