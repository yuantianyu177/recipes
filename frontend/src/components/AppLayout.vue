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
  <div class="min-h-screen flex flex-col" style="background-color: var(--color-bg);">
    <!-- Header -->
    <header class="sticky top-0 z-50 header-blur">
      <div class="max-w-6xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between">
        <!-- Logo with SVG mark -->
        <router-link to="/" class="flex items-center gap-2 no-underline group">
          <!-- Hand-drawn sprig/whisk SVG logo mark -->
          <svg class="logo-mark" width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 4C14 4 8 8 8 14C8 17 10 20 14 22" stroke="var(--color-primary)" stroke-width="1.8" stroke-linecap="round" fill="none"/>
            <path d="M14 4C14 4 20 8 20 14C20 17 18 20 14 22" stroke="var(--color-secondary)" stroke-width="1.8" stroke-linecap="round" fill="none"/>
            <path d="M14 22V26" stroke="var(--color-accent)" stroke-width="1.8" stroke-linecap="round"/>
            <circle cx="14" cy="4" r="1.5" fill="var(--color-primary)" opacity="0.7"/>
            <path d="M10 10Q12 12 14 10" stroke="var(--color-primary)" stroke-width="1.2" stroke-linecap="round" fill="none" opacity="0.5"/>
            <path d="M14 10Q16 12 18 10" stroke="var(--color-secondary)" stroke-width="1.2" stroke-linecap="round" fill="none" opacity="0.5"/>
          </svg>
          <span class="logo-text">
            My Recipes
          </span>
        </router-link>

        <!-- Nav -->
        <nav class="flex items-center gap-0.5">
          <router-link
            to="/"
            class="nav-link"
            :class="{ 'nav-link-active': route.path === '/' }"
          >
            <svg class="w-4 h-4 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4"/></svg>
            <span class="hidden sm:inline">首页</span>
          </router-link>

          <router-link
            v-if="auth.isLoggedIn"
            to="/admin"
            class="nav-link"
            :class="{ 'nav-link-active': isAdmin }"
          >
            <svg class="w-4 h-4 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"/></svg>
            <span class="hidden sm:inline">管理</span>
          </router-link>

          <router-link
            v-if="auth.isLoggedIn"
            to="/admin/settings"
            class="nav-link"
            :class="{ 'nav-link-active': route.path === '/admin/settings' }"
          >
            <svg class="w-4 h-4 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            <span class="hidden sm:inline">设置</span>
          </router-link>

          <template v-if="auth.isLoggedIn">
            <div class="w-px h-5 mx-1 sm:mx-2 hidden sm:block" style="background: var(--color-border);"></div>
            <button
              class="nav-link"
              style="cursor: pointer; border: none; background: none;"
              @click="handleLogout"
            >
              <svg class="w-4 h-4 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
              <span class="hidden sm:inline">退出</span>
            </button>
          </template>
          <router-link
            v-else
            to="/login"
            class="nav-link"
          >
            <span>登录</span>
          </router-link>
        </nav>
      </div>
      <!-- Bottom decorative line -->
      <div class="wavy-divider"></div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 max-w-6xl mx-auto w-full px-4 md:px-8 py-8">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="mt-auto" style="border-top: 1px solid var(--color-border);">
      <div class="max-w-6xl mx-auto px-4 md:px-8 py-6 flex items-center justify-center gap-2 text-xs" style="color: var(--color-text-muted);">
        <!-- Tiny footer logo mark -->
        <svg width="14" height="14" viewBox="0 0 28 28" fill="none" opacity="0.5">
          <path d="M14 4C14 4 8 8 8 14C8 17 10 20 14 22" stroke="var(--color-primary)" stroke-width="2" stroke-linecap="round" fill="none"/>
          <path d="M14 4C14 4 20 8 20 14C20 17 18 20 14 22" stroke="var(--color-secondary)" stroke-width="2" stroke-linecap="round" fill="none"/>
          <path d="M14 22V26" stroke="var(--color-accent)" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span style="font-family: var(--font-heading); font-style: italic; letter-spacing: 0.05em;">Crafted with care by nate</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.header-blur {
  background: rgba(245, 240, 232, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border);
}

.logo-mark {
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.group:hover .logo-mark {
  transform: rotate(8deg) scale(1.05);
}

.logo-text {
  font-family: var(--font-heading);
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: -0.01em;
  transition: color 0.25s ease;
}
.group:hover .logo-text {
  color: var(--color-primary-hover);
}
</style>
