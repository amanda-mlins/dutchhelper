<template>
    <div class="admin-page">
        <div class="admin-header">
            <div class="admin-title">
                <h1>🔤 Verb Conjugation Cache</h1>
                <span class="verb-count" v-if="verbs.length">{{ verbs.length }} verb{{ verbs.length !== 1 ? 's' : ''
                    }}</span>
            </div>
            <div class="admin-actions">
                <button class="btn-secondary" @click="openBulkImport">📂 Import Verbs</button>
                <button class="btn-primary" @click="openAddVerb">+ Add Verb</button>
            </div>
        </div>

        <!-- Filters -->
        <div class="filters">
            <input v-model="filterText" class="filter-input" placeholder="Filter by infinitive or translation…" />
            <select v-model="filterType" class="filter-select">
                <option value="">All types</option>
                <option value="regular">Regular</option>
                <option value="irregular">Irregular</option>
                <option value="separable">Separable</option>
                <option value="mixed">Mixed</option>
            </select>
            <button class="btn-ghost" @click="clearFilters">Clear</button>
        </div>

        <!-- Table -->
        <div class="table-wrap">
            <div v-if="loading" class="state-msg">Loading verbs…</div>
            <div v-else-if="loadError" class="state-msg error">{{ loadError }}</div>
            <div v-else-if="filteredVerbs.length === 0" class="state-msg">No verbs found.</div>
            <table v-else class="verbs-table">
                <thead>
                    <tr>
                        <th @click="setSort('infinitive')" class="sortable">
                            Infinitive <span class="sort-arrow">{{ sortArrow('infinitive') }}</span>
                        </th>
                        <th @click="setSort('english_translation')" class="sortable">
                            Translation <span class="sort-arrow">{{ sortArrow('english_translation') }}</span>
                        </th>
                        <th @click="setSort('verb_type')" class="sortable">
                            Type <span class="sort-arrow">{{ sortArrow('verb_type') }}</span>
                        </th>
                        <th @click="setSort('query_count')" class="sortable">
                            Uses <span class="sort-arrow">{{ sortArrow('query_count') }}</span>
                        </th>
                        <th @click="setSort('created_at')" class="sortable">
                            Cached <span class="sort-arrow">{{ sortArrow('created_at') }}</span>
                        </th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="verb in filteredVerbs" :key="verb.id">
                        <td class="col-infinitive">{{ verb.infinitive }}</td>
                        <td class="col-translation">{{ verb.english_translation || '—' }}</td>
                        <td>
                            <span class="type-badge" :class="'type-' + (verb.verb_type || 'unknown')">
                                {{ verb.verb_type || 'unknown' }}
                            </span>
                        </td>
                        <td class="col-count">{{ verb.query_count }}</td>
                        <td class="col-date">{{ fmtDate(verb.created_at) }}</td>
                        <td class="col-actions">
                            <button class="btn-view" @click="viewVerb(verb)" title="View conjugation">👁</button>
                            <button class="btn-refresh" @click="refreshVerb(verb)" :disabled="refreshingId === verb.id"
                                title="Re-fetch from LLM">
                                <span v-if="refreshingId === verb.id" class="ai-spinner">⟳</span>
                                <span v-else>🔄</span>
                            </button>
                            <button class="btn-del" @click="confirmDelete(verb)" title="Delete">🗑</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- ── View / Conjugation modal ─────────────────────────────────── -->
        <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
            <div class="modal modal-view">
                <h2>{{ viewData?.infinitive }} <span class="translation-sub">— {{ viewData?.english_translation
                        }}</span></h2>
                <div class="verb-meta">
                    <span class="type-badge" :class="'type-' + (viewData?.verb_type || 'unknown')">
                        {{ viewData?.verb_type || 'unknown' }}
                    </span>
                    <span class="meta-item">Queried {{ viewData?.query_count }} times</span>
                    <span class="meta-item">Cached {{ fmtDate(viewData?.created_at) }}</span>
                </div>

                <div v-if="parsedConjugation" class="conj-section">
                    <!-- Tenses -->
                    <div v-for="tense in parsedConjugation.tenses" :key="tense.name" class="tense-block">
                        <h3 class="tense-name">{{ tense.name }}</h3>
                        <table class="conj-table">
                            <tr v-for="form in tense.forms" :key="form.person">
                                <td class="conj-person">{{ form.person }}</td>
                                <td class="conj-word">{{ form.conjugation }}</td>
                            </tr>
                        </table>
                    </div>
                    <!-- Examples -->
                    <div v-if="parsedConjugation.examples?.length" class="examples-block">
                        <h3 class="tense-name">Examples</h3>
                        <ul class="examples-list">
                            <li v-for="(ex, i) in parsedConjugation.examples" :key="i">
                                <span class="ex-dutch">{{ ex.dutch }}</span>
                                <span class="ex-english">{{ ex.english }}</span>
                            </li>
                        </ul>
                    </div>
                </div>
                <div v-else class="raw-json">
                    <pre>{{ viewData?.conjugation_data }}</pre>
                </div>

                <div class="modal-actions">
                    <button class="btn-secondary" @click="showViewModal = false">Close</button>
                </div>
            </div>
        </div>

        <!-- ── Add Verb modal ───────────────────────────────────────────── -->
        <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
            <div class="modal modal-add">
                <h2>Add / Fetch Verb</h2>
                <p class="bulk-desc">
                    Enter a Dutch infinitive. The LLM will generate full conjugation data and save it to the cache.
                    If the verb already exists it will be refreshed.
                </p>
                <div class="verb-input-row">
                    <input v-model="newInfinitive" class="verb-input" placeholder="e.g. lopen" @keyup.enter="doAddVerb"
                        :disabled="addLoading" />
                    <button class="btn-ai" @click="doAddVerb" :disabled="addLoading || !newInfinitive.trim()">
                        <span v-if="addLoading" class="ai-spinner">⟳</span>
                        <span v-else>✨</span>
                        {{ addLoading ? 'Fetching…' : 'AI Fill &amp; Save' }}
                    </button>
                </div>
                <div v-if="addError" class="form-error">{{ addError }}</div>
                <div v-if="addSuccess" class="ai-note">
                    <span class="ai-note-icon">✅</span>
                    <span>Saved <strong>{{ addSuccess.infinitive }}</strong> — {{ addSuccess.english_translation
                        }}</span>
                </div>
                <div class="modal-actions">
                    <button class="btn-ghost" @click="closeAddModal">Close</button>
                </div>
            </div>
        </div>

        <!-- ── Delete confirm modal ─────────────────────────────────────── -->
        <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
            <div class="modal modal-small">
                <h2>Delete verb?</h2>
                <p>Remove <strong>{{ deleteTarget?.infinitive }}</strong> from the cache? It can be re-fetched later.
                </p>
                <div class="modal-actions">
                    <button class="btn-ghost" @click="showDeleteModal = false">Cancel</button>
                    <button class="btn-danger" @click="doDelete" :disabled="deleteLoading">
                        {{ deleteLoading ? 'Deleting…' : 'Delete' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- ── Bulk import modal ────────────────────────────────────────── -->
        <div v-if="showBulkModal" class="modal-overlay" @click.self="closeBulkModal">
            <div class="modal modal-bulk">

                <!-- Step 1: input -->
                <template v-if="bulkStep === 'input'">
                    <h2>📂 Bulk Import Verbs</h2>
                    <p class="bulk-desc">
                        Provide a list of Dutch infinitives — one per line, or comma-separated.
                        Verbs already cached are skipped; new ones are fetched from the LLM.
                    </p>

                    <div class="drop-zone" :class="{ 'drop-zone--over': dragging }" @click="$refs.fileInput.click()"
                        @dragover.prevent="dragging = true" @dragleave="dragging = false" @drop.prevent="onFileDrop">
                        <div class="drop-zone-icon">📄</div>
                        <p v-if="!bulkFileName">Drop a <code>.txt</code> or <code>.csv</code> file here, or click to
                            browse</p>
                        <p v-else class="file-name">{{ bulkFileName }}</p>
                    </div>
                    <input ref="fileInput" type="file" accept=".txt,.csv" class="file-input-hidden"
                        @change="onFileSelect" />

                    <div class="bulk-or">— or paste below —</div>

                    <textarea v-model="bulkPasteText" class="bulk-textarea" rows="6"
                        placeholder="lopen&#10;rennen&#10;schrijven, lezen&#10;..." />

                    <div v-if="parsedVerbs.length" class="parsed-preview">
                        <span class="parsed-count">{{ parsedVerbs.length }} verb{{ parsedVerbs.length !== 1 ? 's' : ''
                            }} detected:</span>
                        <div class="parsed-chips">
                            <span v-for="v in parsedVerbs.slice(0, 40)" :key="v" class="chip">{{ v }}</span>
                            <span v-if="parsedVerbs.length > 40" class="chip chip-more">+{{ parsedVerbs.length - 40 }}
                                more</span>
                        </div>
                    </div>

                    <div v-if="bulkInputError" class="form-error">{{ bulkInputError }}</div>

                    <div class="modal-actions">
                        <button class="btn-ghost" @click="closeBulkModal">Cancel</button>
                        <button class="btn-primary" @click="startBulkImport" :disabled="parsedVerbs.length === 0">
                            Import {{ parsedVerbs.length > 0 ? parsedVerbs.length + ' verbs' : '' }}
                        </button>
                    </div>
                </template>

                <!-- Step 2: progress -->
                <template v-else>
                    <h2>📂 Importing Verbs…</h2>

                    <div class="bulk-progress-header">
                        <div class="bulk-progress-bar-wrap">
                            <div class="bulk-progress-bar" :style="{ width: bulkProgressPct + '%' }"></div>
                        </div>
                        <span class="bulk-progress-label">{{ bulkDone }} / {{ bulkTotal }}</span>
                    </div>

                    <div class="bulk-result-table-wrap">
                        <table class="bulk-result-table">
                            <thead>
                                <tr>
                                    <th>Infinitive</th>
                                    <th>Translation</th>
                                    <th>Type</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="r in bulkResults" :key="r.infinitive" :class="'row-' + r.status">
                                    <td>{{ r.infinitive }}</td>
                                    <td>{{ r.english_translation || '—' }}</td>
                                    <td>{{ r.verb_type || '—' }}</td>
                                    <td>
                                        <span :class="'status-' + r.status" :title="r.error || r.reason || ''">
                                            {{ r.status === 'added' ? '✅ added' : r.status === 'skipped' ? '⏭ skipped' :
                                            r.status === 'error' ? '❌ error' : '⏳' }}
                                        </span>
                                    </td>
                                </tr>
                                <tr v-for="v in pendingVerbs" :key="'p-' + v">
                                    <td>{{ v }}</td>
                                    <td>—</td>
                                    <td>—</td>
                                    <td><span class="status-pending">⏳ pending</span></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div v-if="bulkDone === bulkTotal && bulkSummary" class="bulk-summary">
                        <span class="sum-added">✅ {{ bulkSummary.added }} added</span>
                        <span class="sum-skipped">⏭ {{ bulkSummary.skipped }} skipped</span>
                        <span v-if="bulkSummary.errors" class="sum-error">❌ {{ bulkSummary.errors }} errors</span>
                    </div>

                    <div class="modal-actions">
                        <button v-if="bulkDone < bulkTotal" class="btn-ghost" disabled>Please wait…</button>
                        <button v-else class="btn-primary" @click="finishBulk">Done</button>
                    </div>
                </template>

            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()

// ── State ─────────────────────────────────────────────────────────────────
const verbs = ref([])
const loading = ref(true)
const loadError = ref('')

const filterText = ref('')
const filterType = ref('')

const sortKey = ref('query_count')
const sortDir = ref('desc')

// View modal
const showViewModal = ref(false)
const viewData = ref(null)

// Add modal
const showAddModal = ref(false)
const newInfinitive = ref('')
const addLoading = ref(false)
const addError = ref('')
const addSuccess = ref(null)

// Delete modal
const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const deleteLoading = ref(false)

// Refresh in-table
const refreshingId = ref(null)

// Bulk modal
const showBulkModal = ref(false)
const bulkStep = ref('input')
const bulkPasteText = ref('')
const bulkFileName = ref('')
const dragging = ref(false)
const bulkInputError = ref('')
const bulkResults = ref([])
const bulkSummary = ref(null)
const bulkTotal = ref(0)
const bulkDone = ref(0)

// ── Computed ──────────────────────────────────────────────────────────────
const filteredVerbs = computed(() => {
    let list = [...verbs.value]
    const q = filterText.value.trim().toLowerCase()
    if (q) list = list.filter(v => v.infinitive.includes(q) || (v.english_translation || '').toLowerCase().includes(q))
    if (filterType.value) list = list.filter(v => (v.verb_type || '').toLowerCase() === filterType.value)

    list.sort((a, b) => {
        const av = a[sortKey.value] ?? ''
        const bv = b[sortKey.value] ?? ''
        if (av < bv) return sortDir.value === 'asc' ? -1 : 1
        if (av > bv) return sortDir.value === 'asc' ? 1 : -1
        return 0
    })
    return list
})

const parsedConjugation = computed(() => {
    if (!viewData.value?.conjugation_data) return null
    try { return JSON.parse(viewData.value.conjugation_data) } catch { return null }
})

const bulkProgressPct = computed(() =>
    bulkTotal.value > 0 ? Math.round((bulkDone.value / bulkTotal.value) * 100) : 0
)

const parsedVerbs = computed(() => {
    const text = bulkPasteText.value
    if (!text.trim()) return []
    const raw = text.split(/[\n\r,;]+/).map(s => s.trim().toLowerCase()).filter(Boolean)
    return [...new Set(raw)]
})

const pendingVerbs = computed(() => {
    const done = new Set(bulkResults.value.map(r => r.infinitive))
    return parsedVerbs.value.filter(v => !done.has(v)).slice(0, bulkTotal.value - bulkDone.value)
})

// ── Helpers ───────────────────────────────────────────────────────────────
function authAxios() { return auth.getAuthAxios() }

function fmtDate(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

function setSort(key) {
    if (sortKey.value === key) { sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc' }
    else { sortKey.value = key; sortDir.value = 'asc' }
}

function sortArrow(key) {
    if (sortKey.value !== key) return '↕'
    return sortDir.value === 'asc' ? '↑' : '↓'
}

function clearFilters() { filterText.value = ''; filterType.value = '' }

// ── Data loading ──────────────────────────────────────────────────────────
async function loadVerbs() {
    loading.value = true
    loadError.value = ''
    try {
        const ax = authAxios()
        const { data } = await ax.get('/api/admin/verbs')
        verbs.value = data
    } catch (e) {
        loadError.value = e.response?.data?.detail || 'Failed to load verbs'
    } finally {
        loading.value = false
    }
}

// ── View modal ────────────────────────────────────────────────────────────
function viewVerb(verb) { viewData.value = verb; showViewModal.value = true }

// ── Add / Refresh ─────────────────────────────────────────────────────────
function openAddVerb() {
    newInfinitive.value = ''
    addError.value = ''
    addSuccess.value = null
    showAddModal.value = true
}

function closeAddModal() {
    showAddModal.value = false
    if (addSuccess.value) loadVerbs()
}

async function doAddVerb() {
    const inf = newInfinitive.value.trim().toLowerCase()
    if (!inf) return
    addLoading.value = true
    addError.value = ''
    addSuccess.value = null
    try {
        const ax = authAxios()
        const { data } = await ax.post('/api/admin/verbs/lookup', { infinitive: inf })
        addSuccess.value = data
        newInfinitive.value = ''
        // Update in table if already present, else reload
        const idx = verbs.value.findIndex(v => v.id === data.id)
        if (idx >= 0) verbs.value[idx] = data
        else verbs.value.unshift(data)
    } catch (e) {
        addError.value = e.response?.data?.detail || 'LLM fetch failed'
    } finally {
        addLoading.value = false
    }
}

async function refreshVerb(verb) {
    refreshingId.value = verb.id
    try {
        const ax = authAxios()
        const { data } = await ax.post('/api/admin/verbs/lookup', { infinitive: verb.infinitive })
        const idx = verbs.value.findIndex(v => v.id === data.id)
        if (idx >= 0) verbs.value[idx] = data
        // Refresh view modal if open on same verb
        if (showViewModal.value && viewData.value?.id === data.id) viewData.value = data
    } catch (e) {
        alert(`Refresh failed: ${e.response?.data?.detail || e.message}`)
    } finally {
        refreshingId.value = null
    }
}

// ── Delete ────────────────────────────────────────────────────────────────
function confirmDelete(verb) { deleteTarget.value = verb; showDeleteModal.value = true }

async function doDelete() {
    if (!deleteTarget.value) return
    deleteLoading.value = true
    try {
        const ax = authAxios()
        await ax.delete(`/api/admin/verbs/${deleteTarget.value.id}`)
        verbs.value = verbs.value.filter(v => v.id !== deleteTarget.value.id)
        showDeleteModal.value = false
    } catch (e) {
        alert(`Delete failed: ${e.response?.data?.detail || e.message}`)
    } finally {
        deleteLoading.value = false
    }
}

// ── Bulk import ───────────────────────────────────────────────────────────
function openBulkImport() {
    bulkStep.value = 'input'
    bulkPasteText.value = ''
    bulkFileName.value = ''
    dragging.value = false
    bulkInputError.value = ''
    bulkResults.value = []
    bulkSummary.value = null
    bulkTotal.value = 0
    bulkDone.value = 0
    showBulkModal.value = true
}

function closeBulkModal() {
    showBulkModal.value = false
    if (bulkSummary.value?.added > 0) loadVerbs()
}

function finishBulk() {
    closeBulkModal()
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = e => resolve(e.target.result)
        reader.onerror = reject
        reader.readAsText(file)
    })
}

async function onFileSelect(e) {
    const file = e.target.files[0]
    if (!file) return
    bulkFileName.value = file.name
    bulkPasteText.value = await readFileAsText(file)
    e.target.value = ''
}

async function onFileDrop(e) {
    dragging.value = false
    const file = e.dataTransfer.files[0]
    if (!file) return
    bulkFileName.value = file.name
    bulkPasteText.value = await readFileAsText(file)
}

async function startBulkImport() {
    bulkInputError.value = ''
    const list = parsedVerbs.value
    if (!list.length) { bulkInputError.value = 'No verbs detected.'; return }
    if (list.length > 100) { bulkInputError.value = 'Maximum 100 verbs per import.'; return }

    bulkStep.value = 'progress'
    bulkTotal.value = list.length
    bulkDone.value = 0
    bulkResults.value = []
    bulkSummary.value = null

    try {
        const ax = authAxios()
        const { data } = await ax.post('/api/admin/verbs/bulk-import', { infinitives: list })
        bulkResults.value = data.results
        bulkDone.value = data.results.length
        bulkSummary.value = data.summary
    } catch (e) {
        bulkInputError.value = e.response?.data?.detail || 'Import failed'
        bulkStep.value = 'input'
    }
}

// ── Init ──────────────────────────────────────────────────────────────────
onMounted(loadVerbs)
</script>

<style scoped>
.admin-page {
    max-width: 1100px;
    margin: 0 auto;
    padding: 32px 20px;
}

/* ── Header ──────────────────────────────────────────────────────────── */
.admin-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    gap: 12px;
    flex-wrap: wrap;
}

.admin-title {
    display: flex;
    align-items: baseline;
    gap: 12px;
}

.admin-title h1 {
    margin: 0;
    font-size: 1.6rem;
    color: var(--color-text, #222);
}

.verb-count {
    font-size: 0.9rem;
    color: #888;
}

.admin-actions {
    display: flex;
    gap: 10px;
}

/* ── Filters ─────────────────────────────────────────────────────────── */
.filters {
    display: flex;
    gap: 10px;
    margin-bottom: 18px;
    flex-wrap: wrap;
    align-items: center;
}

.filter-input {
    flex: 1;
    min-width: 200px;
    padding: 9px 14px;
    border: 1px solid var(--color-border, #ddd);
    border-radius: 8px;
    font-size: 0.95rem;
}

.filter-select {
    padding: 9px 12px;
    border: 1px solid var(--color-border, #ddd);
    border-radius: 8px;
    font-size: 0.95rem;
    background: var(--color-bg-soft, #f8f8f8);
}

/* ── Table ───────────────────────────────────────────────────────────── */
.table-wrap {
    overflow-x: auto;
    border: 1px solid var(--color-border, #e5e7eb);
    border-radius: 12px;
}

.verbs-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.93rem;
}

.verbs-table thead {
    background: var(--color-bg-soft, #f9fafb);
}

.verbs-table th {
    padding: 12px 14px;
    text-align: left;
    font-weight: 600;
    color: #6b7280;
    border-bottom: 1px solid var(--color-border, #e5e7eb);
    white-space: nowrap;
}

.verbs-table td {
    padding: 11px 14px;
    border-bottom: 1px solid var(--color-border, #f3f4f6);
    vertical-align: middle;
}

.verbs-table tbody tr:last-child td {
    border-bottom: none;
}

.verbs-table tbody tr:hover {
    background: var(--color-bg-soft, #fafafa);
}

.sortable {
    cursor: pointer;
    user-select: none;
}

.sortable:hover {
    color: #374151;
}

.sort-arrow {
    font-size: 0.8em;
    color: #9ca3af;
}

.col-infinitive {
    font-weight: 600;
}

.col-translation {
    color: #6b7280;
}

.col-count {
    text-align: center;
    color: #6b7280;
}

.col-date {
    color: #9ca3af;
    font-size: 0.85rem;
    white-space: nowrap;
}

.col-actions {
    white-space: nowrap;
    display: flex;
    gap: 6px;
    align-items: center;
}

/* ── Verb type badges ────────────────────────────────────────────────── */
.type-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: capitalize;
}

.type-regular {
    background: #d1fae5;
    color: #065f46;
}

.type-irregular {
    background: #fde8d8;
    color: #92400e;
}

.type-separable {
    background: #dbeafe;
    color: #1e40af;
}

.type-mixed {
    background: #ede9fe;
    color: #4c1d95;
}

.type-unknown {
    background: #f3f4f6;
    color: #6b7280;
}

/* ── Action buttons ─────────────────────────────────────────────────── */
.btn-primary {
    padding: 9px 18px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
}

.btn-primary:hover:not(:disabled) {
    opacity: 0.88;
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: default;
}

.btn-secondary {
    padding: 9px 16px;
    background: #fff;
    color: #374151;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s;
}

.btn-secondary:hover {
    background: #f9fafb;
}

.btn-ghost {
    padding: 9px 16px;
    background: transparent;
    color: #6b7280;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 0.9rem;
    cursor: pointer;
}

.btn-ghost:hover {
    background: #f3f4f6;
}

.btn-ghost:disabled {
    opacity: 0.4;
    cursor: default;
}

.btn-danger {
    padding: 9px 18px;
    background: #ef4444;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
}

.btn-danger:disabled {
    opacity: 0.6;
    cursor: default;
}

.btn-danger:hover:not(:disabled) {
    opacity: 0.88;
}

.btn-view,
.btn-refresh,
.btn-del {
    padding: 5px 8px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: #fff;
    cursor: pointer;
    font-size: 0.95rem;
    line-height: 1;
    transition: background 0.1s;
}

.btn-view:hover {
    background: #eff6ff;
}

.btn-refresh:hover {
    background: #f0fdf4;
}

.btn-del:hover {
    background: #fff5f5;
}

.btn-refresh:disabled {
    opacity: 0.4;
    cursor: default;
}

/* ── State messages ──────────────────────────────────────────────────── */
.state-msg {
    padding: 40px;
    text-align: center;
    color: #888;
}

.state-msg.error {
    color: #ef4444;
}

/* ── Modal base ──────────────────────────────────────────────────────── */
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
    background: var(--color-bg, #fff);
    border-radius: 16px;
    padding: 32px;
    width: 100%;
    max-width: 520px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
    max-height: 90vh;
    overflow-y: auto;
}

.modal-small {
    max-width: 380px;
}

.modal h2 {
    margin: 0 0 20px;
    font-size: 1.3rem;
}

.modal p {
    color: #666;
    margin-bottom: 24px;
}

/* ── View modal ──────────────────────────────────────────────────────── */
.modal-view {
    max-width: 700px;
}

.translation-sub {
    font-size: 1rem;
    font-weight: 400;
    color: #6b7280;
}

.verb-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.meta-item {
    font-size: 0.85rem;
    color: #6b7280;
}

.conj-section {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
}

.tense-block {
    flex: 1;
    min-width: 200px;
}

.tense-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #374151;
    margin: 0 0 8px;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 4px;
}

.conj-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
}

.conj-table tr:nth-child(even) {
    background: #f9fafb;
}

.conj-person {
    color: #6b7280;
    padding: 4px 8px 4px 0;
    white-space: nowrap;
}

.conj-word {
    font-weight: 600;
    color: #111827;
    padding: 4px 0;
}

.examples-block {
    width: 100%;
}

.examples-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.examples-list li {
    display: flex;
    flex-direction: column;
    gap: 2px;
    background: #f9fafb;
    border-radius: 8px;
    padding: 8px 12px;
}

.ex-dutch {
    font-weight: 600;
    color: #111827;
    font-size: 0.9rem;
}

.ex-english {
    color: #6b7280;
    font-size: 0.85rem;
}

.raw-json {
    background: #f3f4f6;
    border-radius: 8px;
    padding: 12px;
    overflow-x: auto;
    font-size: 0.78rem;
    max-height: 300px;
    overflow-y: auto;
}

/* ── Add modal ───────────────────────────────────────────────────────── */
.modal-add {
    max-width: 480px;
}

.verb-input-row {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 12px;
}

.verb-input {
    flex: 1;
    padding: 9px 12px;
    border: 1px solid var(--color-border, #ddd);
    border-radius: 8px;
    font-size: 0.95rem;
    background: var(--color-bg-soft, #f8f8f8);
}

.btn-ai {
    display: flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
    padding: 9px 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 0.88rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
}

.btn-ai:hover:not(:disabled) {
    opacity: 0.88;
}

.btn-ai:disabled {
    opacity: 0.45;
    cursor: default;
}

.ai-spinner {
    display: inline-block;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}

.form-error {
    color: #ef4444;
    font-size: 0.88rem;
    background: #fee2e2;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 12px;
}

.ai-note {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 0.85rem;
    color: #1e40af;
    line-height: 1.4;
    margin-bottom: 12px;
}

.ai-note-icon {
    font-size: 1rem;
    flex-shrink: 0;
}

.modal-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 16px;
}

/* ── Bulk import modal ───────────────────────────────────────────────── */
.modal-bulk {
    max-width: 720px;
}

.bulk-desc {
    color: #666;
    font-size: 0.9rem;
    margin-bottom: 16px;
    line-height: 1.5;
}

.bulk-desc code {
    background: #f0f0f0;
    padding: 1px 5px;
    border-radius: 4px;
    font-family: monospace;
}

.bulk-or {
    text-align: center;
    color: #aaa;
    font-size: 0.85rem;
    margin: 12px 0;
}

.drop-zone {
    border: 2px dashed #c4b5fd;
    border-radius: 12px;
    padding: 28px;
    text-align: center;
    cursor: pointer;
    background: #faf5ff;
    transition: border-color 0.2s, background 0.2s;
    margin-bottom: 4px;
}

.drop-zone:hover,
.drop-zone--over {
    border-color: #7c3aed;
    background: #f3e8ff;
}

.drop-zone-icon {
    font-size: 2rem;
    margin-bottom: 8px;
}

.drop-zone p {
    color: #6b7280;
    margin: 0;
    font-size: 0.9rem;
}

.file-name {
    color: #7c3aed !important;
    font-weight: 600;
}

.file-input-hidden {
    display: none;
}

.bulk-textarea {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 0.9rem;
    resize: vertical;
    font-family: monospace;
    background: #f8f8f8;
    box-sizing: border-box;
}

.parsed-preview {
    margin-top: 12px;
}

.parsed-count {
    font-size: 0.85rem;
    font-weight: 600;
    color: #374151;
    display: block;
    margin-bottom: 6px;
}

.parsed-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
}

.chip {
    background: #dbeafe;
    color: #1e40af;
    border-radius: 12px;
    padding: 2px 9px;
    font-size: 0.78rem;
    font-weight: 500;
}

.chip-more {
    background: #e5e7eb;
    color: #6b7280;
}

.bulk-progress-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}

.bulk-progress-bar-wrap {
    flex: 1;
    height: 10px;
    background: #e5e7eb;
    border-radius: 99px;
    overflow: hidden;
}

.bulk-progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    border-radius: 99px;
    transition: width 0.3s;
}

.bulk-progress-label {
    font-size: 0.85rem;
    color: #6b7280;
    white-space: nowrap;
}

.bulk-result-table-wrap {
    max-height: 340px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    margin-bottom: 16px;
}

.bulk-result-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}

.bulk-result-table th {
    padding: 8px 10px;
    background: #f9fafb;
    font-weight: 600;
    color: #6b7280;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
    position: sticky;
    top: 0;
}

.bulk-result-table td {
    padding: 7px 10px;
    border-bottom: 1px solid #f3f4f6;
}

.row-added td {
    background: #f0fdf4;
}

.row-error td {
    background: #fff5f5;
}

.status-pending {
    color: #9ca3af;
}

.status-added {
    color: #16a34a;
    font-weight: 600;
}

.status-skipped {
    color: #6b7280;
}

.status-error {
    color: #dc2626;
    font-weight: 600;
    cursor: help;
}

.bulk-summary {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 16px;
}

.sum-added {
    color: #16a34a;
}

.sum-skipped {
    color: #6b7280;
}

.sum-error {
    color: #dc2626;
}

/* ── Responsive ──────────────────────────────────────────────────────── */
@media (max-width: 600px) {
    .admin-header {
        flex-direction: column;
        align-items: flex-start;
    }

    .filters {
        flex-direction: column;
    }

    .filter-input {
        min-width: unset;
    }

    .modal {
        padding: 24px 18px;
    }

    .modal-bulk {
        max-width: 100%;
    }

    .verb-input-row {
        flex-direction: column;
        align-items: stretch;
    }

    .btn-ai {
        justify-content: center;
    }

    .conj-section {
        flex-direction: column;
    }
}
</style>
