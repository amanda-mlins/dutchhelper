"""
Unit tests for verb database and conjugation functionality.

Coverage:
  - SQLitePersistence: get_verb, save_verb, verb_exists, get_all_verbs (in-memory)
  - JSONPersistence:   get_verb, save_verb, verb_exists, get_all_verbs (tmp dir)
  - PostgresPersistence: save_verb, get_verb, verb_exists, get_all_verbs (mocked SQLAlchemy)
  - VerbConjugationService._is_valid_conjugation — all validation branches
  - VerbConjugationService.conjugate_verb_with_llm — cache hit, storage hit, LLM path,
    invalid LLM response (raises ProcessingError), generic LLM exception
  - VerbDatabaseManager: update_verb, delete_verb, cleanup_verb_data,
    export_to_json, import_from_json
  - POST /api/conjugate route — success, empty verb, ProcessingError, generic error

All external I/O (LLM, cache, persistent storage singleton) is mocked so the
tests run fully offline and deterministically.
"""

import json
import os
import sys
import tempfile

# Ensure the backend root is on the path when running pytest from any cwd
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

# ---------------------------------------------------------------------------
# Minimal conjugation data used across tests
# ---------------------------------------------------------------------------

def _make_conjugation(infinitive: str = "werken", translation: str = "to work") -> dict:
    """
    Return a conjugation dict that satisfies VerbConjugationService._is_valid_conjugation.
    Has 6 tenses, each with 6 forms, plus at least 1 example.
    """
    forms = [
        {"person": "ik", "conjugation": f"{infinitive}..."},
        {"person": "jij", "conjugation": f"{infinitive}..."},
        {"person": "hij/zij/het", "conjugation": f"{infinitive}..."},
        {"person": "wij", "conjugation": f"{infinitive}..."},
        {"person": "jullie", "conjugation": f"{infinitive}..."},
        {"person": "zij", "conjugation": f"{infinitive}..."},
    ]
    tenses = [
        {"dutchName": f"Tense {i}", "englishName": f"Tense {i}", "forms": forms}
        for i in range(6)
    ]
    return {
        "infinitive": infinitive,
        "englishTranslation": translation,
        "verbType": "regular",
        "tenses": tenses,
        "examples": [{"dutch": "Ik werk.", "english": "I work.", "tense": "present"}],
    }


# ===========================================================================
# 1. SQLitePersistence  (uses a real in-memory :memory: SQLite connection)
# ===========================================================================

class TestSQLitePersistence:
    """CRUD tests for the SQLite-backed persistence layer."""

    def _make_persistence(self):
        """Create a fresh SQLitePersistence instance backed by :memory:."""
        from app.verb_persistence import SQLitePersistence
        return SQLitePersistence(db_path=":memory:")

    # --- save_verb / get_verb ---

    def test_save_and_get_verb(self):
        p = self._make_persistence()
        conj = _make_conjugation("werken")
        assert p.save_verb("werken", conj) is True
        result = p.get_verb("werken")
        assert result is not None
        assert result["infinitive"] == "werken"
        assert result["englishTranslation"] == "to work"

    def test_get_nonexistent_verb_returns_none(self):
        p = self._make_persistence()
        assert p.get_verb("zingen") is None

    def test_save_normalises_to_lowercase(self):
        p = self._make_persistence()
        conj = _make_conjugation("Werken")
        p.save_verb("Werken", conj)
        # Should be retrievable as lowercase
        assert p.get_verb("werken") is not None

    def test_save_overwrites_existing_verb(self):
        p = self._make_persistence()
        conj1 = _make_conjugation("lopen", "to walk")
        conj2 = _make_conjugation("lopen", "to run")
        p.save_verb("lopen", conj1)
        p.save_verb("lopen", conj2)
        result = p.get_verb("lopen")
        assert result["englishTranslation"] == "to run"

    def test_get_verb_increments_query_count(self):
        p = self._make_persistence()
        conj = _make_conjugation("lezen")
        p.save_verb("lezen", conj)
        # First retrieval should succeed
        p.get_verb("lezen")
        # Confirm query_count was incremented in the DB
        cursor = p.connection.cursor()
        cursor.execute("SELECT query_count FROM verbs WHERE infinitive = 'lezen'")
        row = cursor.fetchone()
        assert row["query_count"] == 2  # starts at 1, incremented once

    # --- verb_exists ---

    def test_verb_exists_true(self):
        p = self._make_persistence()
        p.save_verb("zijn", _make_conjugation("zijn", "to be"))
        assert p.verb_exists("zijn") is True

    def test_verb_exists_false(self):
        p = self._make_persistence()
        assert p.verb_exists("hebben") is False

    def test_verb_exists_case_insensitive(self):
        p = self._make_persistence()
        p.save_verb("komen", _make_conjugation("komen"))
        assert p.verb_exists("KOMEN") is True

    # --- get_all_verbs ---

    def test_get_all_verbs_empty(self):
        p = self._make_persistence()
        assert p.get_all_verbs() == {}

    def test_get_all_verbs_returns_all(self):
        p = self._make_persistence()
        p.save_verb("werken", _make_conjugation("werken"))
        p.save_verb("lopen", _make_conjugation("lopen", "to walk"))
        all_verbs = p.get_all_verbs()
        assert set(all_verbs.keys()) == {"werken", "lopen"}

    def test_close_does_not_raise(self):
        p = self._make_persistence()
        p.close()  # Should not raise


# ===========================================================================
# 2. JSONPersistence  (uses a real temp directory)
# ===========================================================================

class TestJSONPersistence:
    """CRUD tests for the JSON file-backed persistence layer."""

    def _make_persistence(self, tmp_dir: str):
        from app.verb_persistence import JSONPersistence
        json_path = os.path.join(tmp_dir, "verbs_test.json")
        return JSONPersistence(json_path=json_path)

    def test_save_and_get_verb(self, tmp_path):
        p = self._make_persistence(str(tmp_path))
        conj = _make_conjugation("schrijven", "to write")
        assert p.save_verb("schrijven", conj) is True
        result = p.get_verb("schrijven")
        assert result is not None
        assert result["englishTranslation"] == "to write"

    def test_get_nonexistent_returns_none(self, tmp_path):
        p = self._make_persistence(str(tmp_path))
        assert p.get_verb("rennen") is None

    def test_save_is_case_insensitive(self, tmp_path):
        p = self._make_persistence(str(tmp_path))
        p.save_verb("Rijden", _make_conjugation("rijden"))
        assert p.get_verb("rijden") is not None

    def test_overwrite_existing(self, tmp_path):
        p = self._make_persistence(str(tmp_path))
        p.save_verb("vinden", _make_conjugation("vinden", "to find"))
        p.save_verb("vinden", _make_conjugation("vinden", "to discover"))
        assert p.get_verb("vinden")["englishTranslation"] == "to discover"

    def test_verb_exists_true(self, tmp_path):
        p = self._make_persistence(str(tmp_path))
        p.save_verb("gaan", _make_conjugation("gaan"))
        assert p.verb_exists("gaan") is True

    def test_verb_exists_false(self, tmp_path):
        p = self._make_persistence(str(tmp_path))
        assert p.verb_exists("staan") is False

    def test_get_all_verbs(self, tmp_path):
        p = self._make_persistence(str(tmp_path))
        p.save_verb("kijken", _make_conjugation("kijken"))
        p.save_verb("horen", _make_conjugation("horen"))
        all_verbs = p.get_all_verbs()
        assert "kijken" in all_verbs
        assert "horen" in all_verbs

    def test_data_persists_across_instances(self, tmp_path):
        """Data saved by one JSONPersistence instance should be readable by another."""
        from app.verb_persistence import JSONPersistence
        json_path = str(tmp_path / "shared.json")
        p1 = JSONPersistence(json_path=json_path)
        p1.save_verb("doen", _make_conjugation("doen"))

        p2 = JSONPersistence(json_path=json_path)
        assert p2.get_verb("doen") is not None

    def test_close_does_not_raise(self, tmp_path):
        p = self._make_persistence(str(tmp_path))
        p.close()  # Should not raise


# ===========================================================================
# 3. PostgresPersistence  (SQLAlchemy session fully mocked)
# ===========================================================================

class TestPostgresPersistence:
    """Unit tests for PostgresPersistence with mocked SQLAlchemy session."""

    def _make_persistence(self):
        from app.verb_persistence import PostgresPersistence
        return PostgresPersistence()

    def _make_mock_row(self, infinitive: str, conj: dict, query_count: int = 1):
        """Build a mock VerbConjugation ORM row."""
        row = MagicMock()
        row.infinitive = infinitive
        row.query_count = query_count
        row.conjugation_data = json.dumps(conj)
        return row

    def test_get_verb_found(self):
        """get_verb returns parsed conjugation data when the row exists."""
        p = self._make_persistence()
        conj = _make_conjugation("werken")
        mock_row = self._make_mock_row("werken", conj)

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_row

        with patch.object(p, "_session", return_value=mock_session):
            result = p.get_verb("werken")

        assert result is not None
        assert result["infinitive"] == "werken"

    def test_get_verb_not_found_returns_none(self):
        """get_verb returns None when no row is found."""
        p = self._make_persistence()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch.object(p, "_session", return_value=mock_session):
            result = p.get_verb("bestaan")

        assert result is None

    def test_save_verb_inserts_new_row(self):
        """save_verb creates a new row when the verb doesn't exist yet."""
        p = self._make_persistence()
        conj = _make_conjugation("lachen")

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch.object(p, "_session", return_value=mock_session):
            result = p.save_verb("lachen", conj)

        assert result is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_save_verb_updates_existing_row(self):
        """save_verb updates conjugation_data when the verb already exists."""
        p = self._make_persistence()
        conj = _make_conjugation("lachen")
        mock_row = self._make_mock_row("lachen", _make_conjugation("lachen", "to smile"))

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_row

        with patch.object(p, "_session", return_value=mock_session):
            result = p.save_verb("lachen", conj)

        assert result is True
        assert mock_row.conjugation_data == json.dumps(conj)

    def test_save_verb_returns_false_on_exception(self):
        """save_verb returns False and rolls back when an exception occurs."""
        p = self._make_persistence()
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("DB error")

        with patch.object(p, "_session", return_value=mock_session):
            result = p.save_verb("breken", _make_conjugation("breken"))

        assert result is False
        mock_session.rollback.assert_called_once()

    def test_verb_exists_true(self):
        p = self._make_persistence()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()

        with patch.object(p, "_session", return_value=mock_session):
            assert p.verb_exists("zijn") is True

    def test_verb_exists_false(self):
        p = self._make_persistence()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch.object(p, "_session", return_value=mock_session):
            assert p.verb_exists("zijn") is False

    def test_get_all_verbs_returns_dict(self):
        p = self._make_persistence()
        conj = _make_conjugation("lopen")
        row = MagicMock()
        row.infinitive = "lopen"
        row.conjugation_data = json.dumps(conj)
        mock_session = MagicMock()
        mock_session.query.return_value.order_by.return_value.all.return_value = [row]

        with patch.object(p, "_session", return_value=mock_session):
            result = p.get_all_verbs()

        assert "lopen" in result


# ===========================================================================
# 4. VerbConjugationService._is_valid_conjugation
# ===========================================================================

class TestIsValidConjugation:
    """Tests for the static validation method."""

    def _call(self, data):
        from app.verb_conjugation_service import VerbConjugationService
        return VerbConjugationService._is_valid_conjugation(data)

    def test_valid_conjugation_returns_true(self):
        assert self._call(_make_conjugation()) is True

    def test_non_dict_returns_false(self):
        assert self._call("not a dict") is False
        assert self._call(None) is False
        assert self._call(42) is False

    def test_missing_infinitive_returns_false(self):
        data = _make_conjugation()
        del data["infinitive"]
        assert self._call(data) is False

    def test_none_infinitive_returns_false(self):
        data = _make_conjugation()
        data["infinitive"] = None
        assert self._call(data) is False

    def test_missing_english_translation_returns_false(self):
        data = _make_conjugation()
        del data["englishTranslation"]
        assert self._call(data) is False

    def test_missing_tenses_returns_false(self):
        data = _make_conjugation()
        del data["tenses"]
        assert self._call(data) is False

    def test_fewer_than_6_tenses_returns_false(self):
        data = _make_conjugation()
        data["tenses"] = data["tenses"][:5]
        assert self._call(data) is False

    def test_tenses_not_a_list_returns_false(self):
        data = _make_conjugation()
        data["tenses"] = "not a list"
        assert self._call(data) is False

    def test_tense_not_dict_returns_false(self):
        data = _make_conjugation()
        data["tenses"][0] = "invalid tense"
        assert self._call(data) is False

    def test_tense_with_fewer_than_6_forms_returns_false(self):
        data = _make_conjugation()
        data["tenses"][0]["forms"] = data["tenses"][0]["forms"][:5]
        assert self._call(data) is False

    def test_form_missing_person_returns_false(self):
        data = _make_conjugation()
        data["tenses"][0]["forms"][0] = {"conjugation": "werk"}  # no 'person'
        assert self._call(data) is False

    def test_form_missing_conjugation_returns_false(self):
        data = _make_conjugation()
        data["tenses"][0]["forms"][0] = {"person": "ik"}  # no 'conjugation'
        assert self._call(data) is False

    def test_empty_examples_returns_false(self):
        data = _make_conjugation()
        data["examples"] = []
        assert self._call(data) is False

    def test_examples_not_list_returns_false(self):
        data = _make_conjugation()
        data["examples"] = "not a list"
        assert self._call(data) is False

    def test_missing_examples_key_returns_false(self):
        data = _make_conjugation()
        del data["examples"]
        assert self._call(data) is False


# ===========================================================================
# 5. VerbConjugationService.conjugate_verb_with_llm
# ===========================================================================

class TestConjugateVerbWithLlm:
    """
    Tests for the three-tier lookup: cache → storage → LLM.

    Because verb_conjugation_service.py imports CacheManager, OpenRouterService,
    and get_persistence lazily (inside the function body), patch.object / patching
    the source module directly is required instead of patching the
    verb_conjugation_service namespace.
    """

    @pytest.fixture(autouse=True)
    def reset_verb_persistence_singleton(self):
        """Reset the global persistence singleton before each test."""
        import app.verb_persistence as vp
        original = vp._persistence_instance
        vp._persistence_instance = None
        yield
        vp._persistence_instance = original

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self):
        """When the cache has the verb, the result is returned without hitting storage or LLM."""
        from app.verb_conjugation_service import VerbConjugationService
        import app.cache_service as cs
        conj = _make_conjugation("werken")

        with patch.object(cs.CacheManager, "generate_key", return_value="key_werken"), \
             patch.object(cs.CacheManager, "get", return_value=conj):
            result = await VerbConjugationService.conjugate_verb_with_llm("werken")

        assert result == conj

    @pytest.mark.asyncio
    async def test_storage_hit_skips_llm(self):
        """When the verb is in persistent storage but not in cache, LLM is not called."""
        from app.verb_conjugation_service import VerbConjugationService
        import app.cache_service as cs
        import app.verb_persistence as vp
        conj = _make_conjugation("lopen")

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = conj

        with patch.object(cs.CacheManager, "generate_key", return_value="key_lopen"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(cs.CacheManager, "set"), \
             patch.object(vp, "get_persistence", return_value=mock_persistence):
            result = await VerbConjugationService.conjugate_verb_with_llm("lopen")

        assert result == conj
        mock_persistence.get_verb.assert_called_once_with("lopen")

    @pytest.mark.asyncio
    async def test_llm_called_when_cache_and_storage_miss(self):
        """When both cache and storage miss, LLM is called and result is persisted + cached."""
        from app.verb_conjugation_service import VerbConjugationService
        import app.cache_service as cs
        import app.verb_persistence as vp
        from app.llm_service import OpenRouterService
        conj = _make_conjugation("rijden")

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = None

        mock_llm = AsyncMock(return_value=conj)

        with patch.object(cs.CacheManager, "generate_key", return_value="key_rijden"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(cs.CacheManager, "set"), \
             patch.object(vp, "get_persistence", return_value=mock_persistence), \
             patch.object(OpenRouterService, "conjugate_dutch_verb", mock_llm):
            result = await VerbConjugationService.conjugate_verb_with_llm("rijden")

        assert result == conj
        mock_llm.assert_awaited_once_with("rijden")
        mock_persistence.save_verb.assert_called_once_with("rijden", conj)

    @pytest.mark.asyncio
    async def test_invalid_llm_response_raises_processing_error(self):
        """If LLM returns invalid data, ProcessingError is raised."""
        from app.verb_conjugation_service import VerbConjugationService
        from app.exceptions import ProcessingError
        import app.cache_service as cs
        import app.verb_persistence as vp
        from app.llm_service import OpenRouterService

        bad_conj = {"infinitive": "werken"}  # missing required fields

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = None

        mock_llm = AsyncMock(return_value=bad_conj)

        with patch.object(cs.CacheManager, "generate_key", return_value="key_werken"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(vp, "get_persistence", return_value=mock_persistence), \
             patch.object(OpenRouterService, "conjugate_dutch_verb", mock_llm):
            with pytest.raises(ProcessingError):
                await VerbConjugationService.conjugate_verb_with_llm("werken")

    @pytest.mark.asyncio
    async def test_llm_exception_raises_processing_error(self):
        """If LLM raises an unexpected exception, ProcessingError is raised."""
        from app.verb_conjugation_service import VerbConjugationService
        from app.exceptions import ProcessingError
        import app.cache_service as cs
        import app.verb_persistence as vp
        from app.llm_service import OpenRouterService

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = None

        mock_llm = AsyncMock(side_effect=RuntimeError("Network failure"))

        with patch.object(cs.CacheManager, "generate_key", return_value="key_gaan"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(vp, "get_persistence", return_value=mock_persistence), \
             patch.object(OpenRouterService, "conjugate_dutch_verb", mock_llm):
            with pytest.raises(ProcessingError):
                await VerbConjugationService.conjugate_verb_with_llm("gaan")

    @pytest.mark.asyncio
    async def test_verb_is_lowercased_before_lookup(self):
        """The verb is normalised to lowercase before any lookup."""
        from app.verb_conjugation_service import VerbConjugationService
        import app.cache_service as cs
        import app.verb_persistence as vp
        conj = _make_conjugation("werken")

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = conj

        with patch.object(cs.CacheManager, "generate_key", return_value="key_werken"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(cs.CacheManager, "set"), \
             patch.object(vp, "get_persistence", return_value=mock_persistence):
            result = await VerbConjugationService.conjugate_verb_with_llm("WERKEN")

        # Storage was called with lowercase
        mock_persistence.get_verb.assert_called_once_with("werken")
        assert result == conj


# ===========================================================================
# 6. VerbDatabaseManager
# ===========================================================================

class TestVerbDatabaseManager:
    """Tests for VerbDatabaseManager utility methods (all using SQLitePersistence :memory:)."""

    def _make_sqlite_persistence(self):
        from app.verb_persistence import SQLitePersistence
        return SQLitePersistence(db_path=":memory:")

    def test_update_verb_success(self):
        """update_verb succeeds when the verb exists and has english_translation."""
        from app.verb_database_manager import VerbDatabaseManager

        p = self._make_sqlite_persistence()
        conj = _make_conjugation("kopen", "to buy")
        p.save_verb("kopen", conj)

        updated = dict(conj)
        updated["english_translation"] = "to purchase"

        with patch("app.verb_database_manager.get_persistence", return_value=p):
            result = VerbDatabaseManager.update_verb("kopen", updated)

        assert result is True

    def test_update_verb_not_found_returns_false(self):
        """update_verb returns False when the verb is not in the database."""
        from app.verb_database_manager import VerbDatabaseManager

        p = self._make_sqlite_persistence()

        with patch("app.verb_database_manager.get_persistence", return_value=p):
            result = VerbDatabaseManager.update_verb("bestaan", {"english_translation": "to exist"})

        assert result is False

    def test_update_verb_missing_english_translation_returns_false(self):
        """update_verb returns False if english_translation is absent from conjugation_data."""
        from app.verb_database_manager import VerbDatabaseManager

        p = self._make_sqlite_persistence()
        conj = _make_conjugation("slaan")
        p.save_verb("slaan", conj)

        with patch("app.verb_database_manager.get_persistence", return_value=p):
            result = VerbDatabaseManager.update_verb("slaan", {"infinitive": "slaan"})

        assert result is False

    def test_delete_verb_success(self):
        """delete_verb returns True and removes the verb from the DB."""
        from app.verb_database_manager import VerbDatabaseManager

        p = self._make_sqlite_persistence()
        p.save_verb("springen", _make_conjugation("springen"))

        with patch("app.verb_database_manager.get_persistence", return_value=p):
            result = VerbDatabaseManager.delete_verb("springen")

        assert result is True
        assert p.get_verb("springen") is None

    def test_delete_nonexistent_verb_returns_false(self):
        """delete_verb returns False when the verb isn't in the DB."""
        from app.verb_database_manager import VerbDatabaseManager

        p = self._make_sqlite_persistence()

        with patch("app.verb_database_manager.get_persistence", return_value=p):
            result = VerbDatabaseManager.delete_verb("vliegen")

        assert result is False

    def test_export_and_import_roundtrip(self, tmp_path):
        """Verbs exported to JSON can be re-imported without data loss."""
        from app.verb_database_manager import VerbDatabaseManager

        p = self._make_sqlite_persistence()
        p.save_verb("rennen", _make_conjugation("rennen", "to run"))
        p.save_verb("fietsen", _make_conjugation("fietsen", "to cycle"))

        export_path = str(tmp_path / "export.json")

        with patch("app.verb_database_manager.get_persistence", return_value=p):
            VerbDatabaseManager.export_to_json(export_path)

        # Verify exported file structure
        with open(export_path) as f:
            data = json.load(f)

        assert data["total_verbs"] == 2
        assert "rennen" in data["verbs"]
        assert "fietsen" in data["verbs"]

        # Import into a fresh persistence layer
        p2 = self._make_sqlite_persistence()
        with patch("app.verb_database_manager.get_persistence", return_value=p2):
            count = VerbDatabaseManager.import_from_json(export_path)

        assert count == 2
        assert p2.get_verb("rennen") is not None
        assert p2.get_verb("fietsen") is not None

    def test_cleanup_removes_verbs_without_english_translation(self, tmp_path):
        """cleanup_verb_data removes verbs whose conjugation_data lacks english_translation."""
        from app.verb_database_manager import VerbDatabaseManager

        p = self._make_sqlite_persistence()

        # Insert a valid verb: cleanup checks for 'english_translation' (snake_case) in the JSON
        good_conj = _make_conjugation("helpen", "to help")
        good_conj["english_translation"] = "to help"  # cleanup reads this key, not englishTranslation
        p.save_verb("helpen", good_conj)

        # Insert an invalid verb by writing directly to SQLite (no english_translation key)
        bad_data = {"infinitive": "stoppen"}
        cursor = p.connection.cursor()
        cursor.execute(
            "INSERT INTO verbs (infinitive, conjugation_data) VALUES (?, ?)",
            ("stoppen", json.dumps(bad_data))
        )
        p.connection.commit()

        with patch("app.verb_database_manager.get_persistence", return_value=p):
            stats = VerbDatabaseManager.cleanup_verb_data()

        assert stats["removed_count"] >= 1
        assert p.verb_exists("helpen") is True
        assert p.verb_exists("stoppen") is False


# ===========================================================================
# 7. POST /api/conjugate  route
# ===========================================================================

class TestConjugateRoute:
    """HTTP-level tests for the conjugate endpoint."""

    @pytest.fixture(autouse=True)
    def reset_verb_persistence_singleton(self):
        import app.verb_persistence as vp
        original = vp._persistence_instance
        vp._persistence_instance = None
        yield
        vp._persistence_instance = original

    @pytest.fixture()
    def api(self):
        """TestClient with rate-limiter disabled."""
        from starlette.testclient import TestClient
        from app.main import app

        # Disable rate limiter by patching its key func
        with patch("app.limiter.limiter.enabled", False, create=True):
            with TestClient(app, raise_server_exceptions=False) as client:
                yield client

    def test_conjugate_success(self, api):
        """Valid verb returns 200 with conjugation data."""
        import app.cache_service as cs
        import app.verb_persistence as vp
        from app.llm_service import OpenRouterService
        conj = _make_conjugation("werken")
        mock_llm = AsyncMock(return_value=conj)

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = None
        mock_persistence.save_verb.return_value = True

        with patch.object(cs.CacheManager, "generate_key", return_value="key_werken"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(cs.CacheManager, "set"), \
             patch.object(vp, "get_persistence", return_value=mock_persistence), \
             patch.object(OpenRouterService, "conjugate_dutch_verb", mock_llm):
            resp = api.post("/api/conjugate", json={"verb": "werken"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["infinitive"] == "werken"
        assert "tenses" in data

    def test_conjugate_empty_verb_returns_422(self, api):
        """Blank verb string fails Pydantic validation (whitespace stripped → empty → 422)."""
        resp = api.post("/api/conjugate", json={"verb": "   "})
        assert resp.status_code == 422

    def test_conjugate_verb_with_invalid_characters_returns_422(self, api):
        """Verb with disallowed characters (digits) fails Pydantic validation → 422."""
        resp = api.post("/api/conjugate", json={"verb": "w3rk3n"})
        assert resp.status_code == 422

    def test_conjugate_processing_error_returns_404(self, api):
        """ProcessingError from service layer is mapped to 404."""
        import app.cache_service as cs
        import app.verb_persistence as vp
        from app.llm_service import OpenRouterService
        from app.exceptions import ProcessingError

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = None

        mock_llm = AsyncMock(side_effect=ProcessingError("LLM failed"))

        with patch.object(cs.CacheManager, "generate_key", return_value="key_xyz"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(vp, "get_persistence", return_value=mock_persistence), \
             patch.object(OpenRouterService, "conjugate_dutch_verb", mock_llm):
            resp = api.post("/api/conjugate", json={"verb": "xyzabc"})

        assert resp.status_code == 404

    def test_conjugate_unexpected_error_returns_404(self, api):
        """
        An unexpected exception from the LLM is wrapped in ProcessingError by the service,
        then the route maps ProcessingError → 404.
        """
        import app.cache_service as cs
        import app.verb_persistence as vp
        from app.llm_service import OpenRouterService

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = None

        mock_llm = AsyncMock(side_effect=RuntimeError("Boom"))

        with patch.object(cs.CacheManager, "generate_key", return_value="key_err"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(vp, "get_persistence", return_value=mock_persistence), \
             patch.object(OpenRouterService, "conjugate_dutch_verb", mock_llm):
            resp = api.post("/api/conjugate", json={"verb": "klappen"})

        assert resp.status_code == 404

    def test_conjugate_uses_storage_hit_without_llm(self, api):
        """When verb is in storage, LLM is never called and response is 200."""
        import app.cache_service as cs
        import app.verb_persistence as vp
        from app.llm_service import OpenRouterService
        conj = _make_conjugation("lopen")

        mock_persistence = MagicMock()
        mock_persistence.get_verb.return_value = conj

        mock_llm = AsyncMock()

        with patch.object(cs.CacheManager, "generate_key", return_value="key_lopen"), \
             patch.object(cs.CacheManager, "get", return_value=None), \
             patch.object(cs.CacheManager, "set"), \
             patch.object(vp, "get_persistence", return_value=mock_persistence), \
             patch.object(OpenRouterService, "conjugate_dutch_verb", mock_llm):
            resp = api.post("/api/conjugate", json={"verb": "lopen"})

        assert resp.status_code == 200
        mock_llm.assert_not_awaited()

    def test_conjugate_missing_body_returns_422(self, api):
        """Request with no body returns 422 Unprocessable Entity."""
        resp = api.post("/api/conjugate", json={})
        assert resp.status_code == 422

    def test_conjugate_verb_too_long_returns_422(self, api):
        """Verb exceeding max_length=50 fails Pydantic validation."""
        resp = api.post("/api/conjugate", json={"verb": "a" * 51})
        assert resp.status_code == 422
