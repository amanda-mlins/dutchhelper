<template>
    <nav class="navbar">
        <div class="navbar-container">
            <router-link to="/" class="navbar-logo">
                🇳🇱 DutchHelper
            </router-link>
            <div class="navbar-links">
                <router-link to="/" class="nav-link">Home</router-link>
                <router-link to="/sentence-explainer" class="nav-link" :class="{ locked: !auth.isAuthenticated }">
                    Sentence Explainer<span v-if="!auth.isAuthenticated" class="lock-icon">🔒</span>
                </router-link>
                <router-link to="/conjugator" class="nav-link">Verb Conjugator</router-link>
                <router-link to="/article-game" class="nav-link">Article Game</router-link>
                <router-link to="/word-bank" class="nav-link" :class="{ locked: !auth.isAuthenticated }">
                    Word Bank<span v-if="!auth.isAuthenticated" class="lock-icon">🔒</span>
                </router-link>
            </div>
            <div class="navbar-user">
                <template v-if="auth.isAuthenticated">
                    <span class="user-email">{{ auth.user?.email }}</span>
                    <button class="btn-logout" @click="handleLogout">Sign out</button>
                </template>
                <template v-else>
                    <router-link to="/login" class="nav-link">Sign in</router-link>
                    <router-link to="/register" class="btn-register">Create account</router-link>
                </template>
            </div>
        </div>
    </nav>
</template>

<script setup>
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
    await auth.logout()
    router.push('/login')
}
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

.nav-link.locked {
    opacity: 0.6;
}

.nav-link.locked:hover {
    background-color: rgba(255, 255, 255, 0.08);
}

.lock-icon {
    font-size: 11px;
    margin-left: 4px;
    vertical-align: middle;
    opacity: 0.85;
}

.navbar-user {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-left: 20px;
}

.user-email {
    color: rgba(255, 255, 255, 0.85);
    font-size: 14px;
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.btn-logout {
    background: rgba(255, 255, 255, 0.15);
    color: white;
    border: 1.5px solid rgba(255, 255, 255, 0.4);
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
}

.btn-logout:hover {
    background: rgba(255, 255, 255, 0.28);
}

.btn-register {
    background: white;
    color: #764ba2;
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
    transition: opacity 0.2s;
}

.btn-register:hover {
    opacity: 0.9;
}
</style>
