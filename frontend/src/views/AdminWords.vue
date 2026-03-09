<template>
    <div class="admin-page">
        <div class="admin-header">
            <h1>🛠️ Article Word Manager</h1>
            <p class="subtitle">{{ words.length }} words in the database</p>
            <button class="btn-primary" @click="openAdd">+ Add Word</button>
        </div>

        <!-- Filters -->
        <div class="filters">
            <input v-model="search" placeholder="Search word or translation…" class="filter-input" />
            <select v-model="filterArticle" class="filter-select">
                <option value="">All articles</option>
                <option value="de">de</option>
                <option value="het">het</option>
            </select>
            <select v-model="filterDifficulty" class="filter-select">
                <option value="">All difficulties</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
            </select>
            <select v-model="filterActive" class="filter-select">
                <option value="">All status</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
            </select>
        </div>

        <!-- Loading / Error -->
        <div v-if="loading" class="state-msg">Loading words…</div>
        <div v-else-if="error" class="state-msg error">{{ error }}</div>

        <!-- Table -->
        <div v-else class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th @click="sortBy('word')" class="sortable">
                            Word <span class="sort-arrow">{{ sortIcon('word') }}</span>
                        </th>
                        <th @click="sortBy('article')" class="sortable">
                            Article <span class="sort-arrow">{{ sortIcon('article') }}</span>
                        </th>
                        <th>Translation</th>
                        <th @click="sortBy('difficulty')" class="sortable">
                            Difficulty <span class="sort-arrow">{{ sortIcon('difficulty') }}</span>
                        </th>
                        <th>Category</th>
                        <th @click="sortBy('is_active')" class="sortable">
                            Status <span class="sort-arrow">{{ sortIcon('is_active') }}</span>
                        </th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-if="filteredWords.length === 0">
                        <td colspan="7" class="empty-row">No words match your filters.</td>
                    </tr>
                    <tr v-for="w in filteredWords" :key="w.id" :class="{ inactive: !w.is_active }">
                        <td class="word-cell">{{ w.word }}</td>
                        <td>
                            <span :class="['badge', w.article === 'de' ? 'badge-de' : 'badge-het']">
                                {{ w.article }}
                            </span>
                        </td>
                        <td>{{ w.translation || '—' }}</td>
                        <td>
                            <span :class="['badge', `badge-${w.difficulty}`]">{{ w.difficulty }}</span>
                        </td>
                        <td>{{ w.category || '—' }}</td>
                        <td>
                            <span :class="['badge', w.is_active ? 'badge-active' : 'badge-inactive']">
                                {{ w.is_active ? 'Active' : 'Inactive' }}
                            </span>
                        </td>
                        <td class="actions-cell">
                            <button class="btn-icon" title="Edit" @click="openEdit(w)">✏️</button>
                            <button class="btn-icon btn-del" title="Delete" @click="confirmDelete(w)">🗑️</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Add / Edit Modal -->
        <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
            <div class="modal">
                <h2>{{ editingWord ? 'Edit Word' : 'Add New Word' }}</h2>
                <form @submit.prevent="saveWord" class="word-form">

                    <!-- Word input + AI auto-fill (only shown when adding) -->
                    <label>
                        Word *
                        <div class="word-input-row">
                            <input v-model="form.word" required placeholder="e.g. appel" :disabled="!!editingWord"
                                class="word-input" />
                            <button v-if="!editingWord" type="button" class="btn-ai"
                                :disabled="!form.word.trim() || aiLoading" @click="autofillWithAI"
                                title="Let the AI fill in article, translation, difficulty and category">
                                <span v-if="aiLoading" class="ai-spinner">⏳</span>
                                <span v-else>✨ AI Fill</span>
                            </button>
                        </div>
                    </label>

                    <!-- AI result banner -->
                    <div v-if="aiNote" class="ai-note">
                        <span class="ai-note-icon">🤖</span>
                        <span>{{ aiNote }}</span>
                    </div>
                    <div v-if="aiError" class="ai-error">{{ aiError }}</div>

                    <label>
                        Article *
                        <select v-model="form.article" required>
                            <option value="de">de</option>
                            <option value="het">het</option>
                        </select>
                    </label>
                    <label>
                        Translation
                        <input v-model="form.translation" placeholder="e.g. apple" />
                    </label>
                    <label>
                        Difficulty
                        <select v-model="form.difficulty">
                            <option value="easy">Easy</option>
                            <option value="medium">Medium</option>
                            <option value="hard">Hard</option>
                        </select>
                    </label>
                    <label>
                        Category
                        <input v-model="form.category" placeholder="e.g. food, nature, abstract…" />
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" v-model="form.is_active" />
                        Active (included in game)
                    </label>
                    <div v-if="formError" class="form-error">{{ formError }}</div>
                    <div class="modal-actions">
                        <button type="button" class="btn-secondary" @click="closeModal">Cancel</button>
                        <button type="submit" class="btn-primary" :disabled="saving">
                            {{ saving ? 'Saving…' : (editingWord ? 'Save Changes' : 'Add Word') }}
                        </button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
            <div class="modal modal-small">
                <h2>Delete "{{ deleteTarget.word }}"?</h2>
                <p>This will permanently remove the word from the database and the game.</p>
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
const words = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const filterArticle = ref('')
const filterDifficulty = ref('')
const filterActive = ref('')
const sortKey = ref('word')
const sortDir = ref('asc')

const showModal = ref(false)
const editingWord = ref(null)
const form = ref(defaultForm())
const formError = ref('')
const saving = ref(false)
const deleteTarget = ref(null)

// AI auto-fill state
const aiLoading = ref(false)
const aiNote = ref('')
const aiError = ref('')

// ── Computed ───────────────────────────────────────────────────────────────
const filteredWords = computed(() => {
    let list = words.value
    const q = search.value.toLowerCase()
    if (q) list = list.filter(w => w.word.includes(q) || (w.translation || '').toLowerCase().includes(q))
    if (filterArticle.value) list = list.filter(w => w.article === filterArticle.value)
    if (filterDifficulty.value) list = list.filter(w => w.difficulty === filterDifficulty.value)
    if (filterActive.value !== '') list = list.filter(w => String(w.is_active) === filterActive.value)

    return [...list].sort((a, b) => {
        let va = a[sortKey.value] ?? ''
        let vb = b[sortKey.value] ?? ''
        if (typeof va === 'boolean') va = va ? 1 : 0
        if (typeof vb === 'boolean') vb = vb ? 1 : 0
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
    await fetchWords()
})

// ── API ────────────────────────────────────────────────────────────────────
async function fetchWords() {
    loading.value = true
    error.value = ''
    try {
        const ax = auth.getAuthAxios()
        const { data } = await ax.get('/api/admin/article-words')
        words.value = data
    } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to load words.'
    } finally {
        loading.value = false
    }
}

async function saveWord() {
    formError.value = ''
    saving.value = true
    try {
        const ax = auth.getAuthAxios()
        if (editingWord.value) {
            // Only send changed fields
            const payload = {
                article: form.value.article,
                translation: form.value.translation || null,
                difficulty: form.value.difficulty,
                category: form.value.category || null,
                is_active: form.value.is_active,
            }
            const { data } = await ax.put(`/api/admin/article-words/${editingWord.value.id}`, payload)
            const idx = words.value.findIndex(w => w.id === data.id)
            if (idx !== -1) words.value[idx] = data
        } else {
            const { data } = await ax.post('/api/admin/article-words', {
                ...form.value,
                translation: form.value.translation || null,
                category: form.value.category || null,
            })
            words.value.push(data)
        }
        closeModal()
    } catch (e) {
        formError.value = e.response?.data?.detail || 'Failed to save word.'
    } finally {
        saving.value = false
    }
}

async function doDelete() {
    if (!deleteTarget.value) return
    saving.value = true
    try {
        const ax = auth.getAuthAxios()
        await ax.delete(`/api/admin/article-words/${deleteTarget.value.id}`)
        words.value = words.value.filter(w => w.id !== deleteTarget.value.id)
        deleteTarget.value = null
    } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to delete word.'
        deleteTarget.value = null
    } finally {
        saving.value = false
    }
}

// ── UI helpers ─────────────────────────────────────────────────────────────
function defaultForm() {
    return { word: '', article: 'de', translation: '', difficulty: 'medium', category: '', is_active: true }
}

function openAdd() {
    editingWord.value = null
    form.value = defaultForm()
    formError.value = ''
    aiNote.value = ''
    aiError.value = ''
    showModal.value = true
}

function openEdit(w) {
    editingWord.value = w
    form.value = { word: w.word, article: w.article, translation: w.translation || '', difficulty: w.difficulty, category: w.category || '', is_active: w.is_active }
    formError.value = ''
    aiNote.value = ''
    aiError.value = ''
    showModal.value = true
}

function closeModal() {
    showModal.value = false
    editingWord.value = null
    aiNote.value = ''
    aiError.value = ''
}

async function autofillWithAI() {
    const word = form.value.word.trim().toLowerCase()
    if (!word) return
    aiLoading.value = true
    aiNote.value = ''
    aiError.value = ''
    try {
        const ax = auth.getAuthAxios()
        const { data } = await ax.post('/api/admin/article-words/lookup', { word })
        form.value.article = data.article || form.value.article
        form.value.translation = data.translation || form.value.translation
        form.value.difficulty = data.difficulty || form.value.difficulty
        form.value.category = data.category || form.value.category
        aiNote.value = data.confidence_note || 'Fields filled by AI — please review before saving.'
    } catch (e) {
        aiError.value = e.response?.data?.detail || 'AI lookup failed. Please fill the fields manually.'
    } finally {
        aiLoading.value = false
    }
}

function confirmDelete(w) {
    deleteTarget.value = w
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
</script>

<style scoped>
.admin-page {
    max-width: 1100px;
    margin: 0 auto;
    padding: 32px 20px 60px;
}

.admin-header {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 24px;
}

.admin-header h1 {
    font-size: 1.8rem;
    margin: 0;
    flex: 1;
}

.subtitle {
    color: var(--color-text-muted, #888);
    font-size: 0.95rem;
    margin: 0;
}

/* Filters */
.filters {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.filter-input {
    flex: 1;
    min-width: 200px;
    padding: 8px 12px;
    border: 1px solid var(--color-border, #ddd);
    border-radius: 8px;
    font-size: 0.9rem;
    background: var(--color-bg-soft, #f8f8f8);
}

.filter-select {
    padding: 8px 12px;
    border: 1px solid var(--color-border, #ddd);
    border-radius: 8px;
    font-size: 0.9rem;
    background: var(--color-bg-soft, #f8f8f8);
}

/* Table */
.table-wrap {
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid var(--color-border, #e0e0e0);
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
}

thead {
    background: var(--color-bg-soft, #f5f5f5);
}

th {
    padding: 12px 14px;
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
    color: var(--color-text-muted, #666);
    border-bottom: 2px solid var(--color-border, #e0e0e0);
}

th.sortable {
    cursor: pointer;
    user-select: none;
}

th.sortable:hover {
    color: var(--color-primary, #1a7fe8);
}

.sort-arrow {
    font-size: 0.75rem;
    opacity: 0.6;
}

td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--color-border, #eee);
    vertical-align: middle;
}

tr:last-child td {
    border-bottom: none;
}

tr.inactive {
    opacity: 0.5;
}

.word-cell {
    font-weight: 600;
    font-family: 'Georgia', serif;
}

.empty-row {
    text-align: center;
    color: #aaa;
    padding: 32px;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 600;
}

.badge-de {
    background: #dbeafe;
    color: #1d4ed8;
}

.badge-het {
    background: #dcfce7;
    color: #166534;
}

.badge-easy {
    background: #d1fae5;
    color: #065f46;
}

.badge-medium {
    background: #fef9c3;
    color: #854d0e;
}

.badge-hard {
    background: #fee2e2;
    color: #991b1b;
}

.badge-active {
    background: #d1fae5;
    color: #065f46;
}

.badge-inactive {
    background: #f3f4f6;
    color: #6b7280;
}

/* Actions */
.actions-cell {
    display: flex;
    gap: 6px;
}

.btn-icon {
    background: none;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: background 0.15s;
}

.btn-icon:hover {
    background: var(--color-bg-soft, #f0f0f0);
}

.btn-del:hover {
    background: #fee2e2;
}

/* Buttons */
.btn-primary {
    background: var(--color-primary, #1a7fe8);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
}

.btn-primary:disabled {
    opacity: 0.6;
    cursor: default;
}

.btn-primary:hover:not(:disabled) {
    opacity: 0.88;
}

.btn-secondary {
    background: var(--color-bg-soft, #f0f0f0);
    color: var(--color-text, #333);
    border: 1px solid var(--color-border, #ddd);
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
}

.btn-secondary:hover {
    background: #e4e4e4;
}

.btn-danger {
    background: #ef4444;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
}

.btn-danger:disabled {
    opacity: 0.6;
    cursor: default;
}

.btn-danger:hover:not(:disabled) {
    opacity: 0.88;
}

/* State messages */
.state-msg {
    padding: 40px;
    text-align: center;
    color: #888;
}

.state-msg.error {
    color: #ef4444;
}

/* Modal */
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
    max-width: 480px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
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

/* Form */
.word-form {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.word-form label {
    display: flex;
    flex-direction: column;
    gap: 5px;
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--color-text, #333);
}

.word-form input,
.word-form select {
    padding: 9px 12px;
    border: 1px solid var(--color-border, #ddd);
    border-radius: 8px;
    font-size: 0.95rem;
    background: var(--color-bg-soft, #f8f8f8);
}

.word-form input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.checkbox-label {
    flex-direction: row !important;
    align-items: center;
    gap: 10px !important;
    font-weight: 500;
    cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
    width: 18px;
    height: 18px;
    padding: 0;
    cursor: pointer;
}

.form-error {
    color: #ef4444;
    font-size: 0.88rem;
    background: #fee2e2;
    border-radius: 6px;
    padding: 8px 12px;
}

.modal-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 8px;
}

/* AI auto-fill elements */
.word-input-row {
    display: flex;
    gap: 8px;
    align-items: center;
}

.word-input {
    flex: 1;
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
    flex-shrink: 0;
}

.btn-ai:hover:not(:disabled) {
    opacity: 0.88;
}

.btn-ai:disabled {
    opacity: 0.45;
    cursor: default;
}

.ai-spinner {
    animation: spin 1s linear infinite;
    display: inline-block;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
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
}

.ai-note-icon {
    font-size: 1rem;
    flex-shrink: 0;
}

.ai-error {
    background: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 0.85rem;
    color: #991b1b;
}

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

    .word-input-row {
        flex-direction: column;
        align-items: stretch;
    }

    .btn-ai {
        justify-content: center;
    }
}
</style>
