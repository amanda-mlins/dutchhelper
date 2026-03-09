"""API routes for DutchHelper"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
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

class GameWordsRequest(BaseModel):
    count: int = 20
    mode: str = "smart"   # smart | mistakes | wordbank | random  (ignored for guests)

class SubmitAnswerRequest(BaseModel):
    word: str
    user_answer: str

class SaveGameRequest(BaseModel):
    answers: List[dict]


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


# --- Word Bank API Endpoints (require authentication) ---

@router.post("/word-bank/words", response_model=models.UserWordSchema, status_code=201)
async def add_user_word(
    word_data: models.UserWordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Adds a new word to the authenticated user's word bank."""
    service = WordListService(db)
    try:
        new_word = await service.add_word(word=word_data.word, user_id=current_user.id)
        return new_word
    except Exception as e:
        logger.error(f"Error adding word '{word_data.word}': {e}")
        raise HTTPException(status_code=500, detail="Failed to add word.")

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
