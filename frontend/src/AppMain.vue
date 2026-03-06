<template>
  <navbar />
  <router-view />
</template>

<script>
import Navbar from './components/Navbar.vue'

export default {
  name: 'AppMain',
  components: {
    Navbar
  }
}
</script>

<style>
body {
  margin: 0;
  padding: 0;
}
</style>
