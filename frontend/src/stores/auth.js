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

// ---------------------------------------------------------------------------
// 401 auto-refresh interceptor
// When any authAxios request gets a 401 (expired access token), silently call
// /api/auth/refresh once, update the token, and retry the original request.
// A flag prevents infinite retry loops (e.g. if the refresh cookie itself is gone).
// ---------------------------------------------------------------------------
let _isRefreshing = false
let _refreshSubscribers = []   // callbacks waiting for the new token

// The store registers this after creation so the interceptor can call _applySession.
let _onRefreshSuccess = null
let _onRefreshFailure = null

function _subscribeRefresh(cb) { _refreshSubscribers.push(cb) }
function _notifyRefreshed(token) { _refreshSubscribers.forEach(cb => cb(token)); _refreshSubscribers = [] }
function _notifyRefreshFailed() { _refreshSubscribers.forEach(cb => cb(null)); _refreshSubscribers = [] }

authAxios.interceptors.response.use(
    res => res,
    async err => {
        const original = err.config
        // Only intercept 401s that haven't already been retried, and skip the
        // /api/auth/refresh endpoint itself to avoid an infinite loop.
        if (
            err.response?.status !== 401 ||
            original._retry ||
            original.url?.includes('/api/auth/refresh')
        ) {
            return Promise.reject(err)
        }

        original._retry = true

        if (_isRefreshing) {
            // Another request is already refreshing — queue this one
            return new Promise((resolve, reject) => {
                _subscribeRefresh(token => {
                    if (!token) return reject(err)
                    original.headers['Authorization'] = `Bearer ${token}`
                    resolve(authAxios(original))
                })
            })
        }

        _isRefreshing = true
        try {
            const { data } = await axios.post(
                `${API}/api/auth/refresh`,
                {},
                { withCredentials: true },
            )
            if (_onRefreshSuccess) _onRefreshSuccess(data)
            _notifyRefreshed(data.access_token)
            original.headers['Authorization'] = `Bearer ${data.access_token}`
            return authAxios(original)
        } catch (refreshErr) {
            if (_onRefreshFailure) _onRefreshFailure()
            _notifyRefreshFailed()
            return Promise.reject(refreshErr)
        } finally {
            _isRefreshing = false
        }
    },
)

export const useAuthStore = defineStore('auth', () => {
    // ── State ──────────────────────────────────────────────────────────────────
    const accessToken = ref(null)   // in memory only
    const user = ref(null)
    const loading = ref(false)
    const initializing = ref(true)  // true while the silent refresh is in flight

    // Single in-flight promise — prevents concurrent initialize() calls from
    // each firing their own /api/auth/refresh and racing on the rotated cookie.
    let _initPromise = null

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

    // Wire the interceptor callbacks now that _applySession/_clearSession exist.
    _onRefreshSuccess = (data) => _applySession(data)
    _onRefreshFailure = () => _clearSession()

    // ── Actions ────────────────────────────────────────────────────────────────

    /** Called once on app boot to restore session from the refresh cookie. */
    async function initialize() {
        // If already initialised (or not needed), return immediately.
        if (!initializing.value) return

        // If a refresh call is already in-flight, wait for that same promise
        // instead of firing a second request (which would race on the rotated cookie).
        if (_initPromise) return _initPromise

        _initPromise = (async () => {
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
                _initPromise = null
            }
        })()

        return _initPromise
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

    async function login(email, password, rememberMe = false) {
        loading.value = true
        try {
            const { data } = await axios.post(
                `${API}/api/auth/login`,
                { email, password, remember_me: rememberMe },
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

    /** Update the user's profile (nickname). Updates the in-memory user ref on success. */
    async function updateProfile({ username }) {
        const { data } = await authAxios.patch(`${API}/api/auth/me`, { username })
        user.value = data
        return data
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
        getAuthAxios,
        updateProfile,
    }
})
