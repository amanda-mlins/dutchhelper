<template>
    <div class="pv-game-container">

        <!-- ══════════════════════════════════════════════════════════════ -->
        <!-- SETUP PHASE                                                    -->
        <!-- ══════════════════════════════════════════════════════════════ -->
        <div v-if="phase === 'setup'" class="setup-screen">
            <div class="setup-header">
                <h2>🔗 Vaste Voorzetselwerkwoorden</h2>
                <p>Practice Dutch verbs with their fixed prepositions —<br>
                    <em>beginnen <strong>met</strong>, denken <strong>aan</strong>, houden <strong>van</strong>…</em>
                </p>
            </div>

            <!-- Mini stats for returning players -->
            <div v-if="stats && stats.total_games" class="stats-panel">
                <div class="stats-panel-header">
                    <h3>📊 Your Progress</h3>
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
                        <div class="stat-label">Questions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{{ stats.current_streak }}🔥</div>
                        <div class="stat-label">Win streak</div>
                    </div>
                </div>
                <div v-if="stats.hardest_pairs?.length" class="hardest-section">
                    <h4>⚠️ Pairs to work on</h4>
                    <div class="hv-list">
                        <div v-for="hp in stats.hardest_pairs.slice(0, 5)" :key="hp.pair" class="hv-item">
                            <span class="hv-verb">{{ hp.pair }}</span>
                            <span class="hv-rate">{{ hp.times_wrong }}✗ / {{ hp.times_seen }} seen</span>
                        </div>
                    </div>
                </div>
                <div v-if="stats.review_queue_size" class="review-notice">
                    🔁 You have <strong>{{ stats.review_queue_size }}</strong> pair{{
                        stats.review_queue_size !== 1 ? 's' : '' }} queued for review!
                </div>
            </div>

            <!-- Mode selection -->
            <div class="mode-section">
                <p class="section-label">Game mode</p>
                <div class="mode-options">
                    <button v-for="m in MODES" :key="m.value" :class="['mode-btn', { active: mode === m.value }]"
                        @click="mode = m.value">
                        <span class="mode-icon">{{ m.icon }}</span>
                        <span class="mode-name">{{ m.label }}</span>
                        <span class="mode-desc">{{ m.desc }}</span>
                    </button>
                </div>
            </div>

            <!-- Question count -->
            <p class="section-label">How many questions?</p>
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

            <!-- Progress bar -->
            <div class="progress-section">
                <div class="progress-info">
                    <span>{{ currentIndex + 1 }} / {{ questionCount }}</span>
                    <span class="mode-badge">{{ currentMode === 'hard' ? '🔴 Hard' : '🟢 Prep' }}</span>
                    <span class="score-inline">✓ {{ correctSoFar }}</span>
                </div>
                <div class="progress-bar-wrap">
                    <div class="progress-bar" :style="{ width: (currentIndex / questionCount * 100) + '%' }"></div>
                </div>
            </div>

            <!-- Loading -->
            <div v-if="isLoadingQuestion" class="question-loading">
                <div class="spinner-large">⟳</div>
                <p>Generating question…</p>
            </div>

            <template v-else-if="currentQuestion">

                <!-- Pair header -->
                <div class="pair-header">
                    <span class="pair-label">Verb + preposition</span>
                    <span class="pair-badge">
                        {{ currentQuestion.reflexive ? 'zich ' : '' }}{{ currentQuestion.verb }}
                        <strong>_______</strong>
                    </span>
                    <span class="pair-en">{{ currentQuestion.english_translation }}</span>
                    <span v-if="currentQuestion.is_review" class="review-badge">🔁 Review</span>
                </div>

                <!-- Sentence card -->
                <div class="sentence-card">
                    <p class="sentence-text" v-html="formattedSentence"></p>
                    <p class="sentence-hint">{{ currentQuestion.english_hint }}</p>
                </div>

                <!-- ── PREP MODE ─────────────────────────────────────────── -->
                <template v-if="currentMode === 'prep'">
                    <!-- Multiple choice options -->
                    <div v-if="!answered" class="options-grid">
                        <button v-for="opt in currentOptions" :key="opt" class="option-btn" @click="submitPrep(opt)">
                            {{ opt }}
                        </button>
                    </div>
                    <div v-if="!answered" class="or-separator"><span>or type:</span></div>
                    <div v-if="!answered" class="type-row">
                        <input ref="prepInput" v-model="prepAnswer" type="text" class="answer-input"
                            placeholder="Type the preposition…" @keyup.enter="submitPrep(prepAnswer)" />
                        <button class="btn-submit" @click="submitPrep(prepAnswer)" :disabled="!prepAnswer.trim()">Check
                            ✓</button>
                    </div>
                </template>

                <!-- ── HARD MODE ─────────────────────────────────────────── -->
                <template v-else>
                    <div v-if="!answered" class="hard-inputs">
                        <div class="hard-input-group">
                            <label>Conjugated verb</label>
                            <input ref="verbInput" v-model="hardVerb" type="text" class="answer-input"
                                placeholder="e.g. begint, concentreer…" @keyup.enter="$refs.prepHardInput?.focus()" />
                        </div>
                        <div class="hard-input-group">
                            <label>Preposition</label>
                            <input ref="prepHardInput" v-model="hardPrep" type="text" class="answer-input"
                                placeholder="e.g. met, aan, op…" @keyup.enter="submitHard" />
                        </div>
                        <button class="btn-submit" @click="submitHard" :disabled="!hardVerb.trim() || !hardPrep.trim()">
                            Check ✓
                        </button>
                    </div>
                </template>

                <!-- Feedback -->
                <div v-if="answered" class="feedback-card"
                    :class="lastWasCorrect ? 'feedback-correct' : 'feedback-wrong'">
                    <p class="feedback-verdict">
                        {{ lastWasCorrect ? '✓ Correct!' : '✗ Incorrect' }}
                    </p>
                    <template v-if="currentMode === 'prep'">
                        <p class="feedback-detail">
                            Preposition: <strong>{{ currentQuestion.correct_answer }}</strong>
                        </p>
                        <p v-if="!lastWasCorrect" class="feedback-your">
                            Your answer: <span class="user-wrong">{{ lastUserAnswer }}</span>
                        </p>
                        <p class="feedback-sentence-full">
                            {{ resolvedSentence }}
                        </p>
                    </template>
                    <template v-else>
                        <p class="feedback-detail">
                            Correct: <strong>{{ currentQuestion.correct_verb }}</strong>
                            + <strong>{{ currentQuestion.correct_prep }}</strong>
                        </p>
                        <p v-if="!lastWasCorrect" class="feedback-your">
                            Your answer:
                            <span class="user-wrong">{{ lastHardVerb || '(blank)' }}</span>
                            + <span class="user-wrong">{{ lastHardPrep || '(blank)' }}</span>
                        </p>
                        <p class="feedback-sentence-full">
                            {{ resolvedSentence }}
                        </p>
                    </template>
                    <p v-if="currentQuestion.explanation" class="feedback-explanation">
                        💡 {{ currentQuestion.explanation }}
                    </p>
                </div>

                <!-- Next button -->
                <button v-if="answered" class="btn-next" @click="nextQuestion" :disabled="isLoadingQuestion">
                    <span v-if="isLoadingQuestion" class="spinner">⟳</span>
                    <span v-else>{{ currentIndex + 1 >= questionCount ? 'See results →' : 'Next →' }}</span>
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
                    <p v-if="isSaving" class="saving-msg">Saving…</p>
                    <p v-else-if="saveError" class="error-msg">{{ saveError }}</p>
                </div>

                <!-- Answer review -->
                <div class="answer-review">
                    <h3>Answer review</h3>
                    <div class="review-list">
                        <div v-for="(ans, i) in answers" :key="i" class="review-item"
                            :class="ans.is_correct ? 'review-correct' : 'review-wrong'">
                            <div class="review-top">
                                <span class="review-pair">
                                    {{ ans.reflexive ? 'zich ' : '' }}{{ ans.verb }}
                                    <strong>{{ ans.preposition }}</strong>
                                </span>
                                <span class="review-icon">{{ ans.is_correct ? '✓' : '✗' }}</span>
                            </div>
                            <p class="review-sentence-full">
                                {{ resolveAnswerSentence(ans) }}
                            </p>
                            <p v-if="!ans.is_correct" class="review-your">
                                <template v-if="ans.mode === 'prep'">
                                    Your answer: <span>{{ ans.user_answer || '(blank)' }}</span>
                                    → correct: <strong>{{ ans.correct_answer }}</strong>
                                </template>
                                <template v-else>
                                    Your answer: verb=<span>{{ ans.user_verb || '(blank)' }}</span>,
                                    prep=<span>{{ ans.user_prep || '(blank)' }}</span>
                                    → correct: <strong>{{ ans.correct_verb }}</strong> +
                                    <strong>{{ ans.correct_prep }}</strong>
                                </template>
                            </p>
                        </div>
                    </div>
                </div>

                <div class="results-actions">
                    <button class="btn-primary" @click="resetToSetup">🔁 Play again</button>
                </div>
            </div>
        </div>

    </div>
</template>

<script>
import { authAxios } from '../stores/auth.js';

const MODES = [
    {
        value: 'prep',
        label: 'Preposition',
        icon: '🟢',
        desc: 'Fill in the missing preposition',
    },
    {
        value: 'hard',
        label: 'Verb + Prep',
        icon: '🔴',
        desc: 'Type both the conjugated verb AND preposition',
    },
];

export default {
    name: 'PrepVerbGame',

    data() {
        return {
            MODES,
            phase: 'setup',   // 'setup' | 'playing' | 'results'

            // setup
            mode: 'prep',
            questionCount: 10,
            stats: null,
            setupError: null,

            // playing
            currentMode: 'prep',
            currentIndex: 0,
            currentQuestion: null,
            currentOptions: [],
            // prep mode
            prepAnswer: '',
            // hard mode
            hardVerb: '',
            hardPrep: '',
            answered: false,
            lastWasCorrect: false,
            lastUserAnswer: '',
            lastHardVerb: '',
            lastHardPrep: '',
            isLoadingQuestion: false,
            questionError: null,
            answers: [],
            seenPairIds: [],

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
        formattedSentence() {
            if (!this.currentQuestion) return '';
            if (this.currentMode === 'prep') {
                return this.currentQuestion.sentence?.replace(
                    '___',
                    '<span class="blank">___</span>'
                ) || '';
            }
            // hard: two placeholders
            return (this.currentQuestion.sentence || '')
                .replace('___VERB___', '<span class="blank">___</span>')
                .replace('___PREP___', '<span class="blank">___</span>');
        },
        resolvedSentence() {
            if (!this.currentQuestion) return '';
            if (this.currentMode === 'prep') {
                return (this.currentQuestion.sentence || '').replace('___', this.currentQuestion.correct_answer);
            }
            return (this.currentQuestion.sentence || '')
                .replace('___VERB___', this.currentQuestion.correct_verb)
                .replace('___PREP___', this.currentQuestion.correct_prep);
        },
    },

    mounted() {
        this.fetchStats();
    },

    methods: {
        async fetchStats() {
            try {
                const { data } = await authAxios.get('/api/prep-verb-game/stats');
                this.stats = data;
            } catch {
                // optional
            }
        },

        async startGame() {
            this.setupError = null;
            this.answers = [];
            this.currentIndex = 0;
            this.seenPairIds = [];
            this.currentMode = this.mode;
            this.phase = 'playing';
            await this.loadNextQuestion();
        },

        async loadNextQuestion() {
            this.isLoadingQuestion = true;
            this.questionError = null;
            this.currentQuestion = null;
            this.prepAnswer = '';
            this.hardVerb = '';
            this.hardPrep = '';
            this.answered = false;

            try {
                const { data } = await authAxios.post('/api/prep-verb-game/question', {
                    mode: this.currentMode,
                    excluded_pair_ids: this.seenPairIds,
                });
                this.currentQuestion = data;
                if (data.pair_id) {
                    this.seenPairIds = [...this.seenPairIds, data.pair_id];
                }
                if (this.currentMode === 'prep') {
                    this.currentOptions = this.buildOptions(data);
                    this.$nextTick(() => this.$refs.prepInput?.focus());
                } else {
                    this.$nextTick(() => this.$refs.verbInput?.focus());
                }
            } catch (err) {
                this.questionError = err.response?.data?.detail || 'Failed to load question. Please retry.';
            } finally {
                this.isLoadingQuestion = false;
            }
        },

        buildOptions(q) {
            const all = [q.correct_answer, ...(q.distractors || []).slice(0, 3)];
            for (let i = all.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [all[i], all[j]] = [all[j], all[i]];
            }
            return all;
        },

        submitPrep(answer) {
            if (this.answered) return;
            const userAns = (answer || '').trim().toLowerCase();
            const correct = (this.currentQuestion.correct_answer || '').trim().toLowerCase();
            const isCorrect = userAns === correct;
            this.lastWasCorrect = isCorrect;
            this.lastUserAnswer = answer;
            this.answered = true;

            this.answers.push({
                pair_id: this.currentQuestion.pair_id,
                mode: 'prep',
                verb: this.currentQuestion.verb,
                preposition: this.currentQuestion.preposition,
                reflexive: this.currentQuestion.reflexive,
                sentence: this.currentQuestion.sentence,
                correct_answer: this.currentQuestion.correct_answer,
                user_answer: answer,
                is_correct: isCorrect,
                english_hint: this.currentQuestion.english_hint,
            });
        },

        submitHard() {
            if (this.answered) return;
            const userVerb = this.hardVerb.trim().toLowerCase();
            const userPrep = this.hardPrep.trim().toLowerCase();
            const correctVerb = (this.currentQuestion.correct_verb || '').trim().toLowerCase();
            const correctPrep = (this.currentQuestion.correct_prep || '').trim().toLowerCase();
            const isCorrect = userVerb === correctVerb && userPrep === correctPrep;

            this.lastWasCorrect = isCorrect;
            this.lastHardVerb = this.hardVerb;
            this.lastHardPrep = this.hardPrep;
            this.answered = true;

            this.answers.push({
                pair_id: this.currentQuestion.pair_id,
                mode: 'hard',
                verb: this.currentQuestion.verb,
                preposition: this.currentQuestion.preposition,
                reflexive: this.currentQuestion.reflexive,
                sentence: this.currentQuestion.sentence,
                correct_verb: this.currentQuestion.correct_verb,
                correct_prep: this.currentQuestion.correct_prep,
                user_verb: this.hardVerb,
                user_prep: this.hardPrep,
                is_correct: isCorrect,
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

        async finishGame() {
            this.finalScore = this.answers.filter(a => a.is_correct).length;
            this.finalAccuracy = Math.round(this.finalScore / this.answers.length * 100);
            this.phase = 'results';
            await this.saveGame();
        },

        async saveGame() {
            this.isSaving = true;
            this.saveError = null;
            try {
                await authAxios.post('/api/prep-verb-game/save', {
                    mode: this.currentMode,
                    answers: this.answers,
                });
            } catch (err) {
                this.saveError = 'Could not save results.';
            } finally {
                this.isSaving = false;
            }
        },

        resolveAnswerSentence(ans) {
            if (ans.mode === 'prep') {
                return (ans.sentence || '').replace('___', ans.correct_answer);
            }
            return (ans.sentence || '')
                .replace('___VERB___', ans.correct_verb)
                .replace('___PREP___', ans.correct_prep);
        },

        resetToSetup() {
            this.phase = 'setup';
            this.answers = [];
            this.currentIndex = 0;
            this.seenPairIds = [];
            this.currentQuestion = null;
            this.fetchStats();
        },
    },
};
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────────────── */
.pv-game-container {
    max-width: 700px;
    margin: 0 auto;
    padding: 24px 16px 60px;
    font-family: 'Segoe UI', sans-serif;
}

/* ── Setup ──────────────────────────────────────────────────────────────── */
.setup-header {
    text-align: center;
    margin-bottom: 28px;
}

.setup-header h2 {
    font-size: 2rem;
    margin-bottom: 8px;
}

.setup-header p {
    color: #555;
    line-height: 1.5;
}

.section-label {
    font-weight: 600;
    margin: 24px 0 10px;
    color: #333;
}

/* ── Stats panel ─────────────────────────────────────────────────────────── */
.stats-panel {
    background: #f8f9ff;
    border: 1px solid #dde3ff;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 24px;
}

.stats-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.stats-panel-header h3 {
    margin: 0;
    font-size: 1rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 12px;
}

.stat-card {
    background: white;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
    border: 1px solid #e8ebff;
}

.stat-number {
    font-size: 1.4rem;
    font-weight: 700;
    color: #4a5dc7;
}

.stat-label {
    font-size: 0.7rem;
    color: #888;
    margin-top: 2px;
}

.hardest-section {
    margin-top: 12px;
}

.hardest-section h4 {
    margin: 0 0 8px;
    font-size: 0.9rem;
    color: #c04;
}

.hv-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.hv-item {
    display: flex;
    justify-content: space-between;
    padding: 5px 10px;
    background: white;
    border-radius: 6px;
    border: 1px solid #f0d0d0;
    font-size: 0.85rem;
}

.hv-verb {
    font-weight: 600;
}

.hv-rate {
    color: #c04;
}

.review-notice {
    margin-top: 12px;
    background: #fff8e6;
    border: 1px solid #f5c842;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.85rem;
    color: #7a5a00;
}

/* ── Mode buttons ────────────────────────────────────────────────────────── */
.mode-options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 8px;
}

.mode-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 16px 12px;
    border: 2px solid #ddd;
    border-radius: 12px;
    background: white;
    cursor: pointer;
    transition: all 0.15s;
}

.mode-btn:hover {
    border-color: #4a5dc7;
}

.mode-btn.active {
    border-color: #4a5dc7;
    background: #eef0ff;
}

.mode-icon {
    font-size: 1.5rem;
}

.mode-name {
    font-weight: 700;
    font-size: 0.95rem;
}

.mode-desc {
    font-size: 0.75rem;
    color: #777;
    text-align: center;
}

/* ── Count buttons ───────────────────────────────────────────────────────── */
.count-options {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 24px;
}

.count-btn {
    padding: 8px 20px;
    border: 2px solid #ddd;
    border-radius: 8px;
    background: white;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.15s;
}

.count-btn.active,
.count-btn:hover {
    border-color: #4a5dc7;
    background: #eef0ff;
}

/* ── Start button ────────────────────────────────────────────────────────── */
.btn-start {
    width: 100%;
    padding: 14px;
    font-size: 1.1rem;
    font-weight: 700;
    background: linear-gradient(135deg, #4a5dc7, #7c3aed);
    color: white;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    transition: opacity 0.15s;
}

.btn-start:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-start:hover:not(:disabled) {
    opacity: 0.9;
}

/* ── Progress ─────────────────────────────────────────────────────────────── */
.progress-section {
    margin-bottom: 20px;
}

.progress-info {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 6px;
    font-weight: 600;
    color: #555;
}

.mode-badge {
    padding: 2px 10px;
    border-radius: 20px;
    background: #eef0ff;
    color: #4a5dc7;
    font-size: 0.82rem;
}

.score-inline {
    color: #2a9d5c;
}

.progress-bar-wrap {
    height: 6px;
    background: #e0e0e0;
    border-radius: 3px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #4a5dc7, #7c3aed);
    border-radius: 3px;
    transition: width 0.3s;
}

/* ── Question loading ─────────────────────────────────────────────────────── */
.question-loading {
    text-align: center;
    padding: 60px 20px;
    color: #888;
}

.spinner-large {
    font-size: 2.5rem;
    animation: spin 1s linear infinite;
    display: inline-block;
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

/* ── Pair header ──────────────────────────────────────────────────────────── */
.pair-header {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
}

.pair-label {
    font-size: 0.78rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: .05em;
}

.pair-badge {
    background: #eef0ff;
    color: #333;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 1rem;
    font-weight: 600;
}

.pair-badge strong {
    color: #4a5dc7;
}

.pair-en {
    font-size: 0.82rem;
    color: #777;
    font-style: italic;
}

.review-badge {
    background: #fff3cd;
    color: #856404;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.78rem;
}

/* ── Sentence card ─────────────────────────────────────────────────────────── */
.sentence-card {
    background: white;
    border: 1px solid #e0e3f0;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(74, 93, 199, .06);
}

.sentence-text {
    font-size: 1.25rem;
    line-height: 1.6;
    color: #222;
    margin: 0 0 10px;
}

.sentence-hint {
    font-size: 0.9rem;
    color: #777;
    font-style: italic;
    margin: 0;
}

:deep(.blank) {
    display: inline-block;
    min-width: 60px;
    border-bottom: 2px solid #4a5dc7;
    color: #4a5dc7;
    font-weight: 700;
    text-align: center;
    padding: 0 4px;
}

/* ── Options grid ─────────────────────────────────────────────────────────── */
.options-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 12px;
}

.option-btn {
    padding: 12px 16px;
    border: 2px solid #d0d5f0;
    border-radius: 10px;
    background: white;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.12s;
    font-weight: 600;
    color: #333;
}

.option-btn:hover {
    border-color: #4a5dc7;
    background: #eef0ff;
    color: #4a5dc7;
}

/* ── Type row ─────────────────────────────────────────────────────────────── */
.or-separator {
    text-align: center;
    margin: 4px 0;
    font-size: 0.8rem;
    color: #aaa;
}

.type-row {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
}

.answer-input {
    flex: 1;
    padding: 10px 14px;
    border: 2px solid #d0d5f0;
    border-radius: 8px;
    font-size: 1rem;
    outline: none;
    transition: border-color 0.15s;
}

.answer-input:focus {
    border-color: #4a5dc7;
}

/* ── Hard mode inputs ─────────────────────────────────────────────────────── */
.hard-inputs {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 8px;
}

.hard-input-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.hard-input-group label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #555;
}

/* ── Submit button ─────────────────────────────────────────────────────────── */
.btn-submit {
    padding: 10px 20px;
    background: #4a5dc7;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
    transition: opacity 0.15s;
    white-space: nowrap;
}

.btn-submit:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

/* ── Feedback card ─────────────────────────────────────────────────────────── */
.feedback-card {
    border-radius: 12px;
    padding: 18px 20px;
    margin: 16px 0;
}

.feedback-correct {
    background: #e6f9ee;
    border: 1px solid #82d6a4;
}

.feedback-wrong {
    background: #fdecea;
    border: 1px solid #f5a8a0;
}

.feedback-verdict {
    font-size: 1.1rem;
    font-weight: 700;
    margin: 0 0 8px;
}

.feedback-correct .feedback-verdict {
    color: #1a7a40;
}

.feedback-wrong .feedback-verdict {
    color: #c0392b;
}

.feedback-detail {
    margin: 0 0 6px;
    font-size: 0.95rem;
    color: #333;
}

.feedback-your {
    margin: 0 0 6px;
    font-size: 0.9rem;
    color: #555;
}

.user-wrong {
    color: #c0392b;
    font-weight: 600;
}

.feedback-sentence-full {
    font-size: 1rem;
    color: #222;
    background: rgba(255, 255, 255, .6);
    padding: 8px 12px;
    border-radius: 8px;
    margin: 8px 0 6px;
}

.feedback-explanation {
    font-size: 0.88rem;
    color: #444;
    border-top: 1px solid rgba(0, 0, 0, .08);
    padding-top: 8px;
    margin: 8px 0 0;
}

/* ── Next button ───────────────────────────────────────────────────────────── */
.btn-next {
    width: 100%;
    padding: 12px;
    background: #4a5dc7;
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    transition: opacity 0.15s;
}

.btn-next:hover:not(:disabled) {
    opacity: 0.88;
}

.btn-next:disabled {
    opacity: 0.4;
}

/* ── Results ───────────────────────────────────────────────────────────────── */
.results-screen {
    max-width: 600px;
    margin: 0 auto;
}

.results-card {
    background: white;
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, .08);
}

.results-card h2 {
    text-align: center;
    margin-bottom: 24px;
    font-size: 1.8rem;
}

.score-display {
    text-align: center;
    margin-bottom: 28px;
}

.score-circle {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin: 0 auto 10px;
    border: 5px solid;
}

.score-high {
    border-color: #2a9d5c;
    color: #2a9d5c;
}

.score-mid {
    border-color: #e6a817;
    color: #e6a817;
}

.score-low {
    border-color: #e74c3c;
    color: #e74c3c;
}

.score-number {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
}

.score-total {
    font-size: 0.85rem;
}

.accuracy-label {
    font-size: 1.1rem;
    font-weight: 600;
    color: #444;
}

.answer-review h3 {
    margin-bottom: 12px;
    font-size: 1rem;
    color: #555;
}

.review-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.review-item {
    padding: 12px 16px;
    border-radius: 10px;
}

.review-correct {
    background: #e6f9ee;
    border: 1px solid #82d6a4;
}

.review-wrong {
    background: #fdecea;
    border: 1px solid #f5a8a0;
}

.review-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

.review-pair {
    font-weight: 600;
    font-size: 0.95rem;
}

.review-pair strong {
    color: #4a5dc7;
}

.review-icon {
    font-weight: 700;
}

.review-sentence-full {
    font-size: 0.9rem;
    color: #333;
    margin: 4px 0;
}

.review-your {
    font-size: 0.82rem;
    color: #888;
    margin: 2px 0 0;
}

.review-your span {
    font-weight: 600;
    color: #c0392b;
}

.review-your strong {
    color: #333;
}

.results-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    margin-top: 24px;
}

.btn-primary {
    padding: 12px 28px;
    background: linear-gradient(135deg, #4a5dc7, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
}

.btn-secondary {
    padding: 12px 28px;
    border: 2px solid #4a5dc7;
    color: #4a5dc7;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    background: white;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
}

/* ── Misc ─────────────────────────────────────────────────────────────────── */
.error-msg {
    color: #c0392b;
    background: #fdecea;
    border: 1px solid #f5a8a0;
    border-radius: 8px;
    padding: 10px 14px;
    margin-top: 12px;
    font-size: 0.9rem;
}

.btn-retry {
    margin-left: 10px;
    background: #c0392b;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 4px 12px;
    cursor: pointer;
}

.saving-msg {
    color: #888;
    font-style: italic;
}

@media (max-width: 500px) {
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .options-grid {
        grid-template-columns: 1fr 1fr;
    }

    .mode-options {
        grid-template-columns: 1fr;
    }
}
</style>
