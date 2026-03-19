<template>
    <div class="word-bank-container">
        <header class="page-header">
            <h2>My Word Bank</h2>
            <p>Your personal collection of Dutch words.</p>
        </header>

        <!-- ── Add word section ─────────────────────────────────────────── -->
        <div class="add-word-section">
            <!-- Single word -->
            <div class="add-word-form">
                <input v-model="newWord" type="text" placeholder="Enter a Dutch word…" class="add-word-input"
                    @keyup.enter="addWord" :disabled="isAdding" />
                <button @click="addWord" class="add-word-btn" :disabled="isAdding || !newWord.trim()">
                    <span v-if="isAdding" class="spinner">⟳</span>
                    <i v-else class="fas fa-plus"></i>
                    {{ isAdding ? 'Looking up…' : 'Add Word' }}
                </button>
                <button @click="showBulkPanel = !showBulkPanel" class="bulk-toggle-btn"
                    :class="{ active: showBulkPanel }" title="Add multiple words at once">
                    📋 Bulk add
                </button>
            </div>

            <div v-if="addError" class="add-feedback add-feedback--error">
                <span class="feedback-icon">⚠️</span> {{ addError }}
            </div>
            <div v-if="addSuccess" class="add-feedback add-feedback--success">
                <span class="feedback-icon">✅</span> <strong>{{ addSuccess }}</strong> added to your word bank!
            </div>

            <!-- Bulk add panel -->
            <div v-if="showBulkPanel" class="bulk-panel">
                <p class="bulk-desc">
                    Paste words separated by commas, semicolons, or new lines. The AI will look up each one.
                </p>
                <textarea v-model="bulkPasteText" class="bulk-textarea"
                    placeholder="appel, boom, auto, huis, fiets&#10;(one word per line or comma-separated)" rows="4"
                    :disabled="bulkStep === 'progress'" />

                <div class="bulk-category-row">
                    <label class="bulk-category-label" for="bulkCategoryField">🏷️ Tag all with category</label>
                    <input id="bulkCategoryField" v-model="bulkImportCategory" class="bulk-category-field"
                        placeholder="e.g. Travel, Verbs… (optional)" list="bulk-category-suggestions"
                        :disabled="bulkStep === 'progress'" />
                    <datalist id="bulk-category-suggestions">
                        <option v-for="c in categories" :key="c" :value="c" />
                    </datalist>
                </div>

                <div v-if="parsedWords.length" class="parsed-preview">
                    <span class="parsed-count">{{ parsedWords.length }} word{{ parsedWords.length !== 1 ? 's' : '' }}
                        detected:</span>
                    <span class="parsed-chips">
                        <span v-for="w in parsedWords.slice(0, 20)" :key="w" class="chip">{{ w }}</span>
                        <span v-if="parsedWords.length > 20" class="chip chip-more">+{{ parsedWords.length - 20 }}
                            more</span>
                    </span>
                </div>

                <!-- Progress table -->
                <div v-if="bulkStep === 'progress'" class="bulk-progress-section">
                    <div class="bulk-progress-bar-wrap">
                        <div class="bulk-progress-bar" :style="{ width: bulkProgressPct + '%' }"></div>
                    </div>
                    <p class="bulk-progress-label">{{ bulkDone }} / {{ bulkTotal }} processed</p>

                    <div class="bulk-result-table-wrap">
                        <table class="bulk-result-table">
                            <thead>
                                <tr>
                                    <th>Word</th>
                                    <th>Result</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="r in bulkResults" :key="r.word" :class="'row-' + r.status">
                                    <td class="word-cell">{{ r.word }}</td>
                                    <td>
                                        <span v-if="r.status === 'pending'" class="status-pending">⏳ Waiting…</span>
                                        <span v-else-if="r.status === 'added'" class="status-added">✅ Added</span>
                                        <span v-else-if="r.status === 'error'" class="status-error" :title="r.error">⚠️
                                            {{ r.error }}</span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <div v-if="bulkDone === bulkTotal && bulkTotal > 0" class="bulk-summary">
                        <span class="sum-added">✅ {{ bulkSummary.added }} added</span>
                        <span v-if="bulkSummary.errors" class="sum-error">⚠️ {{ bulkSummary.errors }} errors</span>
                    </div>
                </div>

                <div class="bulk-actions">
                    <button class="btn-secondary" @click="closeBulkPanel">Cancel</button>
                    <button class="btn-primary"
                        :disabled="!parsedWords.length || bulkStep === 'progress' && bulkDone < bulkTotal"
                        @click="bulkStep === 'progress' && bulkDone === bulkTotal ? resetBulk() : startBulkImport()">
                        <span v-if="bulkStep === 'progress' && bulkDone < bulkTotal">Processing…</span>
                        <span v-else-if="bulkStep === 'progress' && bulkDone === bulkTotal">✅ Done — Add more</span>
                        <span v-else>✨ Add {{ parsedWords.length }} word{{ parsedWords.length !== 1 ? 's' : '' }}</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- ── Toolbar ──────────────────────────────────────────────── -->
        <div class="toolbar" :class="{ 'toolbar--empty': !words.length }">
            <!-- Select-mode controls -->
            <button v-if="!selectMode" @click="enterSelectMode" class="btn-select-mode" :disabled="!words.length">
                ☑️ Select words
            </button>
            <template v-else>
                <span class="select-count">{{ selectedIds.size }} selected</span>
                <button @click="selectAll" class="btn-tool" :disabled="selectedIds.size === filteredWords.length">
                    Select all
                </button>
                <button @click="selectedIds = new Set()" class="btn-tool" :disabled="selectedIds.size === 0">
                    Deselect all
                </button>
                <!-- Bulk category assignment -->
                <div class="bulk-category-wrap">
                    <input v-model="bulkCategoryValue" class="bulk-category-input" placeholder="Set category…"
                        list="category-suggestions" :disabled="selectedIds.size === 0 || isBulkCategoring" />
                    <datalist id="category-suggestions">
                        <option v-for="c in categories" :key="c" :value="c" />
                    </datalist>
                    <button class="btn-tool btn-tag" :disabled="selectedIds.size === 0 || isBulkCategoring"
                        @click="bulkSetCategory" title="Assign category to selected words">
                        <span v-if="isBulkCategoring" class="spinner">⟳</span>
                        <span v-else>🏷️ Tag</span>
                    </button>
                    <button class="btn-tool" :disabled="selectedIds.size === 0 || isBulkCategoring"
                        @click="bulkClearCategory" title="Remove category from selected words">
                        ✕ Clear tag
                    </button>
                </div>
                <button @click="deleteSelected" class="btn-delete-selected"
                    :disabled="selectedIds.size === 0 || isDeletingSelected">
                    <span v-if="isDeletingSelected" class="spinner">⟳</span>
                    🗑️ Delete selected ({{ selectedIds.size }})
                </button>
                <button @click="exitSelectMode" class="btn-tool">Cancel</button>
            </template>

            <!-- Spacer -->
            <span class="toolbar-spacer"></span>

            <!-- Search -->
            <div class="search-wrap">
                <span class="search-icon">🔍</span>
                <input v-model="searchQuery" class="search-input" type="search" placeholder="Search words…" />
                <button v-if="searchQuery" @click="searchQuery = ''" class="search-clear"
                    title="Clear search">✕</button>
            </div>

            <!-- Type filter -->
            <select v-model="typeFilter" class="type-select" title="Filter by word type">
                <option value="">All types</option>
                <option v-for="t in wordTypes" :key="t" :value="t">{{ t }}</option>
            </select>

            <!-- Category filter -->
            <div v-if="categories.length" class="category-filter">
                <select v-model="categoryFilter" class="category-select">
                    <option value="">All categories</option>
                    <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
                </select>
            </div>

            <!-- Sort controls -->
            <div class="sort-wrap">
                <button @click="toggleSort('alpha')" :class="['sort-btn', { active: sortKey === 'alpha' }]"
                    title="Sort alphabetically">
                    🔤 <span v-if="sortKey === 'alpha'">{{ sortDir === 'asc' ? '↑' : '↓' }}</span>
                </button>
                <button @click="toggleSort('date')" :class="['sort-btn', { active: sortKey === 'date' }]"
                    title="Sort by date added">
                    📅 <span v-if="sortKey === 'date'">{{ sortDir === 'desc' ? '↓' : '↑' }}</span>
                </button>
            </div>

            <!-- View-mode toggle -->
            <div class="view-toggle" title="Switch view">
                <button @click="viewMode = 'grid'" :class="['view-btn', { active: viewMode === 'grid' }]"
                    title="Grid view">⊞</button>
                <button @click="viewMode = 'list'" :class="['view-btn', { active: viewMode === 'list' }]"
                    title="List view">☰</button>
            </div>
        </div>

        <!-- Active filters summary -->
        <div v-if="searchQuery || typeFilter || categoryFilter" class="filter-summary">
            <span class="filter-summary-count">{{ filteredWords.length }} result{{ filteredWords.length !== 1 ? 's' : ''
                }}</span>
            <span v-if="searchQuery" class="filter-chip">
                🔍 "{{ searchQuery }}" <button @click="searchQuery = ''">✕</button>
            </span>
            <span v-if="typeFilter" class="filter-chip">
                📝 {{ typeFilter }} <button @click="typeFilter = ''">✕</button>
            </span>
            <span v-if="categoryFilter" class="filter-chip">
                🏷️ {{ categoryFilter }} <button @click="categoryFilter = ''">✕</button>
            </span>
            <button class="filter-clear-all" @click="searchQuery = ''; typeFilter = ''; categoryFilter = ''">Clear
                all</button>
        </div>

        <!-- ── Loading / error ──────────────────────────────────────────── -->
        <div v-if="isLoading" class="loading-indicator">
            <p>Loading words...</p>
        </div>

        <div v-else-if="error" class="error-message">
            <p>{{ error }}</p>
        </div>

        <!-- ── Grid view ────────────────────────────────────────────────── -->
        <div v-else-if="viewMode === 'grid'" class="words-grid">
            <div v-for="word in filteredWords" :key="word.id" class="word-card-wrapper"
                :class="{ 'card-selected': selectedIds.has(word.id) }"
                @click="selectMode ? toggleSelect(word.id) : null">
                <div v-if="selectMode" class="card-checkbox">
                    <input type="checkbox" :checked="selectedIds.has(word.id)" @change="toggleSelect(word.id)"
                        @click.stop />
                </div>
                <WordCard :word="word" @edit="selectMode ? null : openEditModal(word)"
                    @delete="selectMode ? null : deleteWord(word.id)" />
            </div>
        </div>

        <!-- ── List view ────────────────────────────────────────────────── -->
        <div v-else class="words-list-wrap">
            <table class="words-list">
                <thead>
                    <tr>
                        <th v-if="selectMode" class="col-check">
                            <input type="checkbox"
                                :checked="selectedIds.size === filteredWords.length && filteredWords.length > 0"
                                @change="selectedIds.size === filteredWords.length ? selectedIds = new Set() : selectAll()"
                                title="Select / deselect all" />
                        </th>
                        <th class="col-word">Word</th>
                        <th class="col-type">Type</th>
                        <th class="col-trans">Translation</th>
                        <th class="col-cat">Category</th>
                        <th class="col-def">Definition</th>
                        <th v-if="!selectMode" class="col-actions"></th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="word in filteredWords" :key="word.id"
                        :class="{ 'row-selected': selectedIds.has(word.id) }"
                        @click="selectMode ? toggleSelect(word.id) : null" :style="selectMode ? 'cursor: pointer' : ''">
                        <td v-if="selectMode" class="col-check" @click.stop>
                            <input type="checkbox" :checked="selectedIds.has(word.id)"
                                @change="toggleSelect(word.id)" />
                        </td>
                        <td class="col-word list-word">
                            {{ word.word }}
                            <router-link v-if="word.word_type === 'verb' || word.word_type === 'expression'"
                                :to="`/conjugator/${encodeURIComponent(word.word_type === 'expression' ? word.word.trim().split(' ').at(-1) : word.word)}`"
                                class="conjugate-link" title="See conjugation table">
                                🔀
                            </router-link>
                        </td>
                        <td class="col-type">
                            <span class="word-type-badge">{{ word.word_type }}</span>
                        </td>
                        <td class="col-trans">{{ word.details?.translation_en || '—' }}</td>
                        <td class="col-cat" @click.stop>
                            <!-- Inline category edit -->
                            <template v-if="editingCategoryId === word.id">
                                <input class="inline-cat-input" v-model="editingCategoryValue"
                                    list="category-suggestions" placeholder="Category…"
                                    @keyup.enter="saveCategoryInline(word)" @keyup.escape="cancelCategoryInline"
                                    @blur="saveCategoryInline(word)" ref="catInput" />
                            </template>
                            <template v-else>
                                <span v-if="word.category" class="cat-chip" @click="startCategoryInline(word)"
                                    title="Click to edit">{{ word.category }}</span>
                                <button v-else class="add-cat-btn" @click="startCategoryInline(word)"
                                    title="Add category">+ tag</button>
                            </template>
                        </td>
                        <td class="col-def list-def">{{ word.details?.definition || '—' }}</td>
                        <td v-if="!selectMode" class="col-actions" @click.stop>
                            <button @click="openEditModal(word)" class="list-action-btn edit" title="Edit">✏️</button>
                            <button @click="deleteWord(word.id)" class="list-action-btn delete"
                                title="Delete">🗑️</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <EditWordModal :is-open="isEditModalOpen" :word-to-edit="wordToEdit" @close="closeEditModal"
            @word-saved="fetchWords" />
    </div>
</template>

<script>
import WordCard from '../components/WordCard.vue';
import EditWordModal from '../components/EditWordModal.vue';
import { authAxios } from '../stores/auth.js';

export default {
    name: 'WordBank',
    components: {
        WordCard,
        EditWordModal,
    },
    data() {
        return {
            words: [],
            newWord: '',
            isAdding: false,
            addError: null,
            addSuccess: null,
            isLoading: false,
            error: null,
            isEditModalOpen: false,
            wordToEdit: null,

            // Bulk add
            showBulkPanel: false,
            bulkPasteText: '',
            bulkStep: 'input',       // 'input' | 'progress'
            bulkResults: [],
            bulkSummary: { added: 0, errors: 0 },
            bulkTotal: 0,
            bulkDone: 0,
            bulkImportCategory: '',

            // Multi-select delete
            selectMode: false,
            selectedIds: new Set(),
            isDeletingSelected: false,

            // View mode
            viewMode: 'grid',   // 'grid' | 'list'

            // Category
            categories: [],
            categoryFilter: '',
            editingCategoryId: null,
            editingCategoryValue: '',
            bulkCategoryValue: '',
            isBulkCategoring: false,

            // Search, sort, type filter
            searchQuery: '',
            typeFilter: '',
            sortKey: 'date',    // 'alpha' | 'date'
            sortDir: 'desc',    // 'asc'  | 'desc'
        };
    },
    computed: {
        parsedWords() {
            const raw = this.bulkPasteText;
            if (!raw.trim()) return [];
            return [...new Set(
                raw.split(/[\n\r,;]+/)
                    .map(w => w.trim().toLowerCase())
                    .filter(w => w.length > 0)
            )];
        },
        bulkProgressPct() {
            return this.bulkTotal ? Math.round((this.bulkDone / this.bulkTotal) * 100) : 0;
        },
        filteredWords() {
            const q = this.searchQuery.trim().toLowerCase();
            let list = this.words;

            // 1. Search by word or English translation
            if (q) {
                list = list.filter(w => {
                    const inWord = w.word?.toLowerCase().includes(q);
                    const inTranslation = w.details?.translation_en?.toLowerCase().includes(q);
                    return inWord || inTranslation;
                });
            }

            // 2. Type filter
            if (this.typeFilter) {
                list = list.filter(w => w.word_type === this.typeFilter);
            }

            // 3. Category filter
            if (this.categoryFilter) {
                list = list.filter(w => w.category === this.categoryFilter);
            }

            // 4. Sort
            list = [...list].sort((a, b) => {
                let cmp = 0;
                if (this.sortKey === 'alpha') {
                    cmp = a.word.localeCompare(b.word, 'nl', { sensitivity: 'base' });
                } else {
                    // date: sort by created_at
                    cmp = new Date(a.created_at) - new Date(b.created_at);
                }
                return this.sortDir === 'asc' ? cmp : -cmp;
            });

            return list;
        },
        wordTypes() {
            const types = [...new Set(this.words.map(w => w.word_type).filter(Boolean))];
            return types.sort();
        },
    },
    methods: {
        async fetchWords() {
            this.isLoading = true;
            this.error = null;
            try {
                const [wordsRes, catsRes] = await Promise.all([
                    authAxios.get('/api/word-bank/words'),
                    authAxios.get('/api/word-bank/categories'),
                ]);
                this.words = wordsRes.data;
                this.categories = catsRes.data;
            } catch (err) {
                this.error = 'Failed to load words. Please try again later.';
                console.error(err);
            } finally {
                this.isLoading = false;
            }
        },

        async addWord() {
            if (!this.newWord.trim()) return;
            this.isAdding = true;
            this.addError = null;
            this.addSuccess = null;
            const word = this.newWord.trim();
            try {
                await authAxios.post('/api/word-bank/words', { word });
                this.newWord = '';
                this.addSuccess = word;
                await this.fetchWords();
            } catch (err) {
                const status = err.response?.status;
                const detail = err.response?.data?.detail;
                if (status === 422 && detail) {
                    this.addError = detail;
                } else if (status === 409) {
                    this.addError = `'${word}' is already in your word bank.`;
                } else {
                    this.addError = detail || 'Failed to add word. Please try again.';
                }
                console.error(err);
            } finally {
                this.isAdding = false;
            }
        },

        // ── Bulk add ────────────────────────────────────────────────────
        closeBulkPanel() {
            this.showBulkPanel = false;
            this.resetBulk();
        },
        resetBulk() {
            this.bulkPasteText = '';
            this.bulkStep = 'input';
            this.bulkResults = [];
            this.bulkSummary = { added: 0, errors: 0 };
            this.bulkTotal = 0;
            this.bulkDone = 0;
            this.bulkImportCategory = '';
        },
        async startBulkImport() {
            const wordList = this.parsedWords;
            if (!wordList.length) return;
            if (wordList.length > 100) {
                alert('Maximum 100 words per import. Please split into smaller batches.');
                return;
            }

            this.bulkTotal = wordList.length;
            this.bulkDone = 0;
            this.bulkResults = wordList.map(w => ({ word: w, status: 'pending' }));
            this.bulkStep = 'progress';

            try {
                const { data } = await authAxios.post('/api/word-bank/words/bulk', {
                    words: wordList,
                    category: this.bulkImportCategory.trim() || null,
                });
                const resultMap = Object.fromEntries(data.results.map(r => [r.word, r]));
                this.bulkResults = this.bulkResults.map(r => resultMap[r.word] ?? r);
                this.bulkDone = this.bulkTotal;
                this.bulkSummary = data.summary;
                await this.fetchWords();
            } catch (err) {
                this.bulkResults = this.bulkResults.map(r =>
                    r.status === 'pending'
                        ? { ...r, status: 'error', error: err.response?.data?.detail || 'Request failed' }
                        : r
                );
                this.bulkDone = this.bulkTotal;
                this.bulkSummary = { added: 0, errors: this.bulkTotal };
            }
        },

        // ── Edit / single delete ────────────────────────────────────────
        openEditModal(word) {
            this.wordToEdit = { ...word };
            this.isEditModalOpen = true;
        },
        closeEditModal() {
            this.isEditModalOpen = false;
            this.wordToEdit = null;
        },
        async deleteWord(wordId) {
            if (confirm('Are you sure you want to delete this word?')) {
                try {
                    await authAxios.delete(`/api/word-bank/words/${wordId}`);
                    this.fetchWords();
                } catch (err) {
                    alert('Failed to delete word.');
                    console.error(err);
                }
            }
        },

        enterSelectMode() {
            this.selectMode = true;
            this.selectedIds = new Set();
        },
        exitSelectMode() {
            this.selectMode = false;
            this.selectedIds = new Set();
            this.bulkCategoryValue = '';
        },
        toggleSelect(wordId) {
            const next = new Set(this.selectedIds);
            if (next.has(wordId)) next.delete(wordId);
            else next.add(wordId);
            this.selectedIds = next;
        },
        selectAll() {
            this.selectedIds = new Set(this.filteredWords.map(w => w.id));
        },
        async deleteSelected() {
            const ids = [...this.selectedIds];
            if (!ids.length) return;
            if (!confirm(`Delete ${ids.length} word${ids.length !== 1 ? 's' : ''}? This cannot be undone.`)) return;

            this.isDeletingSelected = true;
            try {
                await authAxios.delete('/api/word-bank/words/bulk', { data: { word_ids: ids } });
                this.exitSelectMode();
                await this.fetchWords();
            } catch (err) {
                alert('Failed to delete some words. Please try again.');
                console.error(err);
            } finally {
                this.isDeletingSelected = false;
            }
        },

        // ── Sort ────────────────────────────────────────────────────────
        toggleSort(key) {
            if (this.sortKey === key) {
                this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortKey = key;
                // default directions: newest first for date, A→Z for alpha
                this.sortDir = key === 'date' ? 'desc' : 'asc';
            }
        },

        // ── Category (inline, single) ───────────────────────────────────
        startCategoryInline(word) {
            this.editingCategoryId = word.id;
            this.editingCategoryValue = word.category || '';
            this.$nextTick(() => {
                const el = this.$refs.catInput;
                if (el) (Array.isArray(el) ? el[0] : el).focus();
            });
        },
        cancelCategoryInline() {
            this.editingCategoryId = null;
            this.editingCategoryValue = '';
        },
        async saveCategoryInline(word) {
            if (this.editingCategoryId !== word.id) return;
            const newCat = this.editingCategoryValue.trim() || null;
            this.editingCategoryId = null;
            this.editingCategoryValue = '';
            if (newCat === (word.category || null)) return; // no change
            try {
                await authAxios.patch(`/api/word-bank/words/${word.id}/category`, { category: newCat });
                await this.fetchWords();
            } catch (err) {
                console.error('Failed to update category', err);
            }
        },

        // ── Category (bulk) ─────────────────────────────────────────────
        async bulkSetCategory() {
            const ids = [...this.selectedIds];
            if (!ids.length) return;
            const cat = this.bulkCategoryValue.trim() || null;
            this.isBulkCategoring = true;
            try {
                await authAxios.patch('/api/word-bank/words/bulk-category', { word_ids: ids, category: cat });
                await this.fetchWords();
            } catch (err) {
                alert('Failed to set category. Please try again.');
                console.error(err);
            } finally {
                this.isBulkCategoring = false;
            }
        },
        async bulkClearCategory() {
            const ids = [...this.selectedIds];
            if (!ids.length) return;
            this.isBulkCategoring = true;
            try {
                await authAxios.patch('/api/word-bank/words/bulk-category', { word_ids: ids, category: null });
                await this.fetchWords();
            } catch (err) {
                alert('Failed to clear category. Please try again.');
                console.error(err);
            } finally {
                this.isBulkCategoring = false;
            }
        },
    },
    created() {
        this.fetchWords();
    },
};
</script>

<style scoped>
.word-bank-container {
    padding: 40px 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.page-header {
    text-align: center;
    margin-bottom: 40px;
}

.page-header h2 {
    font-size: 36px;
    color: #333;
}

.page-header p {
    font-size: 18px;
    color: #666;
    margin-bottom: 20px;
}

/* ── Add word section ───────────────────────────────────────────────────── */
.add-word-section {
    margin-bottom: 40px;
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
}

.add-word-form {
    display: flex;
    gap: 10px;
    padding: 10px;
    flex-wrap: wrap;
}

.add-word-input {
    flex-grow: 1;
    min-width: 160px;
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 8px;
    font-size: 16px;
}

.add-word-btn {
    background-color: #667eea;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s;
    display: flex;
    align-items: center;
    gap: 8px;
}

.add-word-btn:hover {
    background-color: #5a6edc;
}

.add-word-btn:disabled {
    background-color: #aaa;
    cursor: not-allowed;
}

.bulk-toggle-btn {
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    color: #374151;
    padding: 12px 18px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
    white-space: nowrap;
}

.bulk-toggle-btn:hover,
.bulk-toggle-btn.active {
    background: #e5e7eb;
    border-color: #9ca3af;
}

.add-feedback {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.9rem;
    line-height: 1.4;
    margin-top: 10px;
    margin-left: 10px;
    margin-right: 10px;
}

.add-feedback--error {
    background: #fee2e2;
    border: 1px solid #fca5a5;
    color: #991b1b;
}

.add-feedback--success {
    background: #dcfce7;
    border: 1px solid #86efac;
    color: #166534;
}

.feedback-icon {
    flex-shrink: 0;
}

/* ── Bulk panel ─────────────────────────────────────────────────────────── */
.bulk-panel {
    margin: 12px 10px 0;
    padding: 20px;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}

.bulk-desc {
    color: #6b7280;
    font-size: 0.9rem;
    margin-bottom: 12px;
}

.bulk-category-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 10px 0 14px;
    flex-wrap: wrap;
}

.bulk-category-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #374151;
    white-space: nowrap;
}

.bulk-category-field {
    flex: 1;
    min-width: 160px;
    padding: 7px 11px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 14px;
    font-family: inherit;
    background: #fff;
    transition: border-color 0.15s;
}

.bulk-category-field:focus {
    outline: none;
    border-color: #667eea;
}

.bulk-category-field:disabled {
    background: #f3f4f6;
    color: #9ca3af;
}

.bulk-textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 15px;
    font-family: inherit;
    resize: vertical;
    box-sizing: border-box;
}

.bulk-textarea:disabled {
    background: #f3f4f6;
    color: #9ca3af;
}

.parsed-preview {
    margin-top: 10px;
    font-size: 0.875rem;
    color: #374151;
}

.parsed-count {
    font-weight: 600;
    margin-right: 8px;
}

.parsed-chips {
    display: inline-flex;
    flex-wrap: wrap;
    gap: 4px;
}

.chip {
    background: #e0e7ff;
    color: #3730a3;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.8rem;
}

.chip-more {
    background: #f3f4f6;
    color: #6b7280;
}

.bulk-progress-section {
    margin-top: 16px;
}

.bulk-progress-bar-wrap {
    height: 8px;
    background: #e5e7eb;
    border-radius: 999px;
    overflow: hidden;
}

.bulk-progress-bar {
    height: 100%;
    background: #667eea;
    border-radius: 999px;
    transition: width 0.3s;
}

.bulk-progress-label {
    font-size: 0.85rem;
    color: #6b7280;
    margin: 6px 0 10px;
}

.bulk-result-table-wrap {
    max-height: 260px;
    overflow-y: auto;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}

.bulk-result-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
}

.bulk-result-table th {
    background: #f3f4f6;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
    color: #374151;
    position: sticky;
    top: 0;
}

.bulk-result-table td {
    padding: 7px 12px;
    border-top: 1px solid #f3f4f6;
}

.row-added {
    background: #f0fdf4;
}

.row-error {
    background: #fff7f7;
}

.status-pending {
    color: #9ca3af;
}

.status-added {
    color: #166534;
    font-weight: 600;
}

.status-error {
    color: #991b1b;
}

.bulk-summary {
    display: flex;
    gap: 16px;
    margin-top: 12px;
    font-size: 0.9rem;
    font-weight: 600;
}

.sum-added {
    color: #166534;
}

.sum-error {
    color: #991b1b;
}

.bulk-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 14px;
}

.btn-secondary {
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    color: #374151;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
}

.btn-secondary:hover {
    background: #e5e7eb;
}

.btn-primary {
    background: #667eea;
    border: none;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
}

.btn-primary:hover {
    background: #5a6edc;
}

.btn-primary:disabled {
    background: #aaa;
    cursor: not-allowed;
}

.col-cat {
    width: 130px;
}

.cat-chip {
    display: inline-block;
    background: #ede9fe;
    color: #6d28d9;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
}

.cat-chip:hover {
    background: #ddd6fe;
}

.add-cat-btn {
    background: none;
    border: 1px dashed #d1d5db;
    color: #9ca3af;
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 11px;
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
}

.add-cat-btn:hover {
    border-color: #667eea;
    color: #667eea;
}

.inline-cat-input {
    width: 110px;
    padding: 2px 7px;
    border: 1px solid #667eea;
    border-radius: 6px;
    font-size: 12px;
    outline: none;
}

/* ── Category filter & bulk tag ─────────────────────────────────────────── */
.category-filter {
    display: flex;
    align-items: center;
}

.category-select {
    padding: 7px 10px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    background: #fff;
    color: #374151;
    cursor: pointer;
}

.bulk-category-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
}

.bulk-category-input {
    padding: 6px 10px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    width: 140px;
}

.bulk-category-input:focus {
    outline: none;
    border-color: #667eea;
}

.btn-tag {
    background: #ede9fe;
    color: #6d28d9;
    border-color: #c4b5fd;
}

.btn-tag:not(:disabled):hover {
    background: #ddd6fe;
}

/* ── Toolbar ────────────────────────────────────────────────────────────── */
.toolbar {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.btn-select-mode {
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    color: #374151;
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
}

.btn-select-mode:hover {
    background: #e5e7eb;
}

.select-count {
    font-weight: 600;
    color: #374151;
    font-size: 0.9rem;
}

.btn-tool {
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    color: #374151;
    padding: 7px 14px;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
}

.btn-tool:disabled {
    color: #9ca3af;
    cursor: not-allowed;
}

.btn-tool:not(:disabled):hover {
    background: #e5e7eb;
}

.btn-delete-selected {
    background: #ef4444;
    border: none;
    color: white;
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: background 0.2s;
}

.btn-delete-selected:hover:not(:disabled) {
    background: #dc2626;
}

.btn-delete-selected:disabled {
    background: #fca5a5;
    cursor: not-allowed;
}

.toolbar-spacer {
    flex: 1;
}

/* ── Search ─────────────────────────────────────────────────────────────── */
.search-wrap {
    position: relative;
    display: flex;
    align-items: center;
}

.search-icon {
    position: absolute;
    left: 9px;
    font-size: 13px;
    pointer-events: none;
    line-height: 1;
}

.search-input {
    padding: 7px 28px 7px 30px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    width: 180px;
    background: #fff;
    color: #374151;
    transition: border-color 0.15s, width 0.2s;
}

.search-input:focus {
    outline: none;
    border-color: #667eea;
    width: 220px;
}

/* hide browser's native clear button so we use our own */
.search-input::-webkit-search-cancel-button {
    display: none;
}

.search-clear {
    position: absolute;
    right: 7px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 11px;
    color: #9ca3af;
    padding: 0;
    line-height: 1;
}

.search-clear:hover {
    color: #374151;
}

/* ── Type filter ─────────────────────────────────────────────────────────── */
.type-select {
    padding: 7px 10px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 13px;
    background: #fff;
    color: #374151;
    cursor: pointer;
    text-transform: capitalize;
}

/* ── Sort buttons ────────────────────────────────────────────────────────── */
.sort-wrap {
    display: flex;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    overflow: hidden;
}

.sort-btn {
    background: #f3f4f6;
    border: none;
    padding: 7px 12px;
    font-size: 13px;
    cursor: pointer;
    color: #374151;
    transition: background 0.15s;
    display: flex;
    align-items: center;
    gap: 2px;
    white-space: nowrap;
}

.sort-btn:first-child {
    border-right: 1px solid #d1d5db;
}

.sort-btn:hover {
    background: #e5e7eb;
}

.sort-btn.active {
    background: #667eea;
    color: white;
}

/* ── Active filter summary bar ───────────────────────────────────────────── */
.filter-summary {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    padding: 8px 12px;
    margin-bottom: 14px;
    background: #f0f4ff;
    border: 1px solid #c7d2fe;
    border-radius: 8px;
    font-size: 0.875rem;
}

.filter-summary-count {
    font-weight: 700;
    color: #374151;
    margin-right: 4px;
}

.filter-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #e0e7ff;
    color: #3730a3;
    border-radius: 999px;
    padding: 3px 10px 3px 12px;
    font-size: 0.8rem;
    font-weight: 600;
}

.filter-chip button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 10px;
    color: #6366f1;
    padding: 0;
    line-height: 1;
}

.filter-chip button:hover {
    color: #4338ca;
}

.filter-clear-all {
    margin-left: auto;
    background: none;
    border: 1px solid #818cf8;
    color: #6366f1;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.8rem;
    cursor: pointer;
}

.filter-clear-all:hover {
    background: #e0e7ff;
}

.toolbar--empty .btn-select-mode {
    opacity: 0.4;
    cursor: not-allowed;
}

/* ── View toggle ────────────────────────────────────────────────────────── */
.view-toggle {
    display: flex;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    overflow: hidden;
}

.view-btn {
    background: #f3f4f6;
    border: none;
    padding: 7px 13px;
    font-size: 17px;
    line-height: 1;
    cursor: pointer;
    color: #6b7280;
    transition: background 0.15s, color 0.15s;
}

.view-btn:first-child {
    border-right: 1px solid #d1d5db;
}

.view-btn:hover {
    background: #e5e7eb;
    color: #374151;
}

.view-btn.active {
    background: #667eea;
    color: white;
}

/* ── Word grid ──────────────────────────────────────────────────────────── */
.words-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.word-card-wrapper {
    position: relative;
    border-radius: 12px;
    transition: box-shadow 0.15s;
}

.word-card-wrapper.card-selected {
    box-shadow: 0 0 0 3px #667eea;
}

.card-checkbox {
    position: absolute;
    top: 10px;
    left: 10px;
    z-index: 2;
}

.card-checkbox input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
    accent-color: #667eea;
}

/* Clicking a card in select mode feels natural */
.word-card-wrapper[style*="cursor"] {
    cursor: pointer;
}

/* ── List view ──────────────────────────────────────────────────────────── */
.words-list-wrap {
    overflow-x: auto;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}

.words-list {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}

.words-list thead {
    background: #f9fafb;
    position: sticky;
    top: 0;
    z-index: 1;
}

.words-list th {
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    color: #374151;
    border-bottom: 1px solid #e5e7eb;
    white-space: nowrap;
}

.words-list td {
    padding: 9px 14px;
    border-bottom: 1px solid #f3f4f6;
    color: #374151;
    vertical-align: middle;
}

.words-list tbody tr:last-child td {
    border-bottom: none;
}

.words-list tbody tr:hover {
    background: #f9fafb;
}

.row-selected,
.row-selected:hover {
    background: #eef2ff !important;
}

.col-check {
    width: 36px;
}

.col-word {
    min-width: 110px;
}

.col-type {
    width: 90px;
}

.col-trans {
    min-width: 120px;
}

.col-def {
    min-width: 160px;
}

.col-actions {
    width: 80px;
}

.list-word {
    font-weight: 700;
    color: #667eea;
    white-space: nowrap;
}

.conjugate-link {
    margin-left: 5px;
    font-size: 13px;
    text-decoration: none;
    vertical-align: middle;
    opacity: 0.6;
    transition: opacity 0.15s;
}

.conjugate-link:hover {
    opacity: 1;
}

.list-def {
    color: #6b7280;
    font-size: 0.85rem;
    max-width: 340px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.word-type-badge {
    background: #f0f0f0;
    color: #555;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    text-transform: capitalize;
}

.col-actions {
    display: flex;
    gap: 4px;
    align-items: center;
}

.list-action-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 15px;
    padding: 4px 6px;
    border-radius: 6px;
    line-height: 1;
    transition: background 0.15s;
}

.list-action-btn.edit:hover {
    background: #e0e7ff;
}

.list-action-btn.delete:hover {
    background: #fee2e2;
}

/* ── Misc ───────────────────────────────────────────────────────────────── */
.spinner {
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

.loading-indicator,
.error-message {
    text-align: center;
    color: #e74c3c;
    margin-top: 10px;
}

.loading-indicator {
    color: #6b7280;
}
</style>
