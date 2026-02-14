<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
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
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  if (observer) observer.disconnect()
  window.removeEventListener('scroll', handleScroll)
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

const allFilteredRecipes = computed(() => {
  if (!keyword.value) return store.recipes
  const kw = keyword.value.trim()
  if (!kw) return store.recipes
  return store.recipes.filter((r) => fuzzyMatch(r.name, kw))
})

// Infinite scroll
const PAGE_SIZE = 12
const displayCount = ref(PAGE_SIZE)
const loadingMore = ref(false)
const sentinelRef = ref(null)
let observer = null

const displayedRecipes = computed(() => allFilteredRecipes.value.slice(0, displayCount.value))
const hasMore = computed(() => displayCount.value < allFilteredRecipes.value.length)

function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  setTimeout(() => {
    displayCount.value += PAGE_SIZE
    loadingMore.value = false
  }, 150)
}

// Reset page on search change
watch(keyword, () => {
  displayCount.value = PAGE_SIZE
})

// Setup IntersectionObserver
function setupObserver() {
  if (observer) observer.disconnect()
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) loadMore()
    },
    { rootMargin: '200px' }
  )
  nextTick(() => {
    if (sentinelRef.value) observer.observe(sentinelRef.value)
  })
}

onMounted(setupObserver)

watch(sentinelRef, (el) => {
  if (observer && el) observer.observe(el)
})

// Back to top
const showBackToTop = ref(false)

function handleScroll() {
  showBackToTop.value = window.scrollY > 400
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

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
    <div class="flex items-center justify-between mb-6 sm:mb-8 flex-wrap gap-3 sm:gap-4">
      <div>
        <h1 class="section-heading text-2xl font-bold" style="color: var(--color-text);">菜谱管理</h1>
        <p class="text-sm mt-0.5" style="color: var(--color-text-muted); font-family: var(--font-ui);">管理你的所有菜谱</p>
      </div>
      <div class="flex gap-2 flex-wrap">
        <button
          class="btn-primary px-4 py-2 rounded-xl text-sm font-medium transition-all"
          style="font-family: var(--font-ui);"
          @click="router.push('/admin/recipe/new')"
        >
          + 新建菜谱
        </button>
        <button
          class="btn-ghost px-4 py-2 rounded-xl text-sm font-medium transition-all"
          style="font-family: var(--font-ui);"
          @click="router.push('/admin/tags')"
        >
          标签管理
        </button>
        <button
          class="btn-ghost px-4 py-2 rounded-xl text-sm font-medium transition-all"
          style="font-family: var(--font-ui);"
          @click="router.push('/admin/ingredients')"
        >
          食材管理
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="relative max-w-sm mb-6">
      <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
        <svg class="w-4 h-4" style="color: var(--color-text-muted);" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索菜谱..."
        class="input-warm w-full pr-4 py-2.5 rounded-xl outline-none transition-all text-sm"
        style="padding-left: 2.5rem;"
      />
    </div>

    <!-- Recipe Cards Grid -->
    <div
      v-if="displayedRecipes.length > 0"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
    >
      <div
        v-for="recipe in displayedRecipes"
        :key="recipe.id"
        class="card-warm rounded-2xl overflow-hidden transition-all duration-300 group"
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
            <h3 class="text-white font-bold text-base drop-shadow-lg" style="font-family: var(--font-heading);">{{ recipe.name }}</h3>
            <div class="flex gap-1 mt-1">
              <span
                v-for="tag in recipe.tags.slice(0, 2)"
                :key="tag.id"
                class="text-[10px] px-2 py-0.5 rounded-full bg-white/20 text-white backdrop-blur-sm"
                style="font-family: var(--font-ui);"
              >
                {{ tag.name }}
              </span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="p-4 flex items-center justify-between">
          <span class="text-xs" style="color: var(--color-text-muted); font-family: var(--font-ui);">
            {{ formatDate(recipe.updated_at) }}
          </span>
          <div class="flex gap-1.5">
            <button
              class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
              style="color: var(--color-primary); background: var(--color-primary-light); font-family: var(--font-ui);"
              @click="router.push(`/admin/recipe/${recipe.id}/edit`)"
            >
              编辑
            </button>
            <button
              class="px-3 py-1.5 rounded-lg text-xs font-medium text-red-500 bg-red-50 hover:bg-red-100 transition-colors"
              style="font-family: var(--font-ui);"
              @click="confirmDelete(recipe.id)"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Load more sentinel -->
    <div v-if="hasMore" ref="sentinelRef" class="flex items-center justify-center py-8">
      <div class="spinner-warm"></div>
      <span class="ml-2 text-sm" style="color: var(--color-text-muted); font-family: var(--font-ui);">加载更多...</span>
    </div>

    <!-- All loaded hint -->
    <div v-else-if="displayedRecipes.length > PAGE_SIZE" class="text-center py-6">
      <span class="text-xs" style="color: var(--color-border); font-family: var(--font-ui);">— 已全部加载 —</span>
    </div>

    <!-- Empty -->
    <div v-if="allFilteredRecipes.length === 0" class="text-center py-20">
      <div class="text-5xl mb-3">📋</div>
      <p style="color: var(--color-text-muted);">暂无菜谱</p>
    </div>

    <!-- Delete confirmation dialog -->
    <Teleport to="body">
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
        @click.self="showDeleteConfirm = false"
      >
        <div class="card-warm rounded-2xl p-6 shadow-2xl max-w-sm w-full mx-4">
          <h3 class="section-heading text-lg font-bold mb-2" style="color: var(--color-text);">确认删除</h3>
          <p class="text-sm mb-6" style="color: var(--color-text-muted); font-family: var(--font-ui);">确定要删除这道菜谱吗？此操作不可撤销。</p>
          <div class="flex gap-3 justify-end">
            <button
              class="btn-soft px-4 py-2 rounded-xl text-sm transition-colors"
              style="font-family: var(--font-ui);"
              @click="showDeleteConfirm = false"
            >
              取消
            </button>
            <button
              class="btn-danger px-4 py-2 rounded-xl text-sm transition-colors"
              style="font-family: var(--font-ui);"
              @click="doDelete"
            >
              确认删除
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Back to top button -->
    <Teleport to="body">
      <transition
        enter-active-class="transition-all duration-300 ease-out"
        leave-active-class="transition-all duration-200 ease-in"
        enter-from-class="opacity-0 translate-y-4"
        enter-to-class="opacity-100 translate-y-0"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-4"
      >
        <button
          v-if="showBackToTop"
          class="btn-back-top fixed bottom-6 right-6 z-40"
          title="回到顶部"
          @click="scrollToTop"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
          </svg>
        </button>
      </transition>
    </Teleport>
  </div>
</template>
