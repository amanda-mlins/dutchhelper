<template>
    <div class="auth-page">
        <div class="auth-card">
            <div class="auth-logo">🇳🇱 DutchHelper</div>
            <h1 class="auth-title">Sign in</h1>

            <!-- Show URL error from Google OAuth redirect -->
            <p v-if="urlError" class="error-msg">{{ urlError }}</p>

            <!-- Google OAuth button -->
            <a :href="googleLoginUrl" class="btn-google">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google"
                    class="google-icon" />
                Continue with Google
            </a>

            <div class="divider"><span>or</span></div>

            <!-- Email + password form -->
            <form @submit.prevent="handleLogin" novalidate>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input id="email" v-model="email" type="email" autocomplete="email" placeholder="you@example.com"
                        required />
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input id="password" v-model="password" type="password" autocomplete="current-password"
                        placeholder="Your password" required />
                </div>

                <div class="form-group form-group--remember">
                    <label class="remember-label">
                        <input type="checkbox" v-model="rememberMe" class="remember-checkbox" />
                        <span class="remember-text">Remember me</span>
                    </label>
                </div>

                <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>

                <button type="submit" class="btn-primary" :disabled="auth.loading">
                    <span v-if="auth.loading">Signing in…</span>
                    <span v-else>Sign in</span>
                </button>
            </form>

            <p class="auth-footer">
                Don't have an account?
                <router-link to="/register">Create one</router-link>
            </p>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const googleLoginUrl = `${API}/api/auth/google`

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const errorMessage = ref('')

const urlError = computed(() => {
    const err = route.query.error
    if (err === 'google_denied') return 'Google sign-in was cancelled.'
    if (err === 'google_failed') return 'Google sign-in failed. Please try again.'
    if (err === 'server_error') return 'A server error occurred. Please try again.'
    return null
})

async function handleLogin() {
    errorMessage.value = ''
    try {
        await auth.login(email.value, password.value, rememberMe.value)
        const redirect = route.query.redirect || '/'
        router.push(redirect)
    } catch (err) {
        const detail = err?.response?.data?.detail
        errorMessage.value = detail || 'Sign-in failed. Please check your credentials.'
    }
}
</script>

<style scoped>
.auth-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
}

.auth-card {
    background: white;
    border-radius: 16px;
    padding: 40px;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.auth-logo {
    font-size: 28px;
    text-align: center;
    margin-bottom: 8px;
}

.auth-title {
    font-size: 22px;
    font-weight: 700;
    text-align: center;
    margin: 0 0 24px;
    color: #1a1a2e;
}

.btn-google {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    padding: 12px;
    border: 1.5px solid #ddd;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    color: #333;
    text-decoration: none;
    background: white;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
    box-sizing: border-box;
}

.btn-google:hover {
    background: #f8f8f8;
    border-color: #bbb;
}

.google-icon {
    width: 20px;
    height: 20px;
}

.divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 20px 0;
    color: #aaa;
    font-size: 13px;
}

.divider::before,
.divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #e0e0e0;
}

.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 6px;
    color: #444;
}

.form-group input {
    width: 100%;
    padding: 11px 14px;
    border: 1.5px solid #ddd;
    border-radius: 8px;
    font-size: 15px;
    outline: none;
    transition: border-color 0.2s;
    box-sizing: border-box;
}

.form-group input:focus {
    border-color: #667eea;
}

.btn-primary {
    width: 100%;
    padding: 13px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 4px;
    transition: opacity 0.2s;
}

.btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* ── Remember me ────────────────────────────────────────────────────────── */
.form-group--remember {
    margin-bottom: 8px;
}

/* Override the generic .form-group label block rule */
.form-group--remember .remember-label {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    user-select: none;
    font-weight: normal;
    font-size: 14px;
    color: #555;
    margin-bottom: 0;
    width: fit-content;
}

.remember-checkbox {
    /* Reset the width:100% from .form-group input */
    width: 16px !important;
    height: 16px;
    padding: 0 !important;
    border: none !important;
    accent-color: #667eea;
    cursor: pointer;
    flex-shrink: 0;
}

.remember-text {
    font-size: 14px;
    color: #555;
    font-weight: normal;
    line-height: 1;
}

.error-msg {
    color: #e53e3e;
    font-size: 14px;
    margin: 0 0 12px;
}

.auth-footer {
    text-align: center;
    margin-top: 20px;
    font-size: 14px;
    color: #666;
}

.auth-footer a {
    color: #667eea;
    font-weight: 600;
    text-decoration: none;
}

@media (max-width: 480px) {
    .auth-card {
        padding: 28px 20px;
        border-radius: 12px;
    }
}
</style>
