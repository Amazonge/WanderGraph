import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/Home.vue') },
    { path: '/recommendations', name: 'recommendations', component: () => import('@/views/Recommendations.vue') },
    { path: '/reviews', name: 'reviews', component: () => import('@/views/Reviews.vue') },
    { path: '/plan/:id', name: 'plan', component: () => import('@/views/Plan.vue') },
    { path: '/history', name: 'history', component: () => import('@/views/History.vue') },
    { path: '/profile', name: 'profile', component: () => import('@/views/Profile.vue') },
    { path: '/login', name: 'login', component: () => import('@/views/Auth/Login.vue') },
    { path: '/register', name: 'register', component: () => import('@/views/Auth/Register.vue') },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFound.vue') },
  ],
})

export default router
