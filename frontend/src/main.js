import { createApp } from 'vue'
import { createPinia } from 'pinia'
import AppMain from './AppMain.vue'
import router from './router.js'
import './style.css'
import '@fortawesome/fontawesome-free/css/all.css';

const app = createApp(AppMain)
app.use(createPinia())
app.use(router)
app.mount('#app')
