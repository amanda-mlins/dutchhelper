"""API routes for DutchHelper"""
import logging
from fastapi import APIRouter, HTTPException
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
from app.exceptions import ValidationError, ProcessingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])

@router.post("/message", response_model=Message)
async def send_message(message: Message):
    """
    Echo a message back (placeholder endpoint for testing).
    
    Args:
        message: Message to echo
        
    Returns:
        Echo response with received status
    """
    logger.info(f"Message received: {message.text}")
    return {"text": f"You said: {message.text}", "status": "received"}

@router.post("/split-sentences", response_model=SplitSentencesResponse)
async def split_sentences(request: TextAnalysisRequest):
    """
    Split Dutch text into sentences using robust pysbd library.
    
    This endpoint is fast (no LLM needed) and enables progressive UI updates.
    The frontend receives split sentences immediately and can then analyze each
    one in parallel using the /api/analyze-sentence endpoint.
    
    Args:
        request: TextAnalysisRequest containing the Dutch text to split
        
    Returns:
        SplitSentencesResponse with list of sentences
        
    Raises:
        ValidationError: If text is empty or invalid
    """
    try:
        if not request.text or not request.text.strip():
            raise ValidationError("Text cannot be empty")
        
        logger.info(f"Splitting text: {request.text[:100]}...")
        
        sentences = NLPService.split_sentences(request.text)
        
        logger.info(f"Split complete: {len(sentences)} sentences found")
        
        return SplitSentencesResponse(
            sentences=sentences,
            count=len(sentences)
        )
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error splitting sentences: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to split sentences")

@router.post("/analyze", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze Dutch text and break it down into grammatical components.
    
    Args:
        request: TextAnalysisRequest containing the Dutch text to analyze
        
    Returns:
        TextAnalysisResponse with sentences and their grammatical components
        
    Raises:
        ValidationError: If text is empty or invalid
        ProcessingError: If analysis fails
    """
    try:
        if not request.text or not request.text.strip():
            raise ValidationError("Text cannot be empty")
        
        logger.info(f"Analyzing text: {request.text[:100]}...")
        
        analysis = await SentenceAnalyzerService.analyze_text(request.text)
        
        logger.info(f"Analysis complete: {len(analysis.sentences)} sentences found")
        
        return analysis
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        raise ProcessingError(f"Failed to analyze text: {str(e)}")

@router.post("/analyze-sentence", response_model=SentenceAnalysis)
async def analyze_sentence(request: AnalyzeSentenceRequest):
    """
    Analyze a single sentence for grammatical components.
    
    This endpoint is designed to be called from the frontend for parallel processing.
    Multiple requests are sent concurrently, with each sentence analyzed independently.
    Results are returned as soon as they're ready, enabling progressive UI updates.
    
    Args:
        request: AnalyzeSentenceRequest containing a single sentence to analyze
        
    Returns:
        SentenceAnalysis with sentence translation and grammatical components
        
    Raises:
        HTTPException: If sentence is empty or analysis fails
    """
    try:
        sentence = request.sentence.strip()
        
        if not sentence:
            raise HTTPException(status_code=400, detail="Sentence cannot be empty")
        
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
async def conjugate_verb(request: ConjugateVerbRequest):
    """
    Conjugate a Dutch verb across all tenses and persons.
    
    First tries to find the verb in the local database (~15 common verbs).
    If not found, uses OpenRouter LLM to generate the conjugation.
    
    Args:
        request: ConjugateVerbRequest containing the verb to conjugate
        
    Returns:
        ConjugateVerbResponse with conjugations, translations, and examples
        
    Raises:
        HTTPException: If verb cannot be conjugated or input is invalid
    """
    try:
        if not request.verb or not request.verb.strip():
            raise HTTPException(status_code=400, detail="Verb cannot be empty")
        
        verb = request.verb.strip().lower()
        logger.info(f"Conjugating verb (with LLM fallback): {verb}")
        
        # Use the async method with LLM fallback
        conjugation_data = await VerbConjugationService.conjugate_verb_with_llm(verb)
        
        logger.info(f"Successfully conjugated verb: {verb}")
        
        # Return the data as ConjugateVerbResponse
        return ConjugateVerbResponse(**conjugation_data)
        
    except ProcessingError as e:
        logger.error(f"Failed to conjugate verb: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conjugating verb: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to conjugate verb")

@router.post("/conjugate-database", response_model=ConjugateVerbResponse)
async def conjugate_verb_database_only(request: ConjugateVerbRequest):
    """
    Conjugate a Dutch verb from the local database only (no LLM).
    
    This endpoint only uses the local database and does not call the LLM.
    Useful for fast responses without API calls.
    
    Args:
        request: ConjugateVerbRequest containing the verb to conjugate
        
    Returns:
        ConjugateVerbResponse with conjugations, translations, and examples
        
    Raises:
        HTTPException: If verb is not found in database
    """
    try:
        if not request.verb or not request.verb.strip():
            raise HTTPException(status_code=400, detail="Verb cannot be empty")
        
        verb = request.verb.strip().lower()
        logger.info(f"Conjugating verb from database: {verb}")
        
        # Get conjugation data from service (database only, no LLM)
        conjugation_data = VerbConjugationService.conjugate_verb(verb)
        
        logger.info(f"Successfully conjugated verb from database: {verb}")
        
        # Return the data as ConjugateVerbResponse
        return ConjugateVerbResponse(**conjugation_data)
        
    except KeyError as e:
        logger.error(f"Verb not found in database: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conjugating verb: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to conjugate verb")

