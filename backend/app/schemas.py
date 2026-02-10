"""Pydantic models and schemas for request/response validation"""
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
    translation: Optional[str] = None
    details: Optional[dict] = None

class SentenceAnalysis(BaseModel):
    """Analysis of a single sentence"""
    sentence: str
    sentence_translation: Optional[str] = None
    components: List[SentenceComponent] = []

class TextAnalysisRequest(BaseModel):
    """Request to analyze Dutch text"""
    text: str

class AnalyzeSentenceRequest(BaseModel):
    """Request to analyze a single sentence - for parallel frontend processing"""
    sentence: str

class SplitSentencesResponse(BaseModel):
    """Response with just the split sentences (for progressive UI updates)"""
    sentences: List[str] = []
    count: int = 0

class TextAnalysisResponse(BaseModel):
    """Response with complete text analysis"""
    original_text: str
    sentences: List[SentenceAnalysis] = []
    summary: Optional[dict] = None  # For future use with additional stats

# Verb Conjugation Models
class VerbConjugationForm(BaseModel):
    """Single conjugation form for a person"""
    person: str
    conjugation: str

class VerbTense(BaseModel):
    """Verb tense with all conjugations"""
    dutchName: str
    englishName: Optional[str] = None
    forms: List[VerbConjugationForm] = []

class VerbExample(BaseModel):
    """Usage example of a verb"""
    dutch: str
    english: str
    tense: Optional[str] = None

class ConjugateVerbRequest(BaseModel):
    """Request to conjugate a verb"""
    verb: str

class ConjugateVerbResponse(BaseModel):
    """Response with verb conjugation data"""
    infinitive: str
    englishTranslation: str
    tenses: List[VerbTense] = []
    examples: List[VerbExample] = []
