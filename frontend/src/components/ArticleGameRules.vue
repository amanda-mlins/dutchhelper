<template>
    <div class="rules-section">
        <div class="rules-header">
            <h2>De vs Het: Dutch Article Rules</h2>
            <button @click="toggleRules" class="toggle-button" :class="{ open: showRules }">
                <span class="toggle-icon">{{ showRules ? '▼' : '▶' }}</span>
                {{ showRules ? 'Hide Rules' : 'Show Rules' }}
            </button>
        </div>

        <div v-if="showRules" class="rules-content">
            <!-- Common Words -->
            <div class="rule-category">
                <h3>🎯 Common Patterns - DE</h3>
                <ul>
                    <li>
                        <strong>People/Professions:</strong> Nouns for people are almost always 'de'.<br>
                        <em>Examples: de man (man), de vrouw (woman), de leraar (teacher), de bakker (baker)</em>
                    </li>
                    <li>
                        <strong>Plural Nouns:</strong> All plural nouns use 'de', without exception.<br>
                        <em>Examples: de boeken (the books), de huizen (the houses)</em>
                    </li>
                    <li>
                        <strong>Nouns ending in -ing, -heid, -ij, -ie, -iek, -teit, -tuur:</strong><br>
                        <em>-ing: de rekening (the bill)</em><br>
                        <em>-heid: de waarheid (the truth)</em><br>
                        <em>-ij: de bakkerij (the bakery)</em><br>
                        <em>-ie: de politie (the police)</em><br>
                        <em>-iek: de muziek (the music)</em><br>
                        <em>-teit: de universiteit (the university)</em>
                    </li>
                    <li>
                        <strong>Fruits, Vegetables, Trees & Plants:</strong> Most are 'de'.<br>
                        <em>Examples: de appel (the apple), de banaan (the banana), de eik (the oak tree)</em>
                    </li>
                </ul>
            </div>

            <!-- Het Words -->
            <div class="rule-category">
                <h3>🎯 Common Patterns - HET</h3>
                <ul>
                    <li>
                        <strong>Diminutives (-je, -tje, -pje, etc.):</strong> All diminutives are 'het', without
                        exception.<br>
                        <em>Examples: het huisje (the little house), het meisje (the girl), het boompje (the little
                            tree)</em>
                    </li>
                    <li>
                        <strong>Infinitives as Nouns:</strong> Verbs used as nouns are always 'het'.<br>
                        <em>Examples: het lezen (the reading), het schrijven (the writing)</em>
                    </li>
                    <li>
                        <strong>Nouns ending in -isme, -ment, -sel, -um:</strong><br>
                        <em>-isme: het kapitalisme (capitalism)</em><br>
                        <em>-ment: het document (the document)</em><br>
                        <em>-sel: het mengsel (the mixture)</em><br>
                        <em>-um: het museum (the museum)</em>
                    </li>
                    <li>
                        <strong>Two-Syllable Nouns starting with be-, ge-, ver-, ont-:</strong><br>
                        <em>Examples: het gebouw (the building), het verhaal (the story), het begin (the beginning)</em>
                    </li>
                    <li>
                        <strong>Metals & Materials:</strong><br>
                        <em>Examples: het goud (gold), het zilver (silver), het hout (wood)</em>
                    </li>
                </ul>
            </div>

            <!-- Tips -->
            <div class="rule-category tips">
                <h3>💡 Helpful Tips</h3>
                <ul>
                    <li>
                        <strong>Memorize the exceptions:</strong> While rules are helpful, Dutch has many exceptions.
                        Practice is key!
                    </li>
                    <li>
                        <strong>Listen to native speakers:</strong> Hearing the article pronounced helps build
                        intuition.
                    </li>
                    <li>
                        <strong>The diminutive rule is your best friend:</strong> If it ends in -je, -tje, etc., it's
                        ALWAYS 'het'.
                    </li>
                    <li>
                        <strong>When in doubt, guess 'de':</strong> About 2/3 of Dutch nouns use 'de'.
                    </li>
                    <li>
                        <strong>Plural is always 'de':</strong> This rule has no exceptions.
                    </li>
                </ul>
            </div>

            <!-- Quick Reference -->
            <div class="quick-reference">
                <div class="ref-card">
                    <h4>DE Articles</h4>
                    <p class="stat">~65-75% of nouns</p>
                    <p class="examples">man, vrouw, tafel, rekening, politie, muziek</p>
                </div>
                <div class="ref-card">
                    <h4>HET Articles</h4>
                    <p class="stat">~25-35% of nouns</p>
                    <p class="examples">kind, meisje, huis, gebouw, document, museum</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ArticleGameRules',
    data() {
        return {
            showRules: false
        };
    },
    methods: {
        toggleRules() {
            this.showRules = !this.showRules;
        }
    }
};
</script>

<style scoped>
.rules-section {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 30px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.rules-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
}

.rules-header h2 {
    font-size: 22px;
    margin: 0;
    color: #333;
}

.toggle-button {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    color: #666;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
}

.toggle-button:hover {
    background: #e9ecef;
    border-color: #adb5bd;
}

.toggle-icon {
    display: inline-block;
    transition: transform 0.3s ease;
}

.toggle-button.open .toggle-icon {
    transform: rotate(0deg);
}

.rules-content {
    margin-top: 20px;
    animation: slideDown 0.3s ease;
}

@keyframes slideDown {
    from {
        opacity: 0;
        max-height: 0;
        overflow: hidden;
    }

    to {
        opacity: 1;
        max-height: 2000px;
        overflow: visible;
    }
}

.rule-category {
    margin-bottom: 25px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border-left: 4px solid #007bff;
}

.rule-category h3 {
    margin-top: 0;
    margin-bottom: 15px;
    font-size: 16px;
    color: #333;
}

.rule-category ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.rule-category li {
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e9ecef;
    line-height: 1.6;
    color: #555;
}

.rule-category li:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.rule-category strong {
    color: #333;
}

.rule-category em {
    color: #007bff;
    font-style: italic;
    font-weight: 500;
}

.rule-category.tips {
    border-left-color: #ffc107;
}

.quick-reference {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
    margin-top: 20px;
}

.ref-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    border: 2px solid #e9ecef;
    text-align: center;
}

.ref-card h4 {
    margin: 0 0 10px 0;
    font-size: 16px;
    color: #333;
}

.ref-card .stat {
    font-size: 18px;
    font-weight: bold;
    color: #007bff;
    margin: 10px 0 5px 0;
}

.ref-card .examples {
    font-size: 13px;
    color: #666;
    margin: 5px 0 0 0;
    line-height: 1.5;
}

/* Responsive */
@media (max-width: 768px) {
    .rules-header {
        flex-direction: column;
        align-items: flex-start;
    }

    .quick-reference {
        grid-template-columns: 1fr;
    }
}
</style>
