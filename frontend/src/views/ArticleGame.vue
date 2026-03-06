<template>
    <div class="article-game-container">
        <ArticleGameRules />

        <div class="game-section">

            <!-- ══════════════════════════════════════════════
                 SETUP PHASE
            ══════════════════════════════════════════════ -->
            <div v-if="gamePhase === 'setup'" class="game-setup">



                <!-- ── Game config ── -->
                <div class="setup-header">
                    <h2>Start a Game</h2>
                    <span v-if="!auth.isAuthenticated" class="guest-badge">Guest mode</span>
                </div>

                <!-- Mode picker (logged-in only) -->
                <div v-if="auth.isAuthenticated" class="mode-picker">
                    <p class="mode-label">Game mode</p>
                    <div class="mode-options">
                        <button v-for="m in modes" :key="m.value" class="mode-btn"
                            :class="{ active: gameMode === m.value }" @click="gameMode = m.value">
                            <span class="mode-icon">{{ m.icon }}</span>
                            <span class="mode-name">{{ m.label }}</span>
                            <span class="mode-desc">{{ m.desc }}</span>
                        </button>
                    </div>
                </div>

                <p class="subtitle">How many words?</p>
                <div class="word-count-options">
                    <button v-for="count in [5, 10, 20, 30, 50]" :key="count" class="option-button"
                        @click="startGame(count)">
                        {{ count }} Words
                    </button>
                </div>

                <!-- Guest upsell banner -->
                <div v-if="!auth.isAuthenticated" class="guest-upsell">
                    <div class="upsell-icon">🚀</div>
                    <div class="upsell-body">
                        <p class="upsell-title">You're playing the basic version</p>
                        <ul class="upsell-features">
                            <li>✓ Random words — no personalisation</li>
                            <li>✓ Mistakes shown at the end — not saved</li>
                            <li>✗ <strong>No progress tracking or stats</strong></li>
                            <li>✗ <strong>No smart practice (focus on your weak words)</strong></li>
                            <li>✗ <strong>No Word Bank integration</strong></li>
                        </ul>
                        <div class="upsell-actions">
                            <router-link to="/register" class="upsell-btn-primary">Create free account</router-link>
                            <router-link to="/login" class="upsell-btn-secondary">Sign in</router-link>
                        </div>
                    </div>
                </div>
                <!-- ── Stats panel (logged-in only) ── -->
                <div v-if="auth.isAuthenticated && stats" class="stats-panel">
                    <div class="stats-panel-header">
                        <h3>📊 Your Progress</h3>
                        <router-link to="/article-game/stats" class="stats-full-link">
                            View full stats →
                        </router-link>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{{ stats.total_games }}</div>
                            <div class="stat-label">Games played</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ stats.avg_accuracy }}%</div>
                            <div class="stat-label">Avg accuracy</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ stats.words_studied }}</div>
                            <div class="stat-label">Words studied</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{{ stats.current_streak }}🔥</div>
                            <div class="stat-label">Win streak</div>
                        </div>
                    </div>

                    <!-- Hardest words -->
                    <div v-if="stats.hardest_words?.length" class="hardest-words">
                        <h4>⚠️ Words to work on</h4>
                        <div class="hw-list">
                            <div v-for="hw in stats.hardest_words" :key="hw.word" class="hw-item">
                                <span class="hw-word">{{ hw.word }}</span>
                                <span class="hw-article">→ {{ hw.correct_article }}</span>
                                <span class="hw-rate">{{ hw.times_wrong }}✗ / {{ hw.times_seen }}seen</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ══════════════════════════════════════════════
                 PLAYING PHASE
            ══════════════════════════════════════════════ -->
            <div v-else-if="gamePhase === 'playing'" class="game-playing">
                <div class="progress-section">
                    <div class="progress-info">
                        <span>{{ currentQuestionIndex + 1 }} / {{ gameWords.length }}</span>
                        <span>✓ {{ correctAnswers }}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill"
                            :style="{ width: (currentQuestionIndex / gameWords.length * 100) + '%' }">
                        </div>
                    </div>
                </div>

                <div class="word-display">
                    <div class="word-card">
                        <h3 class="word-text">{{ currentWord.word }}</h3>
                        <p class="word-translation">🇺🇸 {{ currentWord.translation }}</p>
                        <p class="word-hint">{{ currentWord.category }}</p>
                    </div>
                </div>

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

                <div v-if="feedback" class="feedback"
                    :class="{ correct: feedback.is_correct, wrong: !feedback.is_correct }">
                    <p class="feedback-text">{{ feedback.is_correct ? '✓ Correct!' : '✗ Wrong!' }}</p>
                    <p class="feedback-answer">Correct: <strong>{{ feedback.correct_article }} {{ currentWord.word
                    }}</strong></p>
                </div>
            </div>

            <!-- ══════════════════════════════════════════════
                 RESULTS PHASE
            ══════════════════════════════════════════════ -->
            <div v-else-if="gamePhase === 'results'" class="game-results">
                <div class="results-card">
                    <h2>Game Complete!</h2>

                    <div class="score-display">
                        <div class="large-score">
                            <div class="score-number">{{ finalScore }}</div>
                            <div class="score-total">/ {{ gameAnswers.length }}</div>
                        </div>
                        <div class="accuracy-display">
                            <div class="accuracy-percentage">{{ Math.round(finalAccuracy) }}%</div>
                            <div class="accuracy-label">Accuracy</div>
                        </div>
                    </div>

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

                    <!-- Mistakes list -->
                    <div v-if="mistakes.length > 0" class="mistakes-section">
                        <h3>Words to review</h3>
                        <div class="mistakes-list">
                            <div v-for="(m, i) in mistakes" :key="i" class="mistake-item">
                                <span class="mistake-word">{{ m.word }}</span>
                                <span class="mistake-answer">You: <strong>{{ m.user_answer }}</strong></span>
                                <span class="mistake-correct">Correct: <strong>{{ m.correct_article }}</strong></span>
                            </div>
                        </div>
                        <p v-if="auth.isAuthenticated" class="save-note">
                            ✅ These {{ mistakes.length }} mistake{{ mistakes.length > 1 ? 's' : '' }}
                            will appear more often in your next game.
                        </p>
                    </div>

                    <div class="results-actions">
                        <button @click="playAgain" class="action-button play-again">Play Again</button>
                        <button @click="$router.push('/')" class="action-button go-home">Back to Home</button>
                    </div>
                </div>
            </div>

        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { authAxios, useAuthStore } from '../stores/auth.js'
import ArticleGameRules from '../components/ArticleGameRules.vue'

const auth = useAuthStore()

// ── state ────────────────────────────────────────────────────
const gamePhase = ref('setup')
const gameWords = ref([])
const gameAnswers = ref([])
const currentQuestionIndex = ref(0)
const correctAnswers = ref(0)
const feedback = ref(null)
const answering = ref(false)
const finalScore = ref(0)
const finalAccuracy = ref(0)
const mistakes = ref([])
const stats = ref(null)
const gameMode = ref('smart')

// ── mode options (logged-in only) ───────────────────────────
const modes = [
    { value: 'smart', icon: '🧠', label: 'Smart', desc: 'Mix of your mistakes + word bank + random' },
    { value: 'mistakes', icon: '⚠️', label: 'Mistakes', desc: 'Focus on words you get wrong' },
    { value: 'wordbank', icon: '📚', label: 'Word Bank', desc: 'Words from your personal dictionary' },
    { value: 'random', icon: '🎲', label: 'Random', desc: 'Fully random selection' },
]

// ── computed ─────────────────────────────────────────────────
const currentWord = computed(() =>
    gameWords.value[currentQuestionIndex.value] ?? { word: '', translation: '', category: '' }
)

// ── lifecycle ────────────────────────────────────────────────
onMounted(async () => {
    if (auth.isAuthenticated) {
        await loadStats()
    }
})

// ── methods ──────────────────────────────────────────────────
async function loadStats() {
    try {
        let authAxios = auth.getAuthAxios()
        const res = await authAxios.get('/api/game/stats')
        stats.value = res.data
    } catch {
        // not fatal
    }
}

async function startGame(wordCount) {
    try {
        const payload = { count: wordCount, mode: auth.isAuthenticated ? gameMode.value : 'random' }
        const headers = {}
        let res

        if (auth.isAuthenticated) {
            let authAxios = auth.getAuthAxios()
            res = await authAxios.post('/api/game/words', payload)
        } else {
            // guest — plain fetch, no auth header
            const r = await fetch('/api/game/words', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })
            res = { data: await r.json() }
        }

        gameWords.value = res.data.words
        gameAnswers.value = []
        currentQuestionIndex.value = 0
        correctAnswers.value = 0
        feedback.value = null
        mistakes.value = []
        gamePhase.value = 'playing'
    } catch (e) {
        console.error(e)
        alert('Failed to start game. Please try again.')
    }
}

async function submitAnswer(answer) {
    if (answering.value) return
    answering.value = true

    try {
        const r = await fetch('/api/game/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: currentWord.value.word, user_answer: answer }),
        })
        const result = await r.json()

        const record = {
            word: currentWord.value.word,
            correct_article: result.correct_article,
            user_answer: answer,
            is_correct: result.is_correct,
        }
        gameAnswers.value.push(record)
        feedback.value = result
        if (result.is_correct) correctAnswers.value++

        setTimeout(() => {
            currentQuestionIndex.value++
            feedback.value = null
            if (currentQuestionIndex.value >= gameWords.value.length) {
                endGame()
            }
            answering.value = false
        }, 1500)
    } catch (e) {
        console.error(e)
        answering.value = false
    }
}

async function endGame() {
    const score = correctAnswers.value
    const total = gameAnswers.value.length
    finalScore.value = score
    finalAccuracy.value = total ? (score / total) * 100 : 0
    mistakes.value = gameAnswers.value.filter(a => !a.is_correct)

    // Only save if logged in
    if (auth.isAuthenticated) {
        try {
            let authAxios = auth.getAuthAxios()
            await authAxios.post('/api/game/save', { answers: gameAnswers.value })
            await loadStats()   // refresh stats panel for next setup screen
        } catch (e) {
            console.error('Failed to save game', e)
        }
    }

    gamePhase.value = 'results'
}

function playAgain() {
    gamePhase.value = 'setup'
    gameWords.value = []
    gameAnswers.value = []
    currentQuestionIndex.value = 0
    correctAnswers.value = 0
    feedback.value = null
    mistakes.value = []
}
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

/* ── Setup ──────────────────────────────────────────────── */
.game-setup h2 {
    font-size: 26px;
    margin-bottom: 10px;
    color: #333;
}

.subtitle {
    font-size: 15px;
    color: #666;
    margin-bottom: 20px;
}

/* Stats panel */
.stats-panel {
    background: #f0f4ff;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 28px;
}

.stats-panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.stats-panel-header h3 {
    margin: 0;
    font-size: 16px;
    color: #444;
}

.stats-full-link {
    font-size: 13px;
    font-weight: 600;
    color: #667eea;
    text-decoration: none;
    white-space: nowrap;
}

.stats-full-link:hover {
    text-decoration: underline;
}

/* Remove old h3 rule now covered by .stats-panel-header h3 */

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}

.stat-card {
    background: white;
    padding: 14px 10px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.07);
}

.stat-number {
    font-size: 22px;
    font-weight: 700;
    color: #667eea;
}

.stat-label {
    font-size: 11px;
    color: #777;
    margin-top: 4px;
}

.hardest-words h4 {
    font-size: 13px;
    color: #e53e3e;
    margin: 0 0 10px;
}

.hw-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.hw-item {
    display: flex;
    align-items: center;
    gap: 12px;
    background: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
}

.hw-word {
    font-weight: 700;
    flex: 0 0 100px;
}

.hw-article {
    color: #38a169;
    flex: 0 0 60px;
}

.hw-rate {
    color: #e53e3e;
    margin-left: auto;
}

/* Mode picker */
.mode-picker {
    margin-bottom: 24px;
}

.mode-label {
    font-size: 14px;
    font-weight: 600;
    color: #444;
    margin-bottom: 10px;
}

.mode-options {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

.mode-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 14px 8px;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
    text-align: center;
}

.mode-btn:hover {
    border-color: #667eea;
}

.mode-btn.active {
    border-color: #667eea;
    background: #f0f4ff;
}

.mode-icon {
    font-size: 20px;
}

.mode-name {
    font-size: 13px;
    font-weight: 700;
    color: #333;
}

.mode-desc {
    font-size: 11px;
    color: #888;
    line-height: 1.3;
}

/* Word count buttons */
.word-count-options {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.option-button {
    padding: 14px 28px;
    font-size: 16px;
    border: 2px solid #667eea;
    background: white;
    color: #667eea;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
}

.option-button:hover {
    background: #667eea;
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* Setup header row */
.setup-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
}

.setup-header h2 {
    font-size: 26px;
    color: #333;
    margin: 0;
}

.guest-badge {
    background: #718096;
    color: white;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* Guest upsell banner */
.guest-upsell {
    display: flex;
    gap: 16px;
    background: linear-gradient(135deg, #667eea11 0%, #764ba222 100%);
    border: 1.5px solid #667eea44;
    border-radius: 12px;
    padding: 20px;
    margin-top: 20px;
}

.upsell-icon {
    font-size: 32px;
    flex-shrink: 0;
    line-height: 1;
}

.upsell-body {
    flex: 1;
}

.upsell-title {
    font-size: 15px;
    font-weight: 700;
    color: #2d3748;
    margin: 0 0 10px;
}

.upsell-features {
    list-style: none;
    padding: 0;
    margin: 0 0 16px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 13.5px;
    color: #4a5568;
}

.upsell-features li strong {
    color: #2d3748;
}

.upsell-actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.upsell-btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 9px 20px;
    border-radius: 7px;
    text-decoration: none;
    font-size: 14px;
    font-weight: 600;
    transition: opacity 0.2s;
}

.upsell-btn-primary:hover {
    opacity: 0.88;
}

.upsell-btn-secondary {
    background: white;
    color: #667eea;
    border: 1.5px solid #667eea;
    padding: 8px 18px;
    border-radius: 7px;
    text-decoration: none;
    font-size: 14px;
    font-weight: 600;
    transition: background 0.2s;
}

.upsell-btn-secondary:hover {
    background: #f0f4ff;
}

/* ── Playing ────────────────────────────────────────────── */
.progress-section {
    margin-bottom: 24px;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    font-size: 14px;
    color: #666;
    margin-bottom: 8px;
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
    background: linear-gradient(90deg, #667eea, #764ba2);
    transition: width 0.3s ease;
}

.word-display {
    text-align: center;
    margin: 36px 0;
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
    margin: 0 0 10px;
    letter-spacing: 2px;
}

.word-translation {
    font-size: 17px;
    opacity: 0.85;
    margin: 0 0 12px;
    font-style: italic;
}

.word-hint {
    font-size: 13px;
    opacity: 0.75;
    margin: 0;
    text-transform: capitalize;
}

.answer-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin: 28px 0;
}

.answer-button {
    padding: 20px;
    font-size: 16px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    font-weight: 500;
}

.de-button {
    background: #38a169;
    color: white;
}

.de-button:hover:not(:disabled) {
    background: #2f855a;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(56, 161, 105, 0.3);
}

.het-button {
    background: #d69e2e;
    color: white;
}

.het-button:hover:not(:disabled) {
    background: #b7791f;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(214, 158, 46, 0.3);
}

.answer-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.article {
    font-size: 22px;
    font-weight: 700;
}

.article-label {
    font-size: 12px;
    opacity: 0.8;
}

.feedback {
    padding: 14px;
    border-radius: 8px;
    text-align: center;
    animation: slideIn 0.25s ease;
}

.feedback.correct {
    background: #c6f6d5;
    color: #276749;
    border: 1px solid #9ae6b4;
}

.feedback.wrong {
    background: #fed7d7;
    color: #9b2c2c;
    border: 1px solid #feb2b2;
}

.feedback-text {
    font-size: 18px;
    font-weight: 700;
    margin: 0 0 6px;
}

.feedback-answer {
    font-size: 14px;
    margin: 0;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(-8px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ── Results ────────────────────────────────────────────── */
.game-results {
    text-align: center;
}

.results-card h2 {
    font-size: 28px;
    margin-bottom: 28px;
    color: #333;
}

.score-display {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 28px;
}

.large-score {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 28px;
    border-radius: 12px;
}

.score-number {
    font-size: 48px;
    font-weight: 700;
}

.score-total {
    font-size: 18px;
    opacity: 0.85;
}

.accuracy-display {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 28px;
    border-radius: 12px;
}

.accuracy-percentage {
    font-size: 48px;
    font-weight: 700;
}

.accuracy-label {
    font-size: 15px;
    opacity: 0.85;
}

.performance-breakdown {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin: 24px 0;
}

.breakdown-item {
    padding: 18px;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.breakdown-item.correct {
    background: #c6f6d5;
    color: #276749;
}

.breakdown-item.wrong {
    background: #fed7d7;
    color: #9b2c2c;
}

.count {
    font-size: 32px;
    font-weight: 700;
}

.label {
    font-size: 14px;
}

.mistakes-section {
    text-align: left;
    margin: 24px 0;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
}

.mistakes-section h3 {
    margin-top: 0;
    font-size: 17px;
    color: #333;
}

.mistakes-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.mistake-item {
    background: white;
    padding: 10px 14px;
    border-left: 4px solid #f5576c;
    border-radius: 4px;
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
    font-size: 14px;
}

.mistake-word {
    font-weight: 700;
    color: #333;
}

.mistake-answer {
    color: #9b2c2c;
}

.mistake-correct {
    color: #276749;
}

.save-note {
    margin: 12px 0 0;
    font-size: 13px;
    color: #38a169;
    font-style: italic;
}

.results-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-top: 28px;
}

.action-button {
    padding: 14px;
    font-size: 16px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
}

.play-again {
    background: #667eea;
    color: white;
}

.play-again:hover {
    background: #5a67d8;
    transform: translateY(-2px);
}

.go-home {
    background: #718096;
    color: white;
}

.go-home:hover {
    background: #4a5568;
    transform: translateY(-2px);
}

/* ── Responsive ─────────────────────────────────────────── */
@media (max-width: 700px) {
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .mode-options {
        grid-template-columns: repeat(2, 1fr);
    }

    .word-count-options {
        flex-direction: column;
    }

    .option-button {
        width: 100%;
    }

    .word-text {
        font-size: 36px;
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
