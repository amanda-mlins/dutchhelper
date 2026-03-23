<template>
    <div class="profile-page">

        <!-- ── Avatar + identity ─────────────────────────────────────────── -->
        <div class="profile-hero">
            <div class="avatar">{{ initials }}</div>
            <div class="identity">
                <h1 class="display-name">{{ displayName }}</h1>
                <p class="member-email">{{ auth.user?.email }}</p>
                <p class="member-since">Member since {{ memberSince }}</p>
            </div>
        </div>

        <!-- ── Nickname card ─────────────────────────────────────────────── -->
        <section class="card">
            <h2>Nickname</h2>
            <p class="card-desc">Set a display name that appears in the navbar and on your profile instead of your email
                address.</p>
            <form @submit.prevent="saveNickname" class="nickname-form">
                <div class="input-row">
                    <input v-model="nicknameInput" type="text" maxlength="30" placeholder="e.g. NederlandsFan42"
                        class="text-input" :disabled="nicknameSaving" />
                    <button type="submit" class="btn-primary" :disabled="nicknameSaving || !nicknameChanged">
                        {{ nicknameSaving ? 'Saving…' : 'Save' }}
                    </button>
                    <button v-if="nicknameInput && auth.user?.username" type="button" class="btn-ghost"
                        :disabled="nicknameSaving" @click="clearNickname">
                        Clear
                    </button>
                </div>
                <p class="char-count" :class="{ warn: nicknameInput.length > 25 }">
                    {{ nicknameInput.length }} / 30
                </p>
                <p v-if="nicknameError" class="field-error">{{ nicknameError }}</p>
                <p v-if="nicknameSuccess" class="field-success">{{ nicknameSuccess }}</p>
            </form>
        </section>

        <!-- ── Stats overview ────────────────────────────────────────────── -->
        <section class="card">
            <h2>Activity Overview</h2>
            <div v-if="statsLoading" class="state-msg">Loading stats…</div>
            <div v-else-if="statsError" class="state-msg state-error">{{ statsError }}</div>
            <div v-else class="stats-grid">
                <!-- Article game -->
                <router-link to="/article-game/stats" class="stat-block stat-link">
                    <div class="stat-icon">📰</div>
                    <div class="stat-label">Article Game</div>
                    <div class="stat-number">{{ articleStats.total_games ?? 0 }}</div>
                    <div class="stat-sub">games played</div>
                    <div class="stat-acc" v-if="articleStats.total_games">
                        {{ articleStats.avg_accuracy ?? 0 }}% avg accuracy
                    </div>
                    <div class="stat-details-hint">View details →</div>
                </router-link>
                <!-- Verb game -->
                <router-link to="/verb-game/stats" class="stat-block stat-link">
                    <div class="stat-icon">🔤</div>
                    <div class="stat-label">Verb Game</div>
                    <div class="stat-number">{{ verbStats.total_games ?? 0 }}</div>
                    <div class="stat-sub">games played</div>
                    <div class="stat-acc" v-if="verbStats.total_games">
                        {{ verbStats.avg_accuracy ?? 0 }}% avg accuracy
                    </div>
                    <div class="stat-details-hint">View details →</div>
                </router-link>
                <!-- Conjunction game -->
                <router-link to="/conjunction-game/stats" class="stat-block stat-link">
                    <div class="stat-icon">🔗</div>
                    <div class="stat-label">Conjunction Game</div>
                    <div class="stat-number">{{ conjStats.total_games ?? 0 }}</div>
                    <div class="stat-sub">games played</div>
                    <div class="stat-acc" v-if="conjStats.total_games">
                        {{ conjStats.avg_accuracy ?? 0 }}% avg accuracy
                        <span v-if="conjStats.review_queue_size" class="review-tag">
                            · 🔁 {{ conjStats.review_queue_size }} in review queue
                        </span>
                    </div>
                    <div class="stat-details-hint">View details →</div>
                </router-link>
                <!-- Preposition game -->
                <router-link to="/prep-verb-game/stats" class="stat-block stat-link">
                    <div class="stat-icon">🔀</div>
                    <div class="stat-label">Preposition Game</div>
                    <div class="stat-number">{{ prepStats.total_games ?? 0 }}</div>
                    <div class="stat-sub">games played</div>
                    <div class="stat-acc" v-if="prepStats.total_games">
                        {{ prepStats.avg_accuracy ?? 0 }}% avg accuracy
                        <span v-if="prepStats.review_queue_size" class="review-tag">
                            · 🔁 {{ prepStats.review_queue_size }} in review queue
                        </span>
                    </div>
                    <div class="stat-details-hint">View details →</div>
                </router-link>
                <!-- Total -->
                <div class="stat-block stat-total">
                    <div class="stat-icon">🏆</div>
                    <div class="stat-label">Total</div>
                    <div class="stat-number">{{ totalGames }}</div>
                    <div class="stat-sub">games across all types</div>
                    <div class="stat-acc" v-if="totalGames">{{ overallAccuracy }}% overall accuracy</div>
                </div>
            </div>
        </section>

        <!-- ── Danger zone ───────────────────────────────────────────────── -->
        <section class="card card-danger">
            <h2>Account</h2>
            <p class="card-desc">Sign out of your account on this device.</p>
            <button class="btn-danger" @click="handleLogout">Sign out</button>
        </section>

    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

// ── Nickname ───────────────────────────────────────────────────────────────
const nicknameInput = ref(auth.user?.username || '')
const nicknameSaving = ref(false)
const nicknameError = ref('')
const nicknameSuccess = ref('')

const nicknameChanged = computed(() => {
    const current = auth.user?.username || ''
    return nicknameInput.value.trim() !== current
})

async function saveNickname() {
    nicknameError.value = ''
    nicknameSuccess.value = ''
    nicknameSaving.value = true
    try {
        await auth.updateProfile({ username: nicknameInput.value.trim() || '' })
        nicknameInput.value = auth.user?.username || ''
        nicknameSuccess.value = auth.user?.username
            ? `Nickname set to "${auth.user.username}" ✓`
            : 'Nickname cleared ✓'
    } catch (e) {
        nicknameError.value = e.response?.data?.detail || 'Failed to save nickname.'
    } finally {
        nicknameSaving.value = false
    }
}

async function clearNickname() {
    nicknameInput.value = ''
    await saveNickname()
}

// ── Computed identity ──────────────────────────────────────────────────────
const displayName = computed(() => auth.user?.username || auth.user?.email?.split('@')[0] || 'My Profile')

const initials = computed(() => {
    const name = auth.user?.username || auth.user?.email || '?'
    return name.slice(0, 2).toUpperCase()
})

const memberSince = computed(() => {
    const d = auth.user?.created_at
    if (!d) return '—'
    return new Date(d).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
})

// ── Stats ──────────────────────────────────────────────────────────────────
const statsLoading = ref(true)
const statsError = ref('')
const articleStats = ref({})
const verbStats = ref({})
const conjStats = ref({})
const prepStats = ref({})

const totalGames = computed(
    () => (articleStats.value.total_games ?? 0)
        + (verbStats.value.total_games ?? 0)
        + (conjStats.value.total_games ?? 0)
        + (prepStats.value.total_games ?? 0)
)

const overallAccuracy = computed(() => {
    const parts = [articleStats.value, verbStats.value, conjStats.value, prepStats.value]
        .filter(s => s.total_games > 0)
    if (!parts.length) return 0
    return Math.round(parts.reduce((sum, s) => sum + s.avg_accuracy, 0) / parts.length)
})

onMounted(async () => {
    if (!auth.isAuthenticated) {
        router.push('/login')
        return
    }
    try {
        const ax = auth.getAuthAxios()
        const [a, v, c, p] = await Promise.all([
            ax.get('/api/game/stats'),
            ax.get('/api/verb-game/stats'),
            ax.get('/api/conjunction-game/stats'),
            ax.get('/api/prep-verb-game/stats'),
        ])
        articleStats.value = a.data
        verbStats.value = v.data
        conjStats.value = c.data
        prepStats.value = p.data
    } catch (e) {
        statsError.value = 'Could not load activity stats.'
    } finally {
        statsLoading.value = false
    }
})

// ── Logout ─────────────────────────────────────────────────────────────────
async function handleLogout() {
    await auth.logout()
    router.push('/')
}
</script>

<style scoped>
.profile-page {
    max-width: 680px;
    margin: 0 auto;
    padding: 40px 20px 80px;
    display: flex;
    flex-direction: column;
    gap: 24px;
}

/* ── Hero ────────────────────────────────────────────────────────────────── */
.profile-hero {
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 28px 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    color: #fff;
}

.avatar {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    font-weight: 800;
    flex-shrink: 0;
    letter-spacing: -1px;
}

.identity {
    flex: 1;
    min-width: 0;
}

.display-name {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.member-email {
    font-size: 0.9rem;
    opacity: 0.85;
    margin: 0 0 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.member-since {
    font-size: 0.82rem;
    opacity: 0.7;
    margin: 0;
}

/* ── Cards ───────────────────────────────────────────────────────────────── */
.card {
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 24px 28px;
}

.card h2 {
    font-size: 1.1rem;
    font-weight: 700;
    margin: 0 0 6px;
    color: #222;
}

.card-desc {
    font-size: 0.9rem;
    color: #777;
    margin: 0 0 18px;
    line-height: 1.5;
}

.card-danger {
    border-color: #fee2e2;
    background: #fff8f8;
}

.card-danger h2 {
    color: #991b1b;
}

/* ── Nickname form ───────────────────────────────────────────────────────── */
.nickname-form {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.input-row {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
}

.text-input {
    flex: 1;
    min-width: 180px;
    padding: 9px 14px;
    border: 1.5px solid #d1d5db;
    border-radius: 10px;
    font-size: 0.95rem;
    transition: border-color 0.15s;
    font-family: inherit;
}

.text-input:focus {
    outline: none;
    border-color: #7c3aed;
}

.char-count {
    font-size: 0.78rem;
    color: #9ca3af;
    margin: 0;
}

.char-count.warn {
    color: #f59e0b;
    font-weight: 600;
}

.field-error {
    font-size: 0.88rem;
    color: #dc2626;
    margin: 0;
}

.field-success {
    font-size: 0.88rem;
    color: #16a34a;
    margin: 0;
}

/* ── Stats grid ──────────────────────────────────────────────────────────── */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 16px;
}

.stat-block {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px 14px;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 3px;
}

.stat-link {
    text-decoration: none;
    color: inherit;
    transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
    cursor: pointer;
}

.stat-link:hover {
    border-color: #a5b4fc;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.12);
    transform: translateY(-2px);
}

.stat-link:hover .stat-details-hint {
    opacity: 1;
}

.stat-details-hint {
    margin-top: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #7c3aed;
    opacity: 0;
    transition: opacity 0.15s;
}

.stat-total {
    background: linear-gradient(135deg, #f0f4ff, #ede9ff);
    border-color: #c7d2fe;
}

.stat-icon {
    font-size: 1.5rem;
}

.stat-label {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #6b7280;
}

.stat-number {
    font-size: 2rem;
    font-weight: 800;
    color: #4f46e5;
    line-height: 1;
}

.stat-sub {
    font-size: 0.75rem;
    color: #9ca3af;
}

.stat-acc {
    font-size: 0.8rem;
    color: #555;
    margin-top: 4px;
    text-align: center;
    line-height: 1.4;
}

.review-tag {
    color: #b45309;
    font-weight: 600;
}

/* ── State ───────────────────────────────────────────────────────────────── */
.state-msg {
    text-align: center;
    padding: 20px;
    color: #888;
}

.state-error {
    color: #dc2626;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.btn-primary {
    padding: 9px 20px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 0.92rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    white-space: nowrap;
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-ghost {
    padding: 9px 16px;
    background: none;
    color: #6b7280;
    border: 1.5px solid #d1d5db;
    border-radius: 10px;
    font-size: 0.88rem;
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
    white-space: nowrap;
}

.btn-ghost:hover {
    border-color: #9ca3af;
    color: #374151;
}

.btn-danger {
    padding: 9px 20px;
    background: #ef4444;
    color: #fff;
    border: none;
    border-radius: 10px;
    font-size: 0.92rem;
    font-weight: 600;
    cursor: pointer;
}

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 480px) {
    .profile-hero {
        flex-direction: column;
        text-align: center;
    }

    .stats-grid {
        grid-template-columns: 1fr 1fr;
    }
}
</style>
