<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isAdmin = computed(() => route.path.startsWith('/admin') && route.path !== '/admin/settings')
const mobileOpen = ref(false)

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex flex-col" style="background-color: var(--color-bg);">
    <!-- Header: Magazine-style fixed nav -->
    <header class="fixed top-0 left-0 right-0 z-50 header-blur">
      <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <!-- Brand: 味之集 -->
        <router-link to="/" class="flex items-center gap-2 no-underline group">
          <span class="brand-text">
            味<span class="brand-accent">之</span>集
          </span>
        </router-link>

        <!-- Nav links -->
        <nav class="hidden md:flex items-center gap-8 text-sm font-medium" style="color: var(--color-text-muted); font-family: var(--font-ui);">
          <router-link
            to="/"
            class="mag-nav-link"
            :class="{ 'mag-nav-active': route.path === '/' }"
          >
            首页
          </router-link>

          <router-link
            v-if="auth.isLoggedIn"
            to="/admin"
            class="mag-nav-link"
            :class="{ 'mag-nav-active': isAdmin }"
          >
            管理
          </router-link>

          <router-link
            v-if="auth.isLoggedIn"
            to="/admin/settings"
            class="mag-nav-link"
            :class="{ 'mag-nav-active': route.path === '/admin/settings' }"
          >
            设置
          </router-link>

          <template v-if="auth.isLoggedIn">
            <div class="w-px h-4" style="background: var(--color-border);"></div>
            <button
              class="mag-nav-link"
              style="cursor: pointer; border: none; background: none;"
              @click="handleLogout"
            >
              退出
            </button>
          </template>
          <router-link v-else to="/login" class="mag-nav-link">
            登录
          </router-link>
        </nav>

        <!-- Mobile menu button -->
        <button class="md:hidden" style="color: var(--color-text);" @click="mobileOpen = !mobileOpen">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>
      </div>

      <!-- Mobile menu -->
      <div v-if="mobileOpen" class="md:hidden border-t" style="border-color: var(--color-border); background: rgba(245, 240, 232, 0.95); backdrop-filter: blur(12px);">
        <div class="px-6 py-4 flex flex-col gap-3 text-sm font-medium" style="color: var(--color-text-muted); font-family: var(--font-ui);">
          <router-link to="/" class="mag-nav-link" :class="{ 'mag-nav-active': route.path === '/' }" @click="mobileOpen = false">首页</router-link>
          <router-link v-if="auth.isLoggedIn" to="/admin" class="mag-nav-link" :class="{ 'mag-nav-active': isAdmin }" @click="mobileOpen = false">管理</router-link>
          <router-link v-if="auth.isLoggedIn" to="/admin/settings" class="mag-nav-link" :class="{ 'mag-nav-active': route.path === '/admin/settings' }" @click="mobileOpen = false">设置</router-link>
          <button v-if="auth.isLoggedIn" class="mag-nav-link text-left" style="border: none; background: none; cursor: pointer;" @click="handleLogout">退出</button>
          <router-link v-else to="/login" class="mag-nav-link" @click="mobileOpen = false">登录</router-link>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 max-w-7xl mx-auto w-full px-6 pt-24 pb-8">
      <router-view />
    </main>

    <!-- Footer: Magazine style -->
    <footer class="mt-auto" style="border-top: 1px solid var(--color-border);">
      <div class="max-w-7xl mx-auto px-6 py-8">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <span class="footer-brand">
            味<span style="color: var(--color-primary);">之</span>集
          </span>
          <div class="w-12 h-px md:hidden" style="background: var(--color-border);"></div>
          <span class="text-xs" style="color: var(--color-text-muted); font-family: var(--font-heading); font-style: italic; letter-spacing: 0.05em;">
            Crafted with care
          </span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.header-blur {
  background: rgb(245, 240, 232);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border);
}

.brand-text {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--color-text);
  transition: color 0.25s ease;
}
.brand-accent {
  color: var(--color-primary);
}
.group:hover .brand-text {
  color: var(--color-primary);
}

.mag-nav-link {
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.2s ease;
  font-family: var(--font-ui);
  font-size: 0.875rem;
}
.mag-nav-link:hover {
  color: var(--color-primary);
}
.mag-nav-active {
  color: var(--color-text);
}

.footer-brand {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}
</style>
