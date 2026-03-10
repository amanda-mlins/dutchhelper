"""Pydantic models for request/response validation"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timezone
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
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    words = relationship("UserWord", back_populates="owner")
    game_sessions = relationship("ArticleGameSession", back_populates="user")
    word_mistakes = relationship("ArticleWordMistake", back_populates="user")

class UserWord(Base):
    __tablename__ = 'user_words'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    word = Column(String, index=True, nullable=False)
    word_type = Column(String, index=True) # E.g., 'noun', 'verb', 'adjective'
    category = Column(String, index=True, nullable=True)  # User-defined category tag
    
    # Storing dictionary-like data as a JSON string
    details = Column(Text) # JSON string: {definition: "", translation_en: "", example: ""}

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
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

class UserWordCategoryUpdate(BaseModel):
    category: Optional[str] = None

class UserWordSchema(UserWordBase):
    id: int
    user_id: int
    word_type: str
    category: Optional[str] = None
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
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserSchema

# --- Article Game ORM models ---

class ArticleGameSession(Base):
    """One completed article game for a logged-in user."""
    __tablename__ = "article_game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    played_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    word_count = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    accuracy = Column(Integer, nullable=False)  # 0-100 integer percent

    user = relationship("User", back_populates="game_sessions")
    answers = relationship("ArticleGameAnswer", back_populates="session", cascade="all, delete-orphan")


class ArticleGameAnswer(Base):
    """One answer within a game session."""
    __tablename__ = "article_game_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("article_game_sessions.id"), nullable=False)
    word = Column(String, nullable=False)
    correct_article = Column(String, nullable=False)
    user_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)

    session = relationship("ArticleGameSession", back_populates="answers")


class ArticleWordMistake(Base):
    """Cumulative mistake tracker per user per word."""
    __tablename__ = "article_word_mistakes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word = Column(String, nullable=False)
    times_seen = Column(Integer, default=0, nullable=False)
    times_wrong = Column(Integer, default=0, nullable=False)
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="word_mistakes")


class ArticleWord(Base):
    """Default word list for the article game (de/het)."""
    __tablename__ = "article_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, nullable=False, index=True)
    article = Column(String, nullable=False)          # "de" or "het"
    translation = Column(String, nullable=True)
    difficulty = Column(String, nullable=False, default="medium")  # easy/medium/hard
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VerbConjugation(Base):
    """Cached verb conjugation data fetched from the LLM."""
    __tablename__ = "verb_conjugations"

    id = Column(Integer, primary_key=True, index=True)
    infinitive = Column(String, unique=True, nullable=False, index=True)
    english_translation = Column(String, nullable=True)
    verb_type = Column(String, nullable=True)
    conjugation_data = Column(Text, nullable=False)  # JSON blob
    query_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))


class VerbGameSession(Base):
    """One completed verb conjugation game for a logged-in user."""
    __tablename__ = "verb_game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    played_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    question_count = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    accuracy = Column(Integer, nullable=False)  # 0-100 integer percent

    answers = relationship("VerbGameAnswer", back_populates="session", cascade="all, delete-orphan")


class VerbGameAnswer(Base):
    """One answer within a verb game session."""
    __tablename__ = "verb_game_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("verb_game_sessions.id"), nullable=False)
    verb_infinitive = Column(String, nullable=False)
    sentence = Column(String, nullable=False)       # full sentence with blank
    correct_answer = Column(String, nullable=False)  # expected conjugated form
    user_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    tense = Column(String, nullable=True)
    person = Column(String, nullable=True)
    english_hint = Column(String, nullable=True)    # English translation of sentence

    session = relationship("VerbGameSession", back_populates="answers")


class ConjunctionGameSession(Base):
    """One completed conjunction game for a logged-in user."""
    __tablename__ = "conjunction_game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    played_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    question_count = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    accuracy = Column(Integer, nullable=False)  # 0-100 integer percent

    answers = relationship("ConjunctionGameAnswer", back_populates="session", cascade="all, delete-orphan")


class ConjunctionGameAnswer(Base):
    """One answer within a conjunction game session."""
    __tablename__ = "conjunction_game_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("conjunction_game_sessions.id"), nullable=False)
    # Optional FK to the canonical sentence cache (NULL for legacy rows)
    sentence_id = Column(Integer, ForeignKey("conjunction_sentences.id"), nullable=True)
    conjunction = Column(String, nullable=False)       # the conjunction being tested
    conjunction_type = Column(String, nullable=True)   # e.g. 'coordinating', 'subordinating'
    sentence = Column(String, nullable=False)          # full sentence with blank
    correct_answer = Column(String, nullable=False)    # the correct conjunction
    user_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    english_hint = Column(String, nullable=True)       # English translation of the sentence

    session = relationship("ConjunctionGameSession", back_populates="answers")
    cached_sentence = relationship("ConjunctionSentence", back_populates="game_answers")


class ConjunctionSentence(Base):
    """
    Canonical cache of LLM-generated conjunction sentences.

    Every time the LLM produces a new sentence we store it here so:
      - We can serve it again without another LLM call.
      - We track global usage + success rates.
      - Users never see the same sentence twice in the same game.
    """
    __tablename__ = "conjunction_sentences"

    id = Column(Integer, primary_key=True, index=True)
    conjunction = Column(String, nullable=False, index=True)
    conjunction_type = Column(String, nullable=False)
    sentence = Column(String, nullable=False)          # Dutch sentence with ___
    correct_answer = Column(String, nullable=False)
    english_hint = Column(String, nullable=True)
    distractors = Column(Text, nullable=True)          # JSON list of 3 strings
    explanation = Column(Text, nullable=True)          # Why correct_answer is right (and distractors aren't)
    # Global aggregate stats (across ALL users)
    times_seen = Column(Integer, default=0, nullable=False)
    times_correct = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user_stats = relationship("ConjunctionSentenceStat", back_populates="sentence", cascade="all, delete-orphan")
    game_answers = relationship("ConjunctionGameAnswer", back_populates="cached_sentence")


class ConjunctionSentenceStat(Base):
    """
    Per-user statistics for a specific ConjunctionSentence.

    Used for:
      - Knowing if a user has already seen a sentence (avoid repeats).
      - Flagging sentences the user got wrong so they resurface in future games.
    """
    __tablename__ = "conjunction_sentence_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sentence_id = Column(Integer, ForeignKey("conjunction_sentences.id"), nullable=False)
    times_seen = Column(Integer, default=0, nullable=False)
    times_correct = Column(Integer, default=0, nullable=False)
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # True when user got this wrong and it should appear in next game(s)
    needs_review = Column(Boolean, default=False, nullable=False)

    user = relationship("User")
    sentence = relationship("ConjunctionSentence", back_populates="user_stats")


# ---------------------------------------------------------------------------
# Fixed-Preposition Verb Game
# ---------------------------------------------------------------------------

class PrepVerbPair(Base):
    """
    Cached verb+preposition pair (e.g. 'beginnen met', 'denken aan').

    Stores:
      - LLM-generated sentences for BOTH game modes.
      - Global usage / correctness stats.
    """
    __tablename__ = "prep_verb_pairs"

    id = Column(Integer, primary_key=True, index=True)
    verb = Column(String, nullable=False, index=True)          # infinitive, e.g. "beginnen"
    preposition = Column(String, nullable=False)                # e.g. "met"
    english_translation = Column(String, nullable=True)        # e.g. "to begin with"
    reflexive = Column(Boolean, default=False, nullable=False) # True for "zich concentreren op"

    # Mode 1: fill-in the PREPOSITION only
    # Sentence has exactly one ___ where the preposition goes.
    prep_sentence = Column(Text, nullable=True)      # Dutch sentence with ___
    prep_english = Column(Text, nullable=True)       # English translation / hint
    prep_explanation = Column(Text, nullable=True)   # Why this preposition

    # Mode 2 (hard): fill in CONJUGATED VERB + PREPOSITION
    # Sentence has ___ ___ (two blanks).
    hard_sentence = Column(Text, nullable=True)
    hard_english = Column(Text, nullable=True)
    hard_correct_verb = Column(String, nullable=True)   # conjugated form used in sentence
    hard_correct_prep = Column(String, nullable=True)   # always == preposition column
    hard_explanation = Column(Text, nullable=True)

    # Distractor prepositions (JSON list of 3 strings)
    prep_distractors = Column(Text, nullable=True)

    # Global aggregate stats
    times_seen = Column(Integer, default=0, nullable=False)
    times_correct = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user_stats = relationship("PrepVerbStat", back_populates="pair", cascade="all, delete-orphan")
    game_answers = relationship("PrepVerbGameAnswer", back_populates="pair")


class PrepVerbStat(Base):
    """Per-user stats for a PrepVerbPair — drives spaced repetition."""
    __tablename__ = "prep_verb_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pair_id = Column(Integer, ForeignKey("prep_verb_pairs.id"), nullable=False)
    times_seen = Column(Integer, default=0, nullable=False)
    times_correct = Column(Integer, default=0, nullable=False)
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    needs_review = Column(Boolean, default=False, nullable=False)

    user = relationship("User")
    pair = relationship("PrepVerbPair", back_populates="user_stats")


class PrepVerbGameSession(Base):
    """One completed fixed-preposition verb game."""
    __tablename__ = "prep_verb_game_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    played_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    mode = Column(String, nullable=False, default="prep")  # "prep" | "hard"
    question_count = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    accuracy = Column(Integer, nullable=False)   # 0-100 integer percent

    answers = relationship("PrepVerbGameAnswer", back_populates="session", cascade="all, delete-orphan")


class PrepVerbGameAnswer(Base):
    """One answer within a PrepVerbGameSession."""
    __tablename__ = "prep_verb_game_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("prep_verb_game_sessions.id"), nullable=False)
    pair_id = Column(Integer, ForeignKey("prep_verb_pairs.id"), nullable=True)
    mode = Column(String, nullable=False)        # "prep" | "hard"
    verb = Column(String, nullable=False)
    preposition = Column(String, nullable=False)
    sentence = Column(Text, nullable=False)
    # For prep mode: single correct answer; for hard: "verb preposition"
    correct_answer = Column(String, nullable=False)
    user_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    english_hint = Column(Text, nullable=True)

    session = relationship("PrepVerbGameSession", back_populates="answers")
    pair = relationship("PrepVerbPair", back_populates="game_answers")


# --- Pydantic Schemas for Article Words Admin ---

class ArticleWordCreate(BaseModel):
    word: str
    article: str   # "de" or "het"
    translation: Optional[str] = None
    difficulty: str = "medium"
    category: Optional[str] = None
    is_active: bool = True

class ArticleWordUpdate(BaseModel):
    word: Optional[str] = None
    article: Optional[str] = None
    translation: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class ArticleWordSchema(BaseModel):
    id: int
    word: str
    article: str
    translation: Optional[str] = None
    difficulty: str
    category: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Pydantic Schemas for Verb Conjugation Admin ---

class VerbConjugationSchema(BaseModel):
    id: int
    infinitive: str
    english_translation: Optional[str] = None
    verb_type: Optional[str] = None
    conjugation_data: str   # raw JSON string
    query_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
