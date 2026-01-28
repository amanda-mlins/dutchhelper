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

      <section class="section">
        <h2>Tools</h2>
        <div class="tools-grid">
          <router-link to="/sentence-explainer" class="tool-card">
            <h3>📖 Sentence Explainer</h3>
            <p>Break down Dutch sentences into grammatical components: subjects, verbs, objects, adjectives, and more.</p>
          </router-link>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {}
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

.header h1 {
  font-size: 48px;
  margin-bottom: 10px;
}

.header p {
  font-size: 18px;
  opacity: 0.9;
}

.main {
  max-width: 900px;
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

.section h2 {
  color: #667eea;
  margin-bottom: 20px;
  font-size: 24px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.tool-card {
  display: block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  border-radius: 8px;
  text-decoration: none;
  transition: transform 0.3s, box-shadow 0.3s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.tool-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
}

.tool-card h3 {
  font-size: 20px;
  margin-bottom: 10px;
}

.tool-card p {
  font-size: 14px;
  opacity: 0.9;
}
</style>
