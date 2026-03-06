<template>
    <div class="auth-page">
        <div class="auth-card">
            <div class="auth-logo">🇳🇱 DutchHelper</div>
            <h1 class="auth-title">Create your account</h1>

            <!-- Google OAuth button -->
            <a :href="googleLoginUrl" class="btn-google">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google"
                    class="google-icon" />
                Continue with Google
            </a>

            <div class="divider"><span>or</span></div>

            <!-- Email + password form -->
            <form @submit.prevent="handleRegister" novalidate>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input id="email" v-model="email" type="email" autocomplete="email" placeholder="you@example.com"
                        required />
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input id="password" v-model="password" type="password" autocomplete="new-password"
                        placeholder="Create a strong password" required />

                    <!-- Strength bar -->
                    <div v-if="password.length > 0" class="strength-bar-track">
                        <div class="strength-bar-fill" :style="{ width: strengthPercent + '%' }" :class="strengthClass">
                        </div>
                    </div>

                    <!-- Per-rule checklist -->
                    <ul v-if="password.length > 0" class="password-rules">
                        <li v-for="rule in rules" :key="rule.label" :class="rule.valid ? 'rule-ok' : 'rule-fail'">
                            <span class="rule-icon">{{ rule.valid ? '✓' : '✗' }}</span>
                            {{ rule.label }}
                        </li>
                    </ul>
                </div>

                <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>

                <button type="submit" class="btn-primary" :disabled="auth.loading || !allRulesPassed">
                    <span v-if="auth.loading">Creating account…</span>
                    <span v-else>Create account</span>
                </button>
            </form>

            <p class="auth-footer">
                Already have an account?
                <router-link to="/login">Sign in</router-link>
            </p>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const googleLoginUrl = `${API}/api/auth/google`

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const errorMessage = ref('')

// ---------------------------------------------------------------------------
// Password rules — must stay in sync with backend validate_password_strength
// ---------------------------------------------------------------------------
const rules = computed(() => [
    { label: 'At least 12 characters', valid: password.value.length >= 12 },
    { label: 'At least one uppercase letter', valid: /[A-Z]/.test(password.value) },
    { label: 'At least one lowercase letter', valid: /[a-z]/.test(password.value) },
    { label: 'At least one number', valid: /\d/.test(password.value) },
    { label: 'At least one special character', valid: /[^A-Za-z0-9]/.test(password.value) },
])

const passedCount = computed(() => rules.value.filter(r => r.valid).length)
const allRulesPassed = computed(() => passedCount.value === rules.value.length)

const strengthPercent = computed(() => (passedCount.value / rules.value.length) * 100)

const strengthClass = computed(() => {
    const p = passedCount.value
    if (p <= 1) return 'strength-weak'
    if (p <= 2) return 'strength-poor'
    if (p <= 3) return 'strength-fair'
    if (p === 4) return 'strength-good'
    return 'strength-strong'
})

async function handleRegister() {
    errorMessage.value = ''
    if (!allRulesPassed.value) return   // Button is disabled, but guard anyway
    try {
        await auth.register(email.value, password.value)
        router.push('/')
    } catch (err) {
        const detail = err?.response?.data?.detail
        errorMessage.value = detail || 'Registration failed. Please try again.'
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

/* Strength bar */
.strength-bar-track {
    height: 5px;
    background: #eee;
    border-radius: 3px;
    margin-top: 8px;
    overflow: hidden;
}

.strength-bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease, background 0.3s ease;
}

.strength-weak {
    background: #e53e3e;
}

.strength-poor {
    background: #f6871f;
}

.strength-fair {
    background: #ecc94b;
}

.strength-good {
    background: #68d391;
}

.strength-strong {
    background: #38a169;
}

/* Rules checklist */
.password-rules {
    list-style: none;
    margin: 8px 0 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.password-rules li {
    font-size: 12.5px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: color 0.2s;
}

.rule-ok {
    color: #38a169;
}

.rule-fail {
    color: #a0aec0;
}

.rule-icon {
    font-size: 11px;
    font-weight: 700;
    width: 14px;
    text-align: center;
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
</style>
