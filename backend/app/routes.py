"""API routes for DutchHelper"""
import logging
from fastapi import APIRouter, HTTPException
from app.models import Message, TextAnalysisRequest, AnalyzeSentenceRequest, TextAnalysisResponse, SentenceAnalysis
from app.services import SentenceAnalyzerService
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
