"""Pydantic models for request/response validation"""
from pydantic import BaseModel
from typing import Optional, List

class Message(BaseModel):
    """Message model"""
    text: str
    status: str = "success"

class SentenceComponent(BaseModel):
    """Represents a grammatical component in a sentence"""
    type: str  # e.g., "subject", "verb", "object", "adjective", "article", "noun"
    value: str
    position: int  # Starting position in the sentence
    translation: Optional[str] = None  # English translation
    details: Optional[dict] = None  # Additional grammatical details (verb tense, gender, etc.)

class SentenceAnalysis(BaseModel):
    """Analysis of a single sentence"""
    sentence: str
    sentence_translation: Optional[str] = None  # English translation of the whole sentence
    components: List[SentenceComponent] = []

class TextAnalysisRequest(BaseModel):
    """Request to analyze Dutch text"""
    text: str

class AnalyzeSentenceRequest(BaseModel):
    """Request to analyze a single sentence - for parallel frontend processing"""
    sentence: str

class TextAnalysisResponse(BaseModel):
    """Response with complete text analysis"""
    original_text: str
    sentences: List[SentenceAnalysis] = []
    summary: Optional[dict] = None  # For future use with additional stats
