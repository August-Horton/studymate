import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import Vant from 'vant'
import 'vant/lib/index.css'
import VantIcon from 'vant/lib/icon'

import './styles/theme.css'

const app = createApp(App)
app.use(router)
app.use(Vant)
app.use(VantIcon)

app.mount('#app')