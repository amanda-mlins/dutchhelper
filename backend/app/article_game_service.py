"""Service for managing article guessing game logic."""

from datetime import datetime
from typing import List, Optional, Dict, Any
import sqlite3
from pathlib import Path
from app.dutch_article_words import get_random_words, get_word_info, DUTCH_ARTICLE_WORDS


class ArticleGameService:
    """Service for managing de/het article guessing game."""
    
    def __init__(self, db_path: str = "article_game.db"):
        """Initialize the game service and setup database."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database for game history."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    word_count INTEGER,
                    score INTEGER,
                    total_questions INTEGER,
                    accuracy REAL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS game_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    correct_article TEXT NOT NULL,
                    user_answer TEXT NOT NULL,
                    is_correct BOOLEAN,
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS word_stats (
                    word TEXT PRIMARY KEY,
                    times_seen INTEGER DEFAULT 0,
                    times_correct INTEGER DEFAULT 0,
                    times_incorrect INTEGER DEFAULT 0,
                    accuracy REAL DEFAULT 0.0
                )
            """)
            
            conn.commit()
    
    def get_game_words(self, count: int = 20, personalized: bool = True) -> List[Dict[str, Any]]:
        """
        Get words for a game session.
        
        Args:
            count: Number of words (20, 30, or 50, defaults to 20)
            personalized: If True, prioritize words user got wrong previously
            
        Returns:
            List of word dictionaries with word, article, difficulty, category
        """
        # Validate count
        if count not in [20, 30, 50]:
            count = 20
        if count > len(DUTCH_ARTICLE_WORDS):
            count = len(DUTCH_ARTICLE_WORDS)
        
        if personalized:
            return self._get_personalized_words(count)
        else:
            return get_random_words(count)
    
    def _get_personalized_words(self, count: int) -> List[Dict[str, Any]]:
        """Get personalized word selection based on user's history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get words with lowest accuracy (highest error rate)
            cursor.execute("""
                SELECT word FROM word_stats 
                WHERE times_seen > 0
                ORDER BY accuracy ASC
                LIMIT ?
            """, (count // 2,))  # Half from difficult words
            
            difficult_words = [row[0] for row in cursor.fetchall()]
        
        # Get word info for difficult words
        result = []
        for word in difficult_words:
            word_info = get_word_info(word)
            if word_info:
                result.append(word_info)
        
        # Fill remaining slots with random words
        remaining = count - len(result)
        if remaining > 0:
            random_words = get_random_words(remaining)
            result.extend(random_words)
        
        return result[:count]
    
    def submit_answer(self, word: str, user_answer: str) -> Dict[str, Any]:
        """
        Submit an answer for a word and check if it's correct.
        
        Args:
            word: The Dutch word
            user_answer: User's answer ('de' or 'het')
            
        Returns:
            Dictionary with is_correct, correct_article, and explanation
        """
        word_info = get_word_info(word)
        if not word_info:
            return {
                "is_correct": False,
                "error": "Word not found in database",
                "word": word
            }
        
        correct_article = word_info["article"]
        is_correct = user_answer.lower() == correct_article.lower()
        
        return {
            "is_correct": is_correct,
            "word": word,
            "correct_article": correct_article,
            "user_answer": user_answer.lower(),
            "difficulty": word_info.get("difficulty", "unknown"),
            "category": word_info.get("category", "unknown")
        }
    
    def save_game(self, answers: List[Dict[str, Any]]) -> int:
        """
        Save a completed game to the database.
        
        Args:
            answers: List of answer dictionaries from game
            
        Returns:
            Game ID of the saved game
        """
        if not answers:
            return -1
        
        # Calculate score and accuracy
        score = sum(1 for ans in answers if ans.get("is_correct", False))
        total = len(answers)
        accuracy = (score / total * 100) if total > 0 else 0
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert game record
            cursor.execute("""
                INSERT INTO games (word_count, score, total_questions, accuracy)
                VALUES (?, ?, ?, ?)
            """, (total, score, total, accuracy))
            
            game_id = cursor.lastrowid
            
            # Insert answer records
            for answer in answers:
                cursor.execute("""
                    INSERT INTO game_answers 
                    (game_id, word, correct_article, user_answer, is_correct)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    game_id,
                    answer.get("word", ""),
                    answer.get("correct_article", ""),
                    answer.get("user_answer", ""),
                    answer.get("is_correct", False)
                ))
                
                # Update word stats
                word = answer.get("word", "").lower()
                is_correct = answer.get("is_correct", False)
                
                cursor.execute("""
                    SELECT times_seen, times_correct, times_incorrect FROM word_stats
                    WHERE word = ?
                """, (word,))
                
                row = cursor.fetchone()
                if row:
                    times_seen, times_correct, times_incorrect = row
                    new_times_seen = times_seen + 1
                    new_times_correct = times_correct + (1 if is_correct else 0)
                    new_times_incorrect = times_incorrect + (0 if is_correct else 1)
                    new_accuracy = (new_times_correct / new_times_seen * 100) if new_times_seen > 0 else 0
                    
                    cursor.execute("""
                        UPDATE word_stats 
                        SET times_seen = ?, times_correct = ?, times_incorrect = ?, accuracy = ?
                        WHERE word = ?
                    """, (new_times_seen, new_times_correct, new_times_incorrect, new_accuracy, word))
                else:
                    new_accuracy = 100.0 if is_correct else 0.0
                    cursor.execute("""
                        INSERT INTO word_stats (word, times_seen, times_correct, times_incorrect, accuracy)
                        VALUES (?, ?, ?, ?, ?)
                    """, (word, 1, 1 if is_correct else 0, 0 if is_correct else 1, new_accuracy))
            
            conn.commit()
        
        return game_id
    
    def get_game_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent game history.
        
        Args:
            limit: Number of games to return
            
        Returns:
            List of game records with score and accuracy
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, date_played, word_count, score, total_questions, accuracy
                FROM games
                ORDER BY date_played DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_game_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics about game performance.
        
        Returns:
            Dictionary with overall stats
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Total games and average score
            cursor.execute("""
                SELECT COUNT(*) as total_games, AVG(accuracy) as avg_accuracy
                FROM games
            """)
            game_stats = dict(cursor.fetchone())
            
            # Word stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as words_studied,
                    SUM(times_seen) as total_attempts,
                    AVG(accuracy) as avg_word_accuracy
                FROM word_stats
                WHERE times_seen > 0
            """)
            word_stats = dict(cursor.fetchone())
            
            # Most difficult words
            cursor.execute("""
                SELECT word, accuracy, times_seen
                FROM word_stats
                WHERE times_seen > 0
                ORDER BY accuracy ASC
                LIMIT 5
            """)
            most_difficult = [dict(row) for row in cursor.fetchall()]
            
            # Best words
            cursor.execute("""
                SELECT word, accuracy, times_seen
                FROM word_stats
                WHERE times_seen > 0
                ORDER BY accuracy DESC
                LIMIT 5
            """)
            best_words = [dict(row) for row in cursor.fetchall()]
            
            return {
                "total_games": game_stats.get("total_games", 0),
                "avg_accuracy": game_stats.get("avg_accuracy", 0),
                "words_studied": word_stats.get("words_studied", 0),
                "total_attempts": word_stats.get("total_attempts", 0),
                "avg_word_accuracy": word_stats.get("avg_word_accuracy", 0),
                "most_difficult_words": most_difficult,
                "best_words": best_words
            }
    
    def get_detailed_game(self, game_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Game details including all answers
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get game info
            cursor.execute("""
                SELECT id, date_played, word_count, score, total_questions, accuracy
                FROM games
                WHERE id = ?
            """, (game_id,))
            
            game = cursor.fetchone()
            if not game:
                return None
            
            game_dict = dict(game)
            
            # Get answers for this game
            cursor.execute("""
                SELECT word, correct_article, user_answer, is_correct
                FROM game_answers
                WHERE game_id = ?
                ORDER BY id ASC
            """, (game_id,))
            
            game_dict["answers"] = [dict(row) for row in cursor.fetchall()]
            
            return game_dict
