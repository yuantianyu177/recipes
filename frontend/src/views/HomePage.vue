<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRecipeStore } from '../stores/recipe'
import RecipeCard from '../components/RecipeCard.vue'
import ShareModal from '../components/ShareModal.vue'

const store = useRecipeStore()

// Share modal state
const shareRecipe = ref(null)
const showShareModal = ref(false)

function handleShare(recipe) {
  shareRecipe.value = recipe
  showShareModal.value = true
}

function closeShareModal() {
  showShareModal.value = false
  shareRecipe.value = null
}

const keyword = ref('')
const selectedTags = ref([])
const filteredRecipes = ref([])

const tagsByCategory = computed(() => store.getTagsByCategory)

onMounted(async () => {
  await store.fetchAll()
  filteredRecipes.value = store.recipes
})

// Debounced search
let searchTimer = null
watch([keyword, selectedTags], () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    filteredRecipes.value = await store.searchRecipes(keyword.value, selectedTags.value)
  }, 200)
}, { deep: true })

function toggleTag(tagName) {
  const idx = selectedTags.value.indexOf(tagName)
  if (idx === -1) {
    selectedTags.value.push(tagName)
  } else {
    selectedTags.value.splice(idx, 1)
  }
}

function clearFilters() {
  keyword.value = ''
  selectedTags.value = []
}

const hasActiveFilter = computed(() => keyword.value || selectedTags.value.length > 0)
</script>

<template>
  <div>
    <!-- Hero Section -->
    <div class="relative -mx-4 md:-mx-8 -mt-8 mb-10 px-4 md:px-8 pt-16 pb-12 overflow-hidden">
      <!-- Background gradient -->
      <div class="absolute inset-0 bg-gradient-to-br from-orange-50 via-red-50 to-amber-50" />
      <div class="absolute top-0 right-0 w-96 h-96 bg-orange-200/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
      <div class="absolute bottom-0 left-0 w-72 h-72 bg-red-200/20 rounded-full blur-3xl translate-y-1/2 -translate-x-1/3" />

      <div class="relative text-center max-w-2xl mx-auto">
        <h1 class="text-4xl md:text-5xl font-extrabold mb-3">
          <span class="bg-gradient-to-r from-orange-500 via-red-500 to-amber-500 bg-clip-text text-transparent">
            我的菜谱
          </span>
        </h1>
        <p class="text-gray-500 text-base md:text-lg mb-8">
          记录每一道美味，分享生活的味道
        </p>

        <!-- Search Bar -->
        <div class="relative max-w-lg mx-auto">
          <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索菜谱、食材..."
            class="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-white shadow-lg shadow-orange-100/50 border border-white focus:border-orange-300 focus:ring-4 focus:ring-orange-100 outline-none transition-all text-sm"
          />
          <button
            v-if="keyword"
            class="absolute inset-y-0 right-3 flex items-center text-gray-400 hover:text-gray-600"
            @click="keyword = ''"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Tag Filters -->
    <div class="mb-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-sm font-semibold text-gray-800 uppercase tracking-wider">筛选标签</h2>
        <button
          v-if="hasActiveFilter"
          class="text-xs text-orange-500 hover:text-orange-600 transition-colors"
          @click="clearFilters"
        >
          清除全部筛选
        </button>
      </div>
      <div v-for="(tags, category) in tagsByCategory" :key="category" class="mb-4 flex items-start gap-3">
        <span class="text-xs font-medium text-gray-400 w-16 shrink-0 pt-2 text-right">{{ category }}</span>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="tag in tags"
            :key="tag.id"
            class="min-w-[3rem] px-3.5 py-1.5 rounded-full text-xs font-medium transition-all duration-200 h-[30px] inline-flex items-center justify-center border"
            :class="
              selectedTags.includes(tag.name)
                ? 'bg-gradient-to-r from-orange-400 to-red-500 text-white shadow-md shadow-orange-200 border-transparent'
                : 'bg-white text-gray-600 hover:bg-orange-50 hover:text-orange-600 border-gray-200 hover:border-orange-300'
            "
            @click="toggleTag(tag.name)"
          >
            {{ tag.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="store.loading" class="flex items-center justify-center py-16">
      <div class="w-8 h-8 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin"></div>
      <span class="ml-3 text-gray-400 text-sm">加载中...</span>
    </div>

    <!-- Results count -->
    <div v-if="!store.loading" class="flex items-center justify-between mb-5">
      <p class="text-sm text-gray-400">
        共 <span class="font-semibold text-gray-700">{{ filteredRecipes.length }}</span> 道菜谱
      </p>
    </div>

    <!-- Recipe Grid -->
    <div
      v-if="filteredRecipes.length > 0"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
    >
      <RecipeCard v-for="recipe in filteredRecipes" :key="recipe.id" :recipe="recipe" @share="handleShare" />
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-24">
      <div class="text-6xl mb-4">🍽️</div>
      <p class="text-lg text-gray-500 mb-2">没有找到菜谱</p>
      <p class="text-sm text-gray-400">试试其他关键词或标签</p>
      <button
        v-if="hasActiveFilter"
        class="mt-4 px-4 py-2 rounded-xl text-sm text-orange-500 border border-orange-300 hover:bg-orange-50 transition-colors"
        @click="clearFilters"
      >
        清除筛选
      </button>
    </div>

    <!-- Share Modal -->
    <ShareModal :show="showShareModal" :recipe="shareRecipe" @close="closeShareModal" />
  </div>
</template>
