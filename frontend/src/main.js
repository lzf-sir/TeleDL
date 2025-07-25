import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import websocket from './api/websocket'

const app = createApp(App)

app.use(router)
app.use(ElementPlus)

app.mount('#app')

// 初始化WebSocket连接
websocket.connect()
