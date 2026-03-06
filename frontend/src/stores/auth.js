/**
 * Auth store (Pinia)
 *
 * Security design:
 *  - Access token is held ONLY in memory (this store). It is never written to
 *    localStorage or sessionStorage, so XSS cannot exfiltrate it.
 *  - Refresh token lives in an httpOnly cookie the backend sets; JavaScript
 *    cannot read it at all.
 *  - On every page load we call /api/auth/refresh to silently restore the
 *    session from the cookie (if it exists and is still valid).
 *  - The Google OAuth callback route reads the token from the URL fragment
 *    (#access_token=...) which the browser never sends to any server.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Axios instance that always sends the access token
export const authAxios = axios.create({ baseURL: API, withCredentials: true })

export const useAuthStore = defineStore('auth', () => {
    // ── State ──────────────────────────────────────────────────────────────────
    const accessToken = ref(null)   // in memory only
    const user = ref(null)
    const loading = ref(false)
    const initializing = ref(true)  // true while the silent refresh is in flight

    // ── Getters ────────────────────────────────────────────────────────────────
    const isAuthenticated = computed(() => !!accessToken.value)

    // ── Helpers ────────────────────────────────────────────────────────────────
    function _applySession(data) {
        accessToken.value = data.access_token
        user.value = data.user
        // Keep the axios instance up to date
        authAxios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
    }

    function _clearSession() {
        accessToken.value = null
        user.value = null
        delete authAxios.defaults.headers.common['Authorization']
    }

    // ── Actions ────────────────────────────────────────────────────────────────

    /** Called once on app boot to restore session from the refresh cookie. */
    async function initialize() {
        try {
            const { data } = await axios.post(
                `${API}/api/auth/refresh`,
                {},
                { withCredentials: true },
            )
            _applySession(data)
        } catch {
            // No valid refresh cookie — user is logged out, that's fine
            _clearSession()
        } finally {
            initializing.value = false
        }
    }

    async function register(email, password) {
        loading.value = true
        try {
            const { data } = await axios.post(
                `${API}/api/auth/register`,
                { email, password },
                { withCredentials: true },
            )
            _applySession(data)
        } finally {
            loading.value = false
        }
    }

    async function login(email, password) {
        loading.value = true
        try {
            const { data } = await axios.post(
                `${API}/api/auth/login`,
                { email, password },
                { withCredentials: true },
            )
            _applySession(data)
        } finally {
            loading.value = false
        }
    }

    async function logout() {
        try {
            await axios.post(`${API}/api/auth/logout`, {}, { withCredentials: true })
        } finally {
            _clearSession()
        }
    }

    /**
     * Called by the /auth/callback route after Google OAuth.
     * The access token comes from the URL fragment (#access_token=...).
     */
    function handleGoogleCallback(token) {
        // Fetch user profile with the token
        authAxios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        return axios
            .get(`${API}/api/auth/me`, {
                headers: { Authorization: `Bearer ${token}` },
                withCredentials: true,
            })
            .then(({ data }) => {
                _applySession({ access_token: token, user: data })
            })
            .catch(() => {
                _clearSession()
                throw new Error('Failed to fetch user profile after Google login.')
            })
    }
    function getAuthAxios() {
        if (!accessToken.value) {
            throw new Error('No access token available. User is not authenticated.')
        }
        return authAxios
    }

    return {
        accessToken,
        user,
        loading,
        initializing,
        isAuthenticated,
        initialize,
        register,
        login,
        logout,
        handleGoogleCallback,
        getAuthAxios
    }
})
