import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import SentenceExplainer from './views/SentenceExplainer.vue'
import Conjugator from './views/Conjugator.vue'
import ArticleGame from './views/ArticleGame.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/sentence-explainer',
    name: 'SentenceExplainer',
    component: SentenceExplainer
  },
  {
    path: '/conjugator',
    name: 'Conjugator',
    component: Conjugator
  },
  {
    path: '/conjugator/:verb',
    name: 'ConjugatorWithVerb',
    component: Conjugator
  },
  {
    path: '/article-game',
    name: 'ArticleGame',
    component: ArticleGame
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
