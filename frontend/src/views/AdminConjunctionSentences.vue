<template>
    <div class="admin-page">

        <!-- ── Header ─────────────────────────────────────────────────────── -->
        <div class="admin-header">
            <div class="admin-header-left">
                <h1>🔗 Conjunction Sentence Cache</h1>
                <p class="subtitle">{{ sentences.length }} sentence{{ sentences.length !== 1 ? 's' : '' }} in the
                    database</p>
            </div>
        </div>

        <!-- ── Filters ────────────────────────────────────────────────────── -->
        <div class="filters">
            <input v-model="search" placeholder="Search sentence or conjunction…" class="filter-input" />
            <select v-model="filterType" class="filter-select">
                <option value="">All types</option>
                <option value="coordinating">Coordinating</option>
                <option value="subordinating">Subordinating</option>
                <option value="correlative">Correlative</option>
            </select>
            <select v-model="filterSeen" class="filter-select">
                <option value="">All sentences</option>
                <option value="seen">Seen ≥ 1×</option>
                <option value="unseen">Never seen</option>
            </select>
            <select v-model="filterError" class="filter-select">
                <option value="">Any error rate</option>
                <option value="high">High error rate (&gt;50%)</option>
                <option value="low">Low error rate (≤50%)</option>
            </select>
        </div>

        <!-- ── Summary chips ──────────────────────────────────────────────── -->
        <div class="summary-chips">
            <span class="chip chip-total">{{ sentences.length }} total</span>
            <span class="chip chip-seen">{{ seenCount }} seen</span>
            <span class="chip chip-unseen">{{ sentences.length - seenCount }} never seen</span>
            <span class="chip chip-hard">{{ highErrorCount }} high error rate</span>
        </div>

        <!-- ── State messages ─────────────────────────────────────────────── -->
        <div v-if="loading" class="state-msg">Loading sentences…</div>
        <div v-else-if="error" class="state-msg state-error">{{ error }}</div>

        <!-- ── Table ──────────────────────────────────────────────────────── -->
        <div v-else class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th class="col-id">#</th>
                        <th @click="sortBy('conjunction')" class="sortable">
                            Conjunction <span class="sort-arrow">{{ sortIcon('conjunction') }}</span>
                        </th>
                        <th @click="sortBy('conjunction_type')" class="sortable">
                            Type <span class="sort-arrow">{{ sortIcon('conjunction_type') }}</span>
                        </th>
                        <th>Sentence</th>
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
                    <tr v-if="filteredSentences.length === 0">
                        <td colspan="9" class="empty-row">No sentences match your filters.</td>
                    </tr>
                    <template v-for="s in filteredSentences" :key="s.id">
                        <!-- Main row -->
                        <tr :class="{ 'row-expanded': expandedId === s.id }" @click="toggleExpand(s.id)"
                            class="main-row">
                            <td class="col-id muted">{{ s.id }}</td>
                            <td>
                                <span class="conj-pill">{{ s.conjunction }}</span>
                            </td>
                            <td>
                                <span :class="['type-badge', `type-${s.conjunction_type}`]">
                                    {{ s.conjunction_type }}
                                </span>
                            </td>
                            <td class="sentence-cell">
                                <span v-html="highlightBlank(s.sentence)"></span>
                            </td>
                            <td class="col-num">
                                <span v-if="s.times_seen === 0" class="muted">—</span>
                                <span v-else>{{ s.times_seen }}</span>
                            </td>
                            <td class="col-num">
                                <span v-if="s.error_rate === null" class="muted">—</span>
                                <span v-else :class="['error-pill', errorClass(s.error_rate)]">{{ s.error_rate
                                    }}%</span>
                            </td>
                            <td class="col-num">{{ s.unique_users }}</td>
                            <td class="col-date muted">{{ formatDate(s.created_at) }}</td>
                            <td class="col-actions" @click.stop>
                                <button class="btn-icon" title="Edit" @click="openEdit(s)">✏️</button>
                                <button class="btn-icon btn-del" title="Delete" @click="confirmDelete(s)">🗑️</button>
                            </td>
                        </tr>
                        <!-- Expanded detail row -->
                        <tr v-if="expandedId === s.id" class="detail-row">
                            <td colspan="9">
                                <div class="detail-grid">
                                    <div class="detail-section">
                                        <div class="detail-label">Full sentence (filled)</div>
                                        <div class="detail-value sentence-full">
                                            {{ s.sentence.replace('___', s.correct_answer) }}
                                        </div>
                                    </div>
                                    <div class="detail-section">
                                        <div class="detail-label">English hint</div>
                                        <div class="detail-value">{{ s.english_hint || '—' }}</div>
                                    </div>
                                    <div class="detail-section">
                                        <div class="detail-label">Distractors</div>
                                        <div class="detail-value">
                                            <span v-for="d in s.distractors" :key="d" class="distractor-chip">{{ d
                                                }}</span>
                                            <span v-if="!s.distractors.length" class="muted">—</span>
                                        </div>
                                    </div>
                                    <div class="detail-section full-width">
                                        <div class="detail-label">💡 Explanation</div>
                                        <div class="detail-value explanation-text">{{ s.explanation || '—' }}</div>
                                    </div>
                                    <div class="detail-section">
                                        <div class="detail-label">Global stats</div>
                                        <div class="detail-value">
                                            {{ s.times_seen }} seen · {{ s.times_correct }} correct ·
                                            <span v-if="s.error_rate !== null">{{ s.error_rate }}% error rate</span>
                                            <span v-else class="muted">no plays yet</span>
                                        </div>
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
                <h2>✏️ Edit Sentence #{{ editTarget?.id }}</h2>
                <div class="edit-meta">
                    <span class="conj-pill">{{ editTarget?.conjunction }}</span>
                    <span :class="['type-badge', `type-${editTarget?.conjunction_type}`]">{{
                        editTarget?.conjunction_type
                        }}</span>
                </div>
                <form @submit.prevent="saveEdit" class="edit-form">
                    <label>
                        Sentence (must contain ___)
                        <textarea v-model="form.sentence" rows="2" required class="full-input"
                            :class="{ 'input-error': form.sentence && !form.sentence.includes('___') }" />
                        <span v-if="form.sentence && !form.sentence.includes('___')" class="field-error">
                            Must contain ___
                        </span>
                    </label>
                    <label>
                        Correct answer
                        <input v-model="form.correct_answer" required class="full-input" />
                    </label>
                    <label>
                        English hint
                        <input v-model="form.english_hint" class="full-input" placeholder="English translation…" />
                    </label>
                    <label>
                        Distractors (exactly 3, comma-separated)
                        <input v-model="distractorInput" class="full-input" placeholder="maar, want, zodat" />
                        <span v-if="distractorParseError" class="field-error">{{ distractorParseError }}</span>
                    </label>
                    <label>
                        💡 Explanation
                        <textarea v-model="form.explanation" rows="3" class="full-input"
                            placeholder="Why this conjunction is correct and the others aren't…" />
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
                <h2>Delete sentence #{{ deleteTarget.id }}?</h2>
                <p class="delete-warning">
                    This removes the sentence from the cache and all user review-queue entries for it.
                    It <strong>cannot be undone</strong>.
                </p>
                <div class="sentence-preview">
                    {{ deleteTarget.sentence.replace('___', deleteTarget.correct_answer) }}
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
import { ref, computed, onMounted, watch } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

// ── State ──────────────────────────────────────────────────────────────────
const sentences = ref([])
const loading = ref(true)
const error = ref('')

const search = ref('')
const filterType = ref('')
const filterSeen = ref('')
const filterError = ref('')
const sortKey = ref('conjunction')
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
const seenCount = computed(() => sentences.value.filter(s => s.times_seen > 0).length)
const highErrorCount = computed(() => sentences.value.filter(s => s.error_rate !== null && s.error_rate > 50).length)

const distractorParseError = computed(() => {
    if (!distractorInput.value.trim()) return ''
    const parts = distractorInput.value.split(',').map(s => s.trim()).filter(Boolean)
    if (parts.length !== 3) return `Need exactly 3 distractors (got ${parts.length})`
    return ''
})

const filteredSentences = computed(() => {
    let list = sentences.value
    const q = search.value.toLowerCase()
    if (q) {
        list = list.filter(s =>
            s.sentence.toLowerCase().includes(q) ||
            s.conjunction.toLowerCase().includes(q) ||
            (s.english_hint || '').toLowerCase().includes(q)
        )
    }
    if (filterType.value) list = list.filter(s => s.conjunction_type === filterType.value)
    if (filterSeen.value === 'seen') list = list.filter(s => s.times_seen > 0)
    if (filterSeen.value === 'unseen') list = list.filter(s => s.times_seen === 0)
    if (filterError.value === 'high') list = list.filter(s => s.error_rate !== null && s.error_rate > 50)
    if (filterError.value === 'low') list = list.filter(s => s.error_rate !== null && s.error_rate <= 50)

    return [...list].sort((a, b) => {
        let va = a[sortKey.value] ?? ''
        let vb = b[sortKey.value] ?? ''
        // treat null error_rate as -1 so unseen sentences sort to bottom
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
    await fetchSentences()
})

// ── API ────────────────────────────────────────────────────────────────────
async function fetchSentences() {
    loading.value = true
    error.value = ''
    try {
        const ax = auth.getAuthAxios()
        const { data } = await ax.get('/api/admin/conjunction-sentences')
        sentences.value = data
    } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to load sentences.'
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
            sentence: form.value.sentence,
            correct_answer: form.value.correct_answer,
            english_hint: form.value.english_hint || null,
            distractors,
            explanation: form.value.explanation || null,
        }

        const ax = auth.getAuthAxios()
        const { data } = await ax.patch(`/api/admin/conjunction-sentences/${editTarget.value.id}`, payload)

        // Update in-place
        const idx = sentences.value.findIndex(s => s.id === data.id)
        if (idx !== -1) {
            sentences.value[idx] = { ...sentences.value[idx], ...data }
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
        await ax.delete(`/api/admin/conjunction-sentences/${deleteTarget.value.id}`)
        sentences.value = sentences.value.filter(s => s.id !== deleteTarget.value.id)
        if (expandedId.value === deleteTarget.value.id) expandedId.value = null
        deleteTarget.value = null
    } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to delete sentence.'
        deleteTarget.value = null
    } finally {
        saving.value = false
    }
}

// ── UI helpers ─────────────────────────────────────────────────────────────
function defaultForm() {
    return { sentence: '', correct_answer: '', english_hint: '', explanation: '' }
}

function openEdit(s) {
    editTarget.value = s
    form.value = {
        sentence: s.sentence,
        correct_answer: s.correct_answer,
        english_hint: s.english_hint || '',
        explanation: s.explanation || '',
    }
    distractorInput.value = (s.distractors || []).join(', ')
    saveError.value = ''
    showModal.value = true
}

function closeModal() {
    showModal.value = false
    editTarget.value = null
}

function confirmDelete(s) {
    deleteTarget.value = s
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

function highlightBlank(sentence) {
    return sentence.replace(/___/g, '<span class="blank">___</span>')
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
    max-width: 1200px;
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

.chip-hard {
    background: #fce4ec;
    color: #c62828;
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

.col-date {
    width: 100px;
    font-size: 0.82rem;
}

.col-actions {
    width: 80px;
}

/* ── Sentence cell ───────────────────────────────────────────────────────── */
.sentence-cell {
    max-width: 360px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

:deep(.blank) {
    font-weight: 700;
    color: #5c35cc;
    letter-spacing: 1px;
}

/* ── Badges ──────────────────────────────────────────────────────────────── */
.conj-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.88rem;
    background: #e8eaf6;
    color: #3949ab;
}

.type-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
}

.type-coordinating {
    background: #e3f2fd;
    color: #1565c0;
}

.type-subordinating {
    background: #f3e5f5;
    color: #6a1b9a;
}

.type-correlative {
    background: #fff8e1;
    color: #f57f17;
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
    max-width: 420px;
}

.modal-edit {
    max-width: 580px;
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

/* ── Delete modal extras ─────────────────────────────────────────────────── */
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
