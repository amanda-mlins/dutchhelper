from sqlalchemy.orm import Session
from . import models
from .llm_service import OpenRouterService


class WordListService:
    def __init__(self, db: Session):
        self.db = db

    async def add_word(self, word: str, user_id: int) -> models.UserWord:
        """
        Adds a new word to the authenticated user's word bank.
        Fetches details from the LLM before saving.
        """
        # Idempotent: return existing word if already saved by this user
        existing = (
            self.db.query(models.UserWord)
            .filter(models.UserWord.user_id == user_id, models.UserWord.word == word)
            .first()
        )
        if existing:
            return existing

        # Enrich with LLM-generated details
        word_details = await OpenRouterService.get_word_details(word)
        word_type = word_details.get("word_type", "unknown")

        new_word = models.UserWord(
            user_id=user_id,
            word=word,
            word_type=word_type,
        )
        new_word.set_details(
            definition=word_details.get("definition", ""),
            translation_en=word_details.get("translation_en", ""),
            example=word_details.get("example", ""),
        )

        self.db.add(new_word)
        self.db.commit()
        self.db.refresh(new_word)
        return new_word

    def get_words_for_user(self, user_id: int) -> list[models.UserWord]:
        """Retrieves all words for the given authenticated user."""
        return (
            self.db.query(models.UserWord)
            .filter(models.UserWord.user_id == user_id)
            .order_by(models.UserWord.created_at.desc())
            .all()
        )

    def update_word(self, word_id: int, updated_data: models.UserWordCreate, user_id: int):
        """
        Updates an existing word. Only allows updating words owned by user_id
        to prevent users from modifying each other's data.
        """
        word_to_update = (
            self.db.query(models.UserWord)
            .filter(models.UserWord.id == word_id, models.UserWord.user_id == user_id)
            .first()
        )
        if not word_to_update:
            return None

        word_to_update.word = updated_data.word

        self.db.commit()
        self.db.refresh(word_to_update)
        return word_to_update

    def delete_word(self, word_id: int, user_id: int) -> bool:
        """
        Deletes a word. Only allows deleting words owned by user_id.
        """
        word_to_delete = (
            self.db.query(models.UserWord)
            .filter(models.UserWord.id == word_id, models.UserWord.user_id == user_id)
            .first()
        )
        if not word_to_delete:
            return False

        self.db.delete(word_to_delete)
        self.db.commit()
        return True
