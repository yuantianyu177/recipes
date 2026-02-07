import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiLogin } from '../api/index'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('recipe_admin_token') || '')
  const isLoggedIn = computed(() => !!token.value)

  async function login(username, password) {
    try {
      const data = await apiLogin(username, password)
      token.value = data.access_token
      localStorage.setItem('recipe_admin_token', data.access_token)
      return true
    } catch (err) {
      return false
    }
  }

  function logout() {
    token.value = ''
    localStorage.removeItem('recipe_admin_token')
  }

  return { token, isLoggedIn, login, logout }
})
