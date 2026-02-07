import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomePage.vue'),
  },
  {
    path: '/recipe/:id',
    name: 'RecipeDetail',
    component: () => import('../views/RecipeDetail.vue'),
    props: true,
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginPage.vue'),
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/admin/RecipeList.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/recipe/new',
    name: 'AdminRecipeNew',
    component: () => import('../views/admin/RecipeEdit.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/recipe/:id/edit',
    name: 'AdminRecipeEdit',
    component: () => import('../views/admin/RecipeEdit.vue'),
    props: true,
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/tags',
    name: 'AdminTags',
    component: () => import('../views/admin/TagManage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/ingredients',
    name: 'AdminIngredients',
    component: () => import('../views/admin/IngredientManage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin/settings',
    name: 'AdminSettings',
    component: () => import('../views/admin/SettingsPage.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

// Auth guard
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const isLoggedIn = localStorage.getItem('recipe_admin_token')
    if (!isLoggedIn) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }
  next()
})

export default router
