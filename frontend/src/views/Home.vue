<template>
  <div id="app" class="container">
    <header class="header">
      <h1>🇳🇱 DutchHelper</h1>
      <p>Learn Dutch with ease</p>
    </header>

    <main class="main">
      <section class="section">
        <h2>Welcome</h2>
        <p>This is a learning platform to help you master the Dutch language through interactive tools.</p>
      </section>

      <!-- Sign-in nudge for guests -->
      <section v-if="!auth.isAuthenticated" class="section nudge">
        <p>
          🔒 Some tools require a free account.
          <router-link to="/login">Sign in</router-link> or
          <router-link to="/register">create an account</router-link> to unlock everything.
        </p>
      </section>

      <section class="section">
        <h2>Tools</h2>
        <div class="tools-grid">

          <!-- Always public -->
          <router-link to="/conjugator" class="tool-card">
            <h3>🔤 Verb Conjugator</h3>
            <p>Learn how to conjugate Dutch verbs across all tenses and persons with real-world examples.</p>
          </router-link>

          <!-- Requires login -->
          <component :is="auth.isAuthenticated ? 'router-link' : 'div'"
            v-bind="auth.isAuthenticated ? { to: '/sentence-explainer' } : {}" class="tool-card"
            :class="{ 'tool-card--locked': !auth.isAuthenticated }">
            <div class="card-header">
              <h3>📖 Sentence Explainer</h3>
              <span v-if="!auth.isAuthenticated" class="lock-badge">🔒 Login required</span>
            </div>
            <p>Break down Dutch sentences into grammatical components: subjects, verbs, objects, adjectives, and more.
            </p>
          </component>

          <router-link to="/article-game" class="tool-card">
            <div class="card-header">
              <h3>🎮 Article Game</h3>
            </div>
            <p>Master Dutch articles! Practice guessing whether words use "de" or "het" with interactive games and
              progress tracking.</p>
          </router-link>

          <router-link to="/verb-game" class="tool-card">
            <div class="card-header">
              <h3>✍️ Verb Game</h3>
            </div>
            <p>Practice conjugating Dutch verbs! Complete sentences with the correct conjugated form and track your
              progress over time.</p>
          </router-link>

          <router-link to="/conjunction-game" class="tool-card">
            <div class="card-header">
              <h3>🔗 Conjunction Game</h3>
            </div>
            <p>Master Dutch conjunctions! Complete sentences with the right connecting word and track your progress.</p>
          </router-link>

          <component :is="auth.isAuthenticated ? 'router-link' : 'div'"
            v-bind="auth.isAuthenticated ? { to: '/word-bank' } : {}" class="tool-card"
            :class="{ 'tool-card--locked': !auth.isAuthenticated }">
            <div class="card-header">
              <h3>🏦 My Word Bank</h3>
              <span v-if="!auth.isAuthenticated" class="lock-badge">🔒 Login required</span>
            </div>
            <p>Create your own personal dictionary. Save words, review definitions, and practice with flashcards.</p>
          </component>

          <component :is="auth.isAuthenticated ? 'router-link' : 'div'"
            v-bind="auth.isAuthenticated ? { to: '/flashcards' } : {}" class="tool-card"
            :class="{ 'tool-card--locked': !auth.isAuthenticated }">
            <div class="card-header">
              <h3>🃏 Flashcards</h3>
              <span v-if="!auth.isAuthenticated" class="lock-badge">🔒 Login required</span>
            </div>
            <p>Practise your saved words with flipping flashcards. Study all words or hand-pick a set, track what you
              know and what still needs work.</p>
          </component>

        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth.js'
const auth = useAuthStore()
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

.header h1 {
  font-size: clamp(28px, 7vw, 48px);
  margin-bottom: 10px;
}

.header p {
  font-size: clamp(15px, 4vw, 18px);
  opacity: 0.9;
}

.main {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.section h2 {
  color: #667eea;
  margin-bottom: 16px;
  font-size: clamp(18px, 5vw, 24px);
}

/* Sign-in nudge banner */
.nudge {
  background: #fffbeb;
  border: 1.5px solid #f6e05e;
  padding: 14px 18px;
}

.nudge p {
  color: #744210;
  font-size: 15px;
  line-height: 1.5;
}

.nudge a {
  color: #667eea;
  font-weight: 600;
  text-decoration: none;
}

.nudge a:hover {
  text-decoration: underline;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.tool-card {
  display: block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px 20px;
  border-radius: 8px;
  text-decoration: none;
  transition: transform 0.3s, box-shadow 0.3s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.tool-card:hover:not(.tool-card--locked) {
  transform: translateY(-4px);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
}

.tool-card--locked {
  background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
  cursor: default;
  opacity: 0.8;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.card-header h3 {
  font-size: clamp(16px, 4vw, 20px);
  margin-bottom: 0;
}

.lock-badge {
  display: inline-block;
  background: rgba(0, 0, 0, 0.25);
  color: white;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 20px;
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 2px;
}

.tool-card h3 {
  font-size: clamp(16px, 4vw, 20px);
  margin-bottom: 10px;
}

.tool-card p {
  font-size: 14px;
  opacity: 0.9;
  line-height: 1.5;
}

@media (max-width: 480px) {
  .tools-grid {
    grid-template-columns: 1fr;
  }

  .section {
    padding: 18px 16px;
  }

  .header {
    padding: 28px 16px;
  }
}
</style>
