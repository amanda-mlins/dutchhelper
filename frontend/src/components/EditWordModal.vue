<template>
    <div v-if="isOpen" class="modal-overlay" @click.self="close">
        <div class="modal-content">
            <header class="modal-header">
                <h3>Edit Word</h3>
                <button @click="close" class="close-btn">&times;</button>
            </header>
            <form @submit.prevent="saveWord" class="modal-form">
                <div class="form-group">
                    <label for="word">Word</label>
                    <input type="text" id="word" v-model="form.word" required>
                </div>
                <div class="form-group">
                    <label for="word_type">Word Type</label>
                    <select id="word_type" v-model="form.word_type" required>
                        <option>noun</option>
                        <option>verb</option>
                        <option>adjective</option>
                        <option>adverb</option>
                        <option>preposition</option>
                        <option>other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="definition">Definition</label>
                    <input type="text" id="definition" v-model="form.details.definition" required>
                </div>
                <div class="form-group">
                    <label for="translation">Translation (EN)</label>
                    <input type="text" id="translation" v-model="form.details.translation_en" required>
                </div>
                <div class="form-group">
                    <label for="example">Example</label>
                    <textarea id="example" v-model="form.details.example" rows="3"></textarea>
                </div>

                <div class="form-actions">
                    <button type="button" @click="close" class="btn-cancel">Cancel</button>
                    <button type="submit" class="btn-save" :disabled="isSaving">
                        {{ isSaving ? 'Saving...' : 'Save' }}
                    </button>
                </div>
                <p v-if="error" class="error-message">{{ error }}</p>
            </form>
        </div>
    </div>
</template>

<script>
import axios from 'axios';

export default {
    name: 'EditWordModal',
    props: {
        isOpen: Boolean,
        wordToEdit: Object,
    },
    data() {
        return {
            form: this.getInitialFormState(),
            isSaving: false,
            error: null,
        };
    },
    watch: {
        isOpen(newVal) {
            if (newVal) {
                this.form = this.getInitialFormState();
            }
        },
        wordToEdit(newWord) {
            if (newWord) {
                this.form = JSON.parse(JSON.stringify(newWord)); // Deep copy
            }
        }
    },
    methods: {
        getInitialFormState() {
            if (this.wordToEdit) {
                return JSON.parse(JSON.stringify(this.wordToEdit));
            }
            return {
                word: '',
                word_type: '',
                details: {
                    definition: '',
                    translation_en: '',
                    example: ''
                }
            };
        },
        close() {
            this.$emit('close');
        },
        async saveWord() {
            this.isSaving = true;
            this.error = null;

            const payload = {
                word: this.form.word,
                word_type: this.form.word_type,
                details: this.form.details
            };

            try {
                await axios.put(`/api/word-bank/words/${this.form.id}`, payload);
                this.$emit('word-saved');
                this.close();
            } catch (err) {
                this.error = 'An error occurred. Please try again.';
                console.error(err);
            } finally {
                this.isSaving = false;
            }
        },
    },
};
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
}

.modal-content {
    background: white;
    padding: 30px;
    border-radius: 10px;
    width: 90%;
    max-width: 500px;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #eee;
    padding-bottom: 15px;
    margin-bottom: 20px;
}

.close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
}

.modal-form .form-group {
    margin-bottom: 15px;
}

.modal-form label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

.modal-form input,
.modal-form select,
.modal-form textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
}

.form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
}

.btn-cancel,
.btn-save {
    padding: 10px 20px;
    border-radius: 5px;
    border: none;
    cursor: pointer;
}

.btn-save {
    background-color: #667eea;
    color: white;
}

.btn-cancel {
    background-color: #f0f0f0;
}
</style>
