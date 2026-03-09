"""
Dutch conjunction fill-in-the-blank game service.

Flow:
  1. Frontend requests a question (backend picks a conjunction at random).
  2. Backend calls LLM to generate a sentence with a blank + correct answer + distractors.
  3. Frontend submits answers → backend scores and saves a ConjunctionGameSession.
"""
import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
    ("of", "subordinating"),  # indirect question
    ("wie", "subordinating"),
    # Correlative
    ("zowel ... als", "correlative"),
    ("noch ... noch", "correlative"),
    ("hetzij ... hetzij", "correlative"),
    ("niet alleen ... maar ook", "correlative"),
]

# Flat list for random sampling
_POOL_LOOKUP: Dict[str, str] = {c: t for c, t in CONJUNCTION_POOL}


async def generate_question(
    conjunction: Optional[str] = None,
    conjunction_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Ask the LLM to generate a fill-in-the-blank question.

    If `conjunction` is provided, use it; otherwise pick randomly from the pool
    (optionally filtered by `conjunction_types`).
    """
    if conjunction:
        c_type = _POOL_LOOKUP.get(conjunction, "coordinating")
    else:
        pool = CONJUNCTION_POOL
        if conjunction_types:
            pool = [(c, t) for c, t in CONJUNCTION_POOL if t in conjunction_types]
        if not pool:
            pool = CONJUNCTION_POOL
        conjunction, c_type = random.choice(pool)

    return await OpenRouterService.generate_conjunction_question(conjunction, c_type)


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

        # Hardest conjunctions
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
        }

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
        Persist a completed game session.
        `answers` is a list of dicts with keys:
            conjunction, conjunction_type, sentence, correct_answer,
            user_answer, english_hint
        """
        if not answers:
            raise ProcessingError("No answers provided")

        scored = []
        for a in answers:
            user_ans = (a.get("user_answer") or "").strip().lower()
            correct = (a.get("correct_answer") or "").strip().lower()
            is_correct = user_ans == correct
            scored.append({**a, "is_correct": is_correct})

        score = sum(1 for a in scored if a["is_correct"])
        accuracy = round(score / len(scored) * 100)

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
            self.db.add(models.ConjunctionGameAnswer(
                session_id=session.id,
                conjunction=a.get("conjunction", ""),
                conjunction_type=a.get("conjunction_type"),
                sentence=a.get("sentence", ""),
                correct_answer=a.get("correct_answer", ""),
                user_answer=a.get("user_answer", ""),
                is_correct=a["is_correct"],
                english_hint=a.get("english_hint"),
            ))

        self.db.commit()
        self.db.refresh(session)
        return session
