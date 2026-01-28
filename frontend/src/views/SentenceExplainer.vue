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

        <!-- Analysis Section -->
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
                <p class="sentence-text">{{ sentenceData.sentence }}</p>
                <div v-if="sentenceData.components.length > 0" class="components-list">
                  <span v-for="(comp, compIdx) in sentenceData.components" :key="compIdx" class="component-tag">
                    <strong>{{ comp.type }}</strong>: {{ comp.value }}
                  </span>
                </div>
                <div v-else class="no-components">
                  <p>No components identified</p>
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
        
        const response = await axios.post(`${API_BASE_URL}/api/analyze`, {
          text: this.dutchText
        }, { timeout: 30000 })
        
        this.analysis = response.data
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
    setInterval(() => this.checkApiHealth(), 10000)
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
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  min-height: 500px;
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
  margin: 0 0 10px 0;
  font-weight: 500;
}

.components-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.component-tag {
  display: inline-block;
  background: #e8eef7;
  color: #667eea;
  padding: 6px 10px;
  border-radius: 3px;
  font-size: 12px;
  border: 1px solid #d0dce6;
}

.component-tag strong {
  color: #667eea;
  font-weight: 600;
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
