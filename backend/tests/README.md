# Backend Unit Tests

This directory contains comprehensive unit tests for the DutchHelper backend.

## Test Coverage

### `test_nlp_service.py`

Tests for the NLPService sentence splitting logic using pysbd. This is the **primary focus** since sentence boundary detection is critical.

**Key test areas:**

- Simple and multiple sentence splitting
- Dutch abbreviation handling (a.u.b., dr., drs., etc.)
- Edge cases (empty strings, whitespace, no trailing punctuation)
- Special punctuation (!?, ..., etc.)
- Unicode/diacritics support (café, naïef)
- Singleton pattern validation

**Notable tests:**

- `test_abbr_aub_dutch_please`: Ensures "a.u.b." (Dutch "please") doesn't cause false splits
- `test_realistic_dutch_paragraph`: Realistic multi-sentence Dutch text with multiple abbreviations

### `test_schemas.py`

Tests for Pydantic data validation and schema integrity.

**Schemas tested:**

- `Message`
- `SentenceComponent`
- `SentenceAnalysis`
- `TextAnalysisRequest`
- `AnalyzeSentenceRequest`
- `TextAnalysisResponse`

### `test_exceptions.py`

Tests for custom exception classes.

## Running Tests

### Run all tests

```bash
cd /Users/alins/dutchhelper/backend
pytest
```

### Run tests with verbose output

```bash
pytest -v
```

### Run only NLP service tests

```bash
pytest tests/test_nlp_service.py -v
```

### Run with coverage report

```bash
pytest --cov=app --cov-report=html
# Opens htmlcov/index.html in browser
```

### Run a specific test

```bash
pytest tests/test_nlp_service.py::TestNLPServiceSentenceSplitting::test_abbr_aub_dutch_please -v
```

## Test Results

All tests should pass with the current implementation. If you add new features:

1. Add corresponding unit tests
2. Run `pytest -v` to verify
3. Ensure coverage remains high (aim for >90%)

## Key Testing Principles

- **Isolation**: Each test is independent
- **Clarity**: Test names clearly describe what is being tested
- **Coverage**: Happy path, edge cases, and error conditions are tested
- **Speed**: Most tests run in milliseconds

## Continuous Integration

These tests can be integrated into CI/CD pipelines. Example GitHub Actions:

```yaml
- name: Run backend tests
  run: |
    cd backend
    pip install -r requirements.txt pytest pytest-asyncio
    pytest --cov=app
```
