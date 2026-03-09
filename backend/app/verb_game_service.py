"""
Verb conjugation fill-in-the-blank game service.

Flow:
  1. Frontend requests N questions, each for a chosen verb (or the backend picks).
  2. Backend calls LLM to generate a sentence with a blank + correct answer.
  3. Frontend submits answers → backend scores and saves a VerbGameSession.
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

# Curated set of common Dutch verbs used as default pool
DEFAULT_VERB_POOL = [
    "zijn", "hebben", "worden", "gaan", "komen", "doen", "zien", "weten",
    "kunnen", "willen", "moeten", "mogen", "zullen", "maken", "lopen",
    "staan", "zitten", "liggen", "kijken", "horen", "spreken", "schrijven",
    "lezen", "werken", "wonen", "leven", "denken", "voelen", "proberen",
    "beginnen", "eindigen", "stoppen", "openen", "sluiten", "kopen", "verkopen",
    "eten", "drinken", "slapen", "wakker worden", "opstaan", "aankomen",
    "vertrekken", "reizen", "rijden", "fietsen", "zwemmen", "leren", "studeren",
]


async def generate_question(verb: str, tenses: list[str] | None = None) -> Dict[str, Any]:
    """
    Ask the LLM to generate a single fill-in-the-blank question for `verb`.
    `tenses` is an optional list of tense names to restrict the question to.
    Returns the raw LLM dict (verb_infinitive, sentence, correct_answer, …).
    Raises ProcessingError on failure.
    """
    return await OpenRouterService.generate_verb_game_question(verb, tenses=tenses)


class VerbGameService:
    """All methods are scoped to a single authenticated user."""

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    # ------------------------------------------------------------------
    # Stats & history
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        sessions = (
            self.db.query(models.VerbGameSession)
            .filter(models.VerbGameSession.user_id == self.user_id)
            .order_by(models.VerbGameSession.played_at.desc())
            .all()
        )
        if not sessions:
            return {
                "total_games": 0,
                "avg_accuracy": 0,
                "questions_answered": 0,
                "current_streak": 0,
                "hardest_verbs": [],
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

        # Hardest verbs: aggregate error rate from VerbGameAnswer rows
        verb_stats: Dict[str, Dict] = {}
        for s in sessions:
            for ans in s.answers:
                v = ans.verb_infinitive
                if v not in verb_stats:
                    verb_stats[v] = {"seen": 0, "wrong": 0}
                verb_stats[v]["seen"] += 1
                if not ans.is_correct:
                    verb_stats[v]["wrong"] += 1

        hardest = sorted(
            [
                {
                    "verb": v,
                    "times_seen": d["seen"],
                    "times_wrong": d["wrong"],
                    "error_rate": round(d["wrong"] / d["seen"] * 100) if d["seen"] else 0,
                }
                for v, d in verb_stats.items()
                if d["wrong"] > 0
            ],
            key=lambda x: -x["error_rate"],
        )[:10]

        return {
            "total_games": total,
            "avg_accuracy": avg_acc,
            "questions_answered": questions_answered,
            "current_streak": streak,
            "hardest_verbs": hardest,
        }

    def get_history(self) -> List[Dict[str, Any]]:
        sessions = (
            self.db.query(models.VerbGameSession)
            .filter(models.VerbGameSession.user_id == self.user_id)
            .order_by(models.VerbGameSession.played_at.desc())
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
                        "verb_infinitive": a.verb_infinitive,
                        "sentence": a.sentence,
                        "correct_answer": a.correct_answer,
                        "user_answer": a.user_answer,
                        "is_correct": a.is_correct,
                        "tense": a.tense,
                        "person": a.person,
                        "english_hint": a.english_hint,
                    }
                    for a in s.answers
                ],
            })
        return result

    def save_game(self, answers: List[Dict[str, Any]]) -> models.VerbGameSession:
        """
        Persist a completed game session.
        `answers` is a list of dicts with keys:
            verb_infinitive, sentence, correct_answer, user_answer,
            tense, person, english_hint
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

        session = models.VerbGameSession(
            user_id=self.user_id,
            played_at=datetime.now(timezone.utc),
            question_count=len(scored),
            score=score,
            accuracy=accuracy,
        )
        self.db.add(session)
        self.db.flush()  # get session.id

        for a in scored:
            self.db.add(models.VerbGameAnswer(
                session_id=session.id,
                verb_infinitive=a.get("verb_infinitive", ""),
                sentence=a.get("sentence", ""),
                correct_answer=a.get("correct_answer", ""),
                user_answer=a.get("user_answer", ""),
                is_correct=a["is_correct"],
                tense=a.get("tense"),
                person=a.get("person"),
                english_hint=a.get("english_hint"),
            ))

        self.db.commit()
        self.db.refresh(session)
        return session
