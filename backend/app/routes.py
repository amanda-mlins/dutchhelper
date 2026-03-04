"""API routes for DutchHelper"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Request, Depends, Response
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
from app.article_game_service import ArticleGameService
from app.exceptions import ValidationError, ProcessingError
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
async def get_database_stats(request: Request):
    """
    Get statistics about the verb conjugation database (admin endpoint).
    
    Returns information about:
    - Total verbs in database
    - Database size
    - Most frequently queried verbs
    - Estimated API savings
    
    Returns:
        Dictionary with database statistics
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
async def export_database(request: Request):
    """
    Export all verbs to a JSON file for version control (admin endpoint).
    
    This creates a JSON snapshot of all verbs in the database, which can be
    tracked in git for backup and portability.
    
    Returns:
        Dictionary with export path and summary
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

# Initialize game service
_game_service = None

def get_game_service():
    """Get or create the game service."""
    global _game_service
    if _game_service is None:
        _game_service = ArticleGameService()
    return _game_service


@router.post("/game/words")
async def get_game_words(request: Request, body: GameWordsRequest):
    """
    Get words for an article guessing game session.
    
    Args:
        body: GameWordsRequest with count (20, 30, or 50) and personalized flag
        
    Returns:
        List of words with their metadata (article hidden from client)
    """
    try:
        if body.count not in [20, 30, 50]:
            raise ValidationError("Word count must be 20, 30, or 50")
        
        game_service = get_game_service()
        words = game_service.get_game_words(body.count, body.personalized)
        
        # Return words without revealing the article
        return {
            "words": [{"word": w["word"], "difficulty": w["difficulty"], "category": w["category"], "translation": w["translation"]} 
                      for w in words],
            "count": len(words)
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting game words: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get game words")


@router.post("/game/submit")
async def submit_answer(request: Request, body: SubmitAnswerRequest):
    """
    Submit an answer for a word in the article game.
    
    Args:
        body: SubmitAnswerRequest with word and user_answer (de or het)
        
    Returns:
        SubmitAnswerResponse with correctness and explanation
    """
    try:
        if not body.word or not body.user_answer:
            raise ValidationError("Word and user_answer are required")
        
        if body.user_answer.lower() not in ['de', 'het']:
            raise ValidationError("User answer must be 'de' or 'het'")
        
        game_service = get_game_service()
        result = game_service.submit_answer(body.word, body.user_answer)
        
        if "error" in result:
            raise ValidationError(result["error"])
        
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit answer")


@router.post("/game/save")
async def save_game(request: Request, body: SaveGameRequest):
    """
    Save a completed game to the database.
    
    Args:
        body: SaveGameRequest with list of answers from the game
        
    Returns:
        GameResult with game_id, score, and accuracy
    """
    try:
        if not body.answers:
            raise ValidationError("Answers list cannot be empty")
        
        game_service = get_game_service()
        game_id = game_service.save_game(body.answers)
        
        # Calculate stats
        score = sum(1 for ans in body.answers if ans.get("is_correct", False))
        total = len(body.answers)
        accuracy = (score / total * 100) if total > 0 else 0
        
        return {
            "game_id": game_id,
            "score": score,
            "total_questions": total,
            "accuracy": accuracy
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving game: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save game")


@router.get("/game/history")
async def get_game_history(request: Request, limit: int = 10):
    """
    Get recent game history.
    
    Args:
        limit: Number of games to retrieve (default 10, max 50)
        
    Returns:
        List of game records with dates and scores
    """
    try:
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 1
        
        game_service = get_game_service()
        history = game_service.get_game_history(limit)
        
        return {"games": history}
    except Exception as e:
        logger.error(f"Error getting game history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve game history")


@router.get("/game/stats")
async def get_game_stats(request: Request):
    """
    Get aggregate game statistics and word mastery stats.
    
    Returns:
        Dictionary with overall performance metrics
    """
    try:
        game_service = get_game_service()
        stats = game_service.get_game_stats()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting game stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve game statistics")


@router.get("/game/detail/{game_id}")
async def get_game_detail(request: Request, game_id: int):
    """
    Get detailed information about a specific game.
    
    Args:
        game_id: ID of the game to retrieve
        
    Returns:
        Detailed game record with all answers
    """
    try:
        game_service = get_game_service()
        game = game_service.get_detailed_game(game_id)
        
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        return game
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve game details")

# --- Word Bank API Endpoints ---

@router.post("/word-bank/words", response_model=models.UserWordSchema, status_code=201)
async def add_user_word(word_data: models.UserWordCreate, db: Session = Depends(get_db)):
    """Adds a new word to the default user's word bank."""
    service = WordListService(db)
    try:
        # For now, we'll use a default user. This can be expanded later.
        new_word = await service.add_word(word=word_data.word)
        return new_word
    except Exception as e:
        logger.error(f"Error adding word '{word_data.word}': {e}")
        raise HTTPException(status_code=500, detail="Failed to add word.")

@router.get("/word-bank/words", response_model=List[models.UserWordSchema])
def get_user_words(db: Session = Depends(get_db)):
    """Retrieves all words for the default user."""
    service = WordListService(db)
    words = service.get_words_for_user()
    return words

@router.put("/word-bank/words/{word_id}", response_model=models.UserWordSchema)
def update_user_word(word_id: int, word_data: models.UserWordCreate, db: Session = Depends(get_db)):
    """Updates a word in the user's word bank."""
    service = WordListService(db)
    updated_word = service.update_word(word_id, word_data)
    if not updated_word:
        raise HTTPException(status_code=404, detail="Word not found.")
    return updated_word

@router.delete("/word-bank/words/{word_id}", status_code=204)
def delete_user_word(word_id: int, db: Session = Depends(get_db)):
    """Deletes a word from the user's word bank."""
    service = WordListService(db)
    success = service.delete_word(word_id)
    if not success:
        raise HTTPException(status_code=404, detail="Word not found.")
    return Response(status_code=204)


