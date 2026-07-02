import { createRouter, createWebHashHistory } from 'vue-router'
import Notes from '../views/Notes.vue'
import Plans from '../views/Plans.vue'
import Courses from '../views/Courses.vue'
import Literature from '../views/Literature.vue'

const routes = [
  { path: '/', redirect: '/notes' },
  { path: '/notes', component: Notes, meta: { title: '笔记闪卡' } },
  { path: '/plans', component: Plans, meta: { title: '备考计划' } },
  { path: '/courses', component: Courses, meta: { title: '课程管理' } },
  { path: '/literature', component: Literature, meta: { title: '文献管理' } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router