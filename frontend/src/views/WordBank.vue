<template>
    <div class="word-bank-container">
        <header class="page-header">
            <h2>My Word Bank</h2>
            <p>Your personal collection of Dutch words.</p>
        </header>
        <div class="add-word-section">
            <div class="add-word-form">
                <input v-model="newWord" type="text" placeholder="Enter a Dutch word…" class="add-word-input"
                    @keyup.enter="addWord" :disabled="isAdding" />
                <button @click="addWord" class="add-word-btn" :disabled="isAdding || !newWord.trim()">
                    <span v-if="isAdding" class="spinner">⟳</span>
                    <i v-else class="fas fa-plus"></i>
                    {{ isAdding ? 'Looking up…' : 'Add Word' }}
                </button>
            </div>
            <div v-if="addError" class="add-feedback add-feedback--error">
                <span class="feedback-icon">⚠️</span> {{ addError }}
            </div>
            <div v-if="addSuccess" class="add-feedback add-feedback--success">
                <span class="feedback-icon">✅</span> <strong>{{ addSuccess }}</strong> added to your word bank!
            </div>
        </div>
        <div v-if="isLoading" class="loading-indicator">
            <p>Loading words...</p>
        </div>

        <div v-else-if="error" class="error-message">
            <p>{{ error }}</p>
        </div>

        <div v-else class="words-grid">
            <WordCard v-for="word in words" :key="word.id" :word="word" @edit="openEditModal" @delete="deleteWord" />
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
        };
    },
    methods: {
        async fetchWords() {
            this.isLoading = true;
            this.error = null;
            try {
                const response = await authAxios.get('/api/word-bank/words');
                this.words = response.data;
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
                    // LLM validation rejection — show the explanation directly
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

.add-word-section {
    margin-bottom: 40px;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

.add-word-form {
    display: flex;
    gap: 10px;
    padding: 10px;
}

.add-word-input {
    flex-grow: 1;
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

.add-feedback {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.9rem;
    line-height: 1.4;
    margin-top: 10px;
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

.error-message {
    color: #e74c3c;
    text-align: center;
    margin-top: 10px;
}

.words-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}
</style>
