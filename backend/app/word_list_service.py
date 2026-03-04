from sqlalchemy.orm import Session
from . import models
from .llm_service import OpenRouterService

class WordListService:
    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_user(self, username: str = "default_user") -> models.User:
        """
        Retrieves a user by username or creates a new one if it doesn't exist.
        For now, it uses a single default user.
        """
        user = self.db.query(models.User).filter(models.User.username == username).first()
        if not user:
            user = models.User(username=username)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    async def add_word(self, word: str, user_id: int = None) -> models.UserWord:
        """
        Adds a new word to a user's word bank.
        It fetches details from the LLM before saving.
        """
        if user_id is None:
            user = self._get_or_create_user()
            user_id = user.id

        # Check if the word already exists for this user
        existing_word = self.db.query(models.UserWord).filter(
            models.UserWord.user_id == user_id,
            models.UserWord.word == word
        ).first()
        if existing_word:
            return existing_word

        # Get details from LLM
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
            example=word_details.get("example", "")
        )
        
        self.db.add(new_word)
        self.db.commit()
        self.db.refresh(new_word)
        return new_word

    def get_words_for_user(self, user_id: int = None) -> list[models.UserWord]:
        """Retrieves all words for a given user."""
        if user_id is None:
            user = self._get_or_create_user()
            user_id = user.id
        
        return self.db.query(models.UserWord).filter(models.UserWord.user_id == user_id).all()

    def update_word(self, word_id: int, updated_data: models.UserWordCreate) -> models.UserWord:
        """Updates an existing word."""
        word_to_update = self.db.query(models.UserWord).filter(models.UserWord.id == word_id).first()
        if not word_to_update:
            return None

        word_to_update.word = updated_data.word
        word_to_update.word_type = updated_data.word_type
        word_to_update.set_details(
            definition=updated_data.details.definition,
            translation_en=updated_data.details.translation_en,
            example=updated_data.details.example
        )

        self.db.commit()
        self.db.refresh(word_to_update)
        return word_to_update

    def delete_word(self, word_id: int) -> bool:
        """Deletes a word from a user's list."""
        word_to_delete = self.db.query(models.UserWord).filter(models.UserWord.id == word_id).first()
        if not word_to_delete:
            return False
        
        self.db.delete(word_to_delete)
        self.db.commit()
        return True
