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
          <textarea v-model="dutchText" placeholder="Enter Dutch text here..." class="textarea"></textarea>
          <div class="controls">
            <div class="char-count">{{ dutchText.length }} characters</div>
            <button @click="analyzeText" :disabled="!dutchText.trim() || loading" class="analyze-button">
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
            <p>🔄 Analyzing text... <strong>{{ pendingCount }} / {{ totalSentences }} remaining</strong></p>
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
                <div class="sentence-text">
                  <span v-for="(seg, sidx) in getSentenceSegments(sentenceData, idx)" :key="sidx">
                    <span v-if="seg.compId" class="sentence-word" :class="{ highlight: hovered === seg.compId }"
                      @mouseenter="setHover(seg.compId)" @mouseleave="clearHover">
                      {{ seg.text }}
                    </span>
                    <span v-else>{{ seg.text }}</span>
                  </span>
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

                  <p v-if="sentenceData.sentence_translation" class="sentence-translation">
                    📝
                    <span v-for="(seg, tsidx) in getTranslationSegments(sentenceData, idx)" :key="tsidx"
                      :class="{ 'translation-highlight': seg.compId && hovered === seg.compId }">
                      {{ seg.text }}
                    </span>
                  </p>
                  <div class="sentence-meta">
                    <span v-if="sentenceData.justCompleted" class="completed-badge">✓</span>
                    <span v-if="sentenceData.completedAt" class="completed-time">Completed at {{
                      formatTime(sentenceData.completedAt) }}</span>
                  </div>
                  <div v-if="sentenceData.components.length > 0" v-show="!sentenceData.collapsed"
                    class="components-list">
                    <div v-for="(comp, compIdx) in sentenceData.components" :key="compIdx" class="component-tag"
                      :class="{ highlight: hovered === ('s' + idx + '-c' + compIdx) }"
                      @mouseenter="setHover('s' + idx + '-c' + compIdx)" @mouseleave="clearHover">
                      <div class="component-header">
                        <strong>{{ comp.type }}</strong>:
                        <router-link v-if="comp.type === 'verb'"
                          :to="{ name: 'ConjugatorWithVerb', params: { verb: comp.value } }" class="verb-link"
                          title="Click to view verb conjugations">
                          {{ comp.value }}
                        </router-link>
                        <span v-else>{{ comp.value }}</span>
                      </div>
                      <div v-if="comp.translation || comp.details" class="component-details">
                        <span v-if="comp.translation" class="detail-item"
                          :class="{ highlight: hovered === ('s' + idx + '-c' + compIdx) }">
                          <em>{{ comp.translation }}</em>
                        </span>
                        <span v-if="comp.details && Object.keys(comp.details).length > 0" class="detail-item"
                          :class="{ highlight: hovered === ('s' + idx + '-c' + compIdx) }"> {{
                            formatDetails(comp.details) }}
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
      , hovered: null
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
    ,
    // Number of sentences still being processed
    pendingCount() {
      return this.sentences.filter(s => s.loading).length
    },
    totalSentences() {
      return this.sentences.length
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
    formatTime(iso) {
      try {
        const d = new Date(iso)
        return d.toLocaleTimeString()
      } catch (e) {
        return iso
      }
    },
    // Hover/state helpers
    setHover(id) {
      this.hovered = id
    },
    clearHover() {
      this.hovered = null
    },
    // Build sentence segments and tag substrings that match component values.
    getSentenceSegments(sentenceData, sentenceIdx) {
      const text = sentenceData.sentence || ''
      const comps = sentenceData.components || []
      if (!comps.length) return [{ text }]

      const lower = text.toLowerCase()
      const ranges = []

      // Find non-overlapping occurrences for each component value
      comps.forEach((comp, compIdx) => {
        const val = (comp.value || '').toString()
        if (!val) return
        const search = val.toLowerCase()
        let start = 0
        while (true) {
          const pos = lower.indexOf(search, start)
          if (pos === -1) break
          const end = pos + search.length
          // check overlap
          const overlap = ranges.some(r => !(end <= r.start || pos >= r.end))
          if (!overlap) {
            ranges.push({ start: pos, end, compIdx })
            break
          }
          start = pos + 1
        }
      })

      if (!ranges.length) return [{ text }]

      ranges.sort((a, b) => a.start - b.start)
      const parts = []
      let last = 0
      ranges.forEach(r => {
        if (r.start > last) parts.push({ text: text.slice(last, r.start) })
        parts.push({ text: text.slice(r.start, r.end), compId: 's' + sentenceIdx + '-c' + r.compIdx })
        last = r.end
      })
      if (last < text.length) parts.push({ text: text.slice(last) })
      return parts
    },
    getTranslationSegments(sentenceData, sentenceIdx) {
      const translation = sentenceData.sentence_translation || ''
      const comps = sentenceData.components || []
      if (!comps.length) return [{ text: translation }]

      // Build a map of component index to its translation
      const compTranslations = {}
      comps.forEach((comp, compIdx) => {
        if (comp.translation) {
          compTranslations[compIdx] = comp.translation.toLowerCase()
        }
      })

      // Find non-overlapping occurrences of component translations in the translation text
      const translationLower = translation.toLowerCase()
      const ranges = []

      Object.entries(compTranslations).forEach(([compIdx, compTranslation]) => {
        const search = compTranslation.trim()
        if (!search) return
        let start = 0
        while (true) {
          const pos = translationLower.indexOf(search, start)
          if (pos === -1) break
          const end = pos + search.length
          // check overlap
          const overlap = ranges.some(r => !(end <= r.start || pos >= r.end))
          if (!overlap) {
            ranges.push({ start: pos, end, compIdx })
            break
          }
          start = pos + 1
        }
      })

      if (!ranges.length) return [{ text: translation }]

      ranges.sort((a, b) => a.start - b.start)
      const parts = []
      let last = 0
      ranges.forEach(r => {
        if (r.start > last) parts.push({ text: translation.slice(last, r.start) })
        parts.push({ text: translation.slice(r.start, r.end), compId: 's' + sentenceIdx + '-c' + r.compIdx })
        last = r.end
      })
      if (last < translation.length) parts.push({ text: translation.slice(last) })
      return parts
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

        // Step 1: Split sentences using backend's robust pysbd (fast, no LLM needed)
        // This returns immediately so we can show sentences and start loading states
        const splitResponse = await axios.post(`${API_BASE_URL}/api/split-sentences`,
          { text: this.dutchText },
          { timeout: 10000 }
        )

        const sentences = splitResponse.data.sentences || []

        if (sentences.length === 0) {
          this.error = 'No valid sentences found. Please enter text with actual words.'
          this.loading = false
          return
        }

        // Step 2: Initialize analysis structure with loading states for each sentence
        // UI shows sentences immediately with "Analyzing..." state
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
        this.loading = false
        // Step 3: Analyze each sentence in parallel and update UI as results arrive
        // This provides the progressive/incremental UI updates the user expects
        const analyzePromises = sentences.map((sentence, index) =>
          axios.post(`${API_BASE_URL}/api/analyze-sentence`, { sentence }, { timeout: 100000 })
            .then(response => {
              const data = response.data || {}
              // Update this specific sentence with the analysis result
              if (this.analysis && this.analysis.sentences && this.analysis.sentences[index]) {
                this.analysis.sentences.splice(index, 1, {
                  sentence: data.sentence ?? sentence,
                  sentence_translation: data.sentence_translation ?? '',
                  components: data.components ?? [],
                  collapsed: true,
                  loading: false,
                  error: null,
                  completedAt: new Date().toISOString(),
                  justCompleted: true
                })

                // Remove the transient justCompleted flag after animation
                setTimeout(() => {
                  if (this.analysis?.sentences?.[index]) {
                    this.analysis.sentences[index].justCompleted = false
                  }
                }, 1400)
              }
            })
            .catch(error => {
              const message = error.response?.data?.detail || error.message || 'Unknown error'
              if (this.analysis?.sentences?.[index]) {
                this.analysis.sentences[index].error = message
                this.analysis.sentences[index].loading = false
              }
            })
        )

        // Step 4: Wait for all analyses to complete
        await Promise.allSettled(analyzePromises)

        this.loading = false
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

.translation-highlight {
  background: rgba(234, 102, 225, 0.25);
  border-radius: 3px;
  padding: 0 2px;
  font-weight: 500;
  transition: all 0.2s ease;
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

.detail-item.highlight {
  color: #f9f9f9;
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

.sentence-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.sentence-word {
  display: inline-block;
}

.sentence-word.highlight {
  background: rgba(234, 102, 225, 0.14);
  border-radius: 3px;
  padding: 0 2px;
}

.component-tag.highlight {
  box-shadow: 0 6px 18px rgba(234, 102, 179, 0.12);
  transform: translateY(-2px);
  color: #edd0e9;
  background: #8984e5;
}

.component-tag.highlight strong {
  color: #e6dae7;
}

.completed-badge {
  display: inline-block;
  background: #52c41a;
  color: white;
  border-radius: 50%;
  width: 26px;
  height: 26px;
  text-align: center;
  line-height: 26px;
  font-weight: 700;
  box-shadow: 0 4px 10px rgba(82, 196, 26, 0.18);
  transform: scale(0.85);
  animation: pop 0.45s ease-out forwards;
}

.completed-time {
  font-size: 12px;
  color: #666;
}

@keyframes pop {
  0% {
    transform: scale(0.6);
    opacity: 0
  }

  60% {
    transform: scale(1.08);
    opacity: 1
  }

  100% {
    transform: scale(1);
  }
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.7;
  }
}

/* Verb link styling */
.verb-link {
  color: white;
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
  padding: 4px 10px;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-block;
  text-decoration: none;
  box-shadow: 0 2px 8px rgba(123, 58, 237, 0.25);
  position: relative;
  font-size: 13px;
}

.verb-link::after {
  content: ' ➜';
  font-size: 12px;
  margin-left: 4px;
  opacity: 0.8;
  transition: all 0.3s ease;
}

.verb-link:hover {
  background: linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%);
  box-shadow: 0 6px 16px rgba(123, 58, 237, 0.4);
  transform: translateY(-1px);
}

.verb-link:hover::after {
  opacity: 1;
  transform: translateX(2px);
}

.verb-link:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(123, 58, 237, 0.25);
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
