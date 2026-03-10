<template>
    <!--
        WordBankButton — add a single word to the user's word bank.

        Props:
          word            (String, required)  – the Dutch word to save
          wordType        (String, default "word") – noun/verb/adjective/conjunction/word
          category        (String, optional)  – category tag in the word bank
          contextSentence (String, optional)  – example sentence shown in the bank
          initialSaved    (Boolean, default false) – pre-mark as already saved

        Emits:
          saved(word)   – after a successful add
    -->
    <button class="wb-btn" :class="stateClass" :title="tooltip"
        :disabled="state === 'saving' || state === 'saved' || state === 'skipped'" @click.stop="save">
        <span class="wb-icon">{{ icon }}</span>
        <span class="wb-label">{{ label }}</span>
    </button>
</template>

<script setup>
import { ref, computed } from 'vue'
import { authAxios } from '../stores/auth.js'

const props = defineProps({
    word: { type: String, required: true },
    wordType: { type: String, default: 'word' },
    category: { type: String, default: null },
    contextSentence: { type: String, default: null },
    initialSaved: { type: Boolean, default: false },
})

const emit = defineEmits(['saved'])

// states: idle | saving | saved | skipped | error
const state = ref(props.initialSaved ? 'saved' : 'idle')

const stateClass = computed(() => `wb-btn--${state.value}`)

const icon = computed(() => {
    if (state.value === 'saving') return '⟳'
    if (state.value === 'saved') return '✓'
    if (state.value === 'skipped') return '✓'
    if (state.value === 'error') return '!'
    return '+'
})

const label = computed(() => {
    if (state.value === 'saving') return 'Saving…'
    if (state.value === 'saved') return 'Saved'
    if (state.value === 'skipped') return 'In bank'
    if (state.value === 'error') return 'Error'
    return 'Save'
})

const tooltip = computed(() => {
    if (state.value === 'saved') return `"${props.word}" added to your Word Bank`
    if (state.value === 'skipped') return `"${props.word}" is already in your Word Bank`
    if (state.value === 'error') return 'Could not save — try again later'
    return `Add "${props.word}" to your Word Bank`
})

async function save() {
    if (state.value !== 'idle' && state.value !== 'error') return
    state.value = 'saving'
    try {
        const { data } = await authAxios.post('/api/word-bank/words/quick', {
            word: props.word,
            word_type: props.wordType,
            category: props.category,
            context_sentence: props.contextSentence,
        })
        state.value = data.status === 'skipped' ? 'skipped' : 'saved'
        if (data.status !== 'skipped') emit('saved', props.word)
    } catch {
        state.value = 'error'
        // Auto-reset after 3 s so the user can retry
        setTimeout(() => { if (state.value === 'error') state.value = 'idle' }, 3000)
    }
}
</script>

<style scoped>
.wb-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1.5px solid #cbd5e0;
    background: #fff;
    color: #4a5568;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
    white-space: nowrap;
    vertical-align: middle;
}

.wb-btn:hover:not(:disabled) {
    background: #667eea;
    border-color: #667eea;
    color: #fff;
}

.wb-btn--saving {
    opacity: 0.6;
    cursor: default;
}

.wb-btn--saved {
    background: #c6f6d5;
    border-color: #68d391;
    color: #276749;
    cursor: default;
}

.wb-btn--skipped {
    background: #e2e8f0;
    border-color: #cbd5e0;
    color: #718096;
    cursor: default;
}

.wb-btn--error {
    background: #fff5f5;
    border-color: #fc8181;
    color: #c53030;
}

.wb-icon {
    font-size: 13px;
    line-height: 1;
}

.wb-label {
    line-height: 1;
}
</style>
