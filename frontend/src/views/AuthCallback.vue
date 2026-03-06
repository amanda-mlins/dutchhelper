<template>
    <div class="callback-page">
        <p v-if="error" class="error-msg">{{ error }}</p>
        <p v-else>Signing you in…</p>
    </div>
</template>

<script setup>
/**
 * This page is the frontend landing target after Google OAuth.
 * The backend redirects to /auth/callback#access_token=<token>
 * We read the token from the URL fragment (which is never sent to any server),
 * hand it to the auth store, then navigate home.
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()
const error = ref(null)

onMounted(async () => {
    const fragment = window.location.hash.substring(1) // strip leading '#'
    const params = new URLSearchParams(fragment)
    const token = params.get('access_token')

    if (!token) {
        error.value = 'Login failed — no token received. Please try again.'
        setTimeout(() => router.push('/login'), 3000)
        return
    }

    try {
        await auth.handleGoogleCallback(token)
        // Clear the fragment from the URL so the token isn't sitting in history
        window.history.replaceState(null, '', window.location.pathname)
        router.push('/')
    } catch {
        error.value = 'Could not complete sign-in. Please try again.'
        setTimeout(() => router.push('/login'), 3000)
    }
})
</script>

<style scoped>
.callback-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: #555;
}

.error-msg {
    color: #e53e3e;
}
</style>
