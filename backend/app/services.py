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

