<template>
    <nav class="navbar">
        <div class="navbar-container">
            <router-link to="/" class="navbar-logo" @click="closeMenu">
                🇳🇱 DutchHelper
            </router-link>

            <!-- Hamburger button (mobile only) -->
            <button class="hamburger" :class="{ open: menuOpen }" @click="toggleMenu" aria-label="Toggle menu">
                <span></span>
                <span></span>
                <span></span>
            </button>

            <!-- Overlay that closes menu when tapped outside -->
            <div v-if="menuOpen" class="menu-overlay" @click="closeMenu" />

            <!-- Nav links + user section — collapses on mobile -->
            <div class="navbar-drawer" :class="{ open: menuOpen }">
                <div class="navbar-links">
                    <router-link to="/" class="nav-link" @click="closeMenu">Home</router-link>
                    <router-link to="/sentence-explainer" class="nav-link" :class="{ locked: !auth.isAuthenticated }"
                        @click="closeMenu">
                        Sentence Explainer<span v-if="!auth.isAuthenticated" class="lock-icon">🔒</span>
                    </router-link>
                    <router-link to="/conjugator" class="nav-link" @click="closeMenu">Verb Conjugator</router-link>
                    <router-link to="/article-game" class="nav-link" @click="closeMenu">Article Game</router-link>
                    <router-link to="/word-bank" class="nav-link" :class="{ locked: !auth.isAuthenticated }"
                        @click="closeMenu">
                        Word Bank<span v-if="!auth.isAuthenticated" class="lock-icon">🔒</span>
                    </router-link>
                    <router-link v-if="auth.user?.is_admin" to="/admin/words" class="nav-link nav-admin"
                        @click="closeMenu">
                        🛠️ Admin
                    </router-link>
                </div>

                <div class="navbar-user">
                    <template v-if="auth.isAuthenticated">
                        <span class="user-email">{{ auth.user?.email }}</span>
                        <button class="btn-logout" @click="handleLogout">Sign out</button>
                    </template>
                    <template v-else>
                        <router-link to="/login" class="nav-link" @click="closeMenu">Sign in</router-link>
                        <router-link to="/register" class="btn-register" @click="closeMenu">Create account</router-link>
                    </template>
                </div>
            </div>
        </div>
    </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const menuOpen = ref(false)

function toggleMenu() { menuOpen.value = !menuOpen.value }
function closeMenu() { menuOpen.value = false }

async function handleLogout() {
    closeMenu()
    await auth.logout()
    router.push('/login')
}
</script>

<style scoped>
.navbar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
    padding: 0 20px;
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
    height: 60px;
}

.navbar-logo {
    color: white;
    font-size: 22px;
    font-weight: bold;
    text-decoration: none;
    flex-shrink: 0;
    z-index: 1001;
}

/* ── Desktop drawer (always visible) ─────────────────────── */
.navbar-drawer {
    display: flex;
    align-items: center;
    gap: 20px;
    flex: 1;
    justify-content: flex-end;
}

.navbar-links {
    display: flex;
    gap: 4px;
}

.nav-link {
    color: white;
    text-decoration: none;
    font-size: 15px;
    padding: 6px 10px;
    border-radius: 5px;
    transition: background-color 0.2s;
    white-space: nowrap;
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

.nav-admin {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    font-weight: 600;
}

.nav-admin:hover {
    background: rgba(255, 255, 255, 0.25) !important;
}

.navbar-user {
    display: flex;
    align-items: center;
    gap: 10px;
    border-left: 1px solid rgba(255, 255, 255, 0.25);
    padding-left: 16px;
    margin-left: 4px;
}

.user-email {
    color: rgba(255, 255, 255, 0.85);
    font-size: 13px;
    max-width: 160px;
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
    white-space: nowrap;
}

.btn-logout:hover {
    background: rgba(255, 255, 255, 0.28);
}

.btn-register {
    background: white;
    color: #764ba2;
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;
    transition: opacity 0.2s;
    white-space: nowrap;
}

.btn-register:hover {
    opacity: 0.9;
}

/* ── Hamburger (hidden on desktop) ───────────────────────── */
.hamburger {
    display: none;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    z-index: 1001;
}

.hamburger span {
    display: block;
    width: 24px;
    height: 2px;
    background: white;
    border-radius: 2px;
    transition: transform 0.25s, opacity 0.25s;
}

.hamburger.open span:nth-child(1) {
    transform: translateY(7px) rotate(45deg);
}

.hamburger.open span:nth-child(2) {
    opacity: 0;
}

.hamburger.open span:nth-child(3) {
    transform: translateY(-7px) rotate(-45deg);
}

/* ── Overlay ──────────────────────────────────────────────── */
.menu-overlay {
    display: none;
}

/* ── Mobile ──────────────────────────────────────────────── */
@media (max-width: 768px) {
    .hamburger {
        display: flex;
    }

    .menu-overlay {
        display: block;
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.35);
        z-index: 999;
    }

    .navbar-drawer {
        position: fixed;
        top: 0;
        right: -100%;
        width: min(300px, 85vw);
        height: 100dvh;
        background: linear-gradient(160deg, #667eea 0%, #764ba2 100%);
        flex-direction: column;
        align-items: stretch;
        justify-content: flex-start;
        padding: 80px 20px 24px;
        gap: 0;
        z-index: 1000;
        transition: right 0.28s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: -4px 0 20px rgba(0, 0, 0, 0.2);
        overflow-y: auto;
    }

    .navbar-drawer.open {
        right: 0;
    }

    .navbar-links {
        flex-direction: column;
        gap: 4px;
    }

    .nav-link {
        font-size: 16px;
        padding: 12px 14px;
        border-radius: 8px;
    }

    .navbar-user {
        border-left: none;
        border-top: 1px solid rgba(255, 255, 255, 0.25);
        padding-left: 0;
        padding-top: 16px;
        margin-left: 0;
        margin-top: 16px;
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
    }

    .user-email {
        max-width: 100%;
        font-size: 13px;
        padding: 0 4px;
    }

    .btn-logout,
    .btn-register {
        text-align: center;
        padding: 12px 14px;
        font-size: 15px;
        border-radius: 8px;
    }

    .btn-register {
        display: block;
    }
}
</style>
