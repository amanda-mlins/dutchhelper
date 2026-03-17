<template>
    <div class="admin-page">
        <div class="admin-header">
            <h1>👥 User Manager</h1>
            <p class="subtitle">{{ users.length }} registered users</p>
            <label class="reveal-toggle" :title="revealEmails ? 'Hide emails' : 'Show full emails'">
                <input type="checkbox" v-model="revealEmails" @change="fetchUsers" />
                <span>{{ revealEmails ? '🔓 Emails visible' : '🔒 Emails masked' }}</span>
            </label>
        </div>

        <!-- Filters -->
        <div class="filters">
            <input v-model="search" placeholder="Search username or email…" class="filter-input" />
            <select v-model="filterActive" class="filter-select">
                <option value="">All status</option>
                <option value="true">Active</option>
                <option value="false">Suspended</option>
            </select>
            <select v-model="filterAdmin" class="filter-select">
                <option value="">All roles</option>
                <option value="true">Admin</option>
                <option value="false">User</option>
            </select>
            <select v-model="filterAuth" class="filter-select">
                <option value="">All auth methods</option>
                <option value="password">Password</option>
                <option value="google">Google</option>
                <option value="google+password">Both</option>
            </select>
        </div>

        <!-- Loading / Error -->
        <div v-if="loading" class="state-msg">Loading users…</div>
        <div v-else-if="error" class="state-msg error">{{ error }}</div>

        <!-- Table -->
        <div v-else class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th @click="sortBy('id')" class="sortable">
                            ID <span class="sort-arrow">{{ sortIcon('id') }}</span>
                        </th>
                        <th @click="sortBy('username')" class="sortable">
                            Username <span class="sort-arrow">{{ sortIcon('username') }}</span>
                        </th>
                        <th>Email</th>
                        <th>Auth</th>
                        <th @click="sortBy('is_active')" class="sortable">
                            Status <span class="sort-arrow">{{ sortIcon('is_active') }}</span>
                        </th>
                        <th>Role</th>
                        <th>Verified</th>
                        <th @click="sortBy('word_count')" class="sortable">
                            Words <span class="sort-arrow">{{ sortIcon('word_count') }}</span>
                        </th>
                        <th @click="sortBy('created_at')" class="sortable">
                            Joined <span class="sort-arrow">{{ sortIcon('created_at') }}</span>
                        </th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-if="filteredUsers.length === 0">
                        <td colspan="10" class="empty-row">No users match your filters.</td>
                    </tr>
                    <tr v-for="u in filteredUsers" :key="u.id" :class="{ suspended: !u.is_active }">
                        <td class="id-cell">{{ u.id }}</td>
                        <td class="username-cell">{{ u.username || '—' }}</td>
                        <td class="email-cell">
                            <span class="email-text" :class="{ masked: !revealEmails }">{{ u.email_masked }}</span>
                        </td>
                        <td>
                            <span :class="['badge', authBadgeClass(u.auth_method)]">{{ u.auth_method }}</span>
                        </td>
                        <td>
                            <span :class="['badge', u.is_active ? 'badge-active' : 'badge-inactive']">
                                {{ u.is_active ? 'Active' : 'Suspended' }}
                            </span>
                        </td>
                        <td>
                            <span :class="['badge', u.is_admin ? 'badge-admin' : 'badge-user']">
                                {{ u.is_admin ? 'Admin' : 'User' }}
                            </span>
                        </td>
                        <td>
                            <span :class="['badge', u.is_verified ? 'badge-verified' : 'badge-unverified']">
                                {{ u.is_verified ? '✓' : '✗' }}
                            </span>
                        </td>
                        <td class="num-cell">{{ u.word_count }}</td>
                        <td class="date-cell">{{ formatDate(u.created_at) }}</td>
                        <td class="actions-cell">
                            <button class="btn-icon" title="Edit flags" @click="openEdit(u)">✏️</button>
                            <button class="btn-icon btn-del" title="Delete user" @click="confirmDelete(u)">🗑️</button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Edit Modal -->
        <div v-if="editTarget" class="modal-overlay" @click.self="editTarget = null">
            <div class="modal">
                <h2>Edit User #{{ editTarget.id }}</h2>
                <p class="modal-subtitle">{{ editTarget.email_masked }}</p>

                <div class="flag-grid">
                    <label class="flag-row">
                        <span class="flag-label">Active</span>
                        <span class="flag-desc">User can log in and use the app</span>
                        <input type="checkbox" v-model="editForm.is_active" class="flag-toggle" />
                    </label>
                    <label class="flag-row">
                        <span class="flag-label">Admin</span>
                        <span class="flag-desc">Full access to admin pages</span>
                        <input type="checkbox" v-model="editForm.is_admin" class="flag-toggle"
                            :disabled="editTarget.id === currentAdminId" />
                    </label>
                    <label class="flag-row">
                        <span class="flag-label">Verified</span>
                        <span class="flag-desc">Email address confirmed</span>
                        <input type="checkbox" v-model="editForm.is_verified" class="flag-toggle" />
                    </label>
                </div>

                <div v-if="editError" class="form-error">{{ editError }}</div>
                <div class="modal-actions">
                    <button class="btn-secondary" @click="editTarget = null">Cancel</button>
                    <button class="btn-primary" :disabled="saving" @click="saveEdit">
                        {{ saving ? 'Saving…' : 'Save Changes' }}
                    </button>
                </div>
            </div>
        </div>

        <!-- Delete Confirmation Modal -->
        <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
            <div class="modal modal-small">
                <h2>Delete user #{{ deleteTarget.id }}?</h2>
                <p>
                    This will <strong>permanently delete</strong> the account for
                    <code>{{ deleteTarget.email_masked }}</code> and all their data
                    (words, game history, mistake records). This cannot be undone.
                </p>
                <div v-if="deleteError" class="form-error">{{ deleteError }}</div>
                <div class="modal-actions">
                    <button class="btn-secondary" @click="deleteTarget = null">Cancel</button>
                    <button class="btn-danger" :disabled="saving" @click="doDelete">
                        {{ saving ? 'Deleting…' : 'Delete permanently' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

// ── State ──────────────────────────────────────────────────────────────────
const users = ref([])
const loading = ref(true)
const error = ref('')
const revealEmails = ref(false)

const search = ref('')
const filterActive = ref('')
const filterAdmin = ref('')
const filterAuth = ref('')
const sortKey = ref('created_at')
const sortDir = ref('desc')

const editTarget = ref(null)
const editForm = ref({ is_active: true, is_admin: false, is_verified: false })
const editError = ref('')
const saving = ref(false)

const deleteTarget = ref(null)
const deleteError = ref('')

const currentAdminId = computed(() => auth.user?.id)

// ── Computed ───────────────────────────────────────────────────────────────
const filteredUsers = computed(() => {
    let list = users.value
    const q = search.value.toLowerCase()
    if (q) list = list.filter(u =>
        (u.username || '').toLowerCase().includes(q) ||
        u.email_masked.toLowerCase().includes(q)
    )
    if (filterActive.value !== '') list = list.filter(u => String(u.is_active) === filterActive.value)
    if (filterAdmin.value !== '') list = list.filter(u => String(u.is_admin) === filterAdmin.value)
    if (filterAuth.value) list = list.filter(u => u.auth_method === filterAuth.value)

    return [...list].sort((a, b) => {
        let va = a[sortKey.value] ?? ''
        let vb = b[sortKey.value] ?? ''
        if (typeof va === 'boolean') { va = va ? 1 : 0; vb = vb ? 1 : 0 }
        if (va < vb) return sortDir.value === 'asc' ? -1 : 1
        if (va > vb) return sortDir.value === 'asc' ? 1 : -1
        return 0
    })
})

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
    if (!auth.user?.is_admin) { router.push('/'); return }
    await fetchUsers()
})

// ── API ────────────────────────────────────────────────────────────────────
async function fetchUsers() {
    loading.value = true
    error.value = ''
    try {
        const ax = auth.getAuthAxios()
        const { data } = await ax.get(`/api/admin/users?reveal=${revealEmails.value}`)
        users.value = data
    } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to load users.'
    } finally {
        loading.value = false
    }
}

async function saveEdit() {
    editError.value = ''
    saving.value = true
    try {
        const ax = auth.getAuthAxios()
        const { data } = await ax.patch(`/api/admin/users/${editTarget.value.id}`, editForm.value)
        const idx = users.value.findIndex(u => u.id === data.id)
        if (idx !== -1) users.value[idx] = data
        editTarget.value = null
    } catch (e) {
        editError.value = e.response?.data?.detail || 'Failed to save changes.'
    } finally {
        saving.value = false
    }
}

async function doDelete() {
    if (!deleteTarget.value) return
    deleteError.value = ''
    saving.value = true
    try {
        const ax = auth.getAuthAxios()
        await ax.delete(`/api/admin/users/${deleteTarget.value.id}`)
        users.value = users.value.filter(u => u.id !== deleteTarget.value.id)
        deleteTarget.value = null
    } catch (e) {
        deleteError.value = e.response?.data?.detail || 'Failed to delete user.'
    } finally {
        saving.value = false
    }
}

// ── UI helpers ─────────────────────────────────────────────────────────────
function openEdit(u) {
    editTarget.value = u
    editForm.value = { is_active: u.is_active, is_admin: u.is_admin, is_verified: u.is_verified }
    editError.value = ''
}

function confirmDelete(u) {
    deleteTarget.value = u
    deleteError.value = ''
}

function sortBy(key) {
    if (sortKey.value === key) {
        sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
    } else {
        sortKey.value = key
        sortDir.value = 'asc'
    }
}

function sortIcon(key) {
    if (sortKey.value !== key) return '↕'
    return sortDir.value === 'asc' ? '↑' : '↓'
}

function formatDate(iso) {
    if (!iso) return '—'
    return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function authBadgeClass(method) {
    if (method === 'google') return 'badge-google'
    if (method === 'google+password') return 'badge-both'
    return 'badge-password'
}
</script>

<style scoped>
.admin-page {
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 20px 60px;
}

.admin-header {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 24px;
}

.admin-header h1 {
    font-size: 1.8rem;
    margin: 0;
    flex: 1;
}

.subtitle {
    color: #888;
    font-size: 0.95rem;
    margin: 0;
}

/* Reveal toggle */
.reveal-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    color: #555;
    padding: 6px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #f9f9f9;
    user-select: none;
}

.reveal-toggle input {
    cursor: pointer;
}

/* Filters */
.filters {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.filter-input {
    flex: 1;
    min-width: 200px;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 0.9rem;
    background: #f8f8f8;
}

.filter-select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 0.9rem;
    background: #f8f8f8;
}

/* Table */
.table-wrap {
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
}

thead {
    background: #f5f5f5;
}

th {
    padding: 12px 14px;
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
    color: #666;
    border-bottom: 2px solid #e0e0e0;
}

th.sortable {
    cursor: pointer;
    user-select: none;
}

th.sortable:hover {
    color: #667eea;
}

.sort-arrow {
    font-size: 0.75rem;
    opacity: 0.6;
}

td {
    padding: 10px 14px;
    border-bottom: 1px solid #eee;
    vertical-align: middle;
}

tr.suspended td {
    opacity: 0.5;
}

.state-msg {
    text-align: center;
    padding: 40px;
    color: #888;
}

.state-msg.error {
    color: #e53e3e;
}

.empty-row {
    text-align: center;
    color: #aaa;
    padding: 32px;
}

/* Cell styles */
.id-cell {
    color: #aaa;
    font-size: 0.85rem;
}

.username-cell {
    font-weight: 600;
}

.email-cell {
    font-family: monospace;
    font-size: 0.88rem;
}

.email-text.masked {
    color: #999;
    letter-spacing: 0.5px;
}

.num-cell,
.date-cell {
    color: #666;
    white-space: nowrap;
}

.actions-cell {
    display: flex;
    gap: 6px;
    align-items: center;
}

/* Badges */
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    white-space: nowrap;
}

.badge-active {
    background: #c6f6d5;
    color: #276749;
}

.badge-inactive {
    background: #fed7d7;
    color: #9b2c2c;
}

.badge-admin {
    background: #feebc8;
    color: #7b341e;
}

.badge-user {
    background: #e2e8f0;
    color: #4a5568;
}

.badge-verified {
    background: #c6f6d5;
    color: #276749;
}

.badge-unverified {
    background: #eee;
    color: #999;
}

.badge-google {
    background: #ebf8ff;
    color: #2b6cb0;
}

.badge-password {
    background: #f0fff4;
    color: #276749;
}

.badge-both {
    background: #faf5ff;
    color: #553c9a;
}

/* Buttons */
.btn-icon {
    background: none;
    border: 1px solid #ddd;
    border-radius: 6px;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 1rem;
    transition: background 0.15s;
}

.btn-icon:hover {
    background: #f0f0f0;
}

.btn-del:hover {
    background: #fff5f5;
    border-color: #fc8181;
}

.btn-primary {
    padding: 9px 20px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
}

.btn-primary:hover:not(:disabled) {
    background: #5a6fd6;
}

.btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.btn-secondary {
    padding: 9px 20px;
    background: white;
    color: #555;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
}

.btn-secondary:hover {
    background: #f5f5f5;
}

.btn-danger {
    padding: 9px 20px;
    background: #e53e3e;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
}

.btn-danger:hover:not(:disabled) {
    background: #c53030;
}

.btn-danger:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Modal */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
}

.modal {
    background: white;
    border-radius: 14px;
    padding: 32px;
    width: 100%;
    max-width: 440px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-small {
    max-width: 380px;
}

.modal h2 {
    margin: 0 0 4px;
    font-size: 1.3rem;
}

.modal-subtitle {
    font-family: monospace;
    font-size: 0.88rem;
    color: #888;
    margin: 0 0 20px;
}

.modal p {
    color: #555;
    line-height: 1.5;
    margin: 12px 0 0;
}

.modal p code {
    background: #f0f0f0;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 0.9em;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 24px;
}

/* Flag grid in edit modal */
.flag-grid {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: 16px;
}

.flag-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.12s;
}

.flag-row:hover {
    background: #f7f7f7;
}

.flag-label {
    font-weight: 700;
    font-size: 0.95rem;
    width: 72px;
    flex-shrink: 0;
}

.flag-desc {
    font-size: 0.85rem;
    color: #888;
    flex: 1;
}

.flag-toggle {
    width: 18px;
    height: 18px;
    cursor: pointer;
    flex-shrink: 0;
}

.form-error {
    margin-top: 12px;
    color: #e53e3e;
    font-size: 0.9rem;
    background: #fff5f5;
    border: 1px solid #fc8181;
    border-radius: 6px;
    padding: 8px 12px;
}
</style>
