<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    message.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  const ok = await auth.login(username.value, password.value)
  loading.value = false
  if (ok) {
    message.success('登录成功')
    const redirect = route.query.redirect || '/admin'
    router.push(redirect)
  } else {
    message.error('用户名或密码错误')
  }
}
</script>

<template>
  <div class="min-h-[80vh] flex items-center justify-center">
    <div class="w-full max-w-sm px-4 sm:px-0 animate-fade-in-up">
      <!-- Logo mark + title -->
      <div class="text-center mb-8">
        <svg class="mx-auto mb-4" width="48" height="48" viewBox="0 0 28 28" fill="none">
          <path d="M14 4C14 4 8 8 8 14C8 17 10 20 14 22" stroke="var(--color-primary)" stroke-width="1.8" stroke-linecap="round" fill="none"/>
          <path d="M14 4C14 4 20 8 20 14C20 17 18 20 14 22" stroke="var(--color-secondary)" stroke-width="1.8" stroke-linecap="round" fill="none"/>
          <path d="M14 22V26" stroke="var(--color-accent)" stroke-width="1.8" stroke-linecap="round"/>
          <circle cx="14" cy="4" r="1.5" fill="var(--color-primary)" opacity="0.7"/>
        </svg>
        <h1 class="text-2xl font-bold mb-1" style="font-family: var(--font-heading); color: var(--color-text);">管理员登录</h1>
        <p class="text-sm" style="color: var(--color-text-muted);">登录后可管理菜谱内容</p>
      </div>

      <!-- Form -->
      <div class="card-warm rounded-2xl p-8" style="box-shadow: 0 4px 20px rgba(61, 51, 41, 0.08);">
        <div class="mb-5">
          <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text); font-family: var(--font-ui);">用户名</label>
          <input
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            class="input-warm"
            @keyup.enter="handleLogin"
          />
        </div>
        <div class="mb-6">
          <label class="block text-sm font-medium mb-1.5" style="color: var(--color-text); font-family: var(--font-ui);">密码</label>
          <input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            class="input-warm"
            @keyup.enter="handleLogin"
          />
        </div>
        <button
          :disabled="loading"
          class="btn-primary w-full py-2.5"
          @click="handleLogin"
        >
          <div v-if="loading" class="spinner-warm-sm" style="border-color: rgba(255,255,255,0.3); border-top-color: white;"></div>
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </div>

      <p class="text-center text-xs mt-4" style="color: var(--color-text-muted);">
        默认账号: admin / admin123
      </p>
    </div>
  </div>
</template>
