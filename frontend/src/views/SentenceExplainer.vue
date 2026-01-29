<template>
  <div id="app" class="container">
    <header class="header">
      <router-link to="/" class="back-link">← Back to Home</router-link>
      <h1>📖 Sentence Explainer</h1>
      <p>Break down Dutch sentences into grammatical components</p>
      <div class="api-status">
        {{ apiHealth === 'healthy' ? '✅ Backend Connected' : '❌ Backend Offline' }}
      </div>
    </header>

    <main class="main">
      <div class="explainer-container">
        <div class="section input-section">
          <h2>Dutch Text</h2>
          <textarea 
            v-model="dutchText"
            placeholder="Enter Dutch text here..."
            class="textarea"
          ></textarea>
          <div class="controls">
            <div class="char-count">{{ dutchText.length }} characters</div>
            <button 
              @click="analyzeText" 
              :disabled="!dutchText.trim() || loading"
              class="analyze-button"
            >
              {{ loading ? '🔄 Analyzing...' : '▶ Analyze' }}
            </button>
          </div>
        </div>
      </div>
        <!-- Analysis Section -->
      <div class="explainer-container">
        <div class="section analysis-section">
          <h2>Grammatical Analysis</h2>
          
          <div v-if="loading" class="loading-state">
            <p>🔄 Analyzing text...</p>
          </div>

          <div v-else-if="error" class="error-state">
            <p>❌ {{ error }}</p>
          </div>

          <div v-else-if="dutchText.trim() === ''" class="empty-state">
            <p>Enter Dutch text on the left and click "Analyze" to see the results here</p>
          </div>

          <div v-else class="analysis-content">
            <!-- Sentences breakdown -->
            <div class="analysis-group">
              <h3>Sentences Found: {{ sentences.length }}</h3>
              <div v-for="(sentenceData, idx) in sentences" :key="idx" class="sentence-block">
                <div class="sentence-text">{{ sentenceData.sentence }}
                <button class="collapse-btn" @click="toggleCollapse(idx)">
                          {{ sentenceData.collapsed ? 'Show details ▼' : 'Hide details ▲' }}
                </button>
                </div>
                <!-- Loading state for individual sentence -->
                <div v-if="sentenceData.loading" class="sentence-loading">
                  <p>⏳ Analyzing this sentence...</p>
                </div>
                
                <!-- Error state for individual sentence -->
                <div v-else-if="sentenceData.error" class="sentence-error">
                  <p>❌ Failed to analyze: {{ sentenceData.error }}</p>
                </div>
                
                <!-- Success state -->
                <div v-else>

                  <p v-if="sentenceData.sentence_translation" class="sentence-translation" >
                    📝 {{ sentenceData.sentence_translation }}
                  
                  </p>
                  <div v-if="sentenceData.components.length > 0" v-show="!sentenceData.collapsed" class="components-list">
                    <div v-for="(comp, compIdx) in sentenceData.components" :key="compIdx" class="component-tag">
                      <div class="component-header">
                        <strong>{{ comp.type }}</strong>: {{ comp.value }}
                      </div>
                      <div v-if="comp.translation || comp.details" class="component-details">
                        <span v-if="comp.translation" class="detail-item">
                          <em>{{ comp.translation }}</em>
                        </span>
                        <span v-if="comp.details && Object.keys(comp.details).length > 0" class="detail-item">
                          {{ formatDetails(comp.details) }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="no-components">
                    <p>No components identified</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Summary -->
            <div class="analysis-group">
              <h3>Summary</h3>
              <div class="summary-stats">
                <div class="stat">
                  <span class="stat-label">Total Sentences</span>
                  <span class="stat-value">{{ sentences.length }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Total Characters</span>
                  <span class="stat-value">{{ dutchText.length }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Total Components</span>
                  <span class="stat-value">{{ totalComponents }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import axios from 'axios'
import { prepareSentences } from '@/utils/sentenceUtils'

const API_BASE_URL = 'http://localhost:8000'

export default {
  name: 'SentenceExplainer',
  data() {
    return {
      dutchText: '',
      analysis: null,
      loading: false,
      error: null,
      apiHealth: 'checking'
    }
  },
  computed: {
    sentences() {
      if (!this.analysis || !this.analysis.sentences) return []
      return this.analysis.sentences
    },
    totalComponents() {
      return this.sentences.reduce((total, sentence) => total + sentence.components.length, 0)
    }
  },
  methods: {
    formatDetails(details) {
      if (!details || typeof details !== 'object') return ''
      
      return Object.entries(details)
        .map(([key, value]) => {
          // Format key (e.g., 'verb-tense' -> 'Verb Tense')
          const formattedKey = key
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ')
          
          return `${formattedKey}: ${value}`
        })
        .join(' • ')
    },
    toggleCollapse(idx) {
        this.sentences[idx].collapsed = !this.sentences[idx].collapsed
    },
    async checkApiHealth() {
      try {
        const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 3000 })
        this.apiHealth = response.data.status === 'healthy' ? 'healthy' : 'unhealthy'
      } catch (error) {
        this.apiHealth = 'offline'
        console.warn('Backend health check failed:', error.message)
      }
    },
    async analyzeText() {
      if (!this.dutchText.trim()) {
        this.analysis = null
        this.error = null
        return
      }

      try {
        this.loading = true
        this.error = null
        
        // Step 1: Split and validate sentences on frontend
        const sentences = prepareSentences(this.dutchText)
        
        if (sentences.length === 0) {
          this.error = 'No valid sentences found. Please enter text with actual words.'
          this.loading = false
          return
        }
        
        // Step 2: Initialize analysis structure with loading states
        this.analysis = {
          sentences: sentences.map(sentence => ({
            sentence: sentence,
            sentence_translation: 'Analyzing...',
            components: [],
            collapsed: true,
            loading: true,
            error: null
          }))
        }
        
        // Step 3: Send ALL requests in parallel and update UI as each response arrives
        const analyzePromises = sentences.map((sentence, index) =>
          axios.post(`${API_BASE_URL}/api/analyze-sentence`, { sentence }, { timeout: 100000 })
            .then(response => {
              const data = response.data || {}
              // preserve the user's collapsed state if present
              const collapsed = this.analysis.sentences[index]?.collapsed ?? true

              // Replace the slot for this sentence so Vue reactivity picks up the change
              this.analysis.sentences.splice(index, 1, {
                sentence: data.sentence ?? sentence,
                sentence_translation: data.sentence_translation ?? '',
                components: data.components ?? [],
                collapsed,
                loading: false,
                error: null
              })
            })
            .catch(error => {
              const message = error.response?.data?.detail || error.message || 'Unknown error'
              if (this.analysis && this.analysis.sentences && this.analysis.sentences[index]) {
                this.analysis.sentences[index].error = message
                this.analysis.sentences[index].loading = false
              }
            })
        )

        // Step 4: Wait for all to settle so we can clear the overall loading indicator.
        // Note: individual updates already occurred in the per-promise handlers above,
        // so the UI will show results progressively as responses arrive.
        await Promise.allSettled(analyzePromises)
        
      } catch (err) {
        console.error('Analysis error:', err)
        if (err.response?.data?.detail) {
          this.error = `Failed to analyze text: ${err.response.data.detail}`
        } else if (err.message === 'Network Error') {
          this.error = 'Backend is not running. Make sure the server is started on http://localhost:8000'
        } else {
          this.error = `Failed to analyze text: ${err.message}`
        }
        this.analysis = null
      } finally {
        this.loading = false
      }
    }
  },
  mounted() {
    this.checkApiHealth()
    // Check health every 10 seconds
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
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  transition: background 0.3s;
}

.back-link:hover {
  background: rgba(255, 255, 255, 0.3);
}

.header h1 {
  font-size: 48px;
  margin-bottom: 10px;
}

.header p {
  font-size: 18px;
  opacity: 0.9;
  margin-bottom: 15px;
}

.api-status {
  font-size: 14px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  display: inline-block;
}

.main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 20px;
}

.explainer-container {
  display: grid;
  grid-template-rows: auto auto;
  gap: 20px;
  min-height: 300px;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 30px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.section h2 {
  color: #667eea;
  margin-bottom: 20px;
  font-size: 24px;
}

.input-section {
  position: relative;
}

.textarea {
  flex: 1;
  width: 100%;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  resize: none;
  transition: border-color 0.3s;
}

.textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.char-count {
  margin-top: 10px;
  font-size: 12px;
  color: #999;
}

.controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-top: 15px;
}

.analyze-button {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
}

.collapse-btn {
  background: none;
  border: none;
  color: #667eea;
  font-size: 12px;
  cursor: pointer;
  margin-left: 30px;
  font-weight: 600;
}

.analyze-button:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.analyze-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  opacity: 0.6;
}

.analysis-section {
  overflow-y: auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  text-align: center;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #667eea;
  text-align: center;
  font-size: 18px;
}

.error-state {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  padding: 15px;
  border-radius: 4px;
  color: #721c24;
}

.analysis-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.analysis-group {
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.analysis-group h3 {
  color: #667eea;
  margin-bottom: 15px;
  font-size: 16px;
}

.sentence-block {
  background: #f9f9f9;
  padding: 15px;
  border-left: 4px solid #667eea;
  border-radius: 4px;
  margin-bottom: 10px;
}

.sentence-text {
  color: #333;
  line-height: 1.6;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.sentence-translation {
  color: #667eea;
  line-height: 1.6;
  margin: 0 0 15px 0;
  font-size: 14px;
  font-style: italic;
  background: #f0f4ff;
  padding: 8px 12px;
  border-radius: 4px;
  border-left: 3px solid #667eea;
}

.components-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.component-tag {
  display: inline-block;
  background: #e8eef7;
  color: #667eea;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 12px;
  border: 1px solid #d0dce6;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.component-header {
  margin-bottom: 6px;
}

.component-tag strong {
  color: #667eea;
  font-weight: 600;
  display: block;
  margin-bottom: 3px;
}

.component-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 6px;
  border-top: 1px solid #d0dce6;
}

.detail-item {
  font-size: 11px;
  color: #555;
  line-height: 1.4;
}

.no-components {
  color: #999;
  font-size: 12px;
  font-style: italic;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.stat {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 4px;
  border: 1px solid #ddd;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #667eea;
  font-weight: 600;
  margin-bottom: 8px;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #333;
}

.sentence-loading {
  background: #e7f3ff;
  border-left: 4px solid #1890ff;
  padding: 12px;
  border-radius: 4px;
  margin-top: 10px;
  animation: pulse 1.5s ease-in-out infinite;
}

.sentence-loading p {
  color: #1890ff;
  font-size: 14px;
  margin: 0;
  font-weight: 500;
}

.sentence-error {
  background: #fff5f5;
  border-left: 4px solid #ff4d4f;
  padding: 12px;
  border-radius: 4px;
  margin-top: 10px;
}

.sentence-error p {
  color: #ff4d4f;
  font-size: 13px;
  margin: 0;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Responsive design */
@media (max-width: 1024px) {
  .explainer-container {
    grid-template-columns: 1fr;
  }

  .section {
    min-height: 300px;
  }
}
</style>
