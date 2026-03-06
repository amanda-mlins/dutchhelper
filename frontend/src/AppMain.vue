<template>
  <navbar />
  <router-view />
</template>

<script>
import Navbar from './components/Navbar.vue'
import { useAuthStore } from './stores/auth.js'

export default {
  name: 'AppMain',
  components: {
    Navbar
  },
  setup() {
    // Kick off the silent token refresh as soon as the app mounts.
    // The router guard also calls initialize(), but doing it here too
    // ensures the Navbar user info is populated on first render.
    const auth = useAuthStore()
    auth.initialize()
  }
}
</script>

<style>
body {
  margin: 0;
  padding: 0;
}
</style>
