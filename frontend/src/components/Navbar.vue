<template>
    <nav class="navbar">
        <div class="navbar-container">
            <router-link to="/" class="navbar-logo">
                🇳🇱 DutchHelper
            </router-link>
            <div class="navbar-links">
                <router-link to="/" class="nav-link">Home</router-link>
                <router-link to="/sentence-explainer" class="nav-link">Sentence Explainer</router-link>
                <router-link to="/conjugator" class="nav-link">Verb Conjugator</router-link>
                <router-link to="/article-game" class="nav-link">Article Game</router-link>
                <router-link to="/word-bank" class="nav-link">Word Bank</router-link>
            </div>
        </div>
    </nav>
</template>

<script>
export default {
    name: 'Navbar',
};
</script>

<style scoped>
.navbar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 15px 30px;
    position: sticky;
    top: 0;
    z-index: 1000;
    width: 100%;
}

.navbar-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

.navbar-logo {
    color: white;
    font-size: 24px;
    font-weight: bold;
    text-decoration: none;
}

.navbar-links {
    display: flex;
    gap: 25px;
}

.nav-link {
    color: white;
    text-decoration: none;
    font-size: 16px;
    padding: 5px 10px;
    border-radius: 5px;
    transition: background-color 0.3s;
}

.nav-link:hover,
.nav-link.router-link-exact-active {
    background-color: rgba(255, 255, 255, 0.2);
}
</style>
