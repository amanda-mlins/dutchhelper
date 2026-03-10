<template>
    <div class="stats-page">

        <!-- ── Header ── -->
        <div class="page-header">
            <router-link to="/verb-game" class="back-link">← Back to game</router-link>
            <h1>✍️ Verb Game — Stats</h1>
            <p class="subtitle">All your games, mistakes and progress in one place.</p>
        </div>

        <!-- ── Loading / error ── -->
        <div v-if="loading" class="loading-state">Loading your stats…</div>
        <div v-else-if="error" class="error-state">{{ error }}</div>

        <template v-else>
            <!-- ══════════════════════════════════════════════
                 SUMMARY CARDS
            ══════════════════════════════════════════════ -->
            <section class="summary-section">
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="sc-value">{{ stats.total_games }}</div>
                        <div class="sc-label">Games played</div>
                    </div>
                    <div class="summary-card accent-green">
                        <div class="sc-value">{{ stats.avg_accuracy }}%</div>
                        <div class="sc-label">Avg accuracy</div>
                    </div>
                    <div class="summary-card accent-blue">
                        <div class="sc-value">{{ stats.questions_answered }}</div>
                        <div class="sc-label">Questions answered</div>
                    </div>
                    <div class="summary-card accent-orange">
                        <div class="sc-value">{{ stats.current_streak }}🔥</div>
                        <div class="sc-label">Win streak</div>
                    </div>
                </div>
            </section>

            <!-- ══════════════════════════════════════════════
                 ACCURACY TREND  (bar chart — last 20 games)
            ══════════════════════════════════════════════ -->
            <section class="section" v-if="history.length">
                <h2 class="section-title">📈 Accuracy trend</h2>
                <div class="trend-chart">
                    <div v-for="(game, i) in trendGames" :key="game.id" class="trend-col"
                        :title="`Game ${history.length - i}: ${game.accuracy}% — ${formatDate(game.played_at)}`">
                        <div class="trend-label-top">{{ game.accuracy }}%</div>
                        <div class="trend-bar-wrap">
                            <div class="trend-bar" :class="accuracyClass(game.accuracy)"
                                :style="{ height: game.accuracy + '%' }"></div>
                        </div>
                        <div class="trend-label-bottom">G{{ history.length - i }}</div>
                    </div>
                </div>
                <div class="trend-legend">
                    <span class="legend-dot poor"></span> &lt;50%
                    <span class="legend-dot ok"></span> 50–79%
                    <span class="legend-dot good"></span> ≥80%
                </div>
            </section>

            <!-- ══════════════════════════════════════════════
                 HARDEST VERBS LEADERBOARD
            ══════════════════════════════════════════════ -->
            <section class="section" v-if="stats.hardest_verbs?.length">
                <h2 class="section-title">⚠️ Hardest verbs</h2>
                <div class="mistakes-table">
                    <div class="mt-header">
                        <span>Verb</span>
                        <span>Wrong / Seen</span>
                        <span>Error rate</span>
                    </div>
                    <div v-for="hv in mistakeLeaderboard" :key="hv.verb" class="mt-row">
                        <span class="mt-word">
                            {{ hv.verb }}
                            <WordBankButton :word="hv.verb" word-type="verb" category="Verb" />
                        </span>
                        <span class="mt-count">{{ hv.times_wrong }} / {{ hv.times_seen }}</span>
                        <span class="mt-bar-cell">
                            <div class="mt-bar-wrap">
                                <div class="mt-bar" :class="errorRateClass(hv.error_rate)"
                                    :style="{ width: hv.error_rate + '%' }"></div>
                            </div>
                            <span class="mt-pct">{{ hv.error_rate }}%</span>
                        </span>
                    </div>
                </div>
            </section>

            <!-- ══════════════════════════════════════════════
                 GAME HISTORY
            ══════════════════════════════════════════════ -->
            <section class="section" v-if="history.length">
                <h2 class="section-title">📋 Game history</h2>
                <div class="history-list">
                    <div v-for="game in history" :key="game.id" class="history-card">
                        <!-- Collapsed header row — always visible -->
                        <button class="history-header" @click="toggleGame(game.id)">
                            <div class="hh-left">
                                <span class="hh-date">{{ formatDate(game.played_at) }}</span>
                                <span class="hh-size">{{ game.question_count }} questions</span>
                            </div>
                            <div class="hh-right">
                                <span class="hh-score">{{ game.score }} / {{ game.question_count }}</span>
                                <span class="hh-accuracy" :class="accuracyClass(game.accuracy)">
                                    {{ game.accuracy }}%
                                </span>
                                <span class="hh-chevron">{{ expandedGames.has(game.id) ? '▲' : '▼' }}</span>
                            </div>
                        </button>

                        <!-- Expanded answer list -->
                        <div v-if="expandedGames.has(game.id)" class="answer-list">
                            <div v-for="ans in game.answers" :key="ans.id" class="answer-row"
                                :class="ans.is_correct ? 'row-correct' : 'row-wrong'">
                                <div class="ans-verb">
                                    <span class="ans-infinitive">{{ ans.verb_infinitive }}</span>
                                    <span class="ans-meta" v-if="ans.tense || ans.person">
                                        {{ [ans.tense, ans.person].filter(Boolean).join(' · ') }}
                                    </span>
                                </div>
                                <div class="ans-sentence">{{ ans.sentence }}</div>
                                <div class="ans-verdict">
                                    <span v-if="ans.is_correct" class="verdict-correct">✓ {{ ans.correct_answer
                                    }}</span>
                                    <span v-else class="verdict-wrong">
                                        ✗ {{ ans.user_answer }}
                                        <span class="verdict-hint">(correct: {{ ans.correct_answer }})</span>
                                    </span>
                                </div>
                                <!-- Word Bank quick-add -->
                                <div class="wb-quick-row">
                                    <span class="wb-quick-label">+ Bank:</span>
                                    <WordBankButton :word="ans.verb_infinitive" word-type="verb" category="Verb"
                                        :context-sentence="ans.sentence" />
                                    <WordBankButton v-for="w in extractWords(ans.sentence)" :key="w" :word="w"
                                        :context-sentence="ans.sentence" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- ── Empty state ── -->
            <div v-if="!history.length" class="empty-state">
                <div class="empty-icon">✍️</div>
                <p>You haven't played any games yet.</p>
                <router-link to="/verb-game" class="play-btn">Play your first game</router-link>
            </div>
        </template>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import WordBankButton from '../components/WordBankButton.vue'

const auth = useAuthStore()

// Dutch stop-words filter
const STOP_WORDS = new Set([
    'de', 'het', 'een', 'in', 'op', 'aan', 'te', 'met', 'van', 'voor', 'door', 'over', 'uit', 'bij',
    'als', 'maar', 'en', 'of', 'dat', 'dit', 'die', 'wat', 'wie', 'hoe', 'waar', 'zijn', 'hebben',
    'worden', 'is', 'was', 'heeft', 'had', 'wordt', 'werd', 'ik', 'jij', 'je', 'hij', 'zij',
    'ze', 'wij', 'we', 'jullie', 'u', 'niet', 'ook', 'er', 'al', 'nog', 'meer', 'dan', 'nu',
    'zo', 'om', 'na', 'tot', 'per', 'af', 'naar', 'toe', 'weg', 'dus', 'toch', 'wel', 'geen',
    'zich', 'mij', 'hem', 'haar', 'ons', 'hen', 'hun', 'mijn', 'jouw', '__', '___',
])

function extractWords(sentence) {
    if (!sentence) return []
    const raw = sentence
        .toLowerCase()
        .replace(/[.,!?;:'"()\[\]{}<>]/g, ' ')
        .split(/\s+/)
        .filter(w => w.length > 2 && !STOP_WORDS.has(w))
    return [...new Set(raw)]
}

const stats = ref(null)
const history = ref([])
const loading = ref(true)
const error = ref(null)
const expandedGames = ref(new Set())

// ── Data fetching ──────────────────────────────────────────────────────────

async function fetchAll() {
    loading.value = true
    error.value = null
    try {
        const ax = auth.getAuthAxios()
        const [statsRes, historyRes] = await Promise.all([
            ax.get('/api/verb-game/stats'),
            ax.get('/api/verb-game/history'),
        ])
        stats.value = statsRes.data
        history.value = historyRes.data
    } catch (e) {
        error.value = e?.response?.data?.detail ?? 'Failed to load stats.'
    } finally {
        loading.value = false
    }
}

onMounted(fetchAll)

// ── Computed ───────────────────────────────────────────────────────────────

/** Last 20 games chronologically (oldest → newest) for the trend chart. */
const trendGames = computed(() =>
    [...history.value].reverse().slice(-20)
)

/** Hardest verbs enriched with a computed error_rate field. */
const mistakeLeaderboard = computed(() =>
    (stats.value?.hardest_verbs ?? []).map(hv => ({
        ...hv,
        error_rate: hv.times_seen > 0
            ? Math.round((hv.times_wrong / hv.times_seen) * 100)
            : 0,
    }))
)

// ── UI helpers ─────────────────────────────────────────────────────────────

function toggleGame(id) {
    const next = new Set(expandedGames.value)
    next.has(id) ? next.delete(id) : next.add(id)
    expandedGames.value = next
}

function formatDate(iso) {
    return new Date(iso).toLocaleDateString('en-GB', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    })
}

function accuracyClass(pct) {
    if (pct >= 80) return 'good'
    if (pct >= 50) return 'ok'
    return 'poor'
}

function errorRateClass(pct) {
    if (pct >= 70) return 'rate-high'
    if (pct >= 40) return 'rate-mid'
    return 'rate-low'
}
</script>

<style scoped>
/* ── Page ──────────────────────────────────────────────────────────────── */
.stats-page {
    max-width: 860px;
    margin: 0 auto;
    padding: 32px 20px 60px;
    font-family: 'Segoe UI', system-ui, sans-serif;
}

.page-header {
    margin-bottom: 32px;
}

.back-link {
    display: inline-block;
    margin-bottom: 12px;
    color: #667eea;
    text-decoration: none;
    font-size: 14px;
    font-weight: 600;
}

.back-link:hover {
    text-decoration: underline;
}

.page-header h1 {
    font-size: 28px;
    color: #1a202c;
    margin: 0 0 6px;
}

.page-header .subtitle {
    color: #718096;
    font-size: 15px;
    margin: 0;
}

/* ── Loading / error ──────────────────────────────────────────────────── */
.loading-state,
.error-state {
    text-align: center;
    padding: 60px 0;
    color: #718096;
    font-size: 16px;
}

.error-state {
    color: #e53e3e;
}

/* ── Section layout ───────────────────────────────────────────────────── */
.section {
    margin-bottom: 40px;
}

.section-title {
    font-size: 18px;
    font-weight: 700;
    color: #2d3748;
    margin: 0 0 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
}

/* ── Summary cards ────────────────────────────────────────────────────── */
.summary-section {
    margin-bottom: 40px;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
}

@media (max-width: 600px) {
    .summary-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

.summary-card {
    background: white;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0, 0, 0, .06);
}

.summary-card.accent-green {
    border-color: #68d391;
    background: #f0fff4;
}

.summary-card.accent-blue {
    border-color: #76e4f7;
    background: #ebfeff;
}

.summary-card.accent-orange {
    border-color: #f6ad55;
    background: #fffaf0;
}

.sc-value {
    font-size: 32px;
    font-weight: 800;
    color: #2d3748;
    line-height: 1.1;
}

.sc-label {
    font-size: 12px;
    color: #718096;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

/* ── Trend chart ──────────────────────────────────────────────────────── */
.trend-chart {
    display: flex;
    align-items: flex-end;
    gap: 6px;
    height: 140px;
    background: #f7fafc;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px 16px 0;
    overflow-x: auto;
}

.trend-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    min-width: 28px;
    max-width: 48px;
    height: 100%;
    cursor: default;
}

.trend-label-top {
    font-size: 9px;
    color: #a0aec0;
    margin-bottom: 4px;
    white-space: nowrap;
}

.trend-bar-wrap {
    flex: 1;
    width: 100%;
    display: flex;
    align-items: flex-end;
}

.trend-bar {
    width: 100%;
    border-radius: 4px 4px 0 0;
    min-height: 4px;
    transition: height 0.3s ease;
}

.trend-bar.good {
    background: #48bb78;
}

.trend-bar.ok {
    background: #ed8936;
}

.trend-bar.poor {
    background: #fc8181;
}

.trend-label-bottom {
    font-size: 9px;
    color: #a0aec0;
    padding: 4px 0 6px;
    white-space: nowrap;
}

.trend-legend {
    display: flex;
    gap: 16px;
    align-items: center;
    margin-top: 8px;
    font-size: 12px;
    color: #718096;
}

.legend-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.legend-dot.good {
    background: #48bb78;
}

.legend-dot.ok {
    background: #ed8936;
}

.legend-dot.poor {
    background: #fc8181;
}

/* ── Hardest verbs table ──────────────────────────────────────────────── */
.mistakes-table {
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    font-size: 14px;
}

.mt-header {
    display: grid;
    grid-template-columns: 2fr 1.4fr 2fr;
    background: #f7fafc;
    padding: 10px 16px;
    font-weight: 700;
    color: #4a5568;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    border-bottom: 1.5px solid #e2e8f0;
}

.mt-row {
    display: grid;
    grid-template-columns: 2fr 1.4fr 2fr;
    padding: 11px 16px;
    align-items: center;
    border-bottom: 1px solid #f0f0f0;
}

.mt-row:last-child {
    border-bottom: none;
}

.mt-row:hover {
    background: #fafafa;
}

.mt-word {
    font-weight: 600;
    color: #2d3748;
}

.mt-count {
    color: #718096;
}

.mt-bar-cell {
    display: flex;
    align-items: center;
    gap: 8px;
}

.mt-bar-wrap {
    flex: 1;
    height: 8px;
    background: #e2e8f0;
    border-radius: 4px;
    overflow: hidden;
}

.mt-bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
}

.mt-bar.rate-high {
    background: #fc8181;
}

.mt-bar.rate-mid {
    background: #ed8936;
}

.mt-bar.rate-low {
    background: #68d391;
}

.mt-pct {
    font-size: 12px;
    color: #718096;
    min-width: 32px;
    text-align: right;
}

/* ── History list ─────────────────────────────────────────────────────── */
.history-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.history-card {
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    background: white;
}

.history-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    padding: 14px 18px;
    background: none;
    border: none;
    cursor: pointer;
    text-align: left;
    gap: 12px;
    transition: background 0.15s;
}

.history-header:hover {
    background: #f7fafc;
}

.hh-left {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.hh-date {
    font-size: 14px;
    font-weight: 600;
    color: #2d3748;
}

.hh-size {
    font-size: 12px;
    color: #718096;
}

.hh-right {
    display: flex;
    align-items: center;
    gap: 10px;
}

.hh-score {
    font-size: 14px;
    color: #4a5568;
}

.hh-accuracy {
    font-size: 15px;
    font-weight: 700;
    min-width: 44px;
    text-align: right;
}

.hh-accuracy.good {
    color: #38a169;
}

.hh-accuracy.ok {
    color: #dd6b20;
}

.hh-accuracy.poor {
    color: #e53e3e;
}

.hh-chevron {
    font-size: 11px;
    color: #a0aec0;
}

/* ── Answer rows ──────────────────────────────────────────────────────── */
.answer-list {
    border-top: 1.5px solid #e2e8f0;
    background: #f9fafb;
}

.answer-row {
    padding: 12px 18px;
    border-bottom: 1px solid #edf2f7;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.answer-row:last-child {
    border-bottom: none;
}

.answer-row.row-correct {
    border-left: 3px solid #68d391;
}

.answer-row.row-wrong {
    border-left: 3px solid #fc8181;
}

.ans-verb {
    display: flex;
    align-items: baseline;
    gap: 8px;
}

.ans-infinitive {
    font-weight: 700;
    color: #2d3748;
    font-size: 14px;
}

.ans-meta {
    font-size: 11px;
    color: #a0aec0;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.ans-sentence {
    font-size: 13px;
    color: #4a5568;
    font-style: italic;
}

.ans-verdict {
    font-size: 13px;
}

.verdict-correct {
    color: #276749;
    font-weight: 600;
}

.verdict-wrong {
    color: #9b2c2c;
    font-weight: 600;
}

.verdict-hint {
    font-weight: 400;
    opacity: 0.8;
    font-size: 12px;
}

/* ── Word Bank quick-add row ──────────────────────────────────────────── */
.wb-quick-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px dashed #e2e8f0;
}

.wb-quick-label {
    font-size: 11px;
    font-weight: 700;
    color: #a0aec0;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    margin-right: 2px;
}

.mt-word {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}

/* ── Empty state ──────────────────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #718096;
}

.empty-icon {
    font-size: 48px;
    margin-bottom: 12px;
}

.empty-state p {
    font-size: 16px;
    margin-bottom: 20px;
}

.play-btn {
    display: inline-block;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 11px 28px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    font-size: 15px;
    transition: opacity 0.2s;
}

.play-btn:hover {
    opacity: 0.88;
}
</style>
