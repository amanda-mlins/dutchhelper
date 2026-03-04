<template>
    <div class="article-game-container">
        <!-- Rules/Explanation Section -->
        <ArticleGameRules />

        <!-- Main Game Area -->
        <div class="game-section">
            <!-- Setup Phase -->
            <div v-if="gamePhase === 'setup'" class="game-setup">
                <h2>Start a Game</h2>
                <p class="subtitle">How many words would you like to practice?</p>

                <div class="word-count-options">
                    <button v-for="count in [20, 30, 50]" :key="count" @click="startGame(count)" class="option-button">
                        {{ count }} Words
                    </button>
                </div>

                <div class="options-checkbox">
                    <label>
                        <input v-model="personalizedGame" type="checkbox" />
                        <span>Personalized game (focus on difficult words)</span>
                    </label>
                </div>

                <!-- Recent Stats -->
                <div v-if="stats && stats.total_games > 0" class="recent-stats">
                    <h3>Your Progress</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{{ stats.total_games }}</div>
                            <div class="stat-label">Games Played</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ (stats.avg_accuracy || 0).toFixed(1) }}%</div>
                            <div class="stat-label">Average Accuracy</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ stats.words_studied || 0 }}</div>
                            <div class="stat-label">Words Studied</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Playing Phase -->
            <div v-else-if="gamePhase === 'playing'" class="game-playing">
                <!-- Progress Bar -->
                <div class="progress-section">
                    <div class="progress-info">
                        <span>Question {{ currentQuestionIndex + 1 }} of {{ gameWords.length }}</span>
                        <span>Score: {{ correctAnswers }} / {{ currentQuestionIndex }}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill"
                            :style="{ width: (currentQuestionIndex / gameWords.length * 100) + '%' }"></div>
                    </div>
                </div>

                <!-- Word Display -->
                <div class="word-display">
                    <div class="word-card">
                        <h3 class="word-text">{{ currentWord.word }}</h3>
                        <p class="word-translation">🇺🇸 Translation: {{ currentWord.translation }}</p>
                        <p class="word-hint">Category: {{ currentWord.category }}</p>
                    </div>
                </div>

                <!-- Answer Buttons -->
                <div class="answer-buttons">
                    <button @click="submitAnswer('de')" :disabled="answering" class="answer-button de-button">
                        <span class="article">de</span>
                        <span class="article-label">The (common)</span>
                    </button>
                    <button @click="submitAnswer('het')" :disabled="answering" class="answer-button het-button">
                        <span class="article">het</span>
                        <span class="article-label">The (neuter)</span>
                    </button>
                </div>

                <!-- Feedback -->
                <div v-if="feedback" class="feedback"
                    :class="{ correct: feedback.is_correct, wrong: !feedback.is_correct }">
                    <p v-if="feedback.is_correct" class="feedback-text">✓ Correct!</p>
                    <p v-else class="feedback-text">✗ Wrong!</p>
                    <p class="feedback-answer">The correct answer is: <strong>{{ feedback.correct_article }}</strong>
                    </p>
                </div>
            </div>

            <!-- Results Phase -->
            <div v-else-if="gamePhase === 'results'" class="game-results">
                <div class="results-card">
                    <h2>Game Complete!</h2>

                    <div class="score-display">
                        <div class="large-score">
                            <div class="score-number">{{ finalScore }}</div>
                            <div class="score-total">/ {{ gameAnswers.length }}</div>
                        </div>
                        <div class="accuracy-display">
                            <div class="accuracy-percentage">{{ finalAccuracy.toFixed(1) }}%</div>
                            <div class="accuracy-label">Accuracy</div>
                        </div>
                    </div>

                    <!-- Performance Breakdown -->
                    <div class="performance-breakdown">
                        <div class="breakdown-item correct">
                            <span class="count">{{ finalScore }}</span>
                            <span class="label">Correct</span>
                        </div>
                        <div class="breakdown-item wrong">
                            <span class="count">{{ gameAnswers.length - finalScore }}</span>
                            <span class="label">Incorrect</span>
                        </div>
                    </div>

                    <!-- Mistakes Review -->
                    <div v-if="mistakes.length > 0" class="mistakes-section">
                        <h3>Words to Review</h3>
                        <div class="mistakes-list">
                            <div v-for="(mistake, idx) in mistakes" :key="idx" class="mistake-item">
                                <span class="mistake-word">{{ mistake.word }}</span>
                                <span class="mistake-answer">
                                    You said: <strong>{{ mistake.user_answer }}</strong>
                                </span>
                                <span class="mistake-correct">
                                    Correct: <strong>{{ mistake.correct_article }}</strong>
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="results-actions">
                        <button @click="playAgain" class="action-button play-again">
                            Play Again
                        </button>
                        <button @click="goHome" class="action-button go-home">
                            Back to Home
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import ArticleGameRules from '../components/ArticleGameRules.vue';

export default {
    name: 'ArticleGame',
    components: {
        ArticleGameRules
    },
    data() {
        return {
            gamePhase: 'setup', // 'setup', 'playing', 'results'
            gameWords: [],
            gameAnswers: [],
            currentQuestionIndex: 0,
            correctAnswers: 0,
            personalizedGame: true,
            feedback: null,
            answering: false,
            stats: null,
            finalScore: 0,
            finalAccuracy: 0,
            mistakes: []
        };
    },
    computed: {
        currentWord() {
            if (this.currentQuestionIndex < this.gameWords.length) {
                return this.gameWords[this.currentQuestionIndex];
            }
            return { word: '', category: '' };
        }
    },
    async mounted() {
        // Load stats on mount
        try {
            const response = await fetch('/api/game/stats');
            if (response.ok) {
                this.stats = await response.json();
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    },
    methods: {
        async startGame(wordCount) {
            try {
                const response = await fetch('/api/game/words', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        count: wordCount,
                        personalized: this.personalizedGame
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to load game words');
                }

                const data = await response.json();
                this.gameWords = data.words;
                this.gameAnswers = [];
                this.currentQuestionIndex = 0;
                this.correctAnswers = 0;
                this.feedback = null;
                this.gamePhase = 'playing';
            } catch (error) {
                console.error('Error starting game:', error);
                alert('Failed to start game. Please try again.');
            }
        },

        async submitAnswer(answer) {
            if (this.answering) return;

            this.answering = true;

            try {
                const response = await fetch('/api/game/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        word: this.currentWord.word,
                        user_answer: answer
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to submit answer');
                }

                const result = await response.json();

                // Store the answer with result
                const answerRecord = {
                    word: this.currentWord.word,
                    correct_article: result.correct_article,
                    user_answer: answer,
                    is_correct: result.is_correct
                };

                this.gameAnswers.push(answerRecord);
                this.feedback = result;

                // Update score
                if (result.is_correct) {
                    this.correctAnswers++;
                }

                // Move to next question after delay
                setTimeout(() => {
                    this.currentQuestionIndex++;
                    this.feedback = null;

                    if (this.currentQuestionIndex >= this.gameWords.length) {
                        this.endGame();
                    }

                    this.answering = false;
                }, 2000);
            } catch (error) {
                console.error('Error submitting answer:', error);
                alert('Error submitting answer. Please try again.');
                this.answering = false;
            }
        },

        async endGame() {
            try {
                // Save game to database
                const response = await fetch('/api/game/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        answers: this.gameAnswers
                    })
                });

                if (response.ok) {
                    const result = await response.json();
                    this.finalScore = result.score;
                    this.finalAccuracy = result.accuracy;
                }
            } catch (error) {
                console.error('Error saving game:', error);
                this.finalScore = this.correctAnswers;
                this.finalAccuracy = (this.correctAnswers / this.gameAnswers.length * 100);
            }

            // Extract mistakes
            this.mistakes = this.gameAnswers.filter(ans => !ans.is_correct);

            this.gamePhase = 'results';
        },

        playAgain() {
            this.gamePhase = 'setup';
            this.gameWords = [];
            this.gameAnswers = [];
            this.currentQuestionIndex = 0;
            this.correctAnswers = 0;
            this.feedback = null;
            this.mistakes = [];

            // Reload stats
            this.loadStats();
        },

        goHome() {
            this.$router.push('/');
        },

        async loadStats() {
            try {
                const response = await fetch('/api/game/stats');
                if (response.ok) {
                    this.stats = await response.json();
                }
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }
    }
};
</script>

<style scoped>
.article-game-container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
}

.game-section {
    background: white;
    border-radius: 12px;
    padding: 30px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Setup Phase */
.game-setup h2 {
    font-size: 28px;
    margin-bottom: 10px;
    color: #333;
}

.subtitle {
    font-size: 16px;
    color: #666;
    margin-bottom: 30px;
}

.word-count-options {
    display: flex;
    gap: 15px;
    margin-bottom: 25px;
    flex-wrap: wrap;
}

.option-button {
    padding: 15px 30px;
    font-size: 16px;
    border: 2px solid #007bff;
    background: white;
    color: #007bff;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
}

.option-button:hover {
    background: #007bff;
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.options-checkbox {
    margin-bottom: 30px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 8px;
}

.options-checkbox label {
    display: flex;
    align-items: center;
    cursor: pointer;
    font-size: 15px;
    color: #555;
}

.options-checkbox input {
    margin-right: 10px;
    width: 18px;
    height: 18px;
    cursor: pointer;
}

/* Stats Section */
.recent-stats {
    margin-top: 30px;
    padding-top: 30px;
    border-top: 1px solid #eee;
}

.recent-stats h3 {
    font-size: 18px;
    margin-bottom: 15px;
    color: #333;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
}

.stat-card {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
}

.stat-number {
    font-size: 24px;
    font-weight: bold;
    color: #007bff;
}

.stat-label {
    font-size: 13px;
    color: #666;
    margin-top: 5px;
}

/* Playing Phase */
.progress-section {
    margin-bottom: 30px;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    font-size: 14px;
    color: #666;
    margin-bottom: 10px;
}

.progress-bar {
    width: 100%;
    height: 6px;
    background: #e9ecef;
    border-radius: 3px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #007bff, #0056b3);
    transition: width 0.3s ease;
}

.word-display {
    text-align: center;
    margin: 40px 0;
}

.word-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 40px;
    border-radius: 12px;
    color: white;
}

.word-text {
    font-size: 48px;
    font-weight: 300;
    margin: 0 0 10px 0;
    letter-spacing: 2px;
}

.word-translation {
    font-size: 18px;
    opacity: 0.85;
    margin: 0 0 15px 0;
    font-style: italic;
}

.word-hint {
    font-size: 14px;
    opacity: 0.9;
    margin: 0;
}

.answer-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin: 30px 0;
}

.answer-button {
    padding: 20px;
    font-size: 16px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    font-weight: 500;
}

.de-button {
    background: #28a745;
    color: white;
}

.de-button:hover:not(:disabled) {
    background: #218838;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
}

.het-button {
    background: #ffc107;
    color: #333;
}

.het-button:hover:not(:disabled) {
    background: #e0a800;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
}

.answer-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.article {
    font-size: 20px;
    font-weight: bold;
}

.article-label {
    font-size: 12px;
    opacity: 0.8;
}

.feedback {
    margin-top: 20px;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    animation: slideIn 0.3s ease;
}

.feedback.correct {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.feedback.wrong {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

.feedback-text {
    font-size: 18px;
    font-weight: bold;
    margin: 0 0 8px 0;
}

.feedback-answer {
    font-size: 14px;
    margin: 0;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Results Phase */
.game-results {
    text-align: center;
}

.results-card {
    background: white;
}

.results-card h2 {
    font-size: 28px;
    margin-bottom: 30px;
    color: #333;
}

.score-display {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin-bottom: 40px;
}

.large-score {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
    border-radius: 12px;
}

.score-number {
    font-size: 48px;
    font-weight: bold;
}

.score-total {
    font-size: 20px;
    opacity: 0.9;
}

.accuracy-display {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 30px;
    border-radius: 12px;
}

.accuracy-percentage {
    font-size: 48px;
    font-weight: bold;
}

.accuracy-label {
    font-size: 16px;
    opacity: 0.9;
}

.performance-breakdown {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin: 30px 0;
}

.breakdown-item {
    padding: 20px;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.breakdown-item.correct {
    background: #d4edda;
    color: #155724;
}

.breakdown-item.wrong {
    background: #f8d7da;
    color: #721c24;
}

.count {
    font-size: 32px;
    font-weight: bold;
}

.label {
    font-size: 14px;
}

/* Mistakes Section */
.mistakes-section {
    text-align: left;
    margin: 30px 0;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
}

.mistakes-section h3 {
    margin-top: 0;
    font-size: 18px;
    color: #333;
}

.mistakes-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.mistake-item {
    background: white;
    padding: 12px;
    border-left: 4px solid #f5576c;
    border-radius: 4px;
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 15px;
    font-size: 14px;
}

.mistake-word {
    font-weight: bold;
    color: #333;
}

.mistake-answer {
    color: #721c24;
}

.mistake-correct {
    color: #155724;
}

/* Results Actions */
.results-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-top: 30px;
}

.action-button {
    padding: 15px;
    font-size: 16px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
}

.play-again {
    background: #007bff;
    color: white;
}

.play-again:hover {
    background: #0056b3;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 123, 255, 0.3);
}

.go-home {
    background: #6c757d;
    color: white;
}

.go-home:hover {
    background: #5a6268;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
}

/* Responsive */
@media (max-width: 768px) {
    .word-count-options {
        flex-direction: column;
    }

    .option-button {
        width: 100%;
    }

    .word-text {
        font-size: 36px;
    }

    .word-translation {
        font-size: 16px;
    }

    .answer-buttons {
        grid-template-columns: 1fr;
    }

    .score-display {
        grid-template-columns: 1fr;
    }

    .mistake-item {
        grid-template-columns: 1fr;
    }

    .results-actions {
        grid-template-columns: 1fr;
    }
}
</style>
