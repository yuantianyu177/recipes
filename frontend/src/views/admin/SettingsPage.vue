<script setup>
import { ref, onMounted } from 'vue'
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
  // Load existing synonyms
  try {
    const data = await apiGetSynonyms()
    if (data && typeof data === 'object') {
      // Deduplicate: collect synonym groups, output one line per group
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
  <div class="max-w-3xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="section-heading text-2xl font-bold">系统设置</h1>
    </div>

    <div class="space-y-6">
      <!-- Password Settings -->
      <div class="card-warm rounded-2xl p-6">
        <h3 class="text-sm font-semibold mb-1 section-heading">修改密码</h3>
        <p class="text-xs mb-4" style="color: var(--color-text-muted); font-family: var(--font-ui);">修改管理员登录密码</p>
        <div class="space-y-3 max-w-sm">
          <input v-model="oldPassword" type="password" placeholder="当前密码" class="input-warm w-full" />
          <input v-model="newPassword" type="password" placeholder="新密码" class="input-warm w-full" />
          <input v-model="confirmPassword" type="password" placeholder="确认新密码" class="input-warm w-full" />
          <button :disabled="passwordLoading" class="btn-primary" @click="handleChangePassword">
            {{ passwordLoading ? '修改中...' : '修改密码' }}
          </button>
        </div>
      </div>

      <!-- Search Index Settings -->
      <div class="card-warm rounded-2xl p-6">
        <h3 class="text-sm font-semibold mb-1 section-heading">搜索引擎配置</h3>
        <p class="text-xs mb-4" style="color: var(--color-text-muted); font-family: var(--font-ui);">初始化/重建 MeiliSearch 索引，使模糊搜索功能生效</p>
        <button :disabled="searchSetupLoading" class="btn-secondary" @click="handleSetupSearch">
          {{ searchSetupLoading ? '配置中...' : '初始化搜索索引' }}
        </button>
      </div>

      <!-- Synonyms -->
      <div class="card-warm rounded-2xl p-6">
        <h3 class="text-sm font-semibold mb-1 section-heading">搜索同义词</h3>
        <p class="text-xs mb-3" style="color: var(--color-text-muted); font-family: var(--font-ui);">配置搜索同义词（双向生效），每行一组，格式：<code class="px-1 rounded" style="background: var(--color-bg);">词A=词B,词C</code>，搜索任意一个词都可以匹配到其他词</p>
        <textarea
          v-model="synonymsText"
          placeholder="番茄=西红柿&#10;土豆=马铃薯&#10;鸡蛋=蛋"
          rows="4"
          class="input-warm w-full resize-none font-mono"
        />
        <button :disabled="synonymsLoading" class="btn-secondary mt-3" @click="handleSaveSynonyms">
          {{ synonymsLoading ? '保存中...' : '保存同义词' }}
        </button>
      </div>

      <!-- Import/Export -->
      <div class="card-warm rounded-2xl p-6">
        <h3 class="text-sm font-semibold mb-1 section-heading">数据导入 / 导出</h3>
        <p class="text-xs mb-4" style="color: var(--color-text-muted); font-family: var(--font-ui);">批量导出菜谱为 ZIP 文件，或从 ZIP 文件批量导入菜谱</p>
        <div class="flex gap-3">
          <button class="btn-secondary" @click="openExportModal">批量导出</button>
          <button :disabled="importing" class="btn-primary" @click="triggerImport">
            {{ importing ? '导入中...' : '导入菜谱' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Export selection modal -->
    <Teleport to="body">
      <div
        v-if="showExportModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
        @click.self="showExportModal = false"
      >
        <div class="rounded-2xl p-6 shadow-2xl max-w-lg w-full mx-4 max-h-[80vh] flex flex-col" style="background: var(--color-card);">
          <h3 class="text-lg font-bold mb-1" style="color: var(--color-text); font-family: var(--font-heading);">选择要导出的菜谱</h3>
          <p class="text-xs mb-4" style="color: var(--color-text-muted); font-family: var(--font-ui);">已选 {{ selectedExportIds.length }} / {{ store.recipes.length }} 道</p>

          <label class="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer mb-2" style="border-bottom: 1px solid var(--color-border);">
            <input
              type="checkbox"
              :checked="selectedExportIds.length === store.recipes.length && store.recipes.length > 0"
              class="w-4 h-4 rounded border-gray-300 text-orange-500 focus:ring-orange-200"
              @change="toggleExportAll"
            />
            <span class="text-sm font-medium" style="color: var(--color-text); font-family: var(--font-ui);">全选</span>
          </label>

          <div class="flex-1 overflow-y-auto space-y-1">
            <label
              v-for="recipe in store.recipes"
              :key="recipe.id"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors"
            >
              <input
                type="checkbox"
                :checked="selectedExportIds.includes(recipe.id)"
                class="w-4 h-4 rounded border-gray-300 text-orange-500 focus:ring-orange-200"
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
              {{ exporting ? '导出中...' : `导出` }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
