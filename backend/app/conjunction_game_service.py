"""
Dutch conjunction fill-in-the-blank game service.

Flow:
  1. Frontend requests a question, sending already-used sentence IDs to avoid repeats.
  2. Backend checks if this user has any "needs_review" sentences first (spaced repetition).
  3. Otherwise it tries to serve a cached ConjunctionSentence the user hasn't seen today.
  4. If no suitable cache hit, the LLM generates a new sentence which is then stored.
  5. Frontend submits answers → backend scores, saves session, and updates per-user stats.
"""
import json
import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app import models
from app.llm_service import OpenRouterService
from app.exceptions import ProcessingError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conjunction pool — (conjunction, type) tuples
# ---------------------------------------------------------------------------
CONJUNCTION_POOL: List[tuple[str, str]] = [
    # Coordinating (nevenschikkend)
    ("en", "coordinating"),
    ("maar", "coordinating"),
    ("of", "coordinating"),
    ("want", "coordinating"),
    ("dus", "coordinating"),
    ("noch", "coordinating"),
    ("toch", "coordinating"),
    ("ofwel", "coordinating"),
    # Subordinating — cause / reason
    ("omdat", "subordinating"),
    ("doordat", "subordinating"),
    ("aangezien", "subordinating"),
    ("nu", "subordinating"),
    # Subordinating — condition
    ("als", "subordinating"),
    ("indien", "subordinating"),
    ("tenzij", "subordinating"),
    ("mits", "subordinating"),
    # Subordinating — concession
    ("hoewel", "subordinating"),
    ("ofschoon", "subordinating"),
    ("al", "subordinating"),
    ("alhoewel", "subordinating"),
    # Subordinating — time
    ("toen", "subordinating"),
    ("terwijl", "subordinating"),
    ("zodra", "subordinating"),
    ("nadat", "subordinating"),
    ("voordat", "subordinating"),
    ("totdat", "subordinating"),
    ("zolang", "subordinating"),
    ("wanneer", "subordinating"),
    # Subordinating — purpose / result
    ("zodat", "subordinating"),
    ("opdat", "subordinating"),
    ("zoals", "subordinating"),
    # Subordinating — content
    ("dat", "subordinating"),
    ("wie", "subordinating"),
    # Correlative
    ("zowel ... als", "correlative"),
    ("noch ... noch", "correlative"),
    ("hetzij ... hetzij", "correlative"),
    ("niet alleen ... maar ook", "correlative"),
]

# Lookup: conjunction → type (last write wins for duplicates)
_POOL_LOOKUP: Dict[str, str] = {c: t for c, t in CONJUNCTION_POOL}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sentence_to_dict(s: models.ConjunctionSentence, is_review: bool = False) -> Dict[str, Any]:
    """Serialize a ConjunctionSentence ORM row to the question payload the frontend expects."""
    try:
        distractors = json.loads(s.distractors) if s.distractors else []
    except (ValueError, TypeError):
        distractors = []
    return {
        "sentence_id": s.id,
        "conjunction": s.conjunction,
        "conjunction_type": s.conjunction_type,
        "sentence": s.sentence,
        "correct_answer": s.correct_answer,
        "english_hint": s.english_hint,
        "distractors": distractors,
        "explanation": s.explanation,
        "is_review": is_review,  # badge hint for frontend
    }


def _pick_from_pool(
    conjunction: Optional[str],
    conjunction_types: Optional[List[str]],
) -> tuple[str, str]:
    """Choose a (conjunction, type) pair from the pool."""
    if conjunction:
        return conjunction, _POOL_LOOKUP.get(conjunction, "coordinating")
    pool = CONJUNCTION_POOL
    if conjunction_types:
        pool = [(c, t) for c, t in CONJUNCTION_POOL if t in conjunction_types]
    if not pool:
        pool = CONJUNCTION_POOL
    return random.choice(pool)


# ---------------------------------------------------------------------------
# Main question generator — called by the route handler
# ---------------------------------------------------------------------------

async def generate_question(
    db: Session,
    user_id: Optional[int],
    conjunction: Optional[str] = None,
    conjunction_types: Optional[List[str]] = None,
    excluded_sentence_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Return a conjunction fill-in-the-blank question.

    Priority order:
      1. (Logged-in users only) Cached sentences the user previously got
         *wrong* (needs_review=True), not already in this game session.
      2. Cached sentences matching the filters that this user hasn't seen yet
         (or all cached sentences for guests), not in excluded_sentence_ids.
      3. Generate a new sentence via LLM, store it, and return it.
    """
    excluded: Set[int] = set(excluded_sentence_ids or [])

    # ── 1. Review queue: sentences the user got wrong previously ──────────
    # (Only applicable for logged-in users)
    if user_id is not None:
        review_q = (
            db.query(models.ConjunctionSentenceStat)
            .join(models.ConjunctionSentence)
            .filter(
                models.ConjunctionSentenceStat.user_id == user_id,
                models.ConjunctionSentenceStat.needs_review == True,  # noqa: E712
            )
        )
        if excluded:
            review_q = review_q.filter(
                models.ConjunctionSentenceStat.sentence_id.notin_(excluded)
            )
        if conjunction_types:
            review_q = review_q.filter(
                models.ConjunctionSentence.conjunction_type.in_(conjunction_types)
            )
        if conjunction:
            review_q = review_q.filter(
                models.ConjunctionSentence.conjunction == conjunction
            )
        review_candidates = review_q.all()
        if review_candidates:
            stat = random.choice(review_candidates)
            return _sentence_to_dict(stat.sentence, is_review=True)

    # ── 2. Cache hit: unseen sentences matching filters ───────────────────
    # "Unseen" = no stat row for this user OR times_seen == 0
    # For guests, treat all cached sentences as candidates (minus excluded).
    if user_id is not None:
        seen_ids_q = (
            db.query(models.ConjunctionSentenceStat.sentence_id)
            .filter(
                models.ConjunctionSentenceStat.user_id == user_id,
                models.ConjunctionSentenceStat.times_seen > 0,
            )
        )
        seen_ids = {row.sentence_id for row in seen_ids_q.all()}
    else:
        seen_ids = set()
    already_excluded = excluded | seen_ids

    cached_q = db.query(models.ConjunctionSentence)
    if already_excluded:
        cached_q = cached_q.filter(
            models.ConjunctionSentence.id.notin_(already_excluded)
        )
    if conjunction_types:
        cached_q = cached_q.filter(
            models.ConjunctionSentence.conjunction_type.in_(conjunction_types)
        )
    if conjunction:
        cached_q = cached_q.filter(
            models.ConjunctionSentence.conjunction == conjunction
        )
    cached_candidates = cached_q.all()
    if cached_candidates:
        sentence = random.choice(cached_candidates)
        return _sentence_to_dict(sentence, is_review=False)

    # ── 3. LLM fallback ───────────────────────────────────────────────────
    conj, c_type = _pick_from_pool(conjunction, conjunction_types)
    raw = await OpenRouterService.generate_conjunction_question(conj, c_type)

    # Persist the new sentence
    new_sentence = models.ConjunctionSentence(
        conjunction=raw["conjunction"],
        conjunction_type=raw["conjunction_type"],
        sentence=raw["sentence"],
        correct_answer=raw["correct_answer"],
        english_hint=raw.get("english_hint"),
        distractors=json.dumps(raw.get("distractors", [])),
        explanation=raw.get("explanation"),
        times_seen=0,
        times_correct=0,
    )
    db.add(new_sentence)
    db.commit()
    db.refresh(new_sentence)

    return _sentence_to_dict(new_sentence, is_review=False)


class ConjunctionGameService:
    """All methods scoped to a single authenticated user."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    # ------------------------------------------------------------------
    # Stats & history
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        sessions = (
            self.db.query(models.ConjunctionGameSession)
            .filter(models.ConjunctionGameSession.user_id == self.user_id)
            .order_by(models.ConjunctionGameSession.played_at.desc())
            .all()
        )
        if not sessions:
            return {
                "total_games": 0,
                "avg_accuracy": 0,
                "questions_answered": 0,
                "current_streak": 0,
                "hardest_conjunctions": [],
                "review_queue_size": self._review_queue_size(),
            }

        total = len(sessions)
        avg_acc = round(sum(s.accuracy for s in sessions) / total)
        questions_answered = sum(s.question_count for s in sessions)

        # Win streak (consecutive sessions ≥ 70%)
        streak = 0
        for s in sessions:
            if s.accuracy >= 70:
                streak += 1
            else:
                break

        # Hardest conjunctions — aggregate from per-user sentence stats
        conj_stats: Dict[str, Dict] = {}
        for s in sessions:
            for ans in s.answers:
                c = ans.conjunction
                if c not in conj_stats:
                    conj_stats[c] = {"seen": 0, "wrong": 0, "type": ans.conjunction_type}
                conj_stats[c]["seen"] += 1
                if not ans.is_correct:
                    conj_stats[c]["wrong"] += 1

        hardest = sorted(
            [
                {
                    "conjunction": c,
                    "conjunction_type": d["type"],
                    "times_seen": d["seen"],
                    "times_wrong": d["wrong"],
                    "error_rate": round(d["wrong"] / d["seen"] * 100) if d["seen"] else 0,
                }
                for c, d in conj_stats.items()
                if d["wrong"] > 0
            ],
            key=lambda x: -x["error_rate"],
        )[:10]

        return {
            "total_games": total,
            "avg_accuracy": avg_acc,
            "questions_answered": questions_answered,
            "current_streak": streak,
            "hardest_conjunctions": hardest,
            "review_queue_size": self._review_queue_size(),
        }

    def _review_queue_size(self) -> int:
        """Number of sentences currently flagged needs_review for this user."""
        return (
            self.db.query(models.ConjunctionSentenceStat)
            .filter(
                models.ConjunctionSentenceStat.user_id == self.user_id,
                models.ConjunctionSentenceStat.needs_review == True,  # noqa: E712
            )
            .count()
        )

    def get_history(self) -> List[Dict[str, Any]]:
        sessions = (
            self.db.query(models.ConjunctionGameSession)
            .filter(models.ConjunctionGameSession.user_id == self.user_id)
            .order_by(models.ConjunctionGameSession.played_at.desc())
            .limit(50)
            .all()
        )
        result = []
        for s in sessions:
            result.append({
                "id": s.id,
                "played_at": s.played_at.isoformat(),
                "question_count": s.question_count,
                "score": s.score,
                "accuracy": s.accuracy,
                "answers": [
                    {
                        "id": a.id,
                        "sentence_id": a.sentence_id,
                        "conjunction": a.conjunction,
                        "conjunction_type": a.conjunction_type,
                        "sentence": a.sentence,
                        "correct_answer": a.correct_answer,
                        "user_answer": a.user_answer,
                        "is_correct": a.is_correct,
                        "english_hint": a.english_hint,
                    }
                    for a in s.answers
                ],
            })
        return result

    def save_game(self, answers: List[Dict[str, Any]]) -> models.ConjunctionGameSession:
        """
        Persist a completed game session and update per-sentence + per-user stats.

        Each answer dict must have:
            conjunction, conjunction_type, sentence, correct_answer,
            user_answer, english_hint, sentence_id (optional)
        """
        if not answers:
            raise ProcessingError("No answers provided")

        # Score answers
        scored = []
        for a in answers:
            user_ans = (a.get("user_answer") or "").strip().lower()
            correct = (a.get("correct_answer") or "").strip().lower()
            is_correct = user_ans == correct
            scored.append({**a, "is_correct": is_correct})

        score = sum(1 for a in scored if a["is_correct"])
        accuracy = round(score / len(scored) * 100)

        # Persist session
        session = models.ConjunctionGameSession(
            user_id=self.user_id,
            played_at=datetime.now(timezone.utc),
            question_count=len(scored),
            score=score,
            accuracy=accuracy,
        )
        self.db.add(session)
        self.db.flush()

        for a in scored:
            sentence_id: Optional[int] = a.get("sentence_id")

            # Create game answer row
            self.db.add(models.ConjunctionGameAnswer(
                session_id=session.id,
                sentence_id=sentence_id,
                conjunction=a.get("conjunction", ""),
                conjunction_type=a.get("conjunction_type"),
                sentence=a.get("sentence", ""),
                correct_answer=a.get("correct_answer", ""),
                user_answer=a.get("user_answer", ""),
                is_correct=a["is_correct"],
                english_hint=a.get("english_hint"),
            ))

            if sentence_id:
                # Update global sentence counters
                sent = self.db.get(models.ConjunctionSentence, sentence_id)
                if sent:
                    sent.times_seen = (sent.times_seen or 0) + 1
                    if a["is_correct"]:
                        sent.times_correct = (sent.times_correct or 0) + 1

                # Upsert per-user sentence stat
                stat = (
                    self.db.query(models.ConjunctionSentenceStat)
                    .filter_by(user_id=self.user_id, sentence_id=sentence_id)
                    .first()
                )
                if stat is None:
                    stat = models.ConjunctionSentenceStat(
                        user_id=self.user_id,
                        sentence_id=sentence_id,
                        times_seen=0,
                        times_correct=0,
                        needs_review=False,
                    )
                    self.db.add(stat)

                stat.times_seen = (stat.times_seen or 0) + 1
                stat.last_seen_at = datetime.now(timezone.utc)
                if a["is_correct"]:
                    stat.times_correct = (stat.times_correct or 0) + 1
                    stat.needs_review = False   # mastered — remove from review queue
                else:
                    stat.needs_review = True    # got it wrong — resurface later

        self.db.commit()
        self.db.refresh(session)
        return session
