"""Pydantic models and schemas for request/response validation"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re


class Message(BaseModel):
    """Message model with length constraints"""
    text: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message text"
    )
    status: str = Field(
        default="success",
        max_length=50,
        description="Status message"
    )


class SentenceComponent(BaseModel):
    """Represents a grammatical component in a sentence"""
    type: str = Field(
        ...,
        max_length=50,
        description="Grammatical type"
    )
    value: str = Field(
        ...,
        max_length=200,
        description="Component text"
    )
    position: int = Field(
        ...,
        ge=0,
        le=10000,
        description="Position in sentence"
    )
    translation: Optional[str] = Field(
        None,
        max_length=500,
        description="English translation"
    )
    details: Optional[dict] = Field(
        None,
        description="Grammatical details"
    )
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Ensure type is from allowed list"""
        allowed = {
            'subject', 'verb', 'object', 'adjective', 'article', 'noun',
            'adverb', 'preposition', 'conjunction', 'pronoun', 'auxiliary',
            'participle', 'infinitive', 'gerund', 'unknown'
        }
        if v.lower() not in allowed:
            raise ValueError(f'Invalid type. Must be one of: {", ".join(allowed)}')
        return v.lower()
    
    @field_validator('details')
    @classmethod
    def validate_details(cls, v: Optional[dict]) -> Optional[dict]:
        """Validate details dictionary"""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError('Details must be a dictionary')
        if len(v) > 20:
            raise ValueError('Details dict exceeds maximum size (20 keys)')
        
        # Validate each key/value
        validated = {}
        for k, val in v.items():
            if not isinstance(k, str) or len(k) > 100:
                continue
            if not isinstance(val, (str, int, float, bool, type(None))):
                continue
            if isinstance(val, str) and len(val) > 200:
                val = val[:200]
            validated[k] = val
        
        return validated if validated else None


class SentenceAnalysis(BaseModel):
    """Analysis of a single sentence"""
    sentence: str = Field(
        ...,
        max_length=2000,
        description="Original sentence"
    )
    sentence_translation: Optional[str] = Field(
        None,
        max_length=2000,
        description="English translation"
    )
    components: List[SentenceComponent] = Field(
        default_factory=list,
        max_length=500,
        description="Sentence components"
    )


class TextAnalysisRequest(BaseModel):
    """Request to analyze Dutch text with strict validation"""
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Dutch text to analyze (1-10000 characters)"
    )
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text content"""
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace-only")
        
        # Check for excessive control characters
        control_count = sum(1 for c in v if ord(c) < 32 and c not in '\n\r\t')
        if control_count > len(v) * 0.1:
            raise ValueError("Text contains excessive control characters")
        
        # Verify UTF-8 validity
        try:
            v.encode('utf-8')
        except UnicodeEncodeError:
            raise ValueError("Text contains invalid UTF-8 characters")
        
        return v


class AnalyzeSentenceRequest(BaseModel):
    """Request to analyze a single sentence - for parallel frontend processing"""
    sentence: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Dutch sentence to analyze"
    )
    
    @field_validator('sentence')
    @classmethod
    def validate_sentence(cls, v: str) -> str:
        """Validate sentence format"""
        if not v.strip():
            raise ValueError("Sentence cannot be empty or whitespace-only")
        
        # Check word count
        words = v.split()
        if len(words) > 200:
            raise ValueError("Sentence exceeds maximum word count (200)")
        
        return v


class SplitSentencesResponse(BaseModel):
    """Response with just the split sentences (for progressive UI updates)"""
    sentences: List[str] = Field(
        default_factory=list,
        max_length=1000,
        description="List of split sentences"
    )
    count: int = Field(
        default=0,
        ge=0,
        le=1000,
        description="Number of sentences"
    )


class TextAnalysisResponse(BaseModel):
    """Response with complete text analysis"""
    original_text: str = Field(
        ...,
        max_length=10000,
        description="Original text analyzed"
    )
    sentences: List[SentenceAnalysis] = Field(
        default_factory=list,
        max_length=1000,
        description="Analysis results"
    )
    summary: Optional[dict] = Field(
        None,
        description="Analysis summary"
    )


# Verb Conjugation Models
class VerbConjugationForm(BaseModel):
    """Single conjugation form for a person"""
    person: str = Field(
        ...,
        max_length=50,
        description="Person (ik, jij, hij, etc.)"
    )
    conjugation: str = Field(
        ...,
        max_length=100,
        description="Conjugated form"
    )


class VerbTense(BaseModel):
    """Verb tense with all conjugations"""
    dutchName: str = Field(
        ...,
        max_length=100,
        description="Dutch name of tense"
    )
    englishName: Optional[str] = Field(
        None,
        max_length=100,
        description="English name of tense"
    )
    forms: List[VerbConjugationForm] = Field(
        default_factory=list,
        max_length=10,
        description="Conjugation forms"
    )


class VerbExample(BaseModel):
    """Usage example of a verb"""
    dutch: str = Field(
        ...,
        max_length=300,
        description="Dutch example"
    )
    english: str = Field(
        ...,
        max_length=300,
        description="English translation"
    )
    tense: Optional[str] = Field(
        None,
        max_length=100,
        description="Tense used"
    )


class ConjugateVerbRequest(BaseModel):
    """Request to conjugate a verb with strict validation"""
    verb: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Dutch verb to conjugate"
    )
    
    @field_validator('verb')
    @classmethod
    def validate_verb(cls, v: str) -> str:
        """Validate verb format"""
        if not v.strip():
            raise ValueError("Verb cannot be empty or whitespace-only")
        
        # Allow letters, hyphens, and apostrophes only (common in Dutch)
        if not all(c.isalpha() or c in "-'" for c in v):
            raise ValueError("Verb contains invalid characters. Only letters, hyphens, and apostrophes allowed")
        
        # Check for excessive special characters
        special_count = sum(1 for c in v if c in "-'")
        if special_count > 3:
            raise ValueError("Verb contains too many special characters")
        
        return v.strip()


class ConjugateVerbResponse(BaseModel):
    """Response with verb conjugation data"""
    infinitive: Optional[str] = Field(
        None,
        max_length=100,
        description="Verb infinitive"
    )
    englishTranslation: Optional[str] = Field(
        None,
        max_length=200,
        description="English translation"
    )
    verbType: Optional[str] = Field(
        None,
        description="regular or irregular"
    )
    tenses: List[VerbTense] = Field(
        default_factory=list,
        max_length=10,
        description="Verb tenses"
    )
    examples: List[VerbExample] = Field(
        default_factory=list,
        max_length=20,
        description="Usage examples"
    )
    error: Optional[str] = Field(
        None,
        max_length=200,
        description="Error message if conjugation failed"
    )
