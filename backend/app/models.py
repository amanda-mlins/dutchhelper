"""Pydantic models for request/response validation"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

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

# --- New Database Models for Word Bank ---

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)  # Null for Google-only accounts
    google_id = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    words = relationship("UserWord", back_populates="owner")

class UserWord(Base):
    __tablename__ = 'user_words'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    word = Column(String, index=True, nullable=False)
    word_type = Column(String, index=True) # E.g., 'noun', 'verb', 'adjective'
    
    # Storing dictionary-like data as a JSON string
    details = Column(Text) # JSON string: {definition: "", translation_en: "", example: ""}

    created_at = Column(DateTime, default=datetime.utcnow)
    last_practiced_at = Column(DateTime)
    practice_count = Column(Integer, default=0)
    
    owner = relationship("User", back_populates="words")

    def set_details(self, definition: str, translation_en: str, example: str):
        self.details = json.dumps({
            "definition": definition,
            "translation_en": translation_en,
            "example": example
        })

    def get_details(self):
        if self.details:
            return json.loads(self.details)
        return {
            "definition": "",
            "translation_en": "",
            "example": ""
        }

# --- Pydantic Schemas for Word Bank API ---

class UserWordDetails(BaseModel):
    definition: str
    translation_en: str
    example: str

class UserWordBase(BaseModel):
    word: str
    
class UserWordCreate(UserWordBase):
    pass

class UserWordSchema(UserWordBase):
    id: int
    user_id: int
    word_type: str
    details: Any
    created_at: datetime
    last_practiced_at: Optional[datetime] = None
    practice_count: int

    @field_validator('details', mode='before')
    def details_to_dict(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True

# --- Pydantic Schemas for Auth ---

class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str

class UserSchema(BaseModel):
    """Schema for returning user info (never expose password)."""
    id: int
    email: str
    username: Optional[str] = None
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserSchema
