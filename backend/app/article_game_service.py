"""
Article game service — stateless answer-checking + user-scoped history/stats.

Two modes:
  guest  — random words from the article_words DB table, nothing persisted.
  user   — words weighted by past mistakes + user's word bank, history saved.
"""
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.dutch_article_words import DUTCH_ARTICLE_WORDS  # kept as fallback seed reference
from app.database import SessionLocal
from app import models
import logging

logger = logging.getLogger(__name__)
# ---------------------------------------------------------------------------
# DB helpers — used by both guest and logged-in paths
# ---------------------------------------------------------------------------

def _get_active_words_from_db(db: Session) -> List[Dict[str, Any]]:
    """Return all active words from the article_words table as plain dicts."""
    rows = db.query(models.ArticleWord).filter_by(is_active=True).all()
    return [
        {
            "word": r.word,
            "article": r.article,
            "translation": r.translation,
            "difficulty": r.difficulty,
            "category": r.category,
        }
        for r in rows
    ]


def _get_db_word_info(word: str, db: Session) -> Optional[Dict[str, Any]]:
    """Look up a single word in the DB. Returns None if not found."""
    row = db.query(models.ArticleWord).filter(
        models.ArticleWord.word == word.lower(),
        models.ArticleWord.is_active == True,  # noqa: E712
    ).first()
    if not row:
        return None
    return {
        "word": row.word,
        "article": row.article,
        "translation": row.translation,
        "difficulty": row.difficulty,
        "category": row.category,
    }


def _random_words_from_db(
    db: Session,
    count: int,
    exclude_words: Optional[set] = None,
) -> List[Dict[str, Any]]:
    """Return a random sample of active words from the DB.

    Uses ORDER BY RANDOM() LIMIT n so the database does the sampling —
    no need to pull the full table into Python memory.
    ``exclude_words`` (a set of word strings) are filtered out in SQL via
    NOT IN, so we never fetch rows we're about to discard.
    """
    if count <= 0:
        return []
    from sqlalchemy import func
    q = db.query(models.ArticleWord).filter_by(is_active=True)
    if exclude_words:
        q = q.filter(models.ArticleWord.word.notin_(exclude_words))
    rows = q.order_by(func.random()).limit(count).all()
    return [
        {
            "word": r.word,
            "article": r.article,
            "translation": r.translation,
            "difficulty": r.difficulty,
            "category": r.category,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Stateless helpers (used by routes for guest and logged-in paths)
# ---------------------------------------------------------------------------

def get_guest_words(count: int) -> List[Dict[str, Any]]:
    """Return a random selection from the DB word list, article hidden."""
    db = SessionLocal()
    try:
        words = _random_words_from_db(db, count)
    finally:
        db.close()
    # Fallback to static list if DB is empty (e.g. before first seed)
    if not words:
        from app.dutch_article_words import get_random_words as _static_random
        words = _static_random(count)
    return _strip_article(words)


def check_answer(word: str, user_answer: str) -> Dict[str, Any]:
    """
    Validate a single answer. Stateless — no DB writes.
    Returns a dict the frontend can use directly.
    """
    db = SessionLocal()
    try:
        info = _get_db_word_info(word, db)
    finally:
        db.close()

    # Fallback: check static list (covers words not yet in DB)
    if not info:
        from app.dutch_article_words import get_word_info as _static_info
        info = _static_info(word)
    if not info:
        return {"error": "Word not found", "word": word}

    correct = info["article"]
    is_correct = user_answer.lower() == correct

    return {
        "is_correct": is_correct,
        "word": word,
        "correct_article": correct,
        "user_answer": user_answer.lower(),
        "difficulty": info.get("difficulty", "unknown"),
        "category": info.get("category", "unknown"),
    }


def get_word_info(word: str) -> Optional[Dict[str, Any]]:
    """Convenience wrapper — used by get_stats hardest_words lookup."""
    db = SessionLocal()
    try:
        info = _get_db_word_info(word, db)
    finally:
        db.close()
    if not info:
        from app.dutch_article_words import get_word_info as _static_info
        info = _static_info(word)
    return info


def _strip_article(words: List[Dict]) -> List[Dict]:
    """Return word dicts without the article field (don't leak the answer)."""
    return [
        {k: v for k, v in w.items() if k != "article"}
        for w in words
    ]


# ---------------------------------------------------------------------------
# User-scoped service (requires a SQLAlchemy Session)
# ---------------------------------------------------------------------------

class ArticleGameService:
    """All methods are scoped to a single authenticated user."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    # ------------------------------------------------------------------
    # Word selection
    # ------------------------------------------------------------------

    def get_words(self, count: int, mode: str = "smart") -> List[Dict[str, Any]]:
        """
        Build a word list for a game.

        mode values:
          "smart"     — 40% mistakes + 30% word-bank nouns + 30% random
          "mistakes"  — 70% mistakes + 30% random
          "wordbank"  — 70% word-bank nouns + 30% random
          "random"    — fully random from DB word list
        """
        from sqlalchemy import func
        total_active = (
            self.db.query(func.count(models.ArticleWord.id))
            .filter_by(is_active=True)
            .scalar() or 0
        )
        pool_size = total_active or len(DUTCH_ARTICLE_WORDS)
        count = max(5, min(count, pool_size))

        if mode == "random":
            return _strip_article(_random_words_from_db(self.db, count))

        mistake_words = self._get_mistake_words()
        wordbank_words = self._get_wordbank_words()

        if mode == "mistakes":
            n_mistakes = int(count * 0.70)
            selected = self._pick(mistake_words, n_mistakes)
        elif mode == "wordbank":
            n_wb = int(count * 0.70)
            selected = self._pick(wordbank_words, n_wb)
        else:  # smart
            n_mistakes = int(count * 0.40)
            n_wb = int(count * 0.30)
            selected = self._pick(mistake_words, n_mistakes)
            selected += self._pick(
                [w for w in wordbank_words if w["word"] not in {x["word"] for x in selected}], n_wb
            )

        # Fill remainder from DB — pass already-selected words so the DB
        # filters them out with NOT IN rather than fetching the full table.
        n_random = count - len(selected)
        if n_random > 0:
            selected_words = {w["word"] for w in selected}
            selected += _random_words_from_db(self.db, n_random, exclude_words=selected_words)

        random.shuffle(selected)
        return _strip_article(selected[:count])

    def _get_mistake_words(self) -> List[Dict]:
        """Return words the user has gotten wrong, weighted by error rate.

        Single JOIN query — avoids N+1 round-trips to article_words.
        """
        rows = (
            self.db.query(models.ArticleWord, models.ArticleWordMistake.times_wrong)
            .join(
                models.ArticleWordMistake,
                models.ArticleWord.word == models.ArticleWordMistake.word,
            )
            .filter(
                models.ArticleWordMistake.user_id == self.user_id,
                models.ArticleWordMistake.times_wrong > 0,
                models.ArticleWord.is_active == True,  # noqa: E712
            )
            .order_by(models.ArticleWordMistake.times_wrong.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "word": r.ArticleWord.word,
                "article": r.ArticleWord.article,
                "translation": r.ArticleWord.translation,
                "difficulty": r.ArticleWord.difficulty,
                "category": r.ArticleWord.category,
            }
            for r in rows
        ]

    def _get_wordbank_words(self) -> List[Dict]:
        """Return user's word-bank entries that appear in the article word list.

        Single JOIN query — avoids N+1 round-trips to article_words.
        """
        rows = (
            self.db.query(models.ArticleWord)
            .join(
                models.UserWord,
                models.ArticleWord.word == models.UserWord.word,
            )
            .filter(
                models.UserWord.user_id == self.user_id,
                models.ArticleWord.is_active == True,  # noqa: E712
            )
            .all()
        )
        return [
            {
                "word": r.word,
                "article": r.article,
                "translation": r.translation,
                "difficulty": r.difficulty,
                "category": r.category,
            }
            for r in rows
        ]

    @staticmethod
    def _pick(pool: List[Dict], n: int) -> List[Dict]:
        """Pick up to n items from pool without replacement."""
        return pool[:n] if len(pool) >= n else pool[:]

    # ------------------------------------------------------------------
    # Saving a completed game
    # ------------------------------------------------------------------

    def save_game(self, answers: List[Dict]) -> models.ArticleGameSession:
        """Persist a completed game and update word-mistake counters."""
        score = sum(1 for a in answers if a.get("is_correct"))
        total = len(answers)
        accuracy = round(score / total * 100) if total else 0

        session = models.ArticleGameSession(
            user_id=self.user_id,
            played_at=datetime.now(timezone.utc),
            word_count=total,
            score=score,
            accuracy=accuracy,
        )
        self.db.add(session)
        self.db.flush()  # get session.id before adding answers

        for ans in answers:
            self.db.add(models.ArticleGameAnswer(
                session_id=session.id,
                word=ans.get("word", ""),
                correct_article=ans.get("correct_article", ""),
                user_answer=ans.get("user_answer", ""),
                is_correct=bool(ans.get("is_correct")),
            ))

        # Bulk-fetch all existing mistake rows for the words in this game
        # in a single query, then update/insert in Python — no N+1.
        words_in_game = [ans.get("word", "") for ans in answers]
        existing_rows = (
            self.db.query(models.ArticleWordMistake)
            .filter(
                models.ArticleWordMistake.user_id == self.user_id,
                models.ArticleWordMistake.word.in_(words_in_game),
            )
            .all()
        )
        mistake_map = {r.word: r for r in existing_rows}

        now = datetime.now(timezone.utc)
        for ans in answers:
            word = ans.get("word", "")
            is_correct = bool(ans.get("is_correct"))
            row = mistake_map.get(word)
            if row is None:
                row = models.ArticleWordMistake(
                    user_id=self.user_id,
                    word=word,
                    times_seen=0,
                    times_wrong=0,
                )
                self.db.add(row)
                mistake_map[word] = row
            row.times_seen += 1
            if not is_correct:
                row.times_wrong += 1
            row.last_seen_at = now

        self.db.commit()
        self.db.refresh(session)
        return session

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregate stats for the user's dashboard."""
        sessions = (
            self.db.query(models.ArticleGameSession)
            .filter_by(user_id=self.user_id)
            .all()
        )

        total_games = len(sessions)
        if total_games == 0:
            return {
                "total_games": 0,
                "avg_accuracy": 0,
                "words_studied": 0,
                "current_streak": 0,
                "hardest_words": [],
                "recent_games": [],
            }

        avg_accuracy = round(sum(s.accuracy for s in sessions) / total_games)
        words_studied = (
            self.db.query(models.ArticleWordMistake)
            .filter_by(user_id=self.user_id)
            .count()
        )

        hardest = (
            self.db.query(models.ArticleWordMistake)
            .filter(
                models.ArticleWordMistake.user_id == self.user_id,
                models.ArticleWordMistake.times_wrong > 0,
            )
            .order_by(models.ArticleWordMistake.times_wrong.desc())
            .limit(5)
            .all()
        )

        # Current streak — consecutive sessions with accuracy >= 70%
        streak = 0
        for s in sorted(sessions, key=lambda x: x.played_at, reverse=True):
            if s.accuracy >= 70:
                streak += 1
            else:
                break

        recent = sorted(sessions, key=lambda x: x.played_at, reverse=True)[:5]

        return {
            "total_games": total_games,
            "avg_accuracy": avg_accuracy,
            "words_studied": words_studied,
            "current_streak": streak,
            "hardest_words": [
                {
                    "word": h.word,
                    "times_wrong": h.times_wrong,
                    "times_seen": h.times_seen,
                    "correct_article": (_get_db_word_info(h.word, self.db) or {}).get("article", "?"),
                }
                for h in hardest
            ],
            "recent_games": [
                {
                    "id": s.id,
                    "played_at": s.played_at.isoformat(),
                    "score": s.score,
                    "word_count": s.word_count,
                    "accuracy": s.accuracy,
                }
                for s in recent
            ],
        }

    def get_history(self) -> List[Dict[str, Any]]:
        """Return all sessions newest-first, each with their per-answer breakdown."""
        sessions = (
            self.db.query(models.ArticleGameSession)
            .filter_by(user_id=self.user_id)
            .order_by(models.ArticleGameSession.played_at.desc())
            .all()
        )
        result = []
        for s in sessions:
            answers = (
                self.db.query(models.ArticleGameAnswer)
                .filter_by(session_id=s.id)
                .all()
            )
            result.append({
                "id": s.id,
                "played_at": s.played_at.isoformat(),
                "score": s.score,
                "word_count": s.word_count,
                "accuracy": s.accuracy,
                "answers": [
                    {
                        "word": a.word,
                        "correct_article": a.correct_article,
                        "user_answer": a.user_answer,
                        "is_correct": a.is_correct,
                    }
                    for a in answers
                ],
            })
        return result
