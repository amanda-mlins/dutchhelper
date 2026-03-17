"""API routes for DutchHelper"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.verb_game_service import VerbGameService, generate_question, DEFAULT_VERB_POOL
from app.conjunction_game_service import ConjunctionGameService, generate_question as conj_generate_question

from app.schemas import (
    Message, 
    TextAnalysisRequest, 
    AnalyzeSentenceRequest, 
    TextAnalysisResponse, 
    SentenceAnalysis,
    SplitSentencesResponse,
    ConjugateVerbRequest,
    ConjugateVerbResponse
)
from app.services import SentenceAnalyzerService
from app.nlp_service import NLPService
from app.verb_conjugation_service import VerbConjugationService
from app.article_game_service import ArticleGameService, get_guest_words, check_answer
from app.exceptions import ValidationError, ProcessingError
from app.auth_service import get_current_user, get_current_user_optional, get_admin_user
from app.database import get_db, init_db
from app.word_list_service import WordListService
from . import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

# Game-related Pydantic models
class GameWordResponse(BaseModel):
    """Response model for game words."""
    word: str
    difficulty: str
    category: str

class GameWordsRequest(BaseModel):
    """Request model for getting game words."""
    count: int = 20
    mode: str = "smart"   # smart | mistakes | wordbank | random  (ignored for guests)
    personalized: bool = True

class SubmitAnswerRequest(BaseModel):
    """Request model for submitting an answer."""
    word: str
    user_answer: str

class SubmitAnswerResponse(BaseModel):
    """Response model for answer submission."""
    is_correct: bool
    word: str
    correct_article: str
    user_answer: str
    difficulty: str
    category: str

class SaveGameRequest(BaseModel):
    """Request model for saving game results."""
    answers: List[dict]

class GameResult(BaseModel):
    """Model for game result."""
    game_id: int
    score: int
    total_questions: int
    accuracy: float

# This will create the database tables if they don't exist
init_db()

@router.post("/message", response_model=Message)
async def send_message(request: Request, message: Message):
    """
    Echo a message back (placeholder endpoint for testing).
    
    Args:
        message: Message to echo
        
    Returns:
        Echo response with received status
    """
    logger.info(f"Message received: {message.text[:100] if message.text else 'empty'}")
    return {"text": f"You said: {message.text[:100]}", "status": "received"}

@router.post("/split-sentences", response_model=SplitSentencesResponse)
async def split_sentences(request: Request, body: TextAnalysisRequest):
    """
    Split Dutch text into sentences using robust pysbd library.
    
    This endpoint is fast (no LLM needed) and enables progressive UI updates.
    The frontend receives split sentences immediately and can then analyze each
    one in parallel using the /api/analyze-sentence endpoint.
    
    Args:
        body: TextAnalysisRequest containing the Dutch text to split
        
    Returns:
        SplitSentencesResponse with list of sentences
        
    Raises:
        HTTPException: If text is empty or invalid (400, 429 for rate limit)
    """
    try:
        if not body.text or not body.text.strip():
            raise ValidationError("Text cannot be empty")
        
        # Additional validation via pydantic handles constraints
        logger.info(f"Splitting text: {body.text[:100]}...")
        
        sentences = NLPService.split_sentences(body.text)
        
        logger.info(f"Split complete: {len(sentences)} sentences found")
        
        return SplitSentencesResponse(
            sentences=sentences,
            count=len(sentences)
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in split_sentences: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Error splitting sentences: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to split sentences")

@router.post("/analyze", response_model=TextAnalysisResponse)
async def analyze_text(request: Request, body: TextAnalysisRequest):
    """
    Analyze Dutch text and break it down into grammatical components.
    
    Args:
        body: TextAnalysisRequest containing the Dutch text to analyze
        
    Returns:
        TextAnalysisResponse with sentences and their grammatical components
        
    Raises:
        HTTPException: If text is empty, invalid, or analysis fails (400, 429, 500)
    """
    try:
        if not body.text or not body.text.strip():
            raise ValidationError("Text cannot be empty")
        
        # Additional validation via pydantic handles constraints
        logger.info(f"Analyzing text: {body.text[:100]}...")
        
        analysis = await SentenceAnalyzerService.analyze_text(body.text)
        
        logger.info(f"Analysis complete: {len(analysis.sentences)} sentences found")
        
        return analysis
        
    except ValidationError as e:
        logger.error(f"Validation error in analyze_text: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except ProcessingError as e:
        logger.error(f"Processing error in analyze_text: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze text")

@router.post("/analyze-sentence", response_model=SentenceAnalysis)
async def analyze_sentence(request: Request, body: AnalyzeSentenceRequest):
    """
    Analyze a single sentence for grammatical components.
    
    This endpoint is designed to be called from the frontend for parallel processing.
    Multiple requests are sent concurrently, with each sentence analyzed independently.
    Results are returned as soon as they're ready, enabling progressive UI updates.
    
    Args:
        body: AnalyzeSentenceRequest containing a single sentence to analyze
        
    Returns:
        SentenceAnalysis with sentence translation and grammatical components
        
    Raises:
        HTTPException: If sentence is empty, invalid, or analysis fails (400, 429, 500)
    """
    try:
        sentence = body.sentence.strip()
        
        if not sentence:
            raise HTTPException(status_code=400, detail="Sentence cannot be empty")
        
        # Validation via pydantic ensures constraints are met
        logger.info(f"[Parallel] Analyzing sentence: {sentence[:50]}...")
        
        # Use service to analyze single sentence
        result = await SentenceAnalyzerService.analyze_single_sentence(sentence)
        
        logger.info(f"[Parallel] Analysis complete for: {sentence[:50]}...")
        
        return result
        
    except ProcessingError as e:
        logger.error(f"[Parallel] Processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Parallel] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/conjugate", response_model=ConjugateVerbResponse)
async def conjugate_verb(request: Request, body: ConjugateVerbRequest):
    """
    Conjugate a Dutch verb across all tenses and persons.
    
    First tries to find the verb in the local database (~15 common verbs).
    If not found, uses OpenRouter LLM to generate the conjugation.
    
    Args:
        body: ConjugateVerbRequest containing the verb to conjugate
        
    Returns:
        ConjugateVerbResponse with conjugations, translations, and examples
        
    Raises:
        HTTPException: If verb is empty, invalid, cannot be conjugated (400, 404, 429, 500)
    """
    try:
        if not body.verb or not body.verb.strip():
            raise HTTPException(status_code=400, detail="Please enter a verb to conjugate")
        
        verb = body.verb.strip().lower()
        # Validation via pydantic ensures format constraints are met
        logger.info(f"Conjugating verb (with LLM fallback): {verb}")
        
        # Use the async method with LLM fallback
        conjugation_data = await VerbConjugationService.conjugate_verb_with_llm(verb)
        
        logger.info(f"Successfully conjugated verb: {verb}")
        
        # Return the data as ConjugateVerbResponse
        return ConjugateVerbResponse(**conjugation_data)
        
    except ProcessingError as e:
        logger.error(f"Failed to conjugate verb: {str(e)}")
        # Provide user-friendly message instead of raw error
        raise HTTPException(
            status_code=404, 
            detail=f"Sorry, I couldn't conjugate '{body.verb}'. Please try another verb or check the spelling."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conjugating verb: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again in a moment.")

@router.get("/database-stats")
async def get_database_stats(
    request: Request,
    _admin: models.User = Depends(get_admin_user),
):
    """
    Get statistics about the verb conjugation database.
    Requires authentication + admin flag.
    """
    try:
        from app.verb_database_manager import VerbDatabaseManager
        
        stats = VerbDatabaseManager.get_database_stats()
        query_stats = VerbDatabaseManager.get_query_statistics()
        savings = VerbDatabaseManager.estimate_llm_savings()
        
        return {
            'database': stats,
            'queries': query_stats,
            'savings': savings
        }
    except Exception as e:
        logger.error(f"Error getting database statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve database statistics")


@router.post("/database-export")
async def export_database(
    request: Request,
    _admin: models.User = Depends(get_admin_user),
):
    """
    Export all verbs to a JSON file for version control.
    Requires authentication + admin flag.
    """
    try:
        from app.verb_database_manager import VerbDatabaseManager
        
        export_path = VerbDatabaseManager.export_to_json()
        stats = VerbDatabaseManager.get_database_stats()
        
        return {
            'success': True,
            'export_path': export_path,
            'verbs_exported': stats.get('total_verbs', 0)
        }
    except Exception as e:
        logger.error(f"Error exporting database: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export database")


# ============================================================================
# Article Game Endpoints
# ============================================================================

@router.post("/game/words")
def api_get_game_words(
    body: GameWordsRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    """
    Return a word list for a game session.
    Guests get a random selection. Authenticated users get a personalised mix.
    """
    try:
        if body.count > 50:
            raise HTTPException(status_code=400, detail="count must be less than 50")
        if current_user:
            svc = ArticleGameService(db, current_user.id)
            words = svc.get_words(body.count, body.mode)
        else:
            words = get_guest_words(body.count)
        return {"words": words, "count": len(words)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game words: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get game words")


@router.post("/game/submit")
def api_submit_answer(body: SubmitAnswerRequest):
    """Stateless: check one answer. Works for guests and logged-in users alike."""
    if body.user_answer.lower() not in ("de", "het"):
        raise HTTPException(status_code=400, detail="Answer must be 'de' or 'het'")
    result = check_answer(body.word, body.user_answer)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/game/save")
def api_save_game(
    body: SaveGameRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Save a completed game and update mistake weights. Requires login."""
    if not body.answers:
        raise HTTPException(status_code=400, detail="answers list cannot be empty")
    svc = ArticleGameService(db, current_user.id)
    session = svc.save_game(body.answers)
    return {
        "session_id": session.id,
        "score": session.score,
        "word_count": session.word_count,
        "accuracy": session.accuracy,
    }


@router.get("/game/stats")
def api_get_game_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the user's game statistics. Requires login."""
    svc = ArticleGameService(db, current_user.id)
    return svc.get_stats()


@router.get("/game/history")
def api_get_game_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return all game sessions with per-answer detail. Requires login."""
    svc = ArticleGameService(db, current_user.id)
    return svc.get_history()


# ============================================================================
# Verb Game Endpoints
# ============================================================================

class VerbGameQuestionRequest(BaseModel):
    verb: Optional[str] = None            # Specific verb; omit to pick randomly
    tenses: Optional[List[str]] = None    # Restrict to these tenses; omit for all
    use_word_bank: bool = False           # Pick random verb from user's word bank

class VerbGameSaveRequest(BaseModel):
    answers: List[dict]


@router.get("/verb-game/word-bank-verbs")
def api_verb_game_word_bank_verbs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return the user's word bank entries that are verbs (word_type='verb').
    Used by the frontend to populate the word-bank verb selection.
    """
    words = (
        db.query(models.UserWord)
        .filter(
            models.UserWord.user_id == current_user.id,
            models.UserWord.word_type == "verb",
        )
        .order_by(models.UserWord.word)
        .all()
    )
    return [{"id": w.id, "word": w.word} for w in words]


@router.post("/verb-game/question")
async def api_verb_game_question(
    body: VerbGameQuestionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    """
    Generate a single fill-in-the-blank question.
    - If verb is provided, use it.
    - Else if use_word_bank=True and user is logged in, pick a random verb from
      the user's word bank verbs (falls back to default pool if word bank is empty).
    - Otherwise pick from the default pool.
    - tenses (optional) restricts which tenses the LLM may generate.
    Works for both logged-in users and guests (guests always use the default pool).
    """
    from app.exceptions import ProcessingError
    import random as _random

    verb = (body.verb or "").strip().lower() or None
    if not verb:
        if body.use_word_bank and current_user:
            wb_verbs = (
                db.query(models.UserWord.word)
                .filter(
                    models.UserWord.user_id == current_user.id,
                    models.UserWord.word_type == "verb",
                )
                .all()
            )
            wb_verb_list = [row.word for row in wb_verbs]
            if wb_verb_list:
                verb = _random.choice(wb_verb_list)
            else:
                # Fall back to default pool if word bank has no verbs
                verb = _random.choice(DEFAULT_VERB_POOL)
        else:
            verb = _random.choice(DEFAULT_VERB_POOL)

    tenses = body.tenses or None
    try:
        question = await generate_question(verb, tenses=tenses)
        return question
    except ProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating verb game question for '{verb}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate question")


@router.post("/verb-game/save")
def api_verb_game_save(
    body: VerbGameSaveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Save a completed verb game session. Requires login."""
    from app.exceptions import ProcessingError
    if not body.answers:
        raise HTTPException(status_code=400, detail="answers list cannot be empty")
    svc = VerbGameService(db, current_user.id)
    try:
        session = svc.save_game(body.answers)
    except ProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "session_id": session.id,
        "score": session.score,
        "question_count": session.question_count,
        "accuracy": session.accuracy,
    }


@router.get("/verb-game/stats")
def api_verb_game_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the user's verb game statistics. Requires login."""
    svc = VerbGameService(db, current_user.id)
    return svc.get_stats()


@router.get("/verb-game/history")
def api_verb_game_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return all verb game sessions with per-answer detail. Requires login."""
    svc = VerbGameService(db, current_user.id)
    return svc.get_history()


# ============================================================================
# Conjunction Game Endpoints
# ============================================================================

class ConjunctionGameQuestionRequest(BaseModel):
    conjunction: Optional[str] = None              # Specific conjunction; omit to pick randomly
    conjunction_types: Optional[List[str]] = None  # Filter by type(s): coordinating / subordinating / correlative
    excluded_sentence_ids: Optional[List[int]] = None  # IDs already used in this game session

class ConjunctionGameSaveRequest(BaseModel):
    answers: List[dict]


@router.post("/conjunction-game/question")
async def api_conjunction_game_question(
    body: ConjunctionGameQuestionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    """
    Return a conjunction fill-in-the-blank question.

    Priority: needs_review sentences → unseen cached sentences → LLM-generated (then cached).
    Pass excluded_sentence_ids to avoid repeating questions within the same game session.
    Works for both logged-in users and guests (guests skip the personal review queue).
    """
    from app.exceptions import ProcessingError
    conjunction = (body.conjunction or "").strip().lower() or None
    user_id = current_user.id if current_user else None
    try:
        question = await conj_generate_question(
            db=db,
            user_id=user_id,
            conjunction=conjunction,
            conjunction_types=body.conjunction_types or None,
            excluded_sentence_ids=body.excluded_sentence_ids or [],
        )
        return question
    except ProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating conjunction question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate question")


@router.post("/conjunction-game/save")
def api_conjunction_game_save(
    body: ConjunctionGameSaveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Save a completed conjunction game session. Requires login."""
    from app.exceptions import ProcessingError
    if not body.answers:
        raise HTTPException(status_code=400, detail="answers list cannot be empty")
    svc = ConjunctionGameService(db, current_user.id)
    try:
        session = svc.save_game(body.answers)
    except ProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "session_id": session.id,
        "score": session.score,
        "question_count": session.question_count,
        "accuracy": session.accuracy,
    }


@router.get("/conjunction-game/stats")
def api_conjunction_game_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the user's conjunction game statistics. Requires login."""
    svc = ConjunctionGameService(db, current_user.id)
    return svc.get_stats()


@router.get("/conjunction-game/history")
def api_conjunction_game_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return all conjunction game sessions with per-answer detail. Requires login."""
    svc = ConjunctionGameService(db, current_user.id)
    return svc.get_history()


@router.get("/conjunction-game/sentence-pool")
def api_conjunction_game_sentence_pool(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return all cached conjunction sentences with global and per-user stats.
    Useful for admins / curious players to see the sentence library.
    Requires login.
    """
    import json as _json

    sentences = (
        db.query(models.ConjunctionSentence)
        .order_by(models.ConjunctionSentence.conjunction, models.ConjunctionSentence.id)
        .all()
    )

    # Build a lookup: sentence_id → user stat row
    user_stats = {
        row.sentence_id: row
        for row in db.query(models.ConjunctionSentenceStat).filter_by(user_id=current_user.id).all()
    }

    result = []
    for s in sentences:
        us = user_stats.get(s.id)
        global_rate = (
            round((1 - s.times_correct / s.times_seen) * 100)
            if s.times_seen else None
        )
        result.append({
            "id": s.id,
            "conjunction": s.conjunction,
            "conjunction_type": s.conjunction_type,
            "sentence": s.sentence,
            "correct_answer": s.correct_answer,
            "english_hint": s.english_hint,
            "distractors": _json.loads(s.distractors) if s.distractors else [],
            "global_times_seen": s.times_seen,
            "global_times_correct": s.times_correct,
            "global_error_rate": global_rate,
            "created_at": s.created_at.isoformat(),
            # Per-user fields (None if user has never seen this sentence)
            "user_times_seen": us.times_seen if us else 0,
            "user_times_correct": us.times_correct if us else 0,
            "user_needs_review": us.needs_review if us else False,
            "user_last_seen_at": us.last_seen_at.isoformat() if us else None,
        })
    return result


# --- Word Bank API Endpoints (require authentication) ---

class WordBulkAddRequest(BaseModel):
    words: List[str]


class WordBulkDeleteRequest(BaseModel):
    word_ids: List[int]


class WordBulkCategoryRequest(BaseModel):
    word_ids: List[int]
    category: Optional[str] = None  # None / "" clears the category


class QuickAddWordRequest(BaseModel):
    word: str
    word_type: Optional[str] = "word"        # noun / verb / adjective / word / …
    category: Optional[str] = None           # e.g. "Conjunction", "Verb"
    context_sentence: Optional[str] = None   # sentence the word appeared in


@router.post("/word-bank/words/quick", status_code=200)
def quick_add_word(
    body: QuickAddWordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Fast, no-LLM path: save a single Dutch word to the user's word bank.

    Use this when the word is already known-good (e.g. extracted from a
    game sentence).  Returns { status: 'added'|'skipped', id }.
    Duplicates (same word, same user) are silently skipped.
    """
    word = body.word.strip().lower()
    if not word:
        raise HTTPException(status_code=400, detail="word cannot be empty")

    existing = (
        db.query(models.UserWord)
        .filter(models.UserWord.user_id == current_user.id,
                models.UserWord.word == word)
        .first()
    )
    if existing:
        return {"status": "skipped", "id": existing.id}

    entry = models.UserWord(
        user_id=current_user.id,
        word=word,
        word_type=body.word_type or "word",
        category=body.category or None,
    )
    entry.set_details(
        definition="",
        translation_en="",
        example=body.context_sentence or "",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "added", "id": entry.id}


@router.post("/word-bank/words", response_model=models.UserWordSchema, status_code=201)
async def add_user_word(
    word_data: models.UserWordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Adds a new word to the authenticated user's word bank."""
    from app.exceptions import ProcessingError
    service = WordListService(db)
    try:
        new_word = await service.add_word(word=word_data.word, user_id=current_user.id)
        return new_word
    except ProcessingError as e:
        # Invalid word — surface the LLM's explanation to the frontend
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding word '{word_data.word}': {e}")
        raise HTTPException(status_code=500, detail="Failed to add word. Please try again.")


class PrepPairWordBankItem(BaseModel):
    """Either a DB pair (id set) or a raw stub (id=None, verb/preposition/english provided)."""
    id: Optional[int] = None
    verb: Optional[str] = None
    preposition: Optional[str] = None
    english_translation: Optional[str] = None
    reflexive: Optional[bool] = False


class PrepPairWordBankRequest(BaseModel):
    pairs: List[PrepPairWordBankItem]


def _word_text_for_pair(verb: str, preposition: str, reflexive: bool) -> str:
    prefix = "zich " if reflexive and "zich" not in verb else ""
    return f"{prefix}{verb} {preposition}".strip()


@router.post("/word-bank/words/prep-pairs-bulk", status_code=200)
def save_prep_pairs_to_word_bank(
    body: PrepPairWordBankRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Save a list of prep-verb pairs to the user's word bank.
    Accepts either DB-row pairs (id set) or raw stubs (id=None with verb/prep/english).
    Skips duplicates matched by word text. Returns { added, skipped }.
    """
    added = 0
    skipped = 0

    for item in body.pairs:
        # Resolve data — prefer DB row if id is set
        if item.id is not None:
            db_pair = db.query(models.PrepVerbPair).filter(models.PrepVerbPair.id == item.id).first()
            if db_pair:
                verb = db_pair.verb
                preposition = db_pair.preposition
                reflexive = db_pair.reflexive
                english = db_pair.english_translation or item.english_translation or ""
                example = db_pair.prep_sentence.replace("___", db_pair.preposition) if db_pair.prep_sentence else ""
            else:
                # id provided but not found — fall back to inline data
                verb = item.verb or ""
                preposition = item.preposition or ""
                reflexive = item.reflexive or False
                english = item.english_translation or ""
                example = ""
        else:
            # Pure stub from built-in catalogue
            verb = item.verb or ""
            preposition = item.preposition or ""
            reflexive = item.reflexive or False
            english = item.english_translation or ""
            example = ""

        if not verb or not preposition:
            continue

        word_text = _word_text_for_pair(verb, preposition, reflexive)

        existing = db.query(models.UserWord).filter(
            models.UserWord.user_id == current_user.id,
            models.UserWord.word == word_text,
        ).first()
        if existing:
            skipped += 1
            continue

        entry = models.UserWord(
            user_id=current_user.id,
            word=word_text,
            word_type="expression",
            category="Verb + Preposition",
        )
        entry.set_details(
            definition=f"Fixed-preposition verb: {word_text}",
            translation_en=english,
            example=example,
        )
        db.add(entry)
        added += 1

    db.commit()
    return {"added": added, "skipped": skipped}


@router.post("/word-bank/words/bulk")
async def bulk_add_user_words(
    body: WordBulkAddRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Bulk-add a list of Dutch words to the authenticated user's word bank.

    Each word is validated via the LLM. Already-saved words are skipped.
    Up to 3 LLM calls run concurrently.

    Returns per-word results:
      { word, status: "added"|"skipped"|"error", error? }
    """
    import asyncio
    from app.exceptions import ProcessingError

    clean_words = list({w.strip().lower() for w in body.words if w.strip()})
    if not clean_words:
        raise HTTPException(status_code=400, detail="No valid words provided.")
    if len(clean_words) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 words per import.")

    service = WordListService(db)
    semaphore = asyncio.Semaphore(3)

    async def add_one(word: str) -> dict:
        async with semaphore:
            try:
                await service.add_word(word=word, user_id=current_user.id)
                return {"word": word, "status": "added"}
            except ProcessingError as e:
                return {"word": word, "status": "error", "error": str(e)}
            except Exception as e:
                logger.error(f"Bulk word-bank add: failed for '{word}': {e}")
                return {"word": word, "status": "error", "error": "Failed to add word."}

    results = await asyncio.gather(*[add_one(w) for w in clean_words])

    # Restore original order
    word_order = {w: i for i, w in enumerate(clean_words)}
    results = sorted(results, key=lambda r: word_order.get(r["word"], 999))

    added = sum(1 for r in results if r["status"] == "added")
    errors = sum(1 for r in results if r["status"] == "error")

    return {
        "summary": {"added": added, "errors": errors, "total": len(results)},
        "results": results,
    }


@router.delete("/word-bank/words/bulk", status_code=200)
def bulk_delete_user_words(
    body: WordBulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete multiple words from the authenticated user's word bank in one request.

    Only deletes words owned by the current user (ignores IDs that don't belong).
    Returns { deleted: N }.
    """
    if not body.word_ids:
        raise HTTPException(status_code=400, detail="No word IDs provided.")

    to_delete = (
        db.query(models.UserWord)
        .filter(
            models.UserWord.id.in_(body.word_ids),
            models.UserWord.user_id == current_user.id,
        )
        .all()
    )
    for word in to_delete:
        db.delete(word)
    db.commit()
    return {"deleted": len(to_delete)}


@router.get("/word-bank/words", response_model=List[models.UserWordSchema])
def get_user_words(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Retrieves all words for the authenticated user."""
    service = WordListService(db)
    words = service.get_words_for_user(user_id=current_user.id)
    return words

@router.put("/word-bank/words/{word_id}", response_model=models.UserWordSchema)
def update_user_word(
    word_id: int,
    word_data: models.UserWordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Updates a word in the authenticated user's word bank."""
    service = WordListService(db)
    updated_word = service.update_word(word_id, word_data, user_id=current_user.id)
    if not updated_word:
        raise HTTPException(status_code=404, detail="Word not found.")
    return updated_word

@router.delete("/word-bank/words/{word_id}", status_code=204)
def delete_user_word(
    word_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Deletes a word from the authenticated user's word bank."""
    service = WordListService(db)
    success = service.delete_word(word_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Word not found.")
    return Response(status_code=204)


@router.patch("/word-bank/words/{word_id}/category", response_model=models.UserWordSchema)
def set_word_category(
    word_id: int,
    body: models.UserWordCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Set or clear the category for a single word."""
    word = (
        db.query(models.UserWord)
        .filter(models.UserWord.id == word_id, models.UserWord.user_id == current_user.id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=404, detail="Word not found.")
    word.category = body.category or None
    db.commit()
    db.refresh(word)
    return word


@router.patch("/word-bank/words/bulk-category", status_code=200)
def bulk_set_category(
    body: WordBulkCategoryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Assign (or clear) a category for multiple words at once."""
    if not body.word_ids:
        raise HTTPException(status_code=400, detail="No word IDs provided.")
    words = (
        db.query(models.UserWord)
        .filter(
            models.UserWord.id.in_(body.word_ids),
            models.UserWord.user_id == current_user.id,
        )
        .all()
    )
    for w in words:
        w.category = body.category or None
    db.commit()
    return {"updated": len(words)}


@router.get("/word-bank/categories")
def get_user_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return all distinct category values used by the current user's words."""
    rows = (
        db.query(models.UserWord.category)
        .filter(
            models.UserWord.user_id == current_user.id,
            models.UserWord.category.isnot(None),
            models.UserWord.category != "",
        )
        .distinct()
        .all()
    )
    return sorted([r[0] for r in rows])


# ============================================================================
# Admin — Article Words CRUD
# ============================================================================

@router.get("/admin/article-words", response_model=List[models.ArticleWordSchema])
def admin_list_article_words(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Return every word in the article_words table (admin only)."""
    return db.query(models.ArticleWord).order_by(models.ArticleWord.word).all()


@router.post("/admin/article-words", response_model=models.ArticleWordSchema, status_code=201)
def admin_create_article_word(
    body: models.ArticleWordCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Add a new word to the article_words table (admin only)."""
    if body.article not in ("de", "het"):
        raise HTTPException(status_code=400, detail="article must be 'de' or 'het'")
    if db.query(models.ArticleWord).filter_by(word=body.word.lower()).first():
        raise HTTPException(status_code=409, detail=f"Word '{body.word}' already exists")
    from datetime import datetime, timezone
    row = models.ArticleWord(
        word=body.word.lower(),
        article=body.article,
        translation=body.translation,
        difficulty=body.difficulty,
        category=body.category,
        is_active=body.is_active,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/admin/article-words/{word_id}", response_model=models.ArticleWordSchema)
def admin_update_article_word(
    word_id: int,
    body: models.ArticleWordUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Update a word in the article_words table (admin only)."""
    row = db.query(models.ArticleWord).filter_by(id=word_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Word not found")
    if body.article is not None and body.article not in ("de", "het"):
        raise HTTPException(status_code=400, detail="article must be 'de' or 'het'")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/admin/article-words/{word_id}", status_code=204)
def admin_delete_article_word(
    word_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Delete a word from the article_words table (admin only)."""
    row = db.query(models.ArticleWord).filter_by(id=word_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Word not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)


class WordLookupRequest(BaseModel):
    word: str


@router.post("/admin/article-words/lookup")
async def admin_lookup_article_word(
    body: WordLookupRequest,
    _admin: models.User = Depends(get_admin_user),
):
    """
    Ask the LLM to suggest article, translation, difficulty and category
    for a Dutch word. Returns the suggestion without saving anything (admin only).
    Raises 422 if the word is not a recognised Dutch noun.
    """
    word = body.word.strip().lower()
    if not word:
        raise HTTPException(status_code=400, detail="word cannot be empty")
    try:
        from app.llm_service import OpenRouterService
        from app.exceptions import ProcessingError
        result = await OpenRouterService.get_article_word_details(word)
        return result
    except ProcessingError as e:
        # User-facing validation error (not a Dutch noun, gibberish, etc.)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"LLM lookup failed for '{word}': {e}")
        raise HTTPException(status_code=500, detail=f"LLM lookup failed: {e}")


class BulkImportRequest(BaseModel):
    words: List[str]


@router.post("/admin/article-words/bulk-import")
async def admin_bulk_import_words(
    body: BulkImportRequest,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """
    Bulk-import a list of Dutch words.

    For each word the LLM is called to determine article/translation/difficulty/category.
    Words already in the database are skipped.
    Up to 5 LLM calls run concurrently (semaphore-limited to avoid rate limits).

    Returns a list of per-word results:
      { word, status: "added"|"skipped"|"error", article?, translation?, difficulty?, category?, error? }
    """
    import asyncio
    from datetime import datetime, timezone
    from app.llm_service import OpenRouterService

    # Sanitise and deduplicate
    clean_words = list({w.strip().lower() for w in body.words if w.strip()})
    if not clean_words:
        raise HTTPException(status_code=400, detail="No valid words provided")
    if len(clean_words) > 200:
        raise HTTPException(status_code=400, detail="Maximum 200 words per import")

    # Find which words already exist
    existing = {
        row.word
        for row in db.query(models.ArticleWord.word)
        .filter(models.ArticleWord.word.in_(clean_words))
        .all()
    }

    to_add = [w for w in clean_words if w not in existing]
    results = [{"word": w, "status": "skipped", "reason": "already exists"} for w in clean_words if w in existing]

    # Concurrently query LLM with a semaphore so we don't hammer the API
    semaphore = asyncio.Semaphore(5)

    async def lookup_and_save(word: str) -> dict:
        async with semaphore:
            try:
                data = await OpenRouterService.get_article_word_details(word)
                row = models.ArticleWord(
                    word=word,
                    article=data["article"],
                    translation=data.get("translation"),
                    difficulty=data.get("difficulty", "medium"),
                    category=data.get("category"),
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(row)
                db.flush()
                return {
                    "word": word,
                    "status": "added",
                    "article": data["article"],
                    "translation": data.get("translation"),
                    "difficulty": data.get("difficulty", "medium"),
                    "category": data.get("category"),
                    "confidence_note": data.get("confidence_note"),
                }
            except Exception as e:
                from app.exceptions import ProcessingError
                # For invalid-word errors the message is already user-friendly;
                # for other errors include the raw detail for debugging.
                error_msg = str(e) if isinstance(e, ProcessingError) else f"LLM error: {e}"
                logger.error(f"Bulk import: failed for '{word}': {e}")
                return {"word": word, "status": "error", "error": error_msg}

    llm_results = await asyncio.gather(*[lookup_and_save(w) for w in to_add])

    # Commit all successful rows in one transaction
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk import: DB commit failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    results.extend(llm_results)

    # Sort by original word order for a predictable response
    word_order = {w: i for i, w in enumerate(clean_words)}
    results.sort(key=lambda r: word_order.get(r["word"], 999))

    added = sum(1 for r in results if r["status"] == "added")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")

    return {
        "summary": {"added": added, "skipped": skipped, "errors": errors, "total": len(results)},
        "results": results,
    }


# ============================================================================
# Admin — Verb Conjugations CRUD
# ============================================================================

@router.get("/admin/verbs", response_model=List[models.VerbConjugationSchema])
def admin_list_verbs(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Return every cached verb conjugation (admin only)."""
    return (
        db.query(models.VerbConjugation)
        .order_by(models.VerbConjugation.query_count.desc())
        .all()
    )


@router.delete("/admin/verbs/{verb_id}", status_code=204)
def admin_delete_verb(
    verb_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Delete a cached verb conjugation (admin only)."""
    row = db.query(models.VerbConjugation).filter_by(id=verb_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Verb not found")
    db.delete(row)
    db.commit()
    return Response(status_code=204)


class VerbLookupRequest(BaseModel):
    infinitive: str


@router.post("/admin/verbs/lookup")
async def admin_lookup_verb(
    body: VerbLookupRequest,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """
    Fetch (or re-fetch) conjugation data for a Dutch verb via LLM and save/update
    it in the database. Returns the saved VerbConjugation row (admin only).
    """
    infinitive = body.infinitive.strip().lower()
    if not infinitive:
        raise HTTPException(status_code=400, detail="infinitive cannot be empty")
    try:
        await VerbConjugationService.conjugate_verb_with_llm(infinitive)
    except Exception as e:
        logger.error(f"Admin verb lookup failed for '{infinitive}': {e}")
        raise HTTPException(status_code=500, detail=f"LLM lookup failed: {e}")

    # The service already persists the result; just return the DB row
    row = db.query(models.VerbConjugation).filter_by(infinitive=infinitive).first()
    if not row:
        raise HTTPException(status_code=500, detail="Verb was not persisted after LLM call")
    db.refresh(row)
    return models.VerbConjugationSchema.model_validate(row)


class VerbBulkImportRequest(BaseModel):
    infinitives: List[str]


@router.post("/admin/verbs/bulk-import")
async def admin_bulk_import_verbs(
    body: VerbBulkImportRequest,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """
    Bulk-import a list of Dutch verb infinitives.

    For each infinitive the LLM is called to generate full conjugation data.
    Verbs already cached in the database are skipped.
    Up to 3 LLM calls run concurrently (semaphore-limited to avoid rate limits).

    Returns { summary: {added, skipped, errors, total}, results: [...] }
    """
    import asyncio

    clean = list({v.strip().lower() for v in body.infinitives if v.strip()})
    if not clean:
        raise HTTPException(status_code=400, detail="No valid infinitives provided")
    if len(clean) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 verbs per import")

    existing = {
        row.infinitive
        for row in db.query(models.VerbConjugation.infinitive)
        .filter(models.VerbConjugation.infinitive.in_(clean))
        .all()
    }

    to_add = [v for v in clean if v not in existing]
    results = [{"infinitive": v, "status": "skipped", "reason": "already cached"} for v in clean if v in existing]

    semaphore = asyncio.Semaphore(3)

    async def fetch_one(infinitive: str) -> dict:
        async with semaphore:
            try:
                data = await VerbConjugationService.conjugate_verb_with_llm(infinitive)
                return {
                    "infinitive": infinitive,
                    "status": "added",
                    "english_translation": data.get("englishTranslation"),
                    "verb_type": data.get("verbType"),
                }
            except Exception as e:
                logger.error(f"Bulk verb import: LLM failed for '{infinitive}': {e}")
                return {"infinitive": infinitive, "status": "error", "error": str(e)}

    llm_results = await asyncio.gather(*[fetch_one(v) for v in to_add])
    results.extend(llm_results)

    infinitive_order = {v: i for i, v in enumerate(clean)}
    results.sort(key=lambda r: infinitive_order.get(r["infinitive"], 999))

    added = sum(1 for r in results if r["status"] == "added")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")

    return {
        "summary": {"added": added, "skipped": skipped, "errors": errors, "total": len(results)},
        "results": results,
    }


# ============================================================================
# Admin — Conjunction Sentences CRUD
# ============================================================================

class ConjunctionSentenceUpdate(BaseModel):
    sentence: Optional[str] = None
    correct_answer: Optional[str] = None
    english_hint: Optional[str] = None
    distractors: Optional[List[str]] = None   # list of 3 strings
    explanation: Optional[str] = None


@router.get("/admin/conjunction-sentences")
def admin_list_conjunction_sentences(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Return all cached conjunction sentences with global aggregate stats (admin only)."""
    import json as _json

    sentences = (
        db.query(models.ConjunctionSentence)
        .order_by(models.ConjunctionSentence.conjunction, models.ConjunctionSentence.id)
        .all()
    )

    # Count distinct users who have seen each sentence
    from sqlalchemy import func
    user_counts = dict(
        db.query(
            models.ConjunctionSentenceStat.sentence_id,
            func.count(models.ConjunctionSentenceStat.user_id),
        )
        .group_by(models.ConjunctionSentenceStat.sentence_id)
        .all()
    )

    result = []
    for s in sentences:
        error_rate = (
            round((1 - s.times_correct / s.times_seen) * 100)
            if s.times_seen else None
        )
        result.append({
            "id": s.id,
            "conjunction": s.conjunction,
            "conjunction_type": s.conjunction_type,
            "sentence": s.sentence,
            "correct_answer": s.correct_answer,
            "english_hint": s.english_hint,
            "distractors": _json.loads(s.distractors) if s.distractors else [],
            "explanation": s.explanation,
            "times_seen": s.times_seen,
            "times_correct": s.times_correct,
            "error_rate": error_rate,
            "unique_users": user_counts.get(s.id, 0),
            "created_at": s.created_at.isoformat(),
        })
    return result


@router.patch("/admin/conjunction-sentences/{sentence_id}")
def admin_update_conjunction_sentence(
    sentence_id: int,
    body: ConjunctionSentenceUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Edit a cached conjunction sentence (admin only)."""
    import json as _json

    s = db.get(models.ConjunctionSentence, sentence_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sentence not found")

    if body.sentence is not None:
        if "___" not in body.sentence:
            raise HTTPException(status_code=400, detail="sentence must contain ___")
        s.sentence = body.sentence
    if body.correct_answer is not None:
        s.correct_answer = body.correct_answer
    if body.english_hint is not None:
        s.english_hint = body.english_hint
    if body.distractors is not None:
        if len(body.distractors) != 3:
            raise HTTPException(status_code=400, detail="distractors must be a list of exactly 3 strings")
        s.distractors = _json.dumps(body.distractors)
    if body.explanation is not None:
        s.explanation = body.explanation

    db.commit()
    db.refresh(s)
    return {
        "id": s.id,
        "conjunction": s.conjunction,
        "conjunction_type": s.conjunction_type,
        "sentence": s.sentence,
        "correct_answer": s.correct_answer,
        "english_hint": s.english_hint,
        "distractors": _json.loads(s.distractors) if s.distractors else [],
        "explanation": s.explanation,
        "times_seen": s.times_seen,
        "times_correct": s.times_correct,
        "created_at": s.created_at.isoformat(),
    }


@router.delete("/admin/conjunction-sentences/{sentence_id}", status_code=204)
def admin_delete_conjunction_sentence(
    sentence_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Delete a cached conjunction sentence and all user stats for it (admin only)."""
    s = db.get(models.ConjunctionSentence, sentence_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sentence not found")
    db.delete(s)
    db.commit()


# ===========================================================================
# Fixed-preposition verb game  (/api/prep-verb-game/*)
# ===========================================================================
from app.prep_verb_game_service import (  # noqa: E402
    PrepVerbGameService,
    generate_question as _pv_generate_question,
    PREP_VERB_PAIRS as _PREP_VERB_PAIRS,
)


class PrepVerbQuestionRequest(BaseModel):
    mode: str = "prep"                        # "prep" | "hard"
    verb_filter: Optional[str] = None         # limit to a specific verb
    excluded_pair_ids: Optional[List[int]] = None


class PrepVerbSaveRequest(BaseModel):
    mode: str = "prep"
    answers: List[dict]


@router.post("/prep-verb-game/question")
async def prep_verb_question(
    body: PrepVerbQuestionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional),
):
    """Return one question for the fixed-preposition verb game."""
    if body.mode not in ("prep", "hard"):
        raise HTTPException(status_code=400, detail="mode must be 'prep' or 'hard'")
    try:
        user_id = current_user.id if current_user else 0
        return await _pv_generate_question(
            db=db,
            user_id=user_id,
            mode=body.mode,
            verb_filter=body.verb_filter,
            excluded_pair_ids=body.excluded_pair_ids,
        )
    except Exception as e:
        logger.error(f"prep_verb_question error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prep-verb-game/save")
def prep_verb_save(
    body: PrepVerbSaveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Save a completed fixed-preposition verb game session."""
    svc = PrepVerbGameService(db, current_user.id)
    try:
        session = svc.save_game(body.answers, body.mode)
        return {
            "session_id": session.id,
            "score": session.score,
            "accuracy": session.accuracy,
            "question_count": session.question_count,
        }
    except Exception as e:
        logger.error(f"prep_verb_save error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prep-verb-game/stats")
def prep_verb_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return stats for the current user's fixed-preposition verb game history."""
    svc = PrepVerbGameService(db, current_user.id)
    return svc.get_stats()


# ===========================================================================
# Admin — Prep-verb pair cache  (/api/admin/prep-verb-pairs/*)
# ===========================================================================

class PrepVerbPairUpdate(BaseModel):
    prep_sentence: Optional[str] = None
    prep_english: Optional[str] = None
    prep_explanation: Optional[str] = None
    prep_distractors: Optional[List[str]] = None   # 3 strings
    hard_sentence: Optional[str] = None
    hard_english: Optional[str] = None
    hard_correct_verb: Optional[str] = None
    hard_explanation: Optional[str] = None
    english_translation: Optional[str] = None


@router.get("/admin/prep-verb-pairs")
def admin_list_prep_verb_pairs(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Return all cached prep-verb pairs with global aggregate stats (admin only)."""
    import json as _json
    from sqlalchemy import func

    pairs = (
        db.query(models.PrepVerbPair)
        .order_by(models.PrepVerbPair.verb, models.PrepVerbPair.preposition)
        .all()
    )

    unique_users = dict(
        db.query(
            models.PrepVerbStat.pair_id,
            func.count(models.PrepVerbStat.user_id),
        )
        .group_by(models.PrepVerbStat.pair_id)
        .all()
    )

    result = []
    for p in pairs:
        error_rate = (
            round((1 - p.times_correct / p.times_seen) * 100)
            if p.times_seen else None
        )
        result.append({
            "id": p.id,
            "verb": p.verb,
            "preposition": p.preposition,
            "english_translation": p.english_translation,
            "reflexive": p.reflexive,
            # prep mode
            "prep_sentence": p.prep_sentence,
            "prep_english": p.prep_english,
            "prep_explanation": p.prep_explanation,
            "prep_distractors": _json.loads(p.prep_distractors) if p.prep_distractors else [],
            # hard mode
            "hard_sentence": p.hard_sentence,
            "hard_english": p.hard_english,
            "hard_correct_verb": p.hard_correct_verb,
            "hard_explanation": p.hard_explanation,
            # stats
            "times_seen": p.times_seen,
            "times_correct": p.times_correct,
            "error_rate": error_rate,
            "unique_users": unique_users.get(p.id, 0),
            "created_at": p.created_at.isoformat(),
        })
    return result


@router.patch("/admin/prep-verb-pairs/{pair_id}")
def admin_update_prep_verb_pair(
    pair_id: int,
    body: PrepVerbPairUpdate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Edit a cached prep-verb pair's sentences (admin only)."""
    import json as _json

    p = db.get(models.PrepVerbPair, pair_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pair not found")

    if body.english_translation is not None:
        p.english_translation = body.english_translation
    if body.prep_sentence is not None:
        if body.prep_sentence and "___" not in body.prep_sentence:
            raise HTTPException(status_code=400, detail="prep_sentence must contain ___")
        p.prep_sentence = body.prep_sentence
    if body.prep_english is not None:
        p.prep_english = body.prep_english
    if body.prep_explanation is not None:
        p.prep_explanation = body.prep_explanation
    if body.prep_distractors is not None:
        if len(body.prep_distractors) != 3:
            raise HTTPException(status_code=400, detail="prep_distractors must be exactly 3 strings")
        p.prep_distractors = _json.dumps(body.prep_distractors)
    if body.hard_sentence is not None:
        p.hard_sentence = body.hard_sentence
    if body.hard_english is not None:
        p.hard_english = body.hard_english
    if body.hard_correct_verb is not None:
        p.hard_correct_verb = body.hard_correct_verb
    if body.hard_explanation is not None:
        p.hard_explanation = body.hard_explanation

    db.commit()
    db.refresh(p)
    import json as _json2
    return {
        "id": p.id,
        "verb": p.verb,
        "preposition": p.preposition,
        "english_translation": p.english_translation,
        "reflexive": p.reflexive,
        "prep_sentence": p.prep_sentence,
        "prep_english": p.prep_english,
        "prep_explanation": p.prep_explanation,
        "prep_distractors": _json2.loads(p.prep_distractors) if p.prep_distractors else [],
        "hard_sentence": p.hard_sentence,
        "hard_english": p.hard_english,
        "hard_correct_verb": p.hard_correct_verb,
        "hard_explanation": p.hard_explanation,
        "times_seen": p.times_seen,
        "times_correct": p.times_correct,
        "created_at": p.created_at.isoformat(),
    }


@router.delete("/admin/prep-verb-pairs/{pair_id}", status_code=204)
def admin_delete_prep_verb_pair(
    pair_id: int,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(get_admin_user),
):
    """Delete a cached prep-verb pair and all associated data (admin only)."""
    p = db.get(models.PrepVerbPair, pair_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pair not found")
    db.delete(p)
    db.commit()


@router.get("/prep-verb-game/pairs")
def prep_verb_pairs(db: Session = Depends(get_db)):
    """Return all DB-persisted pairs (which have LLM-generated sentences) plus
    a stub entry for any built-in pair not yet generated, so the flashcard
    tab always shows the full catalogue."""
    from app.models import PrepVerbPair
    db_pairs = db.query(PrepVerbPair).all()
    db_keys = {(p.verb, p.preposition) for p in db_pairs}

    result = []
    # Persisted pairs first (they have example sentences)
    for p in db_pairs:
        result.append({
            "id": p.id,
            "verb": p.verb,
            "preposition": p.preposition,
            "english_translation": p.english_translation,
            "reflexive": p.reflexive,
            "prep_sentence": p.prep_sentence,
            "prep_english": p.prep_english,
            "prep_explanation": p.prep_explanation,
        })
    # Stubs for built-in pairs not yet in DB
    for v, p, e, r, s in _PREP_VERB_PAIRS:
        if (v, p) not in db_keys:
            result.append({
                "id": None,
                "verb": v,
                "preposition": p,
                "english_translation": e,
                "reflexive": r,
                "prep_sentence": s,
                "prep_english": None,
                "prep_explanation": None,
            })
    return result


# ============================================================================
# Admin — User Management
# ============================================================================

class UserAdminPatch(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_verified: Optional[bool] = None


def _user_to_dict(u: models.User, reveal_email: bool = False) -> dict:
    """Serialise a User row. Email is masked unless reveal_email is True."""
    email_display: str
    if reveal_email:
        email_display = u.email
    else:
        # Show only first char + domain: a***@example.com
        parts = u.email.split("@", 1)
        email_display = parts[0][0] + "***@" + parts[1] if len(parts) == 2 else "***"

    return {
        "id": u.id,
        "username": u.username,
        "email_masked": email_display,
        "auth_method": "google" if u.google_id and not u.hashed_password else
                       ("google+password" if u.google_id and u.hashed_password else "password"),
        "is_active": u.is_active,
        "is_admin": u.is_admin,
        "is_verified": u.is_verified,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "word_count": len(u.words),
    }


@router.get("/admin/users")
def admin_list_users(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user),
    reveal: bool = False,        # ?reveal=true to unmask emails
):
    """Return all registered users. Email masked by default (pass ?reveal=true to show)."""
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return [_user_to_dict(u, reveal_email=reveal) for u in users]


@router.patch("/admin/users/{user_id}")
def admin_patch_user(
    user_id: int,
    body: UserAdminPatch,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user),
):
    """Toggle is_active, is_admin, or is_verified for a user."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Prevent an admin from revoking their own admin flag
    if user.id == admin.id and body.is_admin is False:
        raise HTTPException(status_code=400, detail="You cannot remove your own admin flag")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    if body.is_verified is not None:
        user.is_verified = body.is_verified
    db.commit()
    db.refresh(user)
    return _user_to_dict(user)


@router.delete("/admin/users/{user_id}", status_code=204)
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user),
):
    """Permanently delete a user account and all their data."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account from here")
    db.delete(user)
    db.commit()
