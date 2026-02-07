<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useRecipeStore } from '../../stores/recipe'

const router = useRouter()
const store = useRecipeStore()
const message = useMessage()

const keyword = ref('')
const showDeleteConfirm = ref(false)
const pendingDeleteId = ref(null)

onMounted(() => {
  store.fetchRecipes()
})

function fuzzyMatch(text, query) {
  const t = text.toLowerCase()
  const q = query.toLowerCase()
  let ti = 0
  for (let qi = 0; qi < q.length; qi++) {
    const idx = t.indexOf(q[qi], ti)
    if (idx === -1) return false
    ti = idx + 1
  }
  return true
}

const filteredRecipes = computed(() => {
  if (!keyword.value) return store.recipes
  const kw = keyword.value.trim()
  if (!kw) return store.recipes
  return store.recipes.filter((r) => fuzzyMatch(r.name, kw))
})

function confirmDelete(id) {
  pendingDeleteId.value = id
  showDeleteConfirm.value = true
}

async function doDelete() {
  if (pendingDeleteId.value) {
    try {
      await store.deleteRecipe(pendingDeleteId.value)
      message.success('菜谱已删除')
    } catch (err) {
      message.error(err.message || '删除失败')
    }
  }
  showDeleteConfirm.value = false
  pendingDeleteId.value = null
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '-'
  return d.toLocaleDateString('zh-CN')
}

function getCover(recipe) {
  const img = recipe.images?.[0]
  if (!img) return 'https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=400&h=300&fit=crop'
  return typeof img === 'string' ? img : img.image_path
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center justify-between mb-8 flex-wrap gap-4">
      <div>
        <h1 class="text-2xl font-extrabold text-gray-800">菜谱管理</h1>
        <p class="text-sm text-gray-400 mt-0.5">管理你的所有菜谱</p>
      </div>
      <div class="flex gap-2 flex-wrap">
        <button
          class="px-4 py-2 rounded-xl bg-gradient-to-r from-orange-400 to-red-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-orange-200 transition-all"
          @click="router.push('/admin/recipe/new')"
        >
          + 新建菜谱
        </button>
        <button
          class="px-4 py-2 rounded-xl bg-white text-gray-600 text-sm font-medium border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all"
          @click="router.push('/admin/tags')"
        >
          标签管理
        </button>
        <button
          class="px-4 py-2 rounded-xl bg-white text-gray-600 text-sm font-medium border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all"
          @click="router.push('/admin/ingredients')"
        >
          食材管理
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="relative max-w-sm mb-6">
      <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
        <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索菜谱..."
        class="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white border border-gray-200 focus:border-orange-300 focus:ring-2 focus:ring-orange-100 outline-none transition-all text-sm"
      />
    </div>

    <!-- Recipe Cards Grid -->
    <div
      v-if="filteredRecipes.length > 0"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
    >
      <div
        v-for="recipe in filteredRecipes"
        :key="recipe.id"
        class="bg-white rounded-2xl overflow-hidden border border-gray-100 hover:shadow-lg transition-all duration-300 group"
      >
        <!-- Cover -->
        <div class="relative aspect-[16/10] overflow-hidden">
          <img
            :src="getCover(recipe)"
            :alt="recipe.name"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
          <div class="absolute bottom-3 left-4 right-4">
            <h3 class="text-white font-bold text-base drop-shadow-lg">{{ recipe.name }}</h3>
            <div class="flex gap-1 mt-1">
              <span
                v-for="tag in recipe.tags.slice(0, 2)"
                :key="tag.id"
                class="text-[10px] px-2 py-0.5 rounded-full bg-white/20 text-white backdrop-blur-sm"
              >
                {{ tag.name }}
              </span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="p-4 flex items-center justify-between">
          <span class="text-xs text-gray-400">
            {{ formatDate(recipe.updated_at) }}
          </span>
          <div class="flex gap-1.5">
            <button
              class="px-3 py-1.5 rounded-lg text-xs font-medium text-orange-600 bg-orange-50 hover:bg-orange-100 transition-colors"
              @click="router.push(`/admin/recipe/${recipe.id}/edit`)"
            >
              编辑
            </button>
            <button
              class="px-3 py-1.5 rounded-lg text-xs font-medium text-red-500 bg-red-50 hover:bg-red-100 transition-colors"
              @click="confirmDelete(recipe.id)"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="text-center py-20">
      <div class="text-5xl mb-3">📋</div>
      <p class="text-gray-500">暂无菜谱</p>
    </div>

    <!-- Delete confirmation dialog -->
    <Teleport to="body">
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
        @click.self="showDeleteConfirm = false"
      >
        <div class="bg-white rounded-2xl p-6 shadow-2xl max-w-sm w-full mx-4">
          <h3 class="text-lg font-bold text-gray-800 mb-2">确认删除</h3>
          <p class="text-sm text-gray-500 mb-6">确定要删除这道菜谱吗？此操作不可撤销。</p>
          <div class="flex gap-3 justify-end">
            <button
              class="px-4 py-2 rounded-xl text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors"
              @click="showDeleteConfirm = false"
            >
              取消
            </button>
            <button
              class="px-4 py-2 rounded-xl text-sm text-white bg-red-500 hover:bg-red-600 transition-colors"
              @click="doDelete"
            >
              确认删除
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
