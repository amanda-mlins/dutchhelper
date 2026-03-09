import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import SentenceExplainer from './views/SentenceExplainer.vue'
import Conjugator from './views/Conjugator.vue'
import ArticleGame from './views/ArticleGame.vue'
import ArticleGameStats from './views/ArticleGameStats.vue'
import WordBank from './views/WordBank.vue'
import Flashcards from './views/Flashcards.vue'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import AuthCallback from './views/AuthCallback.vue'
import AdminWords from './views/AdminWords.vue'
import AdminVerbs from './views/AdminVerbs.vue'
import { useAuthStore } from './stores/auth.js'

const routes = [
  // ── Public routes ─────────────────────────────────────────────────────────
  {
    path: '/conjugator',
    name: 'Conjugator',
    component: Conjugator,
    meta: { public: true }
  },
  {
    path: '/conjugator/:verb',
    name: 'ConjugatorWithVerb',
    component: Conjugator,
    meta: { public: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true, guestOnly: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { public: true, guestOnly: true }
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: AuthCallback,
    meta: { public: true }
  },
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { public: true }
  },

  // ── Protected routes (require login) ─────────────────────────────────────
  {
    path: '/sentence-explainer',
    name: 'SentenceExplainer',
    component: SentenceExplainer
  },
  {
    path: '/article-game',
    name: 'ArticleGame',
    component: ArticleGame,
    meta: { public: true }
  },
  {
    path: '/article-game/stats',
    name: 'ArticleGameStats',
    component: ArticleGameStats,
  },
  {
    path: '/word-bank',
    name: 'WordBank',
    component: WordBank
  },
  {
    path: '/flashcards',
    name: 'Flashcards',
    component: Flashcards
  },

  // ── Admin routes (require is_admin) ───────────────────────────────────────
  {
    path: '/admin/words',
    name: 'AdminWords',
    component: AdminWords,
    meta: { adminOnly: true }
  },
  {
    path: '/admin/verbs',
    name: 'AdminVerbs',
    component: AdminVerbs,
    meta: { adminOnly: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Wait for the silent refresh to finish before making any guard decisions
  if (auth.initializing) {
    await auth.initialize()
  }

  // Already logged in → don't let them visit login/register
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'Home' }
  }

  // Route requires auth and user is not logged in → redirect to login
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  // Route requires admin and user is not admin → redirect home
  if (to.meta.adminOnly && !auth.user?.is_admin) {
    return { name: 'Home' }
  }
})

export default router
