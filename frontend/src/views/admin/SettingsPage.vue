<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useMessage } from 'naive-ui'
import { useRecipeStore } from '../../stores/recipe'
import {
  apiSetupSearchIndex, apiSetSynonyms, apiGetSynonyms,
  apiExportRecipeBatch, apiImportRecipes,
  apiChangePassword,
} from '../../api/index'

const store = useRecipeStore()
const message = useMessage()

onMounted(async () => {
  await store.fetchRecipes()
  setupScrollAnimations()
  // Load existing synonyms
  try {
    const data = await apiGetSynonyms()
    if (data && typeof data === 'object') {
      const visited = new Set()
      const lines = []
      for (const [key, vals] of Object.entries(data)) {
        if (visited.has(key)) continue
        const group = [key, ...vals]
        group.forEach((w) => visited.add(w))
        lines.push(`${key}=${vals.join(',')}`)
      }
      synonymsText.value = lines.join('\n')
    }
  } catch {
    // Ignore if MeiliSearch not configured
  }
})

function setupScrollAnimations() {
  const fadeObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible')
      })
    },
    { threshold: 0.1 }
  )
  nextTick(() => {
    document.querySelectorAll('.fade-up').forEach(el => fadeObserver.observe(el))
  })
}

// ===========================================
// Password change
// ===========================================
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordLoading = ref(false)

async function handleChangePassword() {
  if (!oldPassword.value || !newPassword.value) {
    message.warning('请填写完整')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    message.error('两次输入的新密码不一致')
    return
  }
  if (newPassword.value.length < 4) {
    message.error('新密码长度至少 4 位')
    return
  }
  passwordLoading.value = true
  try {
    await apiChangePassword(oldPassword.value, newPassword.value)
    message.success('密码已修改')
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (err) {
    message.error(err.message || '修改失败')
  } finally {
    passwordLoading.value = false
  }
}

// ===========================================
// Search settings
// ===========================================
const searchSetupLoading = ref(false)
const synonymsText = ref('')
const synonymsLoading = ref(false)

async function handleSetupSearch() {
  searchSetupLoading.value = true
  try {
    await apiSetupSearchIndex()
    message.success('搜索索引配置成功')
  } catch (err) {
    message.error('配置失败: ' + (err.message || ''))
  } finally {
    searchSetupLoading.value = false
  }
}

async function handleSaveSynonyms() {
  synonymsLoading.value = true
  try {
    const synonyms = {}
    for (const line of synonymsText.value.split('\n')) {
      const trimmed = line.trim()
      if (!trimmed || !trimmed.includes('=')) continue
      const [key, vals] = trimmed.split('=', 2)
      const k = key.trim()
      if (k && vals) {
        synonyms[k] = vals.split(',').map((v) => v.trim()).filter(Boolean)
      }
    }
    if (Object.keys(synonyms).length === 0) {
      message.warning('没有有效的同义词配置')
      return
    }
    await apiSetSynonyms(synonyms)
    message.success('同义词已保存')
  } catch (err) {
    message.error('保存失败: ' + (err.message || ''))
  } finally {
    synonymsLoading.value = false
  }
}

// ===========================================
// Batch export
// ===========================================
const showExportModal = ref(false)
const selectedExportIds = ref([])
const exporting = ref(false)

function openExportModal() {
  selectedExportIds.value = []
  showExportModal.value = true
}

function toggleExportId(id) {
  const idx = selectedExportIds.value.indexOf(id)
  if (idx === -1) {
    selectedExportIds.value.push(id)
  } else {
    selectedExportIds.value.splice(idx, 1)
  }
}

function toggleExportAll() {
  if (selectedExportIds.value.length === store.recipes.length) {
    selectedExportIds.value = []
  } else {
    selectedExportIds.value = store.recipes.map((r) => r.id)
  }
}

async function handleExport() {
  if (selectedExportIds.value.length === 0) {
    message.warning('请选择至少一道菜谱')
    return
  }
  exporting.value = true
  try {
    const blob = await apiExportRecipeBatch(selectedExportIds.value)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'recipes_export.zip'
    a.click()
    URL.revokeObjectURL(url)
    showExportModal.value = false
    message.success(`已导出 ${selectedExportIds.value.length} 道菜谱`)
  } catch (err) {
    message.error('导出失败: ' + (err.message || ''))
  } finally {
    exporting.value = false
  }
}

// ===========================================
// Batch import
// ===========================================
const importing = ref(false)

function triggerImport() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.zip'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    importing.value = true
    try {
      const result = await apiImportRecipes(file)
      await store.fetchRecipes()
      message.success(`成功导入 ${result.count} 道菜谱`)
    } catch (err) {
      message.error('导入失败: ' + (err.message || ''))
    } finally {
      importing.value = false
    }
  }
  input.click()
}
</script>

<template>
  <div class="admin-settings max-w-3xl mx-auto">
    <!-- Editorial Header -->
    <section class="admin-hero fade-up">
      <p class="admin-subtitle">System Settings</p>
      <div class="deco-line mb-4"></div>
      <h1 class="admin-title">系统设置</h1>
      <p class="admin-desc">管理密码、搜索引擎配置和数据导入导出。</p>
    </section>

    <div class="space-y-8">
      <!-- Password Settings -->
      <section class="fade-up">
        <div class="section-label">
          <svg class="w-4 h-4" style="color: var(--color-primary);" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span>安全设置</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <h3 class="setting-title">修改密码</h3>
          <p class="setting-desc">修改管理员登录密码</p>
          <div class="space-y-3 max-w-sm">
            <input v-model="oldPassword" type="password" placeholder="当前密码" class="input-warm w-full" />
            <input v-model="newPassword" type="password" placeholder="新密码" class="input-warm w-full" />
            <input v-model="confirmPassword" type="password" placeholder="确认新密码" class="input-warm w-full" />
            <button :disabled="passwordLoading" class="btn-primary" @click="handleChangePassword">
              {{ passwordLoading ? '修改中...' : '修改密码' }}
            </button>
          </div>
        </div>
      </section>

      <!-- Search Index Settings -->
      <section class="fade-up">
        <div class="section-label">
          <svg class="w-4 h-4" style="color: var(--color-secondary);" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span>搜索引擎</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <h3 class="setting-title">搜索引擎配置</h3>
          <p class="setting-desc">初始化/重建 MeiliSearch 索引，使模糊搜索功能生效</p>
          <button :disabled="searchSetupLoading" class="btn-secondary" @click="handleSetupSearch">
            {{ searchSetupLoading ? '配置中...' : '初始化搜索索引' }}
          </button>
        </div>
      </section>

      <!-- Synonyms -->
      <section class="fade-up">
        <div class="section-label">
          <svg class="w-4 h-4" style="color: var(--color-accent);" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
          </svg>
          <span>搜索同义词</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <h3 class="setting-title">搜索同义词</h3>
          <p class="setting-desc">配置搜索同义词（双向生效），每行一组，格式：<code class="code-inline">词A=词B,词C</code></p>
          <textarea
            v-model="synonymsText"
            placeholder="番茄=西红柿&#10;土豆=马铃薯&#10;鸡蛋=蛋"
            rows="4"
            class="input-warm w-full resize-none font-mono text-sm"
          />
          <button :disabled="synonymsLoading" class="btn-secondary mt-3" @click="handleSaveSynonyms">
            {{ synonymsLoading ? '保存中...' : '保存同义词' }}
          </button>
        </div>
      </section>

      <!-- Import/Export -->
      <section class="fade-up">
        <div class="section-label">
          <svg class="w-4 h-4" style="color: var(--color-primary);" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          <span>数据管理</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <h3 class="setting-title">数据导入 / 导出</h3>
          <p class="setting-desc">批量导出菜谱为 ZIP 文件，或从 ZIP 文件批量导入菜谱</p>
          <div class="flex gap-3">
            <button class="btn-secondary" @click="openExportModal">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              批量导出
            </button>
            <button :disabled="importing" class="btn-primary" @click="triggerImport">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              {{ importing ? '导入中...' : '导入菜谱' }}
            </button>
          </div>
        </div>
      </section>
    </div>

    <!-- Export selection modal -->
    <Teleport to="body">
      <transition
        enter-active-class="transition-all duration-300 ease-out"
        leave-active-class="transition-all duration-200 ease-in"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showExportModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          @click.self="showExportModal = false"
        >
          <div class="modal-card max-w-lg">
            <div class="modal-deco"></div>
            <h3 class="modal-title">选择要导出的菜谱</h3>
            <p class="text-xs mb-4" style="color: var(--color-text-muted); font-family: var(--font-ui);">
              已选 <strong style="color: var(--color-primary);">{{ selectedExportIds.length }}</strong> / {{ store.recipes.length }} 道
            </p>

            <label class="export-row" style="border-bottom: 1px solid var(--color-border); margin-bottom: 0.5rem;">
              <input
                type="checkbox"
                :checked="selectedExportIds.length === store.recipes.length && store.recipes.length > 0"
                class="export-checkbox"
                @change="toggleExportAll"
              />
              <span class="text-sm font-medium" style="color: var(--color-text); font-family: var(--font-ui);">全选</span>
            </label>

            <div class="export-list">
              <label
                v-for="recipe in store.recipes"
                :key="recipe.id"
                class="export-row"
              >
                <input
                  type="checkbox"
                  :checked="selectedExportIds.includes(recipe.id)"
                  class="export-checkbox"
                  @change="toggleExportId(recipe.id)"
                />
                <span class="text-sm" style="color: var(--color-text); font-family: var(--font-ui);">{{ recipe.name }}</span>
                <span class="text-xs ml-auto" style="color: var(--color-text-muted); font-family: var(--font-ui);">
                  {{ recipe.tags.slice(0, 2).map(t => t.name).join(' · ') }}
                </span>
              </label>
            </div>

            <div class="flex gap-3 justify-end mt-4 pt-4" style="border-top: 1px solid var(--color-border);">
              <button class="btn-soft" @click="showExportModal = false">取消</button>
              <button :disabled="exporting || selectedExportIds.length === 0" class="btn-secondary" @click="handleExport">
                {{ exporting ? '导出中...' : '导出' }}
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ===== Editorial Header ===== */
.admin-hero { padding: 0 0 2.5rem; }
.admin-subtitle {
  color: var(--color-text-muted);
  font-size: 0.7rem;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
  font-weight: 500;
  font-family: var(--font-ui);
}
.deco-line { width: 48px; height: 1px; background: var(--color-primary); }
.admin-title {
  font-family: var(--font-heading);
  font-size: clamp(1.75rem, 3.5vw, 2.5rem);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}
.admin-desc {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  line-height: 1.6;
  font-family: var(--font-body);
}

/* ===== Section Label ===== */
.section-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  font-weight: 600;
  margin-bottom: 0.75rem;
  font-family: var(--font-ui);
}

/* ===== Setting Card Content ===== */
.setting-title {
  font-family: var(--font-heading);
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}
.setting-desc {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  margin-bottom: 1rem;
  line-height: 1.6;
}
.code-inline {
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  background: var(--color-bg);
  font-size: 0.8125rem;
}

/* ===== Modal ===== */
.modal-card {
  background: var(--color-card);
  border-radius: 1rem;
  padding: 1.75rem;
  box-shadow: 0 25px 60px -12px rgba(61, 51, 41, 0.25);
  width: 100%;
  margin: 0 1rem;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}
.modal-deco { width: 40px; height: 2px; background: var(--color-primary); margin-bottom: 1rem; }
.modal-title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.25rem;
}

/* ===== Export List ===== */
.export-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.export-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: background 0.15s;
}
.export-row:hover {
  background: var(--color-bg);
}
.export-checkbox {
  width: 1rem;
  height: 1rem;
  border-radius: 0.25rem;
  accent-color: var(--color-primary);
}

/* ===== Scroll Fade Animation ===== */
.fade-up {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.fade-up.visible {
  opacity: 1;
  transform: translateY(0);
}
</style>
