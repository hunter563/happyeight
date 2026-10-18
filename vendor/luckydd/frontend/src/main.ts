import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'
import App from './App.vue'
import router from './router'
import './style.css'
import { Capacitor } from '@capacitor/core'

// 适配安卓环境下的 API 地址
if (Capacitor.isNativePlatform()) {
  axios.defaults.baseURL = 'http://10.0.2.2:3000';
}

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')