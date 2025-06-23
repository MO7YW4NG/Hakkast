import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Generate from '../views/Generate.vue'
import Library from '../views/Library.vue'
import Subscription from '../views/Subscription.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home
    },
    {
      path: '/generate',
      name: 'Generate',
      component: Generate
    },
    {
      path: '/library',
      name: 'Library',
      component: Library
    },
    {
      path: '/subscription',
      name: 'Subscription',
      component: Subscription
    }
  ]
})

export default router