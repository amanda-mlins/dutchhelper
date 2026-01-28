"""API routes for DutchHelper"""
import logging
from fastapi import APIRouter
from app.models import Message, TextAnalysisRequest, TextAnalysisResponse
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
        
        analysis = SentenceAnalyzerService.analyze_text(request.text)
        
        logger.info(f"Analysis complete: {len(analysis.sentences)} sentences found")
        
        return analysis
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        raise ProcessingError(f"Failed to analyze text: {str(e)}")
