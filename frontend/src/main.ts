import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import 'highlight.js/styles/github-dark.css'
import router from './router' // 🌟 新增引入路由

const app = createApp(App)

app.use(ElementPlus)
app.use(createPinia())
app.use(router) // 🌟 挂载路由
app.mount('#app')