"""
Dutch fixed-preposition verb game service.

A "fixed-preposition verb" (vast voorzetselwerkwoord) is a combination like:
  beginnen met, denken aan, zich concentreren op, deelnemen aan, houden van …

Game modes
----------
  prep   – Fill in the missing PREPOSITION.
             Sentence: "Hij begint ___ zijn werk."   Answer: "met"
  hard   – Fill in the conjugated VERB and the PREPOSITION (two inputs).
             Sentence: "Hij ___VERB___ ___PREP___ zijn werk."
             Answers:  verb="begint", prep="met"

Flow
----
  1. Frontend requests a question for a given mode (prep | hard) and
     optional verb filter, sending already-seen pair_ids to avoid repeats.
  2. Priority: needs_review → unseen cached pair → LLM generate + persist.
  3. Frontend submits answers → backend scores + saves session + updates stats.
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
# Built-in verb+preposition pair list
# ---------------------------------------------------------------------------
# Each entry: (verb_infinitive, preposition, english_translation, reflexive, example sentence)
PREP_VERB_PAIRS: List[tuple] = [
    # ── A ──
    ("aandringen", "op", "to insist on", False, "Ze dringt aan op een snelle beslissing. → She insists on a quick decision."),
    ("afhangen", "van", "to depend on", False, "Het hangt af van het weer. → It depends on the weather."),
    ("antwoorden", "op", "to answer/respond to", False, "Hij antwoordt op de vraag. → He answers the question."),
    # ── B ──
    ("bang zijn", "voor", "to be afraid of", False, "Ze is bang voor spinnen. → She is afraid of spiders."),
    ("bedanken", "voor", "to thank for", False, "Ik wil je bedanken voor je hulp. → I want to thank you for your help."),
    ("beginnen", "met", "to begin with / start", False, "Hij begint met zijn werk. → He starts with his work."),
    ("benieuwd zijn", "naar", "to be curious about", False, "Ik ben benieuwd naar het resultaat. → I'm curious about the result."),
    ("bestaan", "uit", "to consist of", False, "Het team bestaat uit vijf leden. → The team consists of five members."),
    ("bijdragen", "aan", "to contribute to", False, "Hij draagt bij aan het project. → He contributes to the project."),
    ("blij zijn", "met", "to be happy with", False, "Ze is blij met haar nieuwe baan. → She is happy with her new job."),
    # ── D ──
    ("deelnemen", "aan", "to participate in", False, "Hij neemt deel aan de vergadering. → He participates in the meeting."),
    ("denken", "aan", "to think about", False, "Ik denk aan mijn vakantie. → I'm thinking about my vacation."),
    ("dromen", "van", "to dream of", False, "Ze droomt van een wereldreis. → She dreams of a world trip."),
    # ── G ──
    ("geloven", "in", "to believe in", False, "Ik geloof in gelijkheid. → I believe in equality."),
    ("geïnteresseerd zijn", "in", "to be interested in", False, "Ze is geïnteresseerd in kunst. → She is interested in art."),
    # ── H ──
    ("helpen", "met", "to help with", False, "Kun je me helpen met mijn huiswerk? → Can you help me with my homework?"),
    ("hopen", "op", "to hope for", False, "Ik hoop op goed weer morgen. → I hope for good weather tomorrow."),
    ("houden", "van", "to love / like", False, "Ik houd van chocolade. → I love chocolate."),
    # ── I ──
    ("informeren", "naar", "to ask about / inquire about", False, "Ik wil graag informeren naar de openingstijden. → I would like to ask about the opening hours."),
    # ── K ──
    ("kijken", "naar", "to look at / watch", False, "We kijken naar een film. → We are watching a movie."),
    ("klagen", "over", "to complain about", False, "Hij klaagt over het lawaai. → He complains about the noise."),
    # ── L ──
    ("lachen", "om", "to laugh at / about", False, "Ze lachen om de grap. → They laugh at the joke."),
    ("lijden", "aan", "to suffer from", False, "Hij lijdt aan een zeldzame ziekte. → He suffers from a rare disease."),
    ("luisteren", "naar", "to listen to", False, "Ik luister naar muziek. → I listen to music."),
    # ── N ──
    ("nadenken", "over", "to think about / reflect on", False, "Ik moet even nadenken over je voorstel. → I need to think about your proposal."),
    # ── O ──
    ("omgaan", "met", "to deal with / handle", False, "Ze kan goed omgaan met stress. → She can handle stress well."),
    ("ophouden", "met", "to stop / quit", False, "Hij houdt op met roken. → He quits smoking."),
    # ── P ──
    ("praten", "over", "to talk about", False, "We praten over onze plannen. → We are talking about our plans."),
    ("protesteren", "tegen", "to protest against", False, "Ze protesteren tegen de nieuwe wet. → They are protesting against the new law."),
    # ── R ──
    ("reageren", "op", "to react to / respond to", False, "Hij reageert op het nieuws. → He reacts to the news."),
    ("rekenen", "op", "to count on / rely on", False, "Je kunt op me rekenen. → You can count on me."),
    # ── S ──
    ("schrikken", "van", "to be startled by", False, "Ik schrik van harde geluiden. → I am startled by loud noises."),
    ("slagen", "voor", "to pass (an exam)", False, "Hij is geslaagd voor zijn rijexamen. → He passed his driving test."),
    ("spelen", "met", "to play with", False, "De kinderen spelen met hun speelgoed. → The children are playing with their toys."),
    ("stoppen", "met", "to stop / quit", False, "Hij stopt met roken. → He quits smoking."),
    # ── T ──
    ("teleurgesteld zijn", "in", "to be disappointed in", False, "Ze is teleurgesteld in haar resultaten. → She is disappointed in her results."),
    ("terugkomen", "op", "to return to / come back to", False, "Hij komt terug op zijn beslissing. → He comes back to his decision."),
    ("twijfelen", "aan", "to doubt", False, "Ik twijfel aan zijn verhaal. → I doubt his story."),
    # ── V ──
    ("verlangen", "naar", "to long for", False, "Ze verlangt naar een vakantie. → She longs for a vacation."),
    ("vertrouwen", "op", "to trust / rely on", False, "Ik vertrouw op jouw oordeel. → I trust your judgment."),
    ("vragen", "om", "to ask for", False, "Ik vraag om hulp. → I ask for help."),
    ("vriendelijk zijn", "voor", "to be kind to", False, "Wees vriendelijk voor anderen. → Be kind to others."),
    # ── W ──
    ("werken", "aan", "to work on", False, "Hij werkt aan een nieuw project. → He is working on a new project."),
    ("wijzen", "op", "to point out", False, "Hij wijst op de fout. → He points out the mistake."),
    # ── Z ──
    ("zorgen", "voor", "to take care of / provide for", False, "Ze zorgt voor haar kinderen. → She takes care of her children."),
    # ── Reflexive ──
    ("zich aanpassen", "aan", "to adapt to", True, "Je moet je aanpassen aan nieuwe situaties. → You have to adapt to new situations."),
    ("zich afvragen", "of", "to wonder if", True, "Ik vraag me af of hij komt. → I wonder if he is coming."),
    ("zich baseren", "op", "to be based on", True, "Zijn theorie is gebaseerd op onderzoek. → His theory is based on research."),
    ("zich bezighouden", "met", "to occupy oneself with", True, "Ze houdt zich bezig met vrijwilligerswerk. → She occupies herself with volunteer work."),
    ("zich concentreren", "op", "to concentrate on", True, "Je moet je concentreren op je studie. → You need to concentrate on your studies."),
    ("zich herinneren", "aan", "to remember", True, "Ik herinner me dat moment nog goed. → I still remember that moment well."),
    ("zich interesseren", "voor", "to be interested in", True, "Hij interesseert zich voor geschiedenis. → He is interested in history."),
    ("zich neerleggen", "bij", "to accept / resign oneself to", True, "Je moet je neerleggen bij de situatie. → You have to accept the situation."),
    ("zich richten", "op", "to focus on", True, "We richten ons op het verbeteren van de service. → We are focusing on improving the service."),
    ("zich verheugen", "op", "to look forward to", True, "Ik verheug me op het feest. → I'm looking forward to the party."),
    ("zich vergissen", "in", "to be mistaken about", True, "Je vergist je in de datum. → You are mistaken about the date."),
    ("zich verzetten", "tegen", "to oppose / resist", True, "Ze verzetten zich tegen de plannen. → They are opposing the plans."),
    ("zich voorbereiden", "op", "to prepare for", True, "We bereiden ons voor op de presentatie. → We are preparing for the presentation."),
]

# Unique prepositions in the pool (for distractor selection)
_ALL_PREPOSITIONS = sorted({p for _, p, _, _, _ in PREP_VERB_PAIRS})

# Lookup verb → (preposition, english, reflexive, sentence)
_PAIR_LOOKUP: Dict[str, tuple] = {v: (p, e, r, s) for v, p, e, r, s in PREP_VERB_PAIRS}
    

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pair_to_question(pair: models.PrepVerbPair, mode: str, is_review: bool = False) -> Dict[str, Any]:
    """Serialise an ORM PrepVerbPair row to the question payload the frontend expects."""
    try:
        prep_distractors = json.loads(pair.prep_distractors) if pair.prep_distractors else []
    except (ValueError, TypeError):
        prep_distractors = []

    base = {
        "pair_id": pair.id,
        "verb": pair.verb,
        "preposition": pair.preposition,
        "english_translation": pair.english_translation,
        "reflexive": pair.reflexive,
        "mode": mode,
        "is_review": is_review,
    }

    if mode == "prep":
        return {
            **base,
            "sentence": pair.prep_sentence,
            "english_hint": pair.prep_english,
            "correct_answer": pair.preposition,
            "distractors": prep_distractors,
            "explanation": pair.prep_explanation,
        }
    else:  # hard
        return {
            **base,
            "sentence": pair.hard_sentence,
            "english_hint": pair.hard_english,
            "correct_verb": pair.hard_correct_verb,
            "correct_prep": pair.preposition,
            "explanation": pair.hard_explanation,
        }


def _pick_random_pair(verb_filter: Optional[str]) -> tuple:
    """Return a random (verb, preposition, english, reflexive) from the built-in list."""
    pool = PREP_VERB_PAIRS
    if verb_filter:
        pool = [t for t in PREP_VERB_PAIRS if t[0] == verb_filter]
    if not pool:
        pool = PREP_VERB_PAIRS
    return random.choice(pool)


# ---------------------------------------------------------------------------
# Question generator — called by route handler
# ---------------------------------------------------------------------------

async def generate_question(
    db: Session,
    user_id: int,
    mode: str,                               # "prep" | "hard"
    verb_filter: Optional[str] = None,
    excluded_pair_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Return a question dict for the given user and mode.

    Priority:
      1. needs_review pairs (spaced repetition)
      2. Cached pairs this user hasn't seen yet
      3. LLM generate a new sentence for a pair that exists but has no sentences,
         OR choose a random pair from the built-in list and generate sentences.
    """
    excluded: Set[int] = set(excluded_pair_ids or [])

    # ── Helper: does this pair have sentences for the requested mode? ──────
    def _has_sentences(p: models.PrepVerbPair) -> bool:
        if mode == "prep":
            return bool(p.prep_sentence)
        return bool(p.hard_sentence)

    # ── 1. Review queue ────────────────────────────────────────────────────
    review_q = (
        db.query(models.PrepVerbStat)
        .join(models.PrepVerbPair)
        .filter(
            models.PrepVerbStat.user_id == user_id,
            models.PrepVerbStat.needs_review == True,  # noqa: E712
        )
    )
    if excluded:
        review_q = review_q.filter(models.PrepVerbStat.pair_id.notin_(excluded))
    if verb_filter:
        review_q = review_q.filter(models.PrepVerbPair.verb == verb_filter)

    review_candidates = [s for s in review_q.all() if _has_sentences(s.pair)]
    if review_candidates:
        stat = random.choice(review_candidates)
        return _pair_to_question(stat.pair, mode, is_review=True)

    # ── 2. Unseen cached pairs ─────────────────────────────────────────────
    seen_ids = {
        row.pair_id
        for row in db.query(models.PrepVerbStat.pair_id).filter(
            models.PrepVerbStat.user_id == user_id,
            models.PrepVerbStat.times_seen > 0,
        ).all()
    }
    already_excluded = excluded | seen_ids

    cached_q = db.query(models.PrepVerbPair)
    if already_excluded:
        cached_q = cached_q.filter(models.PrepVerbPair.id.notin_(already_excluded))
    if verb_filter:
        cached_q = cached_q.filter(models.PrepVerbPair.verb == verb_filter)

    cached_candidates = [p for p in cached_q.all() if _has_sentences(p)]
    if cached_candidates:
        pair = random.choice(cached_candidates)
        return _pair_to_question(pair, mode, is_review=False)

    # ── 3. LLM fallback ───────────────────────────────────────────────────
    # Choose a pair from the built-in list that exists in DB but lacks sentences,
    # or create a new DB row for a freshly chosen pair.
    verb, preposition, english, reflexive = _pick_random_pair(verb_filter)

    # Find or create the DB row for this pair
    pair = db.query(models.PrepVerbPair).filter(
        models.PrepVerbPair.verb == verb,
        models.PrepVerbPair.preposition == preposition,
    ).first()

    if pair is None:
        pair = models.PrepVerbPair(
            verb=verb,
            preposition=preposition,
            english_translation=english,
            reflexive=reflexive,
        )
        db.add(pair)
        db.flush()  # get pair.id without committing

    # Generate sentences via LLM
    raw = await OpenRouterService.generate_prep_verb_question(verb, preposition, english, reflexive)

    # Persist both modes so we only ever call the LLM once per pair
    pair.prep_sentence = raw["prep_sentence"]
    pair.prep_english = raw["prep_english"]
    pair.prep_explanation = raw["prep_explanation"]
    pair.prep_distractors = json.dumps(raw.get("prep_distractors", [])[:3])
    pair.hard_sentence = raw["hard_sentence"]
    pair.hard_english = raw["hard_english"]
    pair.hard_correct_verb = raw["hard_correct_verb"]
    pair.hard_correct_prep = raw["hard_correct_prep"]
    pair.hard_explanation = raw["hard_explanation"]

    db.commit()
    db.refresh(pair)

    return _pair_to_question(pair, mode, is_review=False)


# ---------------------------------------------------------------------------
# PrepVerbGameService — per-user logic
# ---------------------------------------------------------------------------

class PrepVerbGameService:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        sessions = (
            self.db.query(models.PrepVerbGameSession)
            .filter(models.PrepVerbGameSession.user_id == self.user_id)
            .order_by(models.PrepVerbGameSession.played_at.desc())
            .all()
        )
        if not sessions:
            return {
                "total_games": 0,
                "avg_accuracy": 0,
                "questions_answered": 0,
                "current_streak": 0,
                "hardest_pairs": [],
                "review_queue_size": self._review_queue_size(),
            }

        total = len(sessions)
        avg_acc = round(sum(s.accuracy for s in sessions) / total)
        questions_answered = sum(s.question_count for s in sessions)

        streak = 0
        for s in sessions:
            if s.accuracy >= 70:
                streak += 1
            else:
                break

        pair_stats: Dict[str, Dict] = {}
        for s in sessions:
            for ans in s.answers:
                key = f"{ans.verb} {ans.preposition}"
                if key not in pair_stats:
                    pair_stats[key] = {"seen": 0, "wrong": 0}
                pair_stats[key]["seen"] += 1
                if not ans.is_correct:
                    pair_stats[key]["wrong"] += 1

        hardest = sorted(
            [
                {
                    "pair": k,
                    "times_seen": v["seen"],
                    "times_wrong": v["wrong"],
                    "error_rate": round(v["wrong"] / v["seen"] * 100) if v["seen"] else 0,
                }
                for k, v in pair_stats.items()
                if v["wrong"] > 0
            ],
            key=lambda x: -x["error_rate"],
        )[:10]

        return {
            "total_games": total,
            "avg_accuracy": avg_acc,
            "questions_answered": questions_answered,
            "current_streak": streak,
            "hardest_pairs": hardest,
            "review_queue_size": self._review_queue_size(),
        }

    def _review_queue_size(self) -> int:
        return (
            self.db.query(models.PrepVerbStat)
            .filter(
                models.PrepVerbStat.user_id == self.user_id,
                models.PrepVerbStat.needs_review == True,  # noqa: E712
            )
            .count()
        )

    # ------------------------------------------------------------------
    # Save a completed game
    # ------------------------------------------------------------------

    def save_game(self, answers: List[Dict[str, Any]], mode: str) -> models.PrepVerbGameSession:
        """
        Persist a completed game session and update spaced-repetition stats.

        Each answer dict must have:
            verb, preposition, sentence, correct_answer, user_answer,
            english_hint, pair_id (optional), mode
        For hard mode correct_answer is the preposition only (verb is scored separately).
        """
        if not answers:
            raise ProcessingError("No answers provided")

        scored = []
        for a in answers:
            if mode == "prep":
                user_ans = (a.get("user_answer") or "").strip().lower()
                correct = (a.get("correct_answer") or "").strip().lower()
                is_correct = user_ans == correct
            else:
                # Hard mode: user submits verb + prep separately
                user_verb = (a.get("user_verb") or "").strip().lower()
                user_prep = (a.get("user_prep") or "").strip().lower()
                correct_verb = (a.get("correct_verb") or "").strip().lower()
                correct_prep = (a.get("correct_prep") or "").strip().lower()
                is_correct = user_verb == correct_verb and user_prep == correct_prep
                a = {
                    **a,
                    "correct_answer": f"{a.get('correct_verb', '')} {a.get('correct_prep', '')}",
                    "user_answer": f"{a.get('user_verb', '')} {a.get('user_prep', '')}",
                }
            scored.append({**a, "is_correct": is_correct})

        score = sum(1 for a in scored if a["is_correct"])
        accuracy = round(score / len(scored) * 100)

        session = models.PrepVerbGameSession(
            user_id=self.user_id,
            played_at=datetime.now(timezone.utc),
            mode=mode,
            question_count=len(scored),
            score=score,
            accuracy=accuracy,
        )
        self.db.add(session)
        self.db.flush()

        for a in scored:
            pair_id: Optional[int] = a.get("pair_id")
            self.db.add(models.PrepVerbGameAnswer(
                session_id=session.id,
                pair_id=pair_id,
                mode=mode,
                verb=a.get("verb", ""),
                preposition=a.get("preposition", ""),
                sentence=a.get("sentence", ""),
                correct_answer=a.get("correct_answer", ""),
                user_answer=a.get("user_answer", ""),
                is_correct=a["is_correct"],
                english_hint=a.get("english_hint"),
            ))

            if pair_id:
                pair = self.db.get(models.PrepVerbPair, pair_id)
                if pair:
                    pair.times_seen = (pair.times_seen or 0) + 1
                    if a["is_correct"]:
                        pair.times_correct = (pair.times_correct or 0) + 1

                stat = (
                    self.db.query(models.PrepVerbStat)
                    .filter_by(user_id=self.user_id, pair_id=pair_id)
                    .first()
                )
                if stat is None:
                    stat = models.PrepVerbStat(
                        user_id=self.user_id,
                        pair_id=pair_id,
                        times_seen=0,
                        times_correct=0,
                        needs_review=False,
                    )
                    self.db.add(stat)

                stat.times_seen = (stat.times_seen or 0) + 1
                stat.last_seen_at = datetime.now(timezone.utc)
                if a["is_correct"]:
                    stat.times_correct = (stat.times_correct or 0) + 1
                    stat.needs_review = False
                else:
                    stat.needs_review = True

        self.db.commit()
        self.db.refresh(session)
        return session
