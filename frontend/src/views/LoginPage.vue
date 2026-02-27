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
  <div class="login-page">
    <!-- Decorative background elements -->
    <div class="login-bg-deco">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
      <div class="bg-circle bg-circle-3"></div>
    </div>

    <div class="login-container">
      <!-- Left: Editorial illustration panel -->
      <div class="login-editorial">
        <div class="editorial-inner">
          <!-- Large decorative leaf SVG -->
          <svg class="editorial-leaf" viewBox="0 0 120 160" fill="none">
            <path d="M60 10C60 10 20 40 20 90C20 115 35 140 60 155" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.8"/>
            <path d="M60 10C60 10 100 40 100 90C100 115 85 140 60 155" stroke="var(--color-secondary)" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.8"/>
            <path d="M60 155V170" stroke="var(--color-accent)" stroke-width="2.5" stroke-linecap="round" opacity="0.6"/>
            <circle cx="60" cy="10" r="4" fill="var(--color-primary)" opacity="0.5"/>
            <!-- Vein lines -->
            <path d="M60 40C60 40 40 55 35 75" stroke="var(--color-primary)" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.2"/>
            <path d="M60 40C60 40 80 55 85 75" stroke="var(--color-secondary)" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.2"/>
            <path d="M60 70C60 70 42 82 38 100" stroke="var(--color-primary)" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.15"/>
            <path d="M60 70C60 70 78 82 82 100" stroke="var(--color-secondary)" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.15"/>
          </svg>

          <!-- Editorial text -->
          <div class="editorial-text">
            <span class="editorial-label">Est. 2024</span>
            <h2 class="editorial-brand">
              味<span class="brand-accent">之</span>集
            </h2>
            <div class="editorial-divider"></div>
            <p class="editorial-tagline">Personal Recipe Collection</p>
            <p class="editorial-desc">记录每一道用心烹制的味道</p>
          </div>

          <!-- Decorative corner marks -->
          <div class="corner-mark corner-tl"></div>
          <div class="corner-mark corner-br"></div>
        </div>
      </div>

      <!-- Right: Login form -->
      <div class="login-form-panel">
        <div class="form-inner">
          <!-- Section label -->
          <div class="form-label-row">
            <span class="form-label-line"></span>
            <span class="form-label-text">Admin Access</span>
            <span class="form-label-line"></span>
          </div>

          <h1 class="form-title">管理员登录</h1>
          <p class="form-subtitle">登录后可管理菜谱内容</p>

          <!-- Form card -->
          <div class="form-card">
            <div class="form-field">
              <label class="field-label">
                <svg class="field-icon" viewBox="0 0 20 20" fill="none">
                  <circle cx="10" cy="7" r="3.5" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M3 18C3 14.134 6.134 11 10 11C13.866 11 17 14.134 17 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
                <span>用户名</span>
              </label>
              <input
                v-model="username"
                type="text"
                placeholder="请输入用户名"
                class="input-warm login-input"
                @keyup.enter="handleLogin"
              />
            </div>

            <div class="form-field">
              <label class="field-label">
                <svg class="field-icon" viewBox="0 0 20 20" fill="none">
                  <rect x="4" y="9" width="12" height="9" rx="2" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M7 9V6C7 4.343 8.343 3 10 3C11.657 3 13 4.343 13 6V9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  <circle cx="10" cy="14" r="1.5" fill="currentColor"/>
                </svg>
                <span>密码</span>
              </label>
              <input
                v-model="password"
                type="password"
                placeholder="请输入密码"
                class="input-warm login-input"
                @keyup.enter="handleLogin"
              />
            </div>

            <button
              :disabled="loading"
              class="login-btn"
              @click="handleLogin"
            >
              <div v-if="loading" class="spinner-warm-sm" style="border-color: rgba(255,255,255,0.3); border-top-color: white;"></div>
              <span>{{ loading ? '登录中...' : '登 录' }}</span>
              <svg v-if="!loading" class="btn-arrow" viewBox="0 0 20 20" fill="none">
                <path d="M4 10H16M16 10L11 5M16 10L11 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>

          <!-- Hint -->
          <div class="form-hint">
            <svg class="hint-icon" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1"/>
              <path d="M8 7V11" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              <circle cx="8" cy="5" r="0.75" fill="currentColor"/>
            </svg>
            <span>默认账号: admin / admin123</span>
          </div>

          <!-- Bottom flourish -->
          <div class="form-flourish">
            <div class="flourish-line"></div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 4L14.5 9.5L20 12L14.5 14.5L12 20L9.5 14.5L4 12L9.5 9.5L12 4Z" fill="var(--color-primary)" opacity="0.25"/>
            </svg>
            <div class="flourish-line"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ===== Page Layout ===== */
.login-page {
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 2rem 1rem;
}

/* ===== Background Decoration ===== */
.login-bg-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.04;
}
.bg-circle-1 {
  width: 500px;
  height: 500px;
  background: var(--color-primary);
  top: -150px;
  right: -100px;
  animation: floatSlow 20s ease-in-out infinite;
}
.bg-circle-2 {
  width: 350px;
  height: 350px;
  background: var(--color-secondary);
  bottom: -100px;
  left: -80px;
  animation: floatSlow 25s ease-in-out infinite reverse;
}
.bg-circle-3 {
  width: 200px;
  height: 200px;
  background: var(--color-accent);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: floatSlow 18s ease-in-out infinite;
}

@keyframes floatSlow {
  0%, 100% { transform: translate(0, 0); }
  33% { transform: translate(15px, -20px); }
  66% { transform: translate(-10px, 15px); }
}

/* ===== Container ===== */
.login-container {
  display: flex;
  width: 100%;
  max-width: 52rem;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1.25rem;
  overflow: hidden;
  box-shadow:
    0 4px 24px rgba(61, 51, 41, 0.06),
    0 12px 48px rgba(61, 51, 41, 0.04);
  animation: cardReveal 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes cardReveal {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ===== Editorial Panel (Left) ===== */
.login-editorial {
  flex: 0 0 44%;
  background: linear-gradient(
    160deg,
    rgba(196, 93, 62, 0.06) 0%,
    rgba(91, 122, 94, 0.06) 50%,
    rgba(212, 168, 83, 0.06) 100%
  );
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid var(--color-border);
}
.login-editorial::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 0L30 60M0 30L60 30' stroke='%23e5ddd1' stroke-width='0.5' opacity='0.3'/%3E%3C/svg%3E");
  background-size: 60px 60px;
  opacity: 0.4;
}

.editorial-inner {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 3rem 2rem;
  animation: editorialFade 0.8s ease-out 0.2s both;
}

@keyframes editorialFade {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.editorial-leaf {
  width: 80px;
  height: auto;
  margin: 0 auto 1.5rem;
  animation: leafDraw 1.5s ease-out 0.5s both;
}

@keyframes leafDraw {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

.editorial-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.editorial-label {
  font-family: var(--font-ui);
  font-size: 0.625rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  font-weight: 500;
}

.editorial-brand {
  font-family: var(--font-heading);
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  line-height: 1.1;
}
.brand-accent {
  color: var(--color-primary);
}

.editorial-divider {
  width: 40px;
  height: 1px;
  background: var(--color-primary);
  margin: 0.5rem 0;
  opacity: 0.5;
}

.editorial-tagline {
  font-family: var(--font-heading);
  font-size: 0.75rem;
  font-style: italic;
  color: var(--color-text-muted);
  letter-spacing: 0.08em;
}

.editorial-desc {
  font-family: var(--font-body);
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  line-height: 1.6;
  margin-top: 0.25rem;
}

/* Corner marks */
.corner-mark {
  position: absolute;
  width: 20px;
  height: 20px;
}
.corner-mark::before,
.corner-mark::after {
  content: '';
  position: absolute;
  background: var(--color-primary);
  opacity: 0.15;
}
.corner-tl {
  top: 1.5rem;
  left: 1.5rem;
}
.corner-tl::before {
  top: 0; left: 0;
  width: 20px; height: 1px;
}
.corner-tl::after {
  top: 0; left: 0;
  width: 1px; height: 20px;
}
.corner-br {
  bottom: 1.5rem;
  right: 1.5rem;
}
.corner-br::before {
  bottom: 0; right: 0;
  width: 20px; height: 1px;
}
.corner-br::after {
  bottom: 0; right: 0;
  width: 1px; height: 20px;
}

/* ===== Form Panel (Right) ===== */
.login-form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 2.5rem;
}

.form-inner {
  width: 100%;
  max-width: 20rem;
  animation: formSlideIn 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both;
}

@keyframes formSlideIn {
  from { opacity: 0; transform: translateX(16px); }
  to { opacity: 1; transform: translateX(0); }
}

/* Section label */
.form-label-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.form-label-line {
  flex: 1;
  height: 1px;
  background: var(--color-border);
}
.form-label-text {
  font-family: var(--font-ui);
  font-size: 0.625rem;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  font-weight: 600;
  white-space: nowrap;
}

.form-title {
  font-family: var(--font-heading);
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
  margin-bottom: 0.375rem;
}

.form-subtitle {
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  margin-bottom: 2rem;
}

/* Form card */
.form-card {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--color-text);
}

.field-icon {
  width: 1rem;
  height: 1rem;
  color: var(--color-text-muted);
}

.login-input {
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.login-input:focus {
  background: var(--color-card);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(196, 93, 62, 0.08);
}

/* Login button */
.login-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem 1.5rem;
  margin-top: 0.5rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  font-family: var(--font-ui);
  color: #fff;
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}
.login-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.1) 50%, transparent 60%);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}
.login-btn:hover::before {
  transform: translateX(100%);
}
.login-btn:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
  box-shadow: 0 6px 20px rgba(196, 93, 62, 0.3);
  transform: translateY(-1px);
}
.login-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(196, 93, 62, 0.2);
}
.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
.login-btn:disabled::before {
  display: none;
}

.btn-arrow {
  width: 1rem;
  height: 1rem;
  transition: transform 0.25s ease;
}
.login-btn:hover .btn-arrow {
  transform: translateX(3px);
}

/* Hint */
.form-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  margin-top: 1.5rem;
  padding: 0.625rem 1rem;
  border-radius: 0.5rem;
  background: rgba(212, 168, 83, 0.08);
  border: 1px solid rgba(212, 168, 83, 0.15);
}
.form-hint span {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--color-accent);
  font-weight: 500;
}
.hint-icon {
  width: 0.875rem;
  height: 0.875rem;
  color: var(--color-accent);
  flex-shrink: 0;
}

/* Bottom flourish */
.form-flourish {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 2rem;
}
.flourish-line {
  width: 40px;
  height: 1px;
  background: var(--color-border);
}

/* ===== Mobile Responsive ===== */
@media (max-width: 767px) {
  .login-page {
    padding: 1rem;
    min-height: 75vh;
  }

  .login-container {
    flex-direction: column;
    max-width: 24rem;
  }

  .login-editorial {
    flex: none;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
    padding: 0;
  }

  .editorial-inner {
    padding: 2rem 1.5rem;
  }

  .editorial-leaf {
    width: 50px;
    margin-bottom: 1rem;
  }

  .editorial-brand {
    font-size: 1.75rem;
  }

  .editorial-desc {
    display: none;
  }

  .corner-mark {
    display: none;
  }

  .login-form-panel {
    padding: 2rem 1.5rem;
  }

  .form-title {
    font-size: 1.5rem;
  }

  .form-label-row {
    margin-bottom: 1rem;
  }

  .form-subtitle {
    margin-bottom: 1.5rem;
  }
}

@media (max-width: 480px) {
  .login-form-panel {
    padding: 1.5rem 1.25rem;
  }

  .login-input {
    font-size: 16px;
  }
}
</style>
