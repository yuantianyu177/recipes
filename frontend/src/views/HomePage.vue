<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
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
const allFilteredRecipes = ref([])

const tagsByCategory = computed(() => store.getTagsByCategory)

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

function resetPagination() {
  displayCount.value = PAGE_SIZE
}

// Setup IntersectionObserver for infinite scroll
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

onMounted(async () => {
  await store.fetchAll()
  allFilteredRecipes.value = store.recipes
  setupObserver()
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  if (observer) observer.disconnect()
  window.removeEventListener('scroll', handleScroll)
})

// Watch sentinel ref changes (v-if toggle)
watch(sentinelRef, (el) => {
  if (observer && el) observer.observe(el)
})

// Debounced search
let searchTimer = null
watch([keyword, selectedTags], () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    allFilteredRecipes.value = await store.searchRecipes(keyword.value, selectedTags.value)
    resetPagination()
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

// Back to top
const showBackToTop = ref(false)

function handleScroll() {
  showBackToTop.value = window.scrollY > 400
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <div>
    <!-- Hero Section -->
    <div class="relative -mx-4 md:-mx-8 -mt-8 mb-10 px-4 md:px-8 pt-14 pb-10 overflow-hidden">
      <div class="relative text-center max-w-2xl mx-auto animate-fade-in-up">
        <!-- Logo mark as hero decoration -->
        <svg class="mx-auto mb-5 hero-mark" width="48" height="48" viewBox="0 0 28 28" fill="none">
          <path d="M14 4C14 4 8 8 8 14C8 17 10 20 14 22" stroke="var(--color-primary)" stroke-width="1.5" stroke-linecap="round" fill="none"/>
          <path d="M14 4C14 4 20 8 20 14C20 17 18 20 14 22" stroke="var(--color-secondary)" stroke-width="1.5" stroke-linecap="round" fill="none"/>
          <path d="M14 22V26" stroke="var(--color-accent)" stroke-width="1.5" stroke-linecap="round"/>
          <circle cx="14" cy="4" r="1.5" fill="var(--color-primary)" opacity="0.6"/>
          <path d="M10 10Q12 12 14 10" stroke="var(--color-primary)" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.4"/>
          <path d="M14 10Q16 12 18 10" stroke="var(--color-secondary)" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.4"/>
        </svg>

        <h1 class="text-3xl sm:text-4xl md:text-5xl font-bold mb-3" style="font-family: var(--font-heading); color: var(--color-text);">
          我的菜谱
        </h1>
        <p class="text-sm sm:text-base md:text-lg mb-6 sm:mb-8" style="color: var(--color-text-muted); font-family: var(--font-body);">
          记录每一道美味，分享生活的味道
        </p>

        <!-- Search Bar -->
        <div class="relative max-w-lg mx-auto">
          <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
            <svg class="w-5 h-5" style="color: var(--color-text-muted); opacity: 0.6;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索菜谱、食材..."
            class="input-warm w-full pr-10 py-3.5 rounded-2xl"
            style="padding-left: 2.5rem; box-shadow: 0 4px 16px rgba(61, 51, 41, 0.06);"
          />
          <button
            v-if="keyword"
            class="absolute inset-y-0 right-3 flex items-center transition-colors"
            style="color: var(--color-text-muted);"
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
        <h2 class="text-sm font-semibold uppercase tracking-wider" style="color: var(--color-text); font-family: var(--font-ui);">筛选标签</h2>
        <button
          v-if="hasActiveFilter"
          class="text-xs transition-colors underline underline-offset-2"
          style="color: var(--color-primary); font-family: var(--font-ui);"
          @click="clearFilters"
        >
          清除全部筛选
        </button>
      </div>
      <div v-for="(tags, category) in tagsByCategory" :key="category" class="mb-4 flex items-start gap-3">
        <span class="text-xs font-medium w-16 shrink-0 pt-2 text-right hidden sm:block" style="color: var(--color-text-muted); font-family: var(--font-ui);">{{ category }}</span>
        <div class="flex flex-wrap gap-2 overflow-x-auto sm:overflow-visible">
          <button
            v-for="tag in tags"
            :key="tag.id"
            class="tag-filter"
            :class="{ 'tag-filter-active': selectedTags.includes(tag.name) }"
            @click="toggleTag(tag.name)"
          >
            {{ tag.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading indicator -->
    <div v-if="store.loading" class="flex items-center justify-center py-16">
      <div class="spinner-warm"></div>
      <span class="ml-3 text-sm" style="color: var(--color-text-muted);">加载中...</span>
    </div>

    <!-- Results count -->
    <div v-if="!store.loading" class="flex items-center justify-between mb-5">
      <p class="text-sm" style="color: var(--color-text-muted); font-family: var(--font-ui);">
        共 <span class="font-semibold" style="color: var(--color-text);">{{ allFilteredRecipes.length }}</span> 道菜谱
      </p>
    </div>

    <!-- Recipe Grid -->
    <div
      v-if="displayedRecipes.length > 0"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 stagger-children"
    >
      <RecipeCard v-for="recipe in displayedRecipes" :key="recipe.id" :recipe="recipe" @share="handleShare" />
    </div>

    <!-- Load more sentinel -->
    <div v-if="hasMore" ref="sentinelRef" class="flex items-center justify-center py-8">
      <div class="spinner-warm-sm"></div>
      <span class="ml-2 text-sm" style="color: var(--color-text-muted);">加载更多...</span>
    </div>

    <!-- All loaded hint -->
    <div v-else-if="displayedRecipes.length > PAGE_SIZE" class="text-center py-6">
      <div class="wavy-divider max-w-xs mx-auto"></div>
      <span class="text-xs mt-2 inline-block" style="color: var(--color-text-muted);">已全部加载</span>
    </div>

    <!-- Empty state -->
    <div v-if="!store.loading && allFilteredRecipes.length === 0" class="text-center py-24 animate-fade-in-up">
      <!-- Hand-drawn empty plate -->
      <svg class="mx-auto mb-6" width="120" height="100" viewBox="0 0 120 100" fill="none">
        <ellipse cx="60" cy="82" rx="38" ry="5" fill="var(--color-border)" opacity="0.4"/>
        <ellipse cx="60" cy="52" rx="32" ry="28" stroke="var(--color-text-muted)" stroke-width="1.5" fill="var(--color-card)" stroke-linecap="round"/>
        <ellipse cx="60" cy="50" rx="22" ry="18" stroke="var(--color-border)" stroke-width="1" fill="none" stroke-dasharray="4 3"/>
        <path d="M48 48Q54 42 60 48Q66 42 72 48" stroke="var(--color-text-muted)" stroke-width="1.2" fill="none" stroke-linecap="round" opacity="0.6"/>
        <path d="M52 56Q60 60 68 56" stroke="var(--color-text-muted)" stroke-width="1.2" fill="none" stroke-linecap="round" opacity="0.4"/>
      </svg>
      <p class="text-lg mb-2" style="color: var(--color-text-muted); font-family: var(--font-heading);">没有找到菜谱</p>
      <p class="text-sm mb-4" style="color: var(--color-text-muted);">试试其他关键词或标签</p>
      <button
        v-if="hasActiveFilter"
        class="btn-ghost btn-sm"
        @click="clearFilters"
      >
        清除筛选
      </button>
    </div>

    <!-- Share Modal -->
    <ShareModal :show="showShareModal" :recipe="shareRecipe" @close="closeShareModal" />

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
          class="fixed bottom-8 right-8 z-40 btn-back-top"
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

<style scoped>
.hero-mark {
  animation: floatGentle 3s ease-in-out infinite;
}
@keyframes floatGentle {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.tag-filter {
  min-width: 3rem;
  padding: 0.375rem 0.875rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
  font-family: var(--font-ui);
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  background: var(--color-card);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.tag-filter:hover {
  border-color: var(--color-secondary);
  color: var(--color-secondary);
  transform: translateY(-1px);
}
.tag-filter-active {
  background: var(--color-secondary);
  color: white;
  border-color: var(--color-secondary);
  box-shadow: 0 2px 8px rgba(91, 122, 94, 0.3);
}
.tag-filter-active:hover {
  background: var(--color-secondary-hover);
  color: white;
}

/* Mobile */
@media (max-width: 640px) {
  .hero-mark {
    width: 36px;
    height: 36px;
  }
}
</style>
