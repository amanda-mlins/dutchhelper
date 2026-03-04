<template>
    <div class="word-bank-container">
        <header class="page-header">
            <h2>My Word Bank</h2>
            <p>Your personal collection of Dutch words.</p>
        </header>
        <div class="add-word-section">
            <div v-if="addError" class="error-message">
                <p>{{ addError }}</p>
            </div>
            <div class="add-word-form">
                <input v-model="newWord" type="text" placeholder="Enter a new word" class="add-word-input" />
                <button @click="addWord" class="add-word-btn" :disabled="isAdding">
                    <i class="fas fa-plus"></i> Add Word
                </button>
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
import axios from 'axios';

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
                const response = await axios.get('/api/word-bank/words');
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
            try {
                await axios.post('/api/word-bank/words', { word: this.newWord });
                this.newWord = '';
                await this.fetchWords();
            } catch (err) {
                this.addError = 'Failed to add word. It might already be in your list.';
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
                    await axios.delete(`/api/word-bank/words/${wordId}`);
                    this.fetchWords(); // Refresh the list
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

.words-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.error-message {
    color: #e74c3c;
    text-align: center;
    margin-top: 10px;
}
</style>
