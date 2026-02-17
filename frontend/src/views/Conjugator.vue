<template>
    <div class="container">
        <header class="header">
            <router-link to="/" class="back-link">← Back to Home</router-link>
            <h1>🇳🇱 Dutch Verb Conjugator</h1>
            <p>Conjugate Dutch verbs in all tenses and persons</p>
        </header>

        <main class="main">
            <!-- Input Section -->
            <section class="section input-section">
                <div class="input-container">
                    <input v-model="inputVerb" type="text"
                        placeholder="Enter a Dutch verb (e.g., 'zijn', 'hebben', 'gaan')" class="verb-input"
                        @keyup.enter="conjugateVerb" />
                    <button @click="conjugateVerb" class="search-button" :disabled="loading">
                        {{ loading ? 'Conjugating...' : 'Conjugate' }}
                    </button>
                </div>
            </section>

            <!-- Error Message -->
            <section v-if="error" class="section error-section">
                <p class="error-text">{{ error }}</p>
            </section>

            <!-- Loading State -->
            <section v-if="loading" class="section loading-section">
                <div class="spinner"></div>
                <p>Conjugating verb...</p>
            </section>

            <!-- Conjugation Results -->
            <section v-if="conjugation && !loading" class="section results-section">
                <!-- Verb Information Header -->
                <div class="verb-header">
                    <h2>{{ conjugation.infinitive }}</h2>
                    <p class="english-translation">English: {{ conjugation.englishTranslation }}</p>
                </div>

                <!-- Verb Metadata (Separable, Type, Preposition, etc.) -->
                <div v-if="hasVerbMetadata" class="verb-metadata">
                    <div class="metadata-grid">
                        <div v-if="conjugation.verbType" class="metadata-item">
                            <span class="metadata-label">Verb Type:</span>
                            <span class="metadata-value">{{ conjugation.verbType }}</span>
                        </div>
                        <div v-if="conjugation.separable" class="metadata-item">
                            <span class="metadata-label">Separable:</span>
                            <span class="metadata-value" :class="{ 'is-separable': conjugation.separable === 'yes' }">
                                {{ conjugation.separable }}
                            </span>
                        </div>
                        <div v-if="conjugation.separation" class="metadata-item">
                            <span class="metadata-label">Separated as:</span>
                            <span class="metadata-value">{{ conjugation.separation }}</span>
                        </div>
                        <div v-if="conjugation.preposition" class="metadata-item">
                            <span class="metadata-label">Preposition:</span>
                            <span class="metadata-value">{{ conjugation.preposition }}</span>
                        </div>
                    </div>

                    <!-- Synonyms -->
                    <div v-if="conjugation.synonyms && conjugation.synonyms.length > 0" class="related-words">
                        <h4>Synonyms</h4>
                        <div class="word-tags">
                            <span v-for="(syn, idx) in conjugation.synonyms" :key="`syn-${idx}`"
                                class="word-tag synonym-tag">
                                <router-link :to="`/conjugator/${syn}`">{{ syn
                                    }}</router-link>
                            </span>
                        </div>
                    </div>

                    <!-- Antonyms -->
                    <div v-if="conjugation.antonyms && conjugation.antonyms.length > 0" class="related-words">
                        <h4>Antonyms</h4>
                        <div class="word-tags">
                            <span v-for="(ant, idx) in conjugation.antonyms" :key="`ant-${idx}`"
                                class="word-tag antonym-tag">
                                <router-link :to="`/conjugator/${ant}`">{{ ant }}</router-link>
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Conjugation Tables -->
                <div class="conjugation-tables">
                    <!-- Present Tense -->
                    <div class="tense-table">
                        <h3 class="tense-title">
                            {{ conjugation.tenses[0]?.dutchName }} <span class="english-name">(Present)</span>
                        </h3>
                        <table class="conjugation-table">
                            <tbody>
                                <tr v-for="(form, index) in conjugation.tenses[0]?.forms" :key="`present-${index}`">
                                    <td class="person-label">{{ form.person }}</td>
                                    <td class="conjugated-form">{{ form.conjugation }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Simple Past (Imperfect) -->
                    <div class="tense-table">
                        <h3 class="tense-title">
                            {{ conjugation.tenses[1]?.dutchName }} <span class="english-name">(Simple Past)</span>
                        </h3>
                        <table class="conjugation-table">
                            <tbody>
                                <tr v-for="(form, index) in conjugation.tenses[1]?.forms" :key="`past-${index}`">
                                    <td class="person-label">{{ form.person }}</td>
                                    <td class="conjugated-form">{{ form.conjugation }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Present Perfect -->
                    <div class="tense-table">
                        <h3 class="tense-title">
                            {{ conjugation.tenses[2]?.dutchName }} <span class="english-name">(Present Perfect)</span>
                        </h3>
                        <table class="conjugation-table">
                            <tbody>
                                <tr v-for="(form, index) in conjugation.tenses[2]?.forms"
                                    :key="`present-perfect-${index}`">
                                    <td class="person-label">{{ form.person }}</td>
                                    <td class="conjugated-form">{{ form.conjugation }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Past Perfect -->
                    <div class="tense-table">
                        <h3 class="tense-title">
                            {{ conjugation.tenses[3]?.dutchName }} <span class="english-name">(Past Perfect)</span>
                        </h3>
                        <table class="conjugation-table">
                            <tbody>
                                <tr v-for="(form, index) in conjugation.tenses[3]?.forms"
                                    :key="`past-perfect-${index}`">
                                    <td class="person-label">{{ form.person }}</td>
                                    <td class="conjugated-form">{{ form.conjugation }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Future Simple -->
                    <div class="tense-table">
                        <h3 class="tense-title">
                            {{ conjugation.tenses[4]?.dutchName }} <span class="english-name">(Future Simple)</span>
                        </h3>
                        <table class="conjugation-table">
                            <tbody>
                                <tr v-for="(form, index) in conjugation.tenses[4]?.forms" :key="`future-${index}`">
                                    <td class="person-label">{{ form.person }}</td>
                                    <td class="conjugated-form">{{ form.conjugation }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Conditional -->
                    <div class="tense-table">
                        <h3 class="tense-title">
                            {{ conjugation.tenses[5]?.dutchName }} <span class="english-name">(Conditional)</span>
                        </h3>
                        <table class="conjugation-table">
                            <tbody>
                                <tr v-for="(form, index) in conjugation.tenses[5]?.forms" :key="`conditional-${index}`">
                                    <td class="person-label">{{ form.person }}</td>
                                    <td class="conjugated-form">{{ form.conjugation }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- Usage Examples -->
            <section v-if="conjugation && !loading && conjugation.examples" class="section examples-section">
                <h2>Usage Examples</h2>
                <div class="examples-list">
                    <div v-for="(example, index) in conjugation.examples" :key="`example-${index}`"
                        class="example-card">
                        <p class="example-dutch">{{ example.dutch }}</p>
                        <p class="example-english">{{ example.english }}</p>
                        <p class="example-tense" v-if="example.tense">{{ example.tense }}</p>
                    </div>
                </div>
            </section>

            <!-- Common Verbs Suggestion -->
            <section class="section suggestion-section">
                <h3>Popular Dutch Verbs to Try</h3>
                <div class="common-verbs">
                    <button v-for="verb in commonVerbs" :key="verb" @click="inputVerb = verb; conjugateVerb()"
                        class="verb-button">
                        {{ verb }}
                    </button>
                </div>
            </section>
        </main>
    </div>
</template>

<script>
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default {
    name: 'Conjugator',
    data() {
        return {
            inputVerb: '',
            conjugation: null,
            loading: false,
            error: null,
            commonVerbs: ['zijn', 'hebben', 'gaan', 'maken', 'doen', 'zeggen', 'kijken', 'werken', 'wonen', 'eten'],
            apiHealth: 'offline'
        }
    },
    computed: {
        isEmpty() {
            return !this.inputVerb || this.inputVerb.trim().length === 0
        },
        hasVerbMetadata() {
            if (!this.conjugation) return false
            return !!(
                this.conjugation.verbType ||
                this.conjugation.separable ||
                this.conjugation.separation ||
                this.conjugation.preposition ||
                (this.conjugation.synonyms && this.conjugation.synonyms.length > 0) ||
                (this.conjugation.antonyms && this.conjugation.antonyms.length > 0)
            )
        }
    },
    methods: {
        async conjugateVerb() {
            // Reset previous state
            this.error = null
            this.conjugation = null

            // Validate input
            if (this.isEmpty) {
                this.error = 'Please enter a Dutch verb'
                return
            }

            try {
                this.loading = true

                // Call the backend conjugation endpoint
                const response = await axios.post(
                    `${API_BASE_URL}/api/conjugate`,
                    { verb: this.inputVerb.trim().toLowerCase() },
                    { timeout: 30000 }
                )

                if (response.data) {
                    this.conjugation = response.data
                    // Clear input after successful conjugation
                    this.inputVerb = ''
                }
            } catch (err) {
                console.error('Conjugation error:', err)

                if (err.response?.data?.detail) {
                    this.error = err.response.data.detail
                } else if (err.message === 'Network Error') {
                    this.error = 'Backend is not running. Make sure the server is started on http://localhost:8000'
                } else if (err.response?.status === 404) {
                    this.error = `Verb "${this.inputVerb}" not found. Try with a common Dutch verb.`
                } else {
                    this.error = `Error: ${err.message}`
                }
            } finally {
                this.loading = false
            }
        },

        checkApiHealth() {
            try {
                axios.get(`${API_BASE_URL}/health`, { timeout: 3000 }).then(response => {
                    this.apiHealth = response.data.status === 'healthy' ? 'healthy' : 'unhealthy'
                })
            } catch (error) {
                this.apiHealth = 'offline'
                console.warn('Backend health check failed:', error.message)
            }
        }
    },
    watch: {
        // Watch for route changes (when user clicks synonym/antonym links)
        '$route.params.verb': function (newVerb) {
            if (newVerb) {
                this.inputVerb = newVerb
                this.$nextTick(() => {
                    this.conjugateVerb()
                })
            }
        },
        '$route.query.verb': function (newVerb) {
            if (newVerb) {
                this.inputVerb = newVerb
                this.$nextTick(() => {
                    this.conjugateVerb()
                })
            }
        }
    },
    mounted() {
        // Check for verb from both path parameter and query parameter
        // Priority: path parameter (/conjugator/zijn) > query parameter (?verb=zijn)
        let verbToConjugate = null

        // Check path parameter first (e.g., /conjugator/zijn)
        if (this.$route.params.verb) {
            verbToConjugate = this.$route.params.verb
        }
        // Fallback to query parameter (e.g., /conjugator?verb=zijn)
        else if (this.$route.query.verb) {
            verbToConjugate = this.$route.query.verb
        }

        if (verbToConjugate) {
            this.inputVerb = verbToConjugate
            this.$nextTick(() => {
                this.conjugateVerb()
            })
        }

        // Check API health
        this.checkApiHealth()
        setInterval(() => this.checkApiHealth(), 300000)
    }
}
</script>

<style scoped>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

.container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

.header {
    background: rgba(0, 0, 0, 0.3);
    color: white;
    padding: 40px 20px;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.back-link {
    display: inline-block;
    color: white;
    text-decoration: none;
    margin-bottom: 20px;
    font-size: 16px;
    opacity: 0.9;
    transition: opacity 0.3s;
}

.back-link:hover {
    opacity: 1;
}

.header h1 {
    font-size: 48px;
    margin-bottom: 10px;
}

.header p {
    font-size: 18px;
    opacity: 0.9;
}

.main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
}

.section {
    background: white;
    border-radius: 8px;
    padding: 30px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* Input Section */
.input-section {
    margin-bottom: 30px;
}

.input-container {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.verb-input {
    flex: 1;
    min-width: 200px;
    padding: 14px 18px;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    font-size: 16px;
    font-family: inherit;
    transition: border-color 0.3s;
}

.verb-input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-button {
    padding: 14px 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

.search-button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
}

.search-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
}

/* Error Section */
.error-section {
    background: #fee;
    border-left: 4px solid #f66;
}

.error-text {
    color: #c33;
    font-size: 16px;
}

/* Loading State */
.loading-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 20px;
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(360deg);
    }
}

.loading-section p {
    color: #667eea;
    font-size: 18px;
}

/* Results Section */
.results-section {
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.verb-header {
    text-align: center;
    margin-bottom: 40px;
    padding-bottom: 20px;
    border-bottom: 2px solid #f0f0f0;
}

.verb-header h2 {
    font-size: 36px;
    color: #333;
    margin-bottom: 8px;
    font-weight: 600;
}

.english-translation {
    color: #888;
    font-size: 16px;
    font-style: italic;
}

.conjugation-tables {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}

.tense-table {
    background: #f9f9f9;
    border-radius: 8px;
    padding: 20px;
    border: 1px solid #e0e0e0;
}

.tense-title {
    color: #667eea;
    font-size: 18px;
    margin-bottom: 15px;
    font-weight: 600;
    border-bottom: 2px solid #667eea;
    padding-bottom: 10px;
}

.english-name {
    color: #999;
    font-size: 14px;
    font-weight: 400;
    margin-left: 8px;
}

.conjugation-table {
    width: 100%;
    border-collapse: collapse;
}

.conjugation-table tr {
    border-bottom: 1px solid #e0e0e0;
}

.conjugation-table tr:last-child {
    border-bottom: none;
}

.person-label {
    padding: 10px 0;
    color: #666;
    font-weight: 500;
    width: 35%;
    vertical-align: top;
}

.conjugated-form {
    padding: 10px 15px;
    color: #333;
    font-weight: 600;
    font-family: 'Courier New', monospace;
    background: white;
    border-radius: 4px;
    margin-left: 10px;
}

/* Examples Section */
.examples-section {
    background: linear-gradient(135deg, #f5f7ff 0%, #f0f4ff 100%);
    border: 1px solid #e0e8ff;
}

.examples-section h2 {
    color: #667eea;
    margin-bottom: 20px;
    font-size: 24px;
}

.examples-list {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 15px;
}

.example-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #667eea;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.example-dutch {
    color: #333;
    font-weight: 600;
    font-size: 16px;
    margin-bottom: 8px;
    line-height: 1.5;
}

.example-english {
    color: #666;
    font-size: 14px;
    margin-bottom: 10px;
    line-height: 1.5;
}

.example-tense {
    color: #999;
    font-size: 12px;
    font-style: italic;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #f0f0f0;
}

/* Suggestion Section */
.suggestion-section {
    background: linear-gradient(135deg, #fff5f5 0%, #fff0f5 100%);
    border: 1px solid #ffe0e8;
}

.suggestion-section h3 {
    color: #764ba2;
    margin-bottom: 20px;
    font-size: 20px;
}

.common-verbs {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.verb-button {
    padding: 10px 18px;
    background: white;
    color: #667eea;
    border: 2px solid #667eea;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s;
}

.verb-button:hover {
    background: #667eea;
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

/* Verb Metadata Styles */
.verb-metadata {
    background: linear-gradient(135deg, #f5f7ff 0%, #ede7f6 100%);
    padding: 20px;
    border-radius: 8px;
    margin-top: 10px;
    margin-bottom: 10px;
    border-left: 4px solid #667eea;
}

.metadata-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.metadata-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.metadata-label {
    font-size: 12px;
    font-weight: 700;
    color: #667eea;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metadata-value {
    font-size: 15px;
    color: #333;
    font-weight: 500;
    padding: 6px 10px;
    background: white;
    border-radius: 4px;
}

.metadata-value.is-separable {
    background: #c7d2e8;
    color: #5b21b6;
    font-weight: 600;
}

.related-words {
    margin-top: 15px;
}

.related-words h4 {
    font-size: 13px;
    font-weight: 700;
    color: #667eea;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.word-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.word-tag {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
}

.word-tag a {
    color: inherit;
    text-decoration: none;
    display: inline;
    cursor: pointer;
    transition: opacity 0.2s;
}

.word-tag a:hover {
    opacity: 0.8;
    text-decoration: underline;
}

.synonym-tag {
    background: #c7e9c0;
    color: #2d5016;
    border: 1px solid #a8d5a8;
}

.antonym-tag {
    background: #f4c2c2;
    color: #6b1b1b;
    border: 1px solid #e8a8a8;
}

/* Responsive Design */
@media (max-width: 768px) {
    .header h1 {
        font-size: 32px;
    }

    .verb-header h2 {
        font-size: 24px;
    }

    .conjugation-tables {
        grid-template-columns: 1fr;
    }

    .input-container {
        flex-direction: column;
    }

    .verb-input,
    .search-button {
        width: 100%;
    }

    .examples-list {
        grid-template-columns: 1fr;
    }
}
</style>
