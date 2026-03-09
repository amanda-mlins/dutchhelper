<template>
    <div class="flashcards-container">

        <!-- ══════════════════════════════════════════════════════════════ -->
        <!-- SCREEN 1 · Setup                                              -->
        <!-- ══════════════════════════════════════════════════════════════ -->
        <div v-if="screen === 'setup'" class="setup-screen">
            <header class="page-header">
                <h2>🃏 Flashcards</h2>
                <p>Flip through your words — Dutch on the front, translation &amp; example on the back.</p>
            </header>

            <div v-if="isLoading" class="loading-indicator">Loading your words…</div>
            <div v-else-if="loadError" class="error-message">{{ loadError }}</div>

            <template v-else-if="allWords.length === 0">
                <div class="empty-state">
                    <p>Your word bank is empty.</p>
                    <router-link to="/word-bank" class="btn-primary">Go add some words →</router-link>
                </div>
            </template>

            <template v-else>
                <!-- Mode tabs -->
                <div class="mode-tabs">
                    <button :class="['mode-tab', { active: setupMode === 'all' }]" @click="setupMode = 'all'">
                        All words <span class="count-badge">{{ allWords.length }}</span>
                    </button>
                    <button :class="['mode-tab', { active: setupMode === 'pick' }]" @click="setupMode = 'pick'">
                        Pick words
                    </button>
                </div>

                <!-- Pick-words panel -->
                <div v-if="setupMode === 'pick'" class="pick-panel">
                    <div class="pick-toolbar">
                        <span class="pick-count">{{ pickedIds.size }} / {{ allWords.length }} selected</span>
                        <button class="btn-tool-sm" @click="pickedIds = new Set(allWords.map(w => w.id))">All</button>
                        <button class="btn-tool-sm" @click="pickedIds = new Set()">None</button>
                    </div>
                    <div class="pick-list">
                        <label v-for="word in allWords" :key="word.id" class="pick-row"
                            :class="{ picked: pickedIds.has(word.id) }">
                            <input type="checkbox" :checked="pickedIds.has(word.id)" @change="togglePick(word.id)" />
                            <span class="pick-word">{{ word.word }}</span>
                            <span class="pick-type">{{ word.word_type }}</span>
                            <span class="pick-trans">{{ word.details?.translation_en || '—' }}</span>
                        </label>
                    </div>
                </div>

                <!-- Options row -->
                <div class="options-row">
                    <label class="option-label">
                        <input type="checkbox" v-model="shuffle" />
                        Shuffle cards
                    </label>
                </div>

                <div v-if="setupMode === 'pick' && pickedIds.size === 0" class="warning-msg">
                    Select at least one word to start.
                </div>

                <button class="btn-start" :disabled="setupMode === 'pick' && pickedIds.size === 0"
                    @click="startSession">
                    Start session ({{ deckSize }} card{{ deckSize !== 1 ? 's' : '' }})
                </button>
            </template>
        </div>

        <!-- ══════════════════════════════════════════════════════════════ -->
        <!-- SCREEN 2 · Study                                              -->
        <!-- ══════════════════════════════════════════════════════════════ -->
        <div v-else-if="screen === 'study'" class="study-screen" @keydown="onKey" tabindex="0" ref="studyEl">

            <!-- Progress bar -->
            <div class="progress-wrap">
                <div class="progress-bar" :style="{ width: progressPct + '%' }"></div>
            </div>
            <div class="progress-label">{{ currentIndex + 1 }} / {{ deck.length }}</div>

            <!-- Card -->
            <div class="card-scene" @click="flip">
                <div class="card-inner" :class="{ flipped: isFlipped }">
                    <!-- Front -->
                    <div class="card-face card-front">
                        <span class="card-side-label">Dutch</span>
                        <p class="card-word">{{ currentCard.word }}</p>
                        <span class="card-type-badge">{{ currentCard.word_type }}</span>
                        <p class="card-hint">Click to reveal →</p>
                    </div>
                    <!-- Back -->
                    <div class="card-face card-back">
                        <span class="card-side-label">Translation &amp; Example</span>
                        <p class="card-translation">{{ currentCard.details?.translation_en || '—' }}</p>
                        <p v-if="currentCard.details?.definition" class="card-definition">
                            {{ currentCard.details.definition }}
                        </p>
                        <p v-if="currentCard.details?.example" class="card-example">
                            "{{ currentCard.details.example }}"
                        </p>
                    </div>
                </div>
            </div>

            <!-- Self-rating buttons (shown after flip) -->
            <div class="rating-row" :class="{ visible: isFlipped }">
                <button class="btn-rating btn-wrong" @click="rate(false)" title="Didn't know it">
                    ✗ Still learning
                </button>
                <button class="btn-rating btn-correct" @click="rate(true)" title="Knew it">
                    ✓ Got it
                </button>
            </div>

            <!-- Navigation row -->
            <div class="nav-row">
                <button class="btn-nav" @click="prev" :disabled="currentIndex === 0">← Prev</button>
                <button class="btn-nav btn-nav-quit" @click="quitSession">Quit</button>
                <button class="btn-nav" @click="next" :disabled="currentIndex === deck.length - 1 && !isFlipped">
                    {{ currentIndex === deck.length - 1 ? 'Finish →' : 'Next →' }}
                </button>
            </div>

            <!-- Keyboard hint -->
            <p class="keyboard-hint">
                <kbd>Space</kbd> flip &nbsp;·&nbsp; <kbd>←</kbd><kbd>→</kbd> navigate &nbsp;·&nbsp;
                <kbd>1</kbd> Still learning &nbsp;·&nbsp; <kbd>2</kbd> Got it
            </p>
        </div>

        <!-- ══════════════════════════════════════════════════════════════ -->
        <!-- SCREEN 3 · Results                                            -->
        <!-- ══════════════════════════════════════════════════════════════ -->
        <div v-else-if="screen === 'results'" class="results-screen">
            <header class="page-header">
                <h2>Session complete 🎉</h2>
                <p>Here's how you did:</p>
            </header>

            <div class="results-summary">
                <div class="result-stat correct">
                    <span class="stat-number">{{ correctCount }}</span>
                    <span class="stat-label">Got it</span>
                </div>
                <div class="result-stat wrong">
                    <span class="stat-number">{{ wrongCount }}</span>
                    <span class="stat-label">Still learning</span>
                </div>
                <div class="result-stat total">
                    <span class="stat-number">{{ ratedCount }}</span>
                    <span class="stat-label">Rated</span>
                </div>
            </div>

            <!-- Words to review again -->
            <div v-if="wrongWords.length" class="review-list">
                <h3>Words to practise more:</h3>
                <div class="review-chips">
                    <span v-for="w in wrongWords" :key="w.id" class="review-chip">
                        {{ w.word }}
                        <span class="review-chip-trans">{{ w.details?.translation_en }}</span>
                    </span>
                </div>
            </div>

            <div class="results-actions">
                <button class="btn-primary" @click="restartSession">🔁 Practise again</button>
                <button class="btn-secondary" @click="practiseWrong" v-if="wrongWords.length">
                    🎯 Practise missed words ({{ wrongWords.length }})
                </button>
                <button class="btn-secondary" @click="screen = 'setup'">⚙️ Change selection</button>
            </div>
        </div>

    </div>
</template>

<script>
import { authAxios } from '../stores/auth.js';

export default {
    name: 'Flashcards',

    data() {
        return {
            // ----- setup -----
            screen: 'setup',         // 'setup' | 'study' | 'results'
            isLoading: false,
            loadError: null,
            allWords: [],
            setupMode: 'all',        // 'all' | 'pick'
            pickedIds: new Set(),
            shuffle: true,

            // ----- study -----
            deck: [],
            currentIndex: 0,
            isFlipped: false,
            ratings: {},             // word.id → true (got it) | false (wrong)

            // ----- results -----
            // computed from ratings at end of session
        };
    },

    computed: {
        deckSize() {
            return this.setupMode === 'all' ? this.allWords.length : this.pickedIds.size;
        },

        currentCard() {
            return this.deck[this.currentIndex] || {};
        },

        progressPct() {
            if (!this.deck.length) return 0;
            return Math.round(((this.currentIndex + 1) / this.deck.length) * 100);
        },

        correctCount() {
            return Object.values(this.ratings).filter(v => v === true).length;
        },
        wrongCount() {
            return Object.values(this.ratings).filter(v => v === false).length;
        },
        ratedCount() {
            return Object.keys(this.ratings).length;
        },
        wrongWords() {
            return this.deck.filter(w => this.ratings[w.id] === false);
        },
    },

    methods: {
        // ── Setup ──────────────────────────────────────────────────────────
        async fetchWords() {
            this.isLoading = true;
            this.loadError = null;
            try {
                const { data } = await authAxios.get('/api/word-bank/words');
                this.allWords = data;
                // Pre-fill pickedIds with everything for convenience
                this.pickedIds = new Set(data.map(w => w.id));
            } catch {
                this.loadError = 'Failed to load your word bank. Please try again.';
            } finally {
                this.isLoading = false;
            }
        },

        togglePick(id) {
            const next = new Set(this.pickedIds);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            this.pickedIds = next;
        },

        buildDeck() {
            const source =
                this.setupMode === 'all'
                    ? [...this.allWords]
                    : this.allWords.filter(w => this.pickedIds.has(w.id));

            if (this.shuffle) {
                for (let i = source.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [source[i], source[j]] = [source[j], source[i]];
                }
            }
            return source;
        },

        startSession() {
            this.deck = this.buildDeck();
            this.currentIndex = 0;
            this.isFlipped = false;
            this.ratings = {};
            this.screen = 'study';
            this.$nextTick(() => this.$refs.studyEl?.focus());
        },

        // ── Study ──────────────────────────────────────────────────────────
        flip() {
            this.isFlipped = !this.isFlipped;
        },

        rate(correct) {
            this.ratings[this.currentCard.id] = correct;
            this.advance();
        },

        advance() {
            if (this.currentIndex < this.deck.length - 1) {
                this.currentIndex++;
                this.isFlipped = false;
            } else {
                // Reached end → go to results
                this.screen = 'results';
            }
        },

        next() {
            if (!this.isFlipped) {
                // Flip first, don't skip
                this.flip();
                return;
            }
            if (this.currentIndex < this.deck.length - 1) {
                this.currentIndex++;
                this.isFlipped = false;
            } else {
                this.screen = 'results';
            }
        },

        prev() {
            if (this.currentIndex > 0) {
                this.currentIndex--;
                this.isFlipped = false;
            }
        },

        quitSession() {
            if (confirm('Quit this session? Your progress will be lost.')) {
                this.screen = 'setup';
            }
        },

        onKey(e) {
            if (e.target.tagName === 'INPUT') return;
            switch (e.key) {
                case ' ':
                case 'Enter':
                    e.preventDefault();
                    this.flip();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.next();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.prev();
                    break;
                case '1':
                    if (this.isFlipped) this.rate(false);
                    break;
                case '2':
                    if (this.isFlipped) this.rate(true);
                    break;
            }
        },

        // ── Results ────────────────────────────────────────────────────────
        restartSession() {
            this.startSession();
        },

        practiseWrong() {
            // Rebuild deck with only the missed words, no shuffle toggle needed
            const missed = this.deck.filter(w => this.ratings[w.id] === false);
            const source = this.shuffle ? [...missed].sort(() => Math.random() - 0.5) : missed;
            this.deck = source;
            this.currentIndex = 0;
            this.isFlipped = false;
            this.ratings = {};
            this.screen = 'study';
            this.$nextTick(() => this.$refs.studyEl?.focus());
        },
    },

    created() {
        this.fetchWords();
    },
};
</script>

<style scoped>
/* ── Layout ─────────────────────────────────────────────────────────────── */
.flashcards-container {
    padding: 40px var(--page-padding, 20px);
    max-width: 780px;
    margin: 0 auto;
    min-height: calc(100vh - 60px);
}

.page-header {
    text-align: center;
    margin-bottom: 36px;
}

.page-header h2 {
    font-size: 32px;
    color: #333;
    margin-bottom: 8px;
}

.page-header p {
    font-size: 17px;
    color: #666;
}

.loading-indicator,
.error-message,
.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #666;
    font-size: 17px;
}

.error-message {
    color: #e74c3c;
}

.empty-state a {
    display: inline-block;
    margin-top: 16px;
}

/* ── Mode tabs ──────────────────────────────────────────────────────────── */
.mode-tabs {
    display: flex;
    gap: 8px;
    justify-content: center;
    margin-bottom: 24px;
}

.mode-tab {
    padding: 10px 24px;
    border-radius: 24px;
    border: 2px solid #d1d5db;
    background: #fff;
    font-size: 15px;
    color: #555;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
}

.mode-tab.active {
    border-color: #667eea;
    background: #667eea;
    color: #fff;
}

.count-badge {
    background: rgba(255, 255, 255, 0.25);
    border-radius: 12px;
    padding: 1px 8px;
    font-size: 13px;
    font-weight: 600;
}

.mode-tab:not(.active) .count-badge {
    background: #f3f4f6;
    color: #555;
}

/* ── Pick list ──────────────────────────────────────────────────────────── */
.pick-panel {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
}

.pick-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    font-size: 14px;
    color: #555;
}

.pick-count {
    flex: 1;
}

.btn-tool-sm {
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid #d1d5db;
    background: #fff;
    font-size: 13px;
    cursor: pointer;
    transition: background 0.15s;
}

.btn-tool-sm:hover {
    background: #f3f4f6;
}

.pick-list {
    max-height: 320px;
    overflow-y: auto;
}

.pick-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    cursor: pointer;
    border-bottom: 1px solid #f3f4f6;
    transition: background 0.15s;
}

.pick-row:last-child {
    border-bottom: none;
}

.pick-row:hover {
    background: #f9fafb;
}

.pick-row.picked {
    background: #f0f3ff;
}

.pick-row input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: #667eea;
    cursor: pointer;
    flex-shrink: 0;
}

.pick-word {
    font-weight: 600;
    color: #333;
    min-width: 100px;
}

.pick-type {
    font-size: 12px;
    color: #888;
    background: #f3f4f6;
    padding: 2px 7px;
    border-radius: 10px;
    white-space: nowrap;
}

.pick-trans {
    color: #555;
    font-size: 14px;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* ── Options & start ────────────────────────────────────────────────────── */
.options-row {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 20px;
}

.option-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    color: #555;
    cursor: pointer;
}

.option-label input {
    accent-color: #667eea;
    width: 16px;
    height: 16px;
}

.warning-msg {
    text-align: center;
    color: #e67e22;
    font-size: 14px;
    margin-bottom: 12px;
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

/* ── Study screen ───────────────────────────────────────────────────────── */
.study-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    outline: none;
}

/* Progress */
.progress-wrap {
    width: 100%;
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 8px;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 3px;
    transition: width 0.4s ease;
}

.progress-label {
    font-size: 13px;
    color: #888;
    margin-bottom: 28px;
    align-self: flex-end;
}

/* Card flip */
.card-scene {
    width: 100%;
    max-width: 560px;
    height: 320px;
    perspective: 1200px;
    cursor: pointer;
    margin-bottom: 28px;
}

.card-inner {
    width: 100%;
    height: 100%;
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.55s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 20px;
}

.card-inner.flipped {
    transform: rotateY(180deg);
}

.card-face {
    position: absolute;
    inset: 0;
    border-radius: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 32px 28px;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    text-align: center;
    gap: 12px;
}

.card-front {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
}

.card-back {
    background: #fff;
    color: #333;
    transform: rotateY(180deg);
    border: 2px solid #e5e7eb;
}

.card-side-label {
    position: absolute;
    top: 16px;
    left: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    opacity: 0.65;
}

.card-word {
    font-size: clamp(26px, 6vw, 44px);
    font-weight: 700;
    line-height: 1.2;
}

.card-type-badge {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 12px;
    padding: 3px 12px;
    font-size: 13px;
    font-weight: 600;
    text-transform: capitalize;
}

.card-hint {
    font-size: 14px;
    opacity: 0.7;
    margin-top: auto;
}

.card-translation {
    font-size: clamp(20px, 4vw, 28px);
    font-weight: 700;
    color: #667eea;
}

.card-definition {
    font-size: 15px;
    color: #555;
    line-height: 1.45;
    max-width: 90%;
}

.card-example {
    font-size: 15px;
    color: #888;
    font-style: italic;
    line-height: 1.45;
    max-width: 90%;
    border-top: 1px solid #f0f0f0;
    padding-top: 10px;
    width: 100%;
}

/* Rating buttons */
.rating-row {
    display: flex;
    gap: 16px;
    margin-bottom: 20px;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s 0.3s;
}

.rating-row.visible {
    opacity: 1;
    pointer-events: auto;
}

.btn-rating {
    padding: 12px 32px;
    border-radius: 10px;
    border: 2px solid transparent;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
}

.btn-rating:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.btn-wrong {
    background: #fff5f5;
    border-color: #f87171;
    color: #b91c1c;
}

.btn-correct {
    background: #f0fdf4;
    border-color: #4ade80;
    color: #15803d;
}

/* Nav row */
.nav-row {
    display: flex;
    gap: 12px;
    align-items: center;
}

.btn-nav {
    padding: 10px 22px;
    border-radius: 8px;
    border: 1px solid #d1d5db;
    background: #fff;
    font-size: 15px;
    cursor: pointer;
    transition: background 0.15s;
}

.btn-nav:hover {
    background: #f3f4f6;
}

.btn-nav:disabled {
    opacity: 0.38;
    cursor: not-allowed;
}

.btn-nav-quit {
    background: #fef2f2;
    border-color: #fca5a5;
    color: #b91c1c;
}

.btn-nav-quit:hover {
    background: #fee2e2;
}

.keyboard-hint {
    margin-top: 20px;
    font-size: 13px;
    color: #aaa;
    text-align: center;
}

kbd {
    display: inline-block;
    padding: 2px 7px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background: #f9fafb;
    font-family: inherit;
    font-size: 12px;
    color: #555;
}

/* ── Results screen ─────────────────────────────────────────────────────── */
.results-screen {
    text-align: center;
}

.results-summary {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin: 0 auto 36px;
    flex-wrap: wrap;
}

.result-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 20px 32px;
    border-radius: 16px;
    min-width: 120px;
}

.result-stat.correct {
    background: #f0fdf4;
    border: 2px solid #4ade80;
}

.result-stat.wrong {
    background: #fff5f5;
    border: 2px solid #f87171;
}

.result-stat.total {
    background: #f0f3ff;
    border: 2px solid #667eea;
}

.stat-number {
    font-size: 42px;
    font-weight: 700;
    line-height: 1;
    color: #333;
}

.stat-label {
    font-size: 14px;
    color: #666;
    font-weight: 500;
}

.review-list {
    margin: 0 auto 32px;
    max-width: 600px;
    text-align: left;
}

.review-list h3 {
    font-size: 17px;
    color: #555;
    margin-bottom: 12px;
    text-align: center;
}

.review-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
}

.review-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #fff5f5;
    border: 1px solid #fca5a5;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 14px;
    font-weight: 600;
    color: #b91c1c;
}

.review-chip-trans {
    font-weight: 400;
    color: #888;
    font-size: 13px;
}

.results-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
}

/* Shared buttons */
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
    .card-scene {
        height: 260px;
    }

    .rating-row {
        gap: 10px;
    }

    .btn-rating {
        padding: 10px 20px;
        font-size: 14px;
    }

    .results-summary {
        gap: 12px;
    }

    .result-stat {
        padding: 16px 20px;
        min-width: 90px;
    }

    .stat-number {
        font-size: 32px;
    }

    .keyboard-hint {
        display: none;
    }
}
</style>
