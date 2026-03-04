import { createApp } from 'vue'
import AppMain from './AppMain.vue'
import router from './router.js'
import './style.css'
import '@fortawesome/fontawesome-free/css/all.css';

createApp(AppMain).use(router).mount('#app')
