import { createRouter, createWebHistory } from 'vue-router'

import TaskList from './views/TaskList.vue'
import TaskDetail from './views/TaskDetail.vue'
import Config from './views/Config.vue'

const routes = [
  { path: '/', component: TaskList },
  { path: '/task/:id', component: TaskDetail },
  { path: '/config', component: Config }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
