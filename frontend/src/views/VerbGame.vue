<template>
    <div class="verb-game-container">

        <!-- ══════════════════════════════════════════════════════════════ -->
        <!-- SETUP PHASE                                                    -->
        <!-- ══════════════════════════════════════════════════════════════ -->
        <div v-if="phase === 'setup'" class="setup-screen">
            <div class="setup-header">
                <h2>✍️ Verb Conjugation Game</h2>
                <p>Fill in the correct conjugated form of the given verb.</p>
            </div>

            <!-- Mini stats for returning players -->
            <div v-if="stats && stats.total_games" class="stats-panel">
                <div class="stats-panel-header">
                    <h3>📊 Your Progress</h3>
                    <router-link to="/verb-game/stats" class="stats-full-link">View full stats →</router-link>
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
                        <div class="stat-number">{{ stats.questions_answered }}</div>
                        <div class="stat-label">Questions answered</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ stats.current_streak }}🔥</div>
                        <div class="stat-label">Win streak</div>
                    </div>
                </div>
                <div v-if="stats.hardest_verbs?.length" class="hardest-verbs">
                    <h4>⚠️ Verbs to work on</h4>
                    <div class="hv-list">
                        <div v-for="hv in stats.hardest_verbs.slice(0, 5)" :key="hv.verb" class="hv-item">
                            <span class="hv-verb">{{ hv.verb }}</span>
                            <span class="hv-rate">{{ hv.times_wrong }}✗ / {{ hv.times_seen }} seen</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Custom verb input -->
            <div class="verb-input-section">
                <p class="mode-label">Enter a specific verb (optional):</p>
                <div class="verb-input-row">
                    <input v-model="customVerb" type="text" placeholder="e.g. werken, gaan, komen…" class="verb-input"
                        :disabled="useWordBank" @input="onCustomVerbInput" @keyup.enter="startGame" />
                </div>
                <p class="verb-input-note">Leave empty to pick a random verb each round.</p>
            </div>

            <!-- Word bank verbs toggle (only shown when authenticated) -->
            <div v-if="wordBankVerbs !== null" class="word-bank-section">
                <div class="toggle-row" @click="toggleWordBank">
                    <div class="toggle-track" :class="{ 'toggle-on': useWordBank }">
                        <div class="toggle-thumb"></div>
                    </div>
                    <span class="toggle-label">
                        Use my word bank verbs
                        <span class="toggle-count">({{ wordBankVerbs.length }} verb{{ wordBankVerbs.length !== 1 ? 's' :
                            '' }})</span>
                    </span>
                </div>
                <div v-if="useWordBank && wordBankVerbs.length === 0" class="wb-empty">
                    Your word bank has no verbs yet. <router-link to="/word-bank">Add some →</router-link>
                </div>
                <div v-if="useWordBank && wordBankVerbs.length" class="wb-preview">
                    <span v-for="v in wordBankVerbs" :key="v.id" class="wb-chip">{{ v.word }}</span>
                </div>
                <p v-if="useWordBank" class="verb-input-note">Custom verb field is ignored when using word bank.</p>
            </div>

            <!-- Tense filter -->
            <div class="tense-section">
                <p class="mode-label">Which tenses to practice?</p>
                <div class="tense-options">
                    <label v-for="t in ALL_TENSES" :key="t" class="tense-chip"
                        :class="{ 'tense-active': selectedTenses.includes(t) }">
                        <input type="checkbox" :value="t" v-model="selectedTenses" hidden />
                        {{ t }}
                    </label>
                </div>
                <p v-if="selectedTenses.length === 0" class="tense-warning">
                    ⚠️ Select at least one tense.
                </p>
            </div>

            <!-- Difficulty -->
            <div class="difficulty-section">
                <p class="mode-label">Difficulty</p>
                <div class="difficulty-options">
                    <button v-for="d in DIFFICULTIES" :key="d.value"
                        :class="['diff-btn', { active: difficulty === d.value }]" @click="difficulty = d.value">
                        <span class="diff-icon">{{ d.icon }}</span>
                        <span class="diff-name">{{ d.label }}</span>
                        <span class="diff-desc">{{ d.desc }}</span>
                    </button>
                </div>
            </div>

            <!-- Question count -->
            <p class="mode-label">How many questions?</p>
            <div class="count-options">
                <button v-for="n in [5, 10, 15, 20]" :key="n" :class="['count-btn', { active: questionCount === n }]"
                    @click="questionCount = n">
                    {{ n }}
                </button>
            </div>

            <button class="btn-start" @click="startGame" :disabled="isLoadingQuestion">
                <span v-if="isLoadingQuestion" class="spinner">⟳</span>
                <span v-else>Start game ({{ questionCount }} questions)</span>
            </button>
            <div v-if="setupError" class="error-msg">{{ setupError }}</div>
        </div>

        <!-- ══════════════════════════════════════════════════════════════ -->
        <!-- PLAYING PHASE                                                  -->
        <!-- ══════════════════════════════════════════════════════════════ -->
        <div v-else-if="phase === 'playing'" class="playing-screen">

            <!-- Progress -->
            <div class="progress-section">
                <div class="progress-info">
                    <span>{{ currentIndex + 1 }} / {{ questionCount }}</span>
                    <span class="diff-badge diff-badge--{{ difficulty }}">{{DIFFICULTIES.find(d => d.value ===
                        difficulty)?.icon}} {{ difficulty }}</span>
                    <span class="score-inline">✓ {{ correctSoFar }}</span>
                </div>
                <div class="progress-bar-wrap">
                    <div class="progress-bar" :style="{ width: (currentIndex / questionCount * 100) + '%' }"></div>
                </div>
            </div>

            <!-- Loading next question -->
            <div v-if="isLoadingQuestion" class="question-loading">
                <div class="spinner-large">⟳</div>
                <p>Generating question…</p>
            </div>

            <template v-else-if="currentQuestion">
                <!-- Verb header -->
                <div class="verb-header">
                    <span class="verb-label">Verb</span>
                    <span class="verb-name">{{ currentQuestion.verb_infinitive }}</span>
                    <span class="verb-tense-badge">{{ currentQuestion.tense }}</span>
                    <span class="verb-person-badge">{{ currentQuestion.person }}</span>
                </div>

                <!-- Sentence card -->
                <div class="sentence-card">
                    <p class="sentence-text" v-html="highlightedSentence"></p>
                    <p class="sentence-hint">{{ currentQuestion.english_hint }}</p>
                </div>

                <!-- ── EASY: options grid + optional type-in ── -->
                <template v-if="difficulty === 'easy'">
                    <div v-if="!answered" class="options-grid">
                        <button v-for="opt in currentOptions" :key="opt" class="option-btn"
                            @click="selectOption(opt)">{{ opt }}</button>
                    </div>
                    <div v-if="!answered" class="or-separator"><span>or type your answer:</span></div>
                    <div v-if="!answered" class="type-row">
                        <input ref="answerInput" v-model="typedAnswer" type="text" class="answer-input"
                            placeholder="Type conjugated form…" @keyup.enter="submitTyped" />
                        <button class="btn-submit" @click="submitTyped" :disabled="!typedAnswer.trim()">
                            Check ✓
                        </button>
                    </div>
                </template>

                <!-- ── MEDIUM: options grid only ── -->
                <template v-else-if="difficulty === 'medium'">
                    <div v-if="!answered" class="options-grid">
                        <button v-for="opt in currentOptions" :key="opt" class="option-btn"
                            @click="selectOption(opt)">{{ opt }}</button>
                    </div>
                </template>

                <!-- ── HARD: type-only, no hints ── -->
                <template v-else-if="difficulty === 'hard'">
                    <div v-if="!answered" class="type-row type-row-hard">
                        <input ref="answerInput" v-model="typedAnswer" type="text" class="answer-input"
                            placeholder="Type the conjugated form…" @keyup.enter="submitTyped" />
                        <button class="btn-submit" @click="submitTyped" :disabled="!typedAnswer.trim()">
                            Check ✓
                        </button>
                    </div>
                </template>

                <!-- Feedback (shown after answered) -->
                <div v-if="answered" class="feedback-card"
                    :class="lastWasCorrect ? 'feedback-correct' : 'feedback-wrong'">
                    <p class="feedback-verdict">
                        {{ lastWasCorrect ? '✓ Correct!' : '✗ Incorrect' }}
                    </p>
                    <p class="feedback-detail">
                        The correct answer is: <strong>{{ currentQuestion.correct_answer }}</strong>
                    </p>
                    <p v-if="!lastWasCorrect" class="feedback-your">
                        Your answer: <span class="user-wrong">{{ lastUserAnswer }}</span>
                    </p>
                    <p class="feedback-sentence-full">
                        {{ currentQuestion.sentence.replace('___', currentQuestion.correct_answer) }}
                    </p>
                </div>

                <!-- Next button -->
                <button v-if="answered" class="btn-next" @click="nextQuestion" :disabled="isLoadingQuestion">
                    <span v-if="isLoadingQuestion" class="spinner">⟳</span>
                    <span v-else>{{ currentIndex + 1 >= questionCount ? 'See results →' : 'Next question →' }}</span>
                </button>
            </template>

            <div v-if="questionError" class="error-msg">
                {{ questionError }}
                <button class="btn-retry" @click="loadNextQuestion">Retry</button>
            </div>
        </div>

        <!-- ══════════════════════════════════════════════════════════════ -->
        <!-- RESULTS PHASE                                                  -->
        <!-- ══════════════════════════════════════════════════════════════ -->
        <div v-else-if="phase === 'results'" class="results-screen">
            <div class="results-card">
                <h2>Game Complete! 🎉</h2>

                <div class="score-display">
                    <div class="score-circle" :class="scoreClass">
                        <span class="score-number">{{ finalScore }}</span>
                        <span class="score-total">/ {{ answers.length }}</span>
                    </div>
                    <p class="accuracy-label">{{ finalAccuracy }}% accuracy</p>
                    <p v-if="isSaving" class="saving-msg">Saving results…</p>
                    <p v-else-if="saveError" class="error-msg">{{ saveError }}</p>
                </div>

                <!-- Answer review -->
                <div class="answer-review">
                    <h3>Answer review</h3>
                    <div class="review-list">
                        <div v-for="(ans, i) in answers" :key="i" class="review-item"
                            :class="ans.is_correct ? 'review-correct' : 'review-wrong'">
                            <div class="review-top">
                                <span class="review-verb">{{ ans.verb_infinitive }}</span>
                                <span class="review-tense">{{ ans.tense }} · {{ ans.person }}</span>
                                <span class="review-icon">{{ ans.is_correct ? '✓' : '✗' }}</span>
                            </div>
                            <p class="review-sentence">
                                {{ ans.sentence.replace('___', ans.correct_answer) }}
                            </p>
                            <p v-if="!ans.is_correct" class="review-your">
                                Your answer: <span>{{ ans.user_answer || '(blank)' }}</span>
                                → correct: <strong>{{ ans.correct_answer }}</strong>
                            </p>
                        </div>
                    </div>
                </div>

                <div class="results-actions">
                    <button class="btn-primary" @click="resetToSetup">🔁 Play again</button>
                    <router-link to="/verb-game/stats" class="btn-secondary">📊 View stats</router-link>
                </div>
            </div>
        </div>

    </div>
</template>

<script>
import { authAxios } from '../stores/auth.js';

const ALL_TENSES = ['Present', 'Simple Past', 'Present Perfect', 'Future'];

const DIFFICULTIES = [
    {
        value: 'easy',
        label: 'Easy',
        icon: '🟢',
        desc: '4 options + type',
    },
    {
        value: 'medium',
        label: 'Medium',
        icon: '🟡',
        desc: '4 options only',
    },
    {
        value: 'hard',
        label: 'Hard',
        icon: '🔴',
        desc: 'Type only',
    },
];

export default {
    name: 'VerbGame',

    data() {
        return {
            ALL_TENSES,
            DIFFICULTIES,
            phase: 'setup',         // 'setup' | 'playing' | 'results'
            // setup
            customVerb: '',
            questionCount: 10,
            selectedTenses: [...ALL_TENSES],  // all tenses selected by default
            difficulty: 'easy',              // 'easy' | 'medium' | 'hard'
            useWordBank: false,
            wordBankVerbs: null,   // null = not loaded yet / not authenticated
            stats: null,
            setupError: null,

            // playing
            questions: [],          // pre-fetched + future questions
            currentIndex: 0,
            currentQuestion: null,
            currentOptions: [],
            typedAnswer: '',
            answered: false,
            lastWasCorrect: false,
            lastUserAnswer: '',
            isLoadingQuestion: false,
            questionError: null,
            answers: [],            // accumulated answer records

            // results
            finalScore: 0,
            finalAccuracy: 0,
            isSaving: false,
            saveError: null,
        };
    },

    computed: {
        correctSoFar() {
            return this.answers.filter(a => a.is_correct).length;
        },
        scoreClass() {
            if (this.finalAccuracy >= 80) return 'score-high';
            if (this.finalAccuracy >= 50) return 'score-mid';
            return 'score-low';
        },
        highlightedSentence() {
            if (!this.currentQuestion) return '';
            return this.currentQuestion.sentence.replace(
                '___',
                '<span class="blank">___</span>'
            );
        },
    },

    methods: {
        // ── Setup ──────────────────────────────────────────────────────────
        onCustomVerbInput() {
            if (this.customVerb) this.useWordBank = false;
        },

        toggleWordBank() {
            this.useWordBank = !this.useWordBank;
            if (this.useWordBank) this.customVerb = '';
        },

        async fetchStats() {
            try {
                const { data } = await authAxios.get('/api/verb-game/stats');
                this.stats = data;
            } catch {
                // Stats are optional, don't block setup
            }
        },

        async fetchWordBankVerbs() {
            try {
                const { data } = await authAxios.get('/api/verb-game/word-bank-verbs');
                this.wordBankVerbs = data;
            } catch {
                // Not authenticated or unavailable — keep null to hide the toggle
                this.wordBankVerbs = null;
            }
        },

        async startGame() {
            if (this.selectedTenses.length === 0) {
                this.setupError = 'Please select at least one tense.';
                return;
            }
            this.setupError = null;
            this.answers = [];
            this.currentIndex = 0;
            this.phase = 'playing';
            await this.loadNextQuestion();
        },

        // ── Playing ────────────────────────────────────────────────────────
        async loadNextQuestion() {
            this.isLoadingQuestion = true;
            this.questionError = null;
            this.currentQuestion = null;
            this.typedAnswer = '';
            this.answered = false;

            try {
                const verb = (!this.useWordBank && this.customVerb.trim().toLowerCase()) || null;
                const payload = {
                    verb,
                    tenses: this.selectedTenses.length < ALL_TENSES.length ? this.selectedTenses : null,
                    use_word_bank: this.useWordBank,
                };
                const { data } = await authAxios.post('/api/verb-game/question', payload);
                this.currentQuestion = data;
                this.currentOptions = this.buildOptions(data);
                this.$nextTick(() => this.$refs.answerInput?.focus());
            } catch (err) {
                this.questionError = err.response?.data?.detail || 'Failed to load question. Please retry.';
            } finally {
                this.isLoadingQuestion = false;
            }
        },

        buildOptions(q) {
            // Shuffle correct answer + distractors into 4 options
            const all = [q.correct_answer, ...(q.distractors || []).slice(0, 3)];
            for (let i = all.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [all[i], all[j]] = [all[j], all[i]];
            }
            return all;
        },

        selectOption(opt) {
            this.typedAnswer = opt;
            this.submitAnswer(opt);
        },

        submitTyped() {
            if (!this.typedAnswer.trim()) return;
            this.submitAnswer(this.typedAnswer.trim());
        },

        submitAnswer(userAnswer) {
            if (this.answered) return;
            const correct = (this.currentQuestion.correct_answer || '').toLowerCase();
            const given = (userAnswer || '').toLowerCase().trim();
            const isCorrect = given === correct;

            this.lastWasCorrect = isCorrect;
            this.lastUserAnswer = userAnswer;
            this.answered = true;

            this.answers.push({
                verb_infinitive: this.currentQuestion.verb_infinitive,
                sentence: this.currentQuestion.sentence,
                correct_answer: this.currentQuestion.correct_answer,
                user_answer: userAnswer,
                is_correct: isCorrect,
                tense: this.currentQuestion.tense,
                person: this.currentQuestion.person,
                english_hint: this.currentQuestion.english_hint,
            });
        },

        async nextQuestion() {
            if (this.currentIndex + 1 >= this.questionCount) {
                await this.finishGame();
                return;
            }
            this.currentIndex++;
            await this.loadNextQuestion();
        },

        // ── Results ────────────────────────────────────────────────────────
        async finishGame() {
            this.finalScore = this.answers.filter(a => a.is_correct).length;
            this.finalAccuracy = Math.round(this.finalScore / this.answers.length * 100);
            this.phase = 'results';

            this.isSaving = true;
            this.saveError = null;
            try {
                await authAxios.post('/api/verb-game/save', { answers: this.answers });
                await this.fetchStats();
            } catch (err) {
                this.saveError = 'Results could not be saved (they are shown above).';
                console.error(err);
            } finally {
                this.isSaving = false;
            }
        },

        resetToSetup() {
            this.phase = 'setup';
            this.answers = [];
            this.currentIndex = 0;
            this.currentQuestion = null;
            this.typedAnswer = '';
            this.answered = false;
            this.setupError = null;
            this.saveError = null;
        },
    },

    created() {
        this.fetchStats();
        this.fetchWordBankVerbs();
    },
};
</script>

<style scoped>
/* ── Container ──────────────────────────────────────────────────────────── */
.verb-game-container {
    padding: 40px var(--page-padding, 20px);
    max-width: 720px;
    margin: 0 auto;
    min-height: calc(100vh - 60px);
}

/* ── Setup ──────────────────────────────────────────────────────────────── */
.setup-header {
    text-align: center;
    margin-bottom: 36px;
}

.setup-header h2 {
    font-size: 30px;
    color: #333;
    margin-bottom: 8px;
}

.setup-header p {
    color: #666;
    font-size: 16px;
}

.mode-label {
    text-align: center;
    font-size: 15px;
    color: #555;
    margin-bottom: 12px;
    font-weight: 600;
}

/* Mini stats */
.stats-panel {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 28px;
}

.stats-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.stats-panel-header h3 {
    font-size: 17px;
    color: #333;
}

.stats-full-link {
    font-size: 13px;
    color: #667eea;
    text-decoration: none;
    font-weight: 600;
}

.stats-full-link:hover {
    text-decoration: underline;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 16px;
}

.stat-card {
    background: #fff;
    border-radius: 10px;
    padding: 14px 10px;
    text-align: center;
    border: 1px solid #e5e7eb;
}

.stat-number {
    font-size: 24px;
    font-weight: 700;
    color: #667eea;
    line-height: 1.2;
}

.stat-label {
    font-size: 11px;
    color: #888;
    margin-top: 4px;
}

.hardest-verbs h4 {
    font-size: 14px;
    color: #555;
    margin-bottom: 10px;
}

.hv-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.hv-item {
    display: flex;
    justify-content: space-between;
    background: #fff;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 14px;
}

.hv-verb {
    font-weight: 600;
    color: #333;
}

.hv-rate {
    color: #991b1b;
    font-size: 13px;
}

/* Verb input */
.verb-input-section {
    margin-bottom: 24px;
}

.verb-input-row {
    display: flex;
    justify-content: center;
}

.verb-input {
    width: 100%;
    max-width: 400px;
    padding: 12px 16px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font-size: 16px;
    text-align: center;
}

.verb-input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

.verb-input-note {
    text-align: center;
    font-size: 13px;
    color: #9ca3af;
    margin-top: 8px;
}

/* Count picker */
.count-options {
    display: flex;
    gap: 10px;
    justify-content: center;
    margin-bottom: 28px;
}

.count-btn {
    padding: 10px 24px;
    border-radius: 10px;
    border: 2px solid #d1d5db;
    background: #fff;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.2s;
}

.count-btn.active {
    border-color: #667eea;
    background: #667eea;
    color: #fff;
}

.btn-start {
    display: block;
    margin: 0 auto;
    padding: 14px 48px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.1s;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.35);
}

.btn-start:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

.btn-start:disabled {
    opacity: 0.45;
    cursor: not-allowed;
    transform: none;
}

.verb-input:disabled {
    background: #f3f4f6;
    color: #9ca3af;
    cursor: not-allowed;
}

/* Word bank section */
.word-bank-section {
    margin-bottom: 24px;
}

.toggle-row {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    user-select: none;
    margin-bottom: 10px;
}

.toggle-track {
    width: 44px;
    height: 24px;
    background: #d1d5db;
    border-radius: 12px;
    position: relative;
    transition: background 0.2s;
    flex-shrink: 0;
}

.toggle-track.toggle-on {
    background: #667eea;
}

.toggle-thumb {
    position: absolute;
    width: 18px;
    height: 18px;
    background: #fff;
    border-radius: 50%;
    top: 3px;
    left: 3px;
    transition: transform 0.2s;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.toggle-track.toggle-on .toggle-thumb {
    transform: translateX(20px);
}

.toggle-label {
    font-size: 15px;
    color: #374151;
    font-weight: 600;
}

.toggle-count {
    font-weight: 400;
    color: #9ca3af;
    font-size: 13px;
}

.wb-empty {
    font-size: 14px;
    color: #9ca3af;
    padding: 8px 12px;
    background: #f9fafb;
    border-radius: 8px;
}

.wb-empty a {
    color: #667eea;
    font-weight: 600;
    text-decoration: none;
}

.wb-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
}

.wb-chip {
    padding: 4px 12px;
    background: #ede9fe;
    color: #6d28d9;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
}

/* Tense picker */
.tense-section {
    margin-bottom: 24px;
}

.tense-options {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin-bottom: 6px;
}

.tense-chip {
    padding: 8px 18px;
    border-radius: 999px;
    border: 2px solid #d1d5db;
    background: #fff;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    color: #374151;
    transition: all 0.15s;
    user-select: none;
}

.tense-chip.tense-active {
    border-color: #667eea;
    background: #667eea;
    color: #fff;
}

.tense-warning {
    text-align: center;
    font-size: 13px;
    color: #b45309;
    background: #fffbeb;
    border-radius: 8px;
    padding: 6px 12px;
}

/* Difficulty picker */
.difficulty-section {
    margin-bottom: 24px;
}

.difficulty-options {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}

.diff-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 14px 8px;
    border-radius: 12px;
    border: 2px solid #d1d5db;
    background: #fff;
    cursor: pointer;
    transition: all 0.15s;
}

.diff-btn:hover {
    border-color: #667eea;
    background: #f5f3ff;
}

.diff-btn.active {
    border-color: #667eea;
    background: #ede9fe;
}

.diff-icon {
    font-size: 20px;
    line-height: 1;
}

.diff-name {
    font-size: 14px;
    font-weight: 700;
    color: #374151;
}

.diff-desc {
    font-size: 11px;
    color: #9ca3af;
}

/* Difficulty badge in progress bar */
.diff-badge {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 999px;
    text-transform: capitalize;
    background: #f3f4f6;
    color: #6b7280;
}

/* type-only hard mode: stretch input row slightly */
.type-row-hard .answer-input {
    font-size: 18px;
    text-align: center;
}

/* ── Playing ────────────────────────────────────────────────────────────── */
.progress-section {
    margin-bottom: 24px;
}

.progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #555;
    margin-bottom: 6px;
}

.score-inline {
    color: #15803d;
    font-weight: 600;
}

.progress-bar-wrap {
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 3px;
    transition: width 0.4s ease;
}

.question-loading {
    text-align: center;
    padding: 60px 0;
    color: #888;
}

.spinner-large {
    font-size: 36px;
    animation: spin 1s linear infinite;
    display: block;
    margin-bottom: 12px;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}

.spinner {
    display: inline-block;
    animation: spin 1s linear infinite;
}

/* Verb header */
.verb-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.verb-label {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #888;
}

.verb-name {
    font-size: 22px;
    font-weight: 700;
    color: #667eea;
}

.verb-tense-badge,
.verb-person-badge {
    font-size: 12px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 999px;
    background: #f3f4f6;
    color: #374151;
}

.verb-tense-badge {
    background: #ede9fe;
    color: #6d28d9;
}

/* Sentence card */
.sentence-card {
    background: #fff;
    border: 2px solid #e5e7eb;
    border-radius: 16px;
    padding: 28px 24px;
    margin-bottom: 24px;
    text-align: center;
}

.sentence-text {
    font-size: clamp(18px, 4vw, 26px);
    font-weight: 600;
    color: #222;
    line-height: 1.5;
    margin-bottom: 12px;
}

:deep(.blank) {
    display: inline-block;
    min-width: 80px;
    border-bottom: 3px solid #667eea;
    color: #667eea;
    font-style: italic;
}

.sentence-hint {
    font-size: 15px;
    color: #888;
    font-style: italic;
}

/* Options */
.options-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 16px;
}

.option-btn {
    padding: 14px 10px;
    border-radius: 10px;
    border: 2px solid #d1d5db;
    background: #fff;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
    color: #374151;
}

.option-btn:hover {
    border-color: #667eea;
    background: #f0f3ff;
    color: #667eea;
}

.or-separator {
    text-align: center;
    font-size: 13px;
    color: #9ca3af;
    margin-bottom: 10px;
}

/* Type answer */
.type-row {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.answer-input {
    flex: 1;
    padding: 12px 16px;
    border: 2px solid #d1d5db;
    border-radius: 10px;
    font-size: 16px;
}

.answer-input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

.btn-submit {
    padding: 12px 24px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
    white-space: nowrap;
}

.btn-submit:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

/* Feedback */
.feedback-card {
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 20px;
    text-align: center;
}

.feedback-correct {
    background: #f0fdf4;
    border: 2px solid #4ade80;
}

.feedback-wrong {
    background: #fff5f5;
    border: 2px solid #f87171;
}

.feedback-verdict {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 10px;
    color: inherit;
}

.feedback-correct .feedback-verdict {
    color: #15803d;
}

.feedback-wrong .feedback-verdict {
    color: #b91c1c;
}

.feedback-detail {
    font-size: 16px;
    color: #374151;
    margin-bottom: 6px;
}

.feedback-your {
    font-size: 14px;
    color: #666;
    margin-bottom: 8px;
}

.user-wrong {
    color: #b91c1c;
    font-weight: 600;
}

.feedback-sentence-full {
    font-size: 15px;
    color: #555;
    font-style: italic;
    margin-top: 8px;
}

.btn-next {
    display: block;
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    border-radius: 12px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
}

.btn-next:disabled {
    opacity: 0.45;
    cursor: not-allowed;
}

.error-msg {
    text-align: center;
    color: #b91c1c;
    font-size: 14px;
    margin-top: 12px;
    padding: 10px;
    background: #fff5f5;
    border-radius: 8px;
}

.btn-retry {
    display: inline-block;
    margin-top: 8px;
    padding: 6px 18px;
    background: #fff;
    border: 1px solid #f87171;
    border-radius: 8px;
    color: #b91c1c;
    cursor: pointer;
    font-size: 14px;
}

/* ── Results ────────────────────────────────────────────────────────────── */
.results-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.results-card {
    width: 100%;
    max-width: 660px;
}

.results-card h2 {
    text-align: center;
    font-size: 28px;
    color: #333;
    margin-bottom: 24px;
}

.score-display {
    text-align: center;
    margin-bottom: 32px;
}

.score-circle {
    display: inline-flex;
    align-items: baseline;
    gap: 4px;
    padding: 20px 36px;
    border-radius: 20px;
    margin-bottom: 12px;
}

.score-high {
    background: #f0fdf4;
    border: 3px solid #4ade80;
}

.score-mid {
    background: #fffbeb;
    border: 3px solid #fbbf24;
}

.score-low {
    background: #fff5f5;
    border: 3px solid #f87171;
}

.score-number {
    font-size: 52px;
    font-weight: 700;
    color: #333;
    line-height: 1;
}

.score-total {
    font-size: 22px;
    color: #888;
}

.accuracy-label {
    font-size: 18px;
    color: #555;
    font-weight: 600;
}

.saving-msg {
    font-size: 13px;
    color: #9ca3af;
    margin-top: 8px;
}

/* Answer review */
.answer-review {
    margin-bottom: 28px;
}

.answer-review h3 {
    font-size: 17px;
    color: #333;
    margin-bottom: 14px;
    text-align: center;
}

.review-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.review-item {
    border-radius: 12px;
    padding: 12px 16px;
}

.review-correct {
    background: #f0fdf4;
    border: 1.5px solid #86efac;
}

.review-wrong {
    background: #fff5f5;
    border: 1.5px solid #fca5a5;
}

.review-top {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.review-verb {
    font-weight: 700;
    color: #667eea;
    font-size: 15px;
}

.review-tense {
    font-size: 12px;
    color: #888;
    flex: 1;
}

.review-icon {
    font-size: 16px;
    font-weight: 700;
}

.review-correct .review-icon {
    color: #15803d;
}

.review-wrong .review-icon {
    color: #b91c1c;
}

.review-sentence {
    font-size: 14px;
    color: #374151;
    line-height: 1.4;
}

.review-your {
    font-size: 13px;
    color: #888;
    margin-top: 4px;
}

.review-your span {
    color: #b91c1c;
    font-weight: 600;
}

.review-your strong {
    color: #15803d;
}

/* Result actions */
.results-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
}

.btn-primary {
    display: inline-block;
    padding: 12px 28px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    transition: opacity 0.2s;
}

.btn-primary:hover {
    opacity: 0.88;
}

.btn-secondary {
    display: inline-block;
    padding: 12px 28px;
    background: #fff;
    color: #333;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    text-decoration: none;
    transition: background 0.15s;
}

.btn-secondary:hover {
    background: #f3f4f6;
}

/* ── Mobile tweaks ──────────────────────────────────────────────────────── */
@media (max-width: 600px) {
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .options-grid {
        grid-template-columns: 1fr;
    }

    .count-options {
        flex-wrap: wrap;
    }

    .type-row {
        flex-direction: column;
    }

    .difficulty-options {
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
    }

    .diff-btn {
        padding: 10px 4px;
    }

    .diff-desc {
        display: none;
    }
}
</style>
