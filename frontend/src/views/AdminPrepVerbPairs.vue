<template>
    <div class="admin-page">

        <!-- ── Header ─────────────────────────────────────────────────────── -->
        <div class="admin-header">
            <div class="admin-header-left">
                <h1>🔧 Prep-Verb Pair Cache</h1>
                <p class="subtitle">{{ pairs.length }} pair{{ pairs.length !== 1 ? 's' : '' }} in the database</p>
            </div>
        </div>

        <!-- ── Filters ────────────────────────────────────────────────────── -->
        <div class="filters">
            <input v-model="search" placeholder="Search verb, preposition or translation…" class="filter-input" />
            <select v-model="filterReflexive" class="filter-select">
                <option value="">All verbs</option>
                <option value="yes">Reflexive only</option>
                <option value="no">Non-reflexive only</option>
            </select>
            <select v-model="filterSeen" class="filter-select">
                <option value="">All pairs</option>
                <option value="seen">Seen ≥ 1×</option>
                <option value="unseen">Never seen</option>
            </select>
            <select v-model="filterSentences" class="filter-select">
                <option value="">Any sentence status</option>
                <option value="both">Both modes ready</option>
                <option value="missing">Missing sentences</option>
            </select>
        </div>

        <!-- ── Summary chips ──────────────────────────────────────────────── -->
        <div class="summary-chips">
            <span class="chip chip-total">{{ pairs.length }} total</span>
            <span class="chip chip-seen">{{ seenCount }} seen</span>
            <span class="chip chip-unseen">{{ pairs.length - seenCount }} never seen</span>
            <span class="chip chip-reflexive">{{ reflexiveCount }} reflexive</span>
            <span class="chip chip-hard">{{ highErrorCount }} high error rate</span>
            <span class="chip chip-missing">{{ missingCount }} missing sentences</span>
        </div>

        <!-- ── State messages ─────────────────────────────────────────────── -->
        <div v-if="loading" class="state-msg">Loading pairs…</div>
        <div v-else-if="error" class="state-msg state-error">{{ error }}</div>

        <!-- ── Table ──────────────────────────────────────────────────────── -->
        <div v-else class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th class="col-id">#</th>
                        <th @click="sortBy('verb')" class="sortable">
                            Verb <span class="sort-arrow">{{ sortIcon('verb') }}</span>
                        </th>
                        <th @click="sortBy('preposition')" class="sortable">
                            Prep <span class="sort-arrow">{{ sortIcon('preposition') }}</span>
                        </th>
                        <th>Translation</th>
                        <th class="col-center">Refl.</th>
                        <th class="col-center">Sentences</th>
                        <th @click="sortBy('times_seen')" class="sortable col-num">
                            Seen <span class="sort-arrow">{{ sortIcon('times_seen') }}</span>
                        </th>
                        <th @click="sortBy('error_rate')" class="sortable col-num">
                            Error % <span class="sort-arrow">{{ sortIcon('error_rate') }}</span>
                        </th>
                        <th @click="sortBy('unique_users')" class="sortable col-num">
                            Users <span class="sort-arrow">{{ sortIcon('unique_users') }}</span>
                        </th>
                        <th @click="sortBy('created_at')" class="sortable col-date">
                            Created <span class="sort-arrow">{{ sortIcon('created_at') }}</span>
                        </th>
                        <th class="col-actions">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-if="filteredPairs.length === 0">
                        <td colspan="11" class="empty-row">No pairs match your filters.</td>
                    </tr>
                    <template v-for="p in filteredPairs" :key="p.id">
                        <!-- Main row -->
                        <tr :class="{ 'row-expanded': expandedId === p.id }" @click="toggleExpand(p.id)"
                            class="main-row">
                            <td class="col-id muted">{{ p.id }}</td>
                            <td>
                                <span class="verb-pill">{{ p.verb }}</span>
                            </td>
                            <td>
                                <span class="prep-pill">{{ p.preposition }}</span>
                            </td>
                            <td class="col-translation muted">{{ p.english_translation || '—' }}</td>
                            <td class="col-center">
                                <span v-if="p.reflexive" class="badge-refl" title="Reflexive">zich</span>
                                <span v-else class="muted">—</span>
                            </td>
                            <td class="col-center">
                                <span :class="sentenceStatusClass(p)" :title="sentenceStatusTitle(p)">
                                    {{ sentenceStatusIcon(p) }}
                                </span>
                            </td>
                            <td class="col-num">
                                <span v-if="p.times_seen === 0" class="muted">—</span>
                                <span v-else>{{ p.times_seen }}</span>
                            </td>
                            <td class="col-num">
                                <span v-if="p.error_rate === null" class="muted">—</span>
                                <span v-else :class="['error-pill', errorClass(p.error_rate)]">{{ p.error_rate
                                    }}%</span>
                            </td>
                            <td class="col-num">{{ p.unique_users }}</td>
                            <td class="col-date muted">{{ formatDate(p.created_at) }}</td>
                            <td class="col-actions" @click.stop>
                                <button class="btn-icon" title="Edit" @click="openEdit(p)">✏️</button>
                                <button class="btn-icon btn-del" title="Delete" @click="confirmDelete(p)">🗑️</button>
                            </td>
                        </tr>

                        <!-- Expanded detail row -->
                        <tr v-if="expandedId === p.id" class="detail-row">
                            <td colspan="11">
                                <div class="detail-grid">

                                    <!-- Prep mode -->
                                    <div class="detail-section full-width">
                                        <div class="detail-label">📝 Prep mode — sentence</div>
                                        <div class="detail-value sentence-full" v-if="p.prep_sentence">
                                            <span v-html="highlightBlanks(p.prep_sentence)"></span>
                                        </div>
                                        <div class="detail-value muted" v-else>No sentence generated yet</div>
                                    </div>
                                    <div class="detail-section">
                                        <div class="detail-label">Prep hint (English)</div>
                                        <div class="detail-value">{{ p.prep_english || '—' }}</div>
                                    </div>
                                    <div class="detail-section">
                                        <div class="detail-label">Prep distractors</div>
                                        <div class="detail-value">
                                            <span v-for="d in p.prep_distractors" :key="d" class="distractor-chip">{{ d
                                                }}</span>
                                            <span v-if="!p.prep_distractors.length" class="muted">—</span>
                                        </div>
                                    </div>
                                    <div class="detail-section full-width">
                                        <div class="detail-label">💡 Prep explanation</div>
                                        <div class="detail-value explanation-text">{{ p.prep_explanation || '—' }}</div>
                                    </div>

                                    <!-- Hard mode -->
                                    <div class="detail-section full-width">
                                        <div class="detail-label">🎯 Hard mode — sentence</div>
                                        <div class="detail-value sentence-full" v-if="p.hard_sentence">
                                            <span v-html="highlightBlanks(p.hard_sentence)"></span>
                                            <span class="correct-verb-hint"> (verb: <strong>{{ p.hard_correct_verb
                                                    }}</strong>, prep: <strong>{{ p.preposition }}</strong>)</span>
                                        </div>
                                        <div class="detail-value muted" v-else>No sentence generated yet</div>
                                    </div>
                                    <div class="detail-section">
                                        <div class="detail-label">Hard hint (English)</div>
                                        <div class="detail-value">{{ p.hard_english || '—' }}</div>
                                    </div>
                                    <div class="detail-section">
                                        <div class="detail-label">Global stats</div>
                                        <div class="detail-value">
                                            {{ p.times_seen }} seen · {{ p.times_correct }} correct ·
                                            <span v-if="p.error_rate !== null">{{ p.error_rate }}% error rate</span>
                                            <span v-else class="muted">no plays yet</span>
                                        </div>
                                    </div>
                                    <div class="detail-section full-width">
                                        <div class="detail-label">💡 Hard explanation</div>
                                        <div class="detail-value explanation-text">{{ p.hard_explanation || '—' }}</div>
                                    </div>

                                </div>
                            </td>
                        </tr>
                    </template>
                </tbody>
            </table>
        </div>

        <!-- ── Edit Modal ────────────────────────────────────────────────── -->
        <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
            <div class="modal modal-edit">
                <h2>✏️ Edit Pair #{{ editTarget?.id }}</h2>
                <div class="edit-meta">
                    <span class="verb-pill">{{ editTarget?.verb }}</span>
                    <span class="prep-pill">{{ editTarget?.preposition }}</span>
                    <span v-if="editTarget?.reflexive" class="badge-refl">zich</span>
                </div>

                <form @submit.prevent="saveEdit" class="edit-form">
                    <div class="form-section-title">General</div>
                    <label>
                        English translation
                        <input v-model="form.english_translation" class="full-input"
                            placeholder="e.g. to begin with / start" />
                    </label>

                    <div class="form-section-title">📝 Prep mode</div>
                    <label>
                        Sentence (must contain ___ for the preposition)
                        <textarea v-model="form.prep_sentence" rows="2" class="full-input"
                            :class="{ 'input-error': form.prep_sentence && !form.prep_sentence.includes('___') }" />
                        <span v-if="form.prep_sentence && !form.prep_sentence.includes('___')" class="field-error">
                            Must contain ___
                        </span>
                    </label>
                    <label>
                        English hint
                        <input v-model="form.prep_english" class="full-input"
                            placeholder="English translation of the sentence…" />
                    </label>
                    <label>
                        Distractors (exactly 3, comma-separated)
                        <input v-model="distractorInput" class="full-input" placeholder="van, voor, in" />
                        <span v-if="distractorParseError" class="field-error">{{ distractorParseError }}</span>
                    </label>
                    <label>
                        💡 Explanation
                        <textarea v-model="form.prep_explanation" rows="3" class="full-input"
                            placeholder="Why this preposition is used…" />
                    </label>

                    <div class="form-section-title">🎯 Hard mode</div>
                    <label>
                        Sentence (leave ___ for each blank — verb then prep)
                        <textarea v-model="form.hard_sentence" rows="2" class="full-input" />
                    </label>
                    <label>
                        Correct conjugated verb form
                        <input v-model="form.hard_correct_verb" class="full-input" placeholder="e.g. begint" />
                    </label>
                    <label>
                        English hint
                        <input v-model="form.hard_english" class="full-input"
                            placeholder="English translation of the sentence…" />
                    </label>
                    <label>
                        💡 Explanation
                        <textarea v-model="form.hard_explanation" rows="3" class="full-input"
                            placeholder="Why this verb form and preposition are used…" />
                    </label>

                    <div v-if="saveError" class="form-error">{{ saveError }}</div>
                    <div class="modal-actions">
                        <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
                        <button type="submit" class="btn-primary" :disabled="saving || !!distractorParseError">
                            {{ saving ? 'Saving…' : 'Save Changes' }}
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- ── Delete Confirm Modal ──────────────────────────────────────── -->
        <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
            <div class="modal modal-small">
                <h2>Delete pair #{{ deleteTarget.id }}?</h2>
                <p class="delete-warning">
                    This removes the pair, all generated sentences, and all user review-queue entries for it.
                    It <strong>cannot be undone</strong>.
                </p>
                <div class="sentence-preview">
                    {{ deleteTarget.verb }} + {{ deleteTarget.preposition }}
                    <span class="muted"> — {{ deleteTarget.english_translation }}</span>
                </div>
                <div class="modal-actions">
                    <button class="btn-secondary" @click="deleteTarget = null">Cancel</button>
                    <button class="btn-danger" :disabled="saving" @click="doDelete">
                        {{ saving ? 'Deleting…' : 'Delete' }}
                    </button>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

// ── State ──────────────────────────────────────────────────────────────────
const pairs = ref([])
const loading = ref(true)
const error = ref('')

const search = ref('')
const filterReflexive = ref('')
const filterSeen = ref('')
const filterSentences = ref('')
const sortKey = ref('verb')
const sortDir = ref('asc')

const expandedId = ref(null)

const showModal = ref(false)
const editTarget = ref(null)
const form = ref(defaultForm())
const distractorInput = ref('')
const saveError = ref('')
const saving = ref(false)
const deleteTarget = ref(null)

// ── Computed ───────────────────────────────────────────────────────────────
const seenCount = computed(() => pairs.value.filter(p => p.times_seen > 0).length)
const reflexiveCount = computed(() => pairs.value.filter(p => p.reflexive).length)
const highErrorCount = computed(() => pairs.value.filter(p => p.error_rate !== null && p.error_rate > 50).length)
const missingCount = computed(() => pairs.value.filter(p => !p.prep_sentence || !p.hard_sentence).length)

const distractorParseError = computed(() => {
    if (!distractorInput.value.trim()) return ''
    const parts = distractorInput.value.split(',').map(s => s.trim()).filter(Boolean)
    if (parts.length !== 3) return `Need exactly 3 distractors (got ${parts.length})`
    return ''
})

const filteredPairs = computed(() => {
    let list = pairs.value
    const q = search.value.toLowerCase()
    if (q) {
        list = list.filter(p =>
            p.verb.toLowerCase().includes(q) ||
            p.preposition.toLowerCase().includes(q) ||
            (p.english_translation || '').toLowerCase().includes(q)
        )
    }
    if (filterReflexive.value === 'yes') list = list.filter(p => p.reflexive)
    if (filterReflexive.value === 'no') list = list.filter(p => !p.reflexive)
    if (filterSeen.value === 'seen') list = list.filter(p => p.times_seen > 0)
    if (filterSeen.value === 'unseen') list = list.filter(p => p.times_seen === 0)
    if (filterSentences.value === 'both') list = list.filter(p => p.prep_sentence && p.hard_sentence)
    if (filterSentences.value === 'missing') list = list.filter(p => !p.prep_sentence || !p.hard_sentence)

    return [...list].sort((a, b) => {
        let va = a[sortKey.value] ?? ''
        let vb = b[sortKey.value] ?? ''
        if (sortKey.value === 'error_rate') {
            va = va ?? -1
            vb = vb ?? -1
        }
        if (va < vb) return sortDir.value === 'asc' ? -1 : 1
        if (va > vb) return sortDir.value === 'asc' ? 1 : -1
        return 0
    })
})

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
    if (!auth.user?.is_admin) {
        router.push('/')
        return
    }
    await fetchPairs()
})

// ── API ────────────────────────────────────────────────────────────────────
async function fetchPairs() {
    loading.value = true
    error.value = ''
    try {
        const ax = auth.getAuthAxios()
        const { data } = await ax.get('/api/admin/prep-verb-pairs')
        pairs.value = data
    } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to load pairs.'
    } finally {
        loading.value = false
    }
}

async function saveEdit() {
    saveError.value = ''
    saving.value = true
    try {
        const distractors = distractorInput.value
            .split(',').map(s => s.trim()).filter(Boolean)

        const payload = {
            english_translation: form.value.english_translation || null,
            prep_sentence: form.value.prep_sentence || null,
            prep_english: form.value.prep_english || null,
            prep_distractors: distractors.length === 3 ? distractors : null,
            prep_explanation: form.value.prep_explanation || null,
            hard_sentence: form.value.hard_sentence || null,
            hard_english: form.value.hard_english || null,
            hard_correct_verb: form.value.hard_correct_verb || null,
            hard_explanation: form.value.hard_explanation || null,
        }

        // remove null values so PATCH only updates what's present
        Object.keys(payload).forEach(k => payload[k] === null && delete payload[k])

        const ax = auth.getAuthAxios()
        const { data } = await ax.patch(`/api/admin/prep-verb-pairs/${editTarget.value.id}`, payload)

        const idx = pairs.value.findIndex(p => p.id === data.id)
        if (idx !== -1) {
            pairs.value[idx] = { ...pairs.value[idx], ...data }
        }
        closeModal()
    } catch (e) {
        saveError.value = e.response?.data?.detail || 'Failed to save.'
    } finally {
        saving.value = false
    }
}

async function doDelete() {
    if (!deleteTarget.value) return
    saving.value = true
    try {
        const ax = auth.getAuthAxios()
        await ax.delete(`/api/admin/prep-verb-pairs/${deleteTarget.value.id}`)
        pairs.value = pairs.value.filter(p => p.id !== deleteTarget.value.id)
        if (expandedId.value === deleteTarget.value.id) expandedId.value = null
        deleteTarget.value = null
    } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to delete pair.'
        deleteTarget.value = null
    } finally {
        saving.value = false
    }
}

// ── UI helpers ─────────────────────────────────────────────────────────────
function defaultForm() {
    return {
        english_translation: '',
        prep_sentence: '', prep_english: '', prep_explanation: '',
        hard_sentence: '', hard_english: '', hard_correct_verb: '', hard_explanation: '',
    }
}

function openEdit(p) {
    editTarget.value = p
    form.value = {
        english_translation: p.english_translation || '',
        prep_sentence: p.prep_sentence || '',
        prep_english: p.prep_english || '',
        prep_explanation: p.prep_explanation || '',
        hard_sentence: p.hard_sentence || '',
        hard_english: p.hard_english || '',
        hard_correct_verb: p.hard_correct_verb || '',
        hard_explanation: p.hard_explanation || '',
    }
    distractorInput.value = (p.prep_distractors || []).join(', ')
    saveError.value = ''
    showModal.value = true
}

function closeModal() {
    showModal.value = false
    editTarget.value = null
}

function confirmDelete(p) {
    deleteTarget.value = p
}

function toggleExpand(id) {
    expandedId.value = expandedId.value === id ? null : id
}

function sortBy(key) {
    if (sortKey.value === key) {
        sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
        sortKey.value = key
        sortDir.value = 'asc'
    }
}

function sortIcon(key) {
    if (sortKey.value !== key) return '↕'
    return sortDir.value === 'asc' ? '↑' : '↓'
}

function highlightBlanks(sentence) {
    return sentence.replace(/___/g, '<span class="blank">___</span>')
}

function sentenceStatusIcon(p) {
    if (p.prep_sentence && p.hard_sentence) return '✅'
    if (p.prep_sentence || p.hard_sentence) return '⚠️'
    return '❌'
}

function sentenceStatusTitle(p) {
    if (p.prep_sentence && p.hard_sentence) return 'Both modes ready'
    if (p.prep_sentence) return 'Only prep mode ready'
    if (p.hard_sentence) return 'Only hard mode ready'
    return 'No sentences generated'
}

function sentenceStatusClass(p) {
    if (p.prep_sentence && p.hard_sentence) return 'status-ok'
    if (p.prep_sentence || p.hard_sentence) return 'status-warn'
    return 'status-missing'
}

function errorClass(rate) {
    if (rate === null) return ''
    if (rate > 70) return 'error-high'
    if (rate > 40) return 'error-mid'
    return 'error-low'
}

function formatDate(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.admin-page {
    max-width: 1300px;
    margin: 0 auto;
    padding: 32px 20px 60px;
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.admin-header {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.admin-header-left {
    flex: 1;
}

.admin-header h1 {
    font-size: 1.8rem;
    margin: 0 0 4px;
}

.subtitle {
    color: #888;
    font-size: 0.95rem;
    margin: 0;
}

/* ── Summary chips ───────────────────────────────────────────────────────── */
.summary-chips {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.chip {
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
}

.chip-total {
    background: #e8eaf6;
    color: #3949ab;
}

.chip-seen {
    background: #e8f5e9;
    color: #2e7d32;
}

.chip-unseen {
    background: #f5f5f5;
    color: #757575;
}

.chip-reflexive {
    background: #e3f2fd;
    color: #1565c0;
}

.chip-hard {
    background: #fce4ec;
    color: #c62828;
}

.chip-missing {
    background: #fff3e0;
    color: #e65100;
}

/* ── Filters ─────────────────────────────────────────────────────────────── */
.filters {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 16px;
}

.filter-input {
    flex: 1;
    min-width: 200px;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 0.9rem;
    background: #f8f8f8;
}

.filter-select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 0.9rem;
    background: #f8f8f8;
}

/* ── State ───────────────────────────────────────────────────────────────── */
.state-msg {
    text-align: center;
    padding: 40px;
    color: #888;
    font-size: 1rem;
}

.state-error {
    color: #c62828;
}

/* ── Table ───────────────────────────────────────────────────────────────── */
.table-wrap {
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

thead {
    background: #f5f5f5;
}

th {
    padding: 11px 14px;
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
    color: #666;
    border-bottom: 2px solid #e0e0e0;
}

th.sortable {
    cursor: pointer;
    user-select: none;
}

th.sortable:hover {
    color: #1a7fe8;
}

.sort-arrow {
    font-size: 0.72rem;
    opacity: 0.55;
}

td {
    padding: 9px 14px;
    border-bottom: 1px solid #eee;
    vertical-align: middle;
}

.main-row {
    cursor: pointer;
    transition: background 0.1s;
}

.main-row:hover {
    background: #fafafa;
}

.row-expanded td {
    background: #f0f4ff;
}

.detail-row td {
    background: #f7f9ff;
    padding: 16px 20px;
    border-bottom: 2px solid #dde4ff;
    cursor: default;
}

.empty-row {
    text-align: center;
    color: #aaa;
    padding: 32px;
}

/* ── Column widths ───────────────────────────────────────────────────────── */
.col-id {
    width: 48px;
}

.col-num {
    width: 72px;
    text-align: right;
}

.col-center {
    width: 60px;
    text-align: center;
}

.col-date {
    width: 100px;
    font-size: 0.82rem;
}

.col-actions {
    width: 80px;
}

.col-translation {
    font-size: 0.85rem;
}

/* ── Pills & badges ──────────────────────────────────────────────────────── */
.verb-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.88rem;
    background: #e8eaf6;
    color: #3949ab;
}

.prep-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.88rem;
    background: #e3f2fd;
    color: #1565c0;
}

.badge-refl {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    background: #f3e5f5;
    color: #6a1b9a;
}

.error-pill {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
}

.error-high {
    background: #fce4ec;
    color: #b71c1c;
}

.error-mid {
    background: #fff3e0;
    color: #e65100;
}

.error-low {
    background: #e8f5e9;
    color: #1b5e20;
}

.muted {
    color: #aaa;
}

/* ── Sentence status icons ───────────────────────────────────────────────── */
.status-ok {
    font-size: 1rem;
}

.status-warn {
    font-size: 1rem;
}

.status-missing {
    font-size: 1rem;
}

/* ── Detail row ──────────────────────────────────────────────────────────── */
.detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px 24px;
}

.detail-section.full-width {
    grid-column: 1 / -1;
}

.detail-label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #888;
    margin-bottom: 4px;
}

.detail-value {
    font-size: 0.92rem;
    color: #333;
    line-height: 1.5;
}

.sentence-full {
    font-style: italic;
    color: #444;
}

.correct-verb-hint {
    font-style: normal;
    font-size: 0.82rem;
    color: #888;
    margin-left: 6px;
}

.explanation-text {
    background: #fffbeb;
    border-left: 3px solid #fbbf24;
    padding: 8px 12px;
    border-radius: 4px;
    color: #78350f;
    font-size: 0.88rem;
}

.distractor-chip {
    display: inline-block;
    margin: 2px 4px 2px 0;
    padding: 2px 10px;
    background: #fce4ec;
    color: #880e4f;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
}

:deep(.blank) {
    font-weight: 700;
    color: #5c35cc;
    letter-spacing: 1px;
}

/* ── Actions ─────────────────────────────────────────────────────────────── */
.col-actions {
    white-space: nowrap;
}

.btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    padding: 4px 6px;
    border-radius: 6px;
    transition: background 0.15s;
}

.btn-icon:hover {
    background: #f0f0f0;
}

.btn-icon.btn-del:hover {
    background: #fce4ec;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.btn-primary {
    padding: 9px 20px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
}

.btn-primary:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}

.btn-secondary {
    padding: 9px 20px;
    background: #f0f0f0;
    color: #444;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
}

.btn-danger {
    padding: 9px 20px;
    background: #ef5350;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
}

.btn-danger:disabled {
    opacity: 0.55;
    cursor: not-allowed;
}

/* ── Modals ──────────────────────────────────────────────────────────────── */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 20px;
}

.modal {
    background: #fff;
    border-radius: 16px;
    padding: 28px 32px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal h2 {
    margin: 0 0 12px;
    font-size: 1.3rem;
}

.modal-small {
    max-width: 440px;
}

.modal-edit {
    max-width: 640px;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
}

/* ── Edit form ───────────────────────────────────────────────────────────── */
.edit-meta {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    align-items: center;
}

.form-section-title {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #5c35cc;
    margin: 12px 0 2px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e8e4f8;
}

.edit-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.edit-form label {
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 0.88rem;
    font-weight: 600;
    color: #555;
}

.full-input {
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 0.92rem;
    font-family: inherit;
    box-sizing: border-box;
    resize: vertical;
}

.full-input.input-error {
    border-color: #ef5350;
}

.field-error {
    font-size: 0.8rem;
    color: #ef5350;
    font-weight: 400;
}

.form-error {
    background: #fce4ec;
    color: #c62828;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.9rem;
}

/* ── Delete modal ────────────────────────────────────────────────────────── */
.delete-warning {
    color: #555;
    font-size: 0.93rem;
    margin: 8px 0;
}

.sentence-preview {
    background: #f5f5f5;
    border-radius: 8px;
    padding: 10px 14px;
    font-style: italic;
    color: #444;
    margin: 12px 0;
    font-size: 0.9rem;
}
</style>
