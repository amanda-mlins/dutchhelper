<template>
    <div class="word-card">
        <div class="card-header">
            <h3>{{ word.word }}</h3>
            <span class="word-type">{{ word.word_type }}</span>
        </div>
        <div class="card-body">
            <p><strong>Definition:</strong> {{ word.details.definition }}</p>
            <p><strong>Translation:</strong> {{ word.details.translation_en }}</p>
            <p><strong>Example:</strong> <em>{{ word.details.example }}</em></p>
        </div>
        <div class="card-footer">
            <button @click="$emit('edit', word)" class="icon-btn edit-btn">
                <i class="fas fa-pencil-alt"></i>
            </button>
            <button @click="$emit('delete', word.id)" class="icon-btn delete-btn">
                <i class="fas fa-trash-alt"></i>
            </button>
        </div>
    </div>
</template>

<script>
export default {
    name: 'WordCard',
    props: {
        word: {
            type: Object,
            required: true,
        },
    },
};
</script>

<style scoped>
.word-card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    padding: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
    margin-bottom: 15px;
}

.card-header h3 {
    margin: 0;
    font-size: 22px;
    color: #667eea;
}

.word-type {
    background-color: #f0f0f0;
    color: #555;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
}

.card-body p {
    margin: 10px 0;
    color: #444;
}

.card-body strong {
    color: #333;
}

.card-footer {
    margin-top: auto;
    padding-top: 15px;
    border-top: 1px solid #eee;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

.icon-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
    color: #888;
    transition: color 0.3s;
}

.edit-btn:hover {
    color: #667eea;
}

.delete-btn:hover {
    color: #e74c3c;
}
</style>
