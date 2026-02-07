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
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center shadow-lg">
          <span class="text-4xl">🍳</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-800">管理员登录</h1>
        <p class="text-gray-400 text-sm mt-1">登录后可管理菜谱内容</p>
      </div>

      <!-- Form -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <div class="mb-5">
          <label class="block text-sm font-medium text-gray-600 mb-1.5">用户名</label>
          <input
            v-model="username"
            type="text"
            placeholder="请输入用户名"
            class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-orange-400 focus:ring-2 focus:ring-orange-100 outline-none transition-all text-sm"
            @keyup.enter="handleLogin"
          />
        </div>
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-600 mb-1.5">密码</label>
          <input
            v-model="password"
            type="password"
            placeholder="请输入密码"
            class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-orange-400 focus:ring-2 focus:ring-orange-100 outline-none transition-all text-sm"
            @keyup.enter="handleLogin"
          />
        </div>
        <button
          :disabled="loading"
          class="w-full py-2.5 rounded-xl bg-gradient-to-r from-orange-400 to-red-500 text-white font-medium text-sm hover:shadow-lg hover:shadow-orange-200 transition-all duration-300 disabled:opacity-60"
          @click="handleLogin"
        >
          {{ loading ? '登录中...' : '登 录' }}
        </button>
      </div>

      <p class="text-center text-xs text-gray-400 mt-4">
        默认账号: admin / admin123
      </p>
    </div>
  </div>
</template>
