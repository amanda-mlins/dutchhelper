"""
Unit tests for word bank functionality.

Coverage:
  - WordListService: add_word, get_words_for_user, update_word, delete_word
  - API routes: POST /word-bank/words, GET /word-bank/words,
                PUT /word-bank/words/{id}, DELETE /word-bank/words/{id},
                POST /word-bank/words/bulk, DELETE /word-bank/words/bulk

The test database is an in-memory SQLite instance created fresh for every test
function (function-scoped fixtures).  The LLM (OpenRouterService) is always
mocked so tests run offline and deterministically.
"""

import json
import sys
import os

# Ensure the backend root is on the path when running pytest from any cwd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, User, UserWord, UserWordCreate
from app.word_list_service import WordListService
from app.exceptions import ProcessingError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_LLM_DETAILS = {
    "valid": True,
    "word_type": "noun",
    "definition": "A round fruit.",
    "translation_en": "apple",
    "example": "Ik eet een appel.",
    "reason": None,
}


def make_engine():
    """
    Create a fresh in-memory SQLite engine.

    StaticPool is critical: it forces all connections (including those opened
    after a session.commit()) to reuse the *same* underlying connection, so the
    schema created by Base.metadata.create_all() remains visible for the whole
    test.  Without it, SQLite `:memory:` gives each new connection a blank DB.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


def make_session(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()


def make_user(db: object, user_id: int = 1, email: str = "test@example.com") -> User:
    """Insert a minimal User row and return it."""
    user = User(id=user_id, email=email, is_active=True, is_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_word(db: object, user_id: int, word: str = "appel", word_type: str = "noun") -> UserWord:
    """Insert a UserWord row directly (bypassing LLM) and return it."""
    uw = UserWord(user_id=user_id, word=word, word_type=word_type)
    uw.set_details(
        definition="A round fruit.",
        translation_en="apple",
        example="Ik eet een appel.",
    )
    db.add(uw)
    db.commit()
    db.refresh(uw)
    return uw


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    """Provide a fresh in-memory DB session for each test."""
    engine = make_engine()
    session = make_session(engine)
    yield session
    session.close()


@pytest.fixture()
def user(db):
    return make_user(db, user_id=1)


@pytest.fixture()
def other_user(db):
    return make_user(db, user_id=2, email="other@example.com")


@pytest.fixture()
def service(db):
    return WordListService(db)


# ---------------------------------------------------------------------------
# Patch helper — avoids repeating the full patch path everywhere
# ---------------------------------------------------------------------------

LLM_PATCH = "app.word_list_service.OpenRouterService.get_word_details"


# ===========================================================================
# WordListService — add_word
# ===========================================================================

class TestAddWord:
    """Tests for WordListService.add_word."""

    @pytest.mark.asyncio
    async def test_add_word_success(self, service, db, user):
        """A valid word is persisted and returned."""
        with patch(LLM_PATCH, new=AsyncMock(return_value=FAKE_LLM_DETAILS)):
            result = await service.add_word("appel", user_id=user.id)

        assert result.word == "appel"
        assert result.word_type == "noun"
        assert result.user_id == user.id
        details = result.get_details()
        assert details["translation_en"] == "apple"

    @pytest.mark.asyncio
    async def test_add_word_strips_and_lowercases(self, service, db, user):
        """Input is stripped of whitespace and lower-cased before saving."""
        with patch(LLM_PATCH, new=AsyncMock(return_value=FAKE_LLM_DETAILS)):
            result = await service.add_word("  APPEL  ", user_id=user.id)

        assert result.word == "appel"

    @pytest.mark.asyncio
    async def test_add_word_idempotent_returns_existing(self, service, db, user):
        """Adding the same word twice returns the existing row without an LLM call."""
        existing = make_word(db, user_id=user.id, word="appel")

        mock_llm = AsyncMock()
        with patch(LLM_PATCH, new=mock_llm):
            result = await service.add_word("appel", user_id=user.id)

        mock_llm.assert_not_called()
        assert result.id == existing.id

    @pytest.mark.asyncio
    async def test_add_word_invalid_raises_processing_error(self, service, db, user):
        """ProcessingError from the LLM bubbles up; nothing is persisted."""
        with patch(LLM_PATCH, new=AsyncMock(side_effect=ProcessingError("Not a Dutch word."))):
            with pytest.raises(ProcessingError, match="Not a Dutch word."):
                await service.add_word("xyzzy", user_id=user.id)

        # The DB must remain empty
        count = db.query(UserWord).filter_by(user_id=user.id).count()
        assert count == 0

    @pytest.mark.asyncio
    async def test_add_word_same_word_different_users(self, service, db, user, other_user):
        """The same word can be saved by two different users independently."""
        with patch(LLM_PATCH, new=AsyncMock(return_value=FAKE_LLM_DETAILS)):
            w1 = await service.add_word("appel", user_id=user.id)
            w2 = await service.add_word("appel", user_id=other_user.id)

        assert w1.id != w2.id
        assert w1.user_id == user.id
        assert w2.user_id == other_user.id

    @pytest.mark.asyncio
    async def test_add_word_persists_all_details(self, service, db, user):
        """All LLM detail fields (definition, translation_en, example) are saved."""
        llm_data = {
            **FAKE_LLM_DETAILS,
            "definition": "The most common Dutch tree.",
            "translation_en": "tree",
            "example": "De boom is groot.",
            "word_type": "noun",
        }
        with patch(LLM_PATCH, new=AsyncMock(return_value=llm_data)):
            result = await service.add_word("boom", user_id=user.id)

        d = result.get_details()
        assert d["definition"] == "The most common Dutch tree."
        assert d["translation_en"] == "tree"
        assert d["example"] == "De boom is groot."


# ===========================================================================
# WordListService — get_words_for_user
# ===========================================================================

class TestGetWordsForUser:
    """Tests for WordListService.get_words_for_user."""

    def test_returns_empty_list_for_new_user(self, service, db, user):
        assert service.get_words_for_user(user_id=user.id) == []

    def test_returns_only_current_users_words(self, service, db, user, other_user):
        """Words belonging to other users must not appear."""
        make_word(db, user_id=user.id, word="appel")
        make_word(db, user_id=other_user.id, word="boom")

        results = service.get_words_for_user(user_id=user.id)
        assert len(results) == 1
        assert results[0].word == "appel"

    def test_returns_multiple_words(self, service, db, user):
        make_word(db, user_id=user.id, word="appel")
        make_word(db, user_id=user.id, word="boom")
        make_word(db, user_id=user.id, word="fiets")

        results = service.get_words_for_user(user_id=user.id)
        assert len(results) == 3

    def test_results_ordered_newest_first(self, service, db, user):
        """Words are returned newest-first (created_at DESC)."""
        from datetime import datetime, timezone, timedelta

        base = datetime.now(timezone.utc)
        for i, word in enumerate(["appel", "boom", "fiets"]):
            uw = UserWord(
                user_id=user.id,
                word=word,
                word_type="noun",
                created_at=base + timedelta(seconds=i),
            )
            uw.set_details("", "", "")
            db.add(uw)
        db.commit()

        results = service.get_words_for_user(user_id=user.id)
        assert results[0].word == "fiets"
        assert results[-1].word == "appel"


# ===========================================================================
# WordListService — update_word
# ===========================================================================

class TestUpdateWord:
    """Tests for WordListService.update_word."""

    def test_update_word_success(self, service, db, user):
        word = make_word(db, user_id=user.id, word="appel")
        payload = UserWordCreate(word="peer")

        result = service.update_word(word.id, payload, user_id=user.id)

        assert result is not None
        assert result.word == "peer"

    def test_update_word_not_found_returns_none(self, service, db, user):
        result = service.update_word(9999, UserWordCreate(word="peer"), user_id=user.id)
        assert result is None

    def test_update_word_wrong_user_returns_none(self, service, db, user, other_user):
        """A user cannot update another user's word."""
        word = make_word(db, user_id=user.id, word="appel")
        result = service.update_word(word.id, UserWordCreate(word="peer"), user_id=other_user.id)
        assert result is None

    def test_update_word_persisted_in_db(self, service, db, user):
        word = make_word(db, user_id=user.id, word="appel")
        service.update_word(word.id, UserWordCreate(word="peer"), user_id=user.id)

        refreshed = db.query(UserWord).get(word.id)
        assert refreshed.word == "peer"


# ===========================================================================
# WordListService — delete_word
# ===========================================================================

class TestDeleteWord:
    """Tests for WordListService.delete_word."""

    def test_delete_word_success_returns_true(self, service, db, user):
        word = make_word(db, user_id=user.id, word="appel")
        result = service.delete_word(word.id, user_id=user.id)
        assert result is True

    def test_delete_word_removes_from_db(self, service, db, user):
        word = make_word(db, user_id=user.id, word="appel")
        service.delete_word(word.id, user_id=user.id)

        gone = db.query(UserWord).get(word.id)
        assert gone is None

    def test_delete_word_not_found_returns_false(self, service, db, user):
        result = service.delete_word(9999, user_id=user.id)
        assert result is False

    def test_delete_word_wrong_user_returns_false(self, service, db, user, other_user):
        """A user cannot delete another user's word."""
        word = make_word(db, user_id=user.id, word="appel")
        result = service.delete_word(word.id, user_id=other_user.id)
        assert result is False

    def test_delete_word_wrong_user_leaves_word_intact(self, service, db, user, other_user):
        """Failed delete attempt leaves the row untouched."""
        word = make_word(db, user_id=user.id, word="appel")
        service.delete_word(word.id, user_id=other_user.id)

        still_there = db.query(UserWord).get(word.id)
        assert still_there is not None

    def test_delete_word_only_removes_target(self, service, db, user):
        """Deleting one word does not affect other words of the same user."""
        w1 = make_word(db, user_id=user.id, word="appel")
        w2 = make_word(db, user_id=user.id, word="boom")

        service.delete_word(w1.id, user_id=user.id)

        remaining = service.get_words_for_user(user_id=user.id)
        assert len(remaining) == 1
        assert remaining[0].word == "boom"


# ===========================================================================
# API routes — HTTP-level tests via TestClient
# ===========================================================================

from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.auth_service import get_current_user


def _make_app_client(db_session, current_user_obj):
    """
    Return a TestClient with get_db and get_current_user overridden so that
    routes use the in-memory test database and a fake authenticated user.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: current_user_obj
    client = TestClient(app, raise_server_exceptions=False)
    return client


@pytest.fixture()
def api(db, user):
    """TestClient wired to the in-memory DB and authenticated as `user`."""
    client = _make_app_client(db, user)
    yield client, db, user
    app.dependency_overrides.clear()


class TestAddWordRoute:
    """POST /api/word-bank/words"""

    def test_add_word_201(self, api):
        client, db, user = api
        with patch(LLM_PATCH, new=AsyncMock(return_value=FAKE_LLM_DETAILS)):
            resp = client.post("/api/word-bank/words", json={"word": "appel"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["word"] == "appel"
        assert data["word_type"] == "noun"

    def test_add_word_invalid_returns_422(self, api):
        client, db, user = api
        with patch(LLM_PATCH, new=AsyncMock(side_effect=ProcessingError("Not a real Dutch word."))):
            resp = client.post("/api/word-bank/words", json={"word": "xyzzy"})
        assert resp.status_code == 422
        assert "Not a real Dutch word." in resp.json()["detail"]

    def test_add_word_duplicate_returns_existing(self, api):
        """Adding the same word twice returns 201 with the existing record."""
        client, db, user = api
        make_word(db, user_id=user.id, word="appel")

        mock_llm = AsyncMock()
        with patch(LLM_PATCH, new=mock_llm):
            resp = client.post("/api/word-bank/words", json={"word": "appel"})

        mock_llm.assert_not_called()
        assert resp.status_code == 201


class TestGetWordsRoute:
    """GET /api/word-bank/words"""

    def test_get_words_empty(self, api):
        client, db, user = api
        resp = client.get("/api/word-bank/words")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_words_returns_users_words(self, api):
        client, db, user = api
        make_word(db, user_id=user.id, word="appel")
        make_word(db, user_id=user.id, word="boom")

        resp = client.get("/api/word-bank/words")
        assert resp.status_code == 200
        words = [w["word"] for w in resp.json()]
        assert set(words) == {"appel", "boom"}


class TestUpdateWordRoute:
    """PUT /api/word-bank/words/{word_id}"""

    def test_update_word_200(self, api):
        client, db, user = api
        word = make_word(db, user_id=user.id, word="appel")

        resp = client.put(f"/api/word-bank/words/{word.id}", json={"word": "peer"})
        assert resp.status_code == 200
        assert resp.json()["word"] == "peer"

    def test_update_word_not_found_404(self, api):
        client, db, user = api
        resp = client.put("/api/word-bank/words/9999", json={"word": "peer"})
        assert resp.status_code == 404


class TestDeleteWordRoute:
    """DELETE /api/word-bank/words/{word_id}"""

    def test_delete_word_204(self, api):
        client, db, user = api
        word = make_word(db, user_id=user.id, word="appel")

        resp = client.delete(f"/api/word-bank/words/{word.id}")
        assert resp.status_code == 204

    def test_delete_word_not_found_404(self, api):
        client, db, user = api
        resp = client.delete("/api/word-bank/words/9999")
        assert resp.status_code == 404

    def test_delete_word_removes_from_db(self, api):
        client, db, user = api
        word = make_word(db, user_id=user.id, word="appel")
        client.delete(f"/api/word-bank/words/{word.id}")

        gone = db.query(UserWord).get(word.id)
        assert gone is None


class TestBulkAddRoute:
    """POST /api/word-bank/words/bulk"""

    def test_bulk_add_success(self, api):
        client, db, user = api
        with patch(LLM_PATCH, new=AsyncMock(return_value=FAKE_LLM_DETAILS)):
            resp = client.post("/api/word-bank/words/bulk", json={"words": ["appel", "boom"]})

        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["added"] == 2
        assert body["summary"]["errors"] == 0
        assert len(body["results"]) == 2

    def test_bulk_add_empty_list_returns_400(self, api):
        client, db, user = api
        resp = client.post("/api/word-bank/words/bulk", json={"words": []})
        assert resp.status_code == 400

    def test_bulk_add_whitespace_only_returns_400(self, api):
        client, db, user = api
        resp = client.post("/api/word-bank/words/bulk", json={"words": ["   ", "  "]})
        assert resp.status_code == 400

    def test_bulk_add_too_many_words_returns_400(self, api):
        client, db, user = api
        words = [f"word{i}" for i in range(101)]
        with patch(LLM_PATCH, new=AsyncMock(return_value=FAKE_LLM_DETAILS)):
            resp = client.post("/api/word-bank/words/bulk", json={"words": words})
        assert resp.status_code == 400

    def test_bulk_add_invalid_word_reported_as_error(self, api):
        """One invalid word among valid ones is reported as error, not 422."""
        client, db, user = api

        def side_effect(word):
            if word == "xyzzy":
                raise ProcessingError("Not a Dutch word.")
            return FAKE_LLM_DETAILS

        with patch(LLM_PATCH, new=AsyncMock(side_effect=side_effect)):
            resp = client.post(
                "/api/word-bank/words/bulk",
                json={"words": ["appel", "xyzzy"]},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["added"] == 1
        assert body["summary"]["errors"] == 1

        error_result = next(r for r in body["results"] if r["word"] == "xyzzy")
        assert error_result["status"] == "error"
        assert "Not a Dutch word." in error_result["error"]

    def test_bulk_add_deduplicates_input(self, api):
        """Duplicate words in the request are deduplicated before LLM calls."""
        client, db, user = api
        call_count = 0

        async def counting_llm(word):
            nonlocal call_count
            call_count += 1
            return FAKE_LLM_DETAILS

        with patch(LLM_PATCH, new=counting_llm):
            resp = client.post(
                "/api/word-bank/words/bulk",
                json={"words": ["appel", "APPEL", "appel"]},
            )

        assert resp.status_code == 200
        assert call_count == 1  # Only one unique word


class TestBulkDeleteRoute:
    """DELETE /api/word-bank/words/bulk"""

    def test_bulk_delete_success(self, api):
        client, db, user = api
        w1 = make_word(db, user_id=user.id, word="appel")
        w2 = make_word(db, user_id=user.id, word="boom")

        resp = client.request(
            "DELETE",
            "/api/word-bank/words/bulk",
            json={"word_ids": [w1.id, w2.id]},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 2

    def test_bulk_delete_removes_words_from_db(self, api):
        client, db, user = api
        w1 = make_word(db, user_id=user.id, word="appel")
        w2 = make_word(db, user_id=user.id, word="boom")

        client.request("DELETE", "/api/word-bank/words/bulk", json={"word_ids": [w1.id, w2.id]})

        remaining = db.query(UserWord).filter_by(user_id=user.id).all()
        assert remaining == []

    def test_bulk_delete_empty_list_returns_400(self, api):
        client, db, user = api
        resp = client.request("DELETE", "/api/word-bank/words/bulk", json={"word_ids": []})
        assert resp.status_code == 400

    def test_bulk_delete_ignores_other_users_words(self, api, other_user):
        """Attempting to delete another user's word is silently ignored."""
        client, db, user = api
        other_word = make_word(db, user_id=other_user.id, word="appel")

        resp = client.request(
            "DELETE",
            "/api/word-bank/words/bulk",
            json={"word_ids": [other_word.id]},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 0  # Nothing owned by `user` was deleted

        still_there = db.query(UserWord).get(other_word.id)
        assert still_there is not None

    def test_bulk_delete_partial_ownership(self, api, other_user):
        """Mix of owned and not-owned IDs — only owned ones are deleted."""
        client, db, user = api
        own_word = make_word(db, user_id=user.id, word="appel")
        other_word = make_word(db, user_id=other_user.id, word="boom")

        resp = client.request(
            "DELETE",
            "/api/word-bank/words/bulk",
            json={"word_ids": [own_word.id, other_word.id]},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 1

        assert db.query(UserWord).get(own_word.id) is None
        assert db.query(UserWord).get(other_word.id) is not None

    def test_bulk_delete_nonexistent_ids_returns_zero(self, api):
        client, db, user = api
        resp = client.request(
            "DELETE",
            "/api/word-bank/words/bulk",
            json={"word_ids": [9999, 8888]},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 0
