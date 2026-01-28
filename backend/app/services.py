"""Text analysis service using OpenRouter LLM"""
from app.models import TextAnalysisResponse, SentenceAnalysis
from app.llm_service import OpenRouterService
from typing import List

class SentenceAnalyzerService:
    """Service for analyzing Dutch sentences using LLM"""
    
    @staticmethod
    async def analyze_text(text: str) -> TextAnalysisResponse:
        """
        Analyze Dutch text and break it down into sentences with grammatical components.
        
        Args:
            text: Dutch text to analyze
            
        Returns:
            TextAnalysisResponse with sentences and their components
        """
        if not text or not text.strip():
            return TextAnalysisResponse(original_text=text, sentences=[])
        
        # Use OpenRouter to analyze sentences
        analyzed_sentences = await OpenRouterService.analyze_dutch_text(text)
        
        return TextAnalysisResponse(
            original_text=text,
            sentences=analyzed_sentences
        )
    
    @staticmethod
    async def analyze_single_sentence(sentence: str) -> SentenceAnalysis:
        """
        Analyze a single sentence for grammatical components.
        
        This method is used when processing sentences in parallel from the frontend.
        Each sentence is sent to this endpoint independently, allowing for concurrent
        processing on the backend.
        
        Args:
            sentence: A single sentence to analyze
            
        Returns:
            SentenceAnalysis with translation and components
            
        Raises:
            ProcessingError: If the sentence cannot be analyzed
        """
        if not sentence or not sentence.strip():
            from app.exceptions import ProcessingError
            raise ProcessingError("Empty sentence")
        
        # Use OpenRouter to analyze the single sentence
        # analyze_dutch_text expects text that may contain multiple sentences,
        # but we pass just one, so it returns a list with one item
        analyzed = await OpenRouterService.analyze_dutch_text(sentence)
        
        if analyzed:
            return analyzed[0]
        
        from app.exceptions import ProcessingError
        raise ProcessingError("Failed to analyze sentence")

