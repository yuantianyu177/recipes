<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isAdmin = computed(() => route.path.startsWith('/admin') && route.path !== '/admin/settings')

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen bg-[#faf9f7] flex flex-col">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-gray-100">
      <div class="max-w-6xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2.5 no-underline group">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow">
            <span class="text-lg">🍳</span>
          </div>
          <span class="text-lg font-bold bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
            我的菜谱
          </span>
        </router-link>

        <!-- Nav -->
        <nav class="flex items-center gap-1">
          <router-link
            to="/"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-all no-underline"
            :class="route.path === '/' ? 'text-orange-600 bg-orange-50' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'"
          >
            首页
          </router-link>

          <router-link
            v-if="auth.isLoggedIn"
            to="/admin"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-all no-underline"
            :class="isAdmin ? 'text-orange-600 bg-orange-50' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'"
          >
            管理
          </router-link>

          <router-link
            v-if="auth.isLoggedIn"
            to="/admin/settings"
            class="px-4 py-2 rounded-lg text-sm font-medium transition-all no-underline"
            :class="route.path === '/admin/settings' ? 'text-orange-600 bg-orange-50' : 'text-gray-500 hover:text-gray-800 hover:bg-gray-50'"
          >
            设置
          </router-link>

          <template v-if="auth.isLoggedIn">
            <div class="w-px h-5 bg-gray-200 mx-1"></div>
            <button
              class="px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all"
              @click="handleLogout"
            >
              退出
            </button>
          </template>
          <router-link
            v-else
            to="/login"
            class="px-4 py-2 rounded-lg text-sm font-medium text-gray-500 hover:text-orange-600 hover:bg-orange-50 transition-all no-underline"
          >
            登录
          </router-link>
        </nav>
      </div>
    </header>

    <!-- Main Content (flex-1 pushes footer to bottom) -->
    <main class="flex-1 max-w-6xl mx-auto w-full px-4 md:px-8 py-8">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="border-t border-gray-100 bg-white mt-auto">
      <div class="max-w-6xl mx-auto px-4 md:px-8 py-6 text-center text-xs text-gray-400">
        Designed by nate · Recipes
      </div>
    </footer>
  </div>
</template>
