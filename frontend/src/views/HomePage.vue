<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRecipeStore } from '../stores/recipe'
import RecipeCard from '../components/RecipeCard.vue'
import ShareModal from '../components/ShareModal.vue'

const store = useRecipeStore()

// Random slogan
const slogans = [
  { cn: '一餐一味，皆是心意', en: 'Every dish, a story told with heart' },
  { cn: '慢火细烹，集味成册', en: 'Slow-cooked, carefully collected' },
  { cn: '厨房有光，四季有味', en: 'Where kitchen light meets every season' },
]
const currentSlogan = ref(slogans[Math.floor(Math.random() * slogans.length)])
const sloganVisible = ref(false)

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
const allTags = computed(() => store.tags || [])

// Infinite scroll
const PAGE_SIZE = 12
const displayCount = ref(PAGE_SIZE)
const loadingMore = ref(false)
const sentinelRef = ref(null)
let observer = null

const displayedRecipes = computed(() => allFilteredRecipes.value.slice(0, displayCount.value))
const hasMore = computed(() => displayCount.value < allFilteredRecipes.value.length)

// Featured recipe: first recipe with images
const featuredRecipe = computed(() => {
  if (hasActiveFilter.value) return null
  return allFilteredRecipes.value.find(r => r.images && r.images.length > 0) || allFilteredRecipes.value[0] || null
})

// Remaining recipes (exclude featured)
const gridRecipes = computed(() => {
  if (!featuredRecipe.value || hasActiveFilter.value) return displayedRecipes.value
  return displayedRecipes.value.filter(r => r.id !== featuredRecipe.value.id)
})

// Stats
const recipeCount = computed(() => store.recipes.length)
const ingredientCount = computed(() => store.ingredients.length)
const tagCount = computed(() => store.tags.length)

function getCoverImage(recipe) {
  if (recipe.images && recipe.images.length > 0) {
    const img = recipe.images[0]
    return typeof img === 'string' ? img : img.image_path
  }
  return 'https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=800&h=600&fit=crop'
}

function getMainIngredients(recipe) {
  if (!recipe.ingredients) return ''
  return recipe.ingredients
    .filter(i => i.category === '主料')
    .map(i => i.ingredient_name || i.name || '')
    .filter(Boolean)
    .join(' · ')
}

function getDescription(recipe) {
  if (recipe.description) return recipe.description
  const ingredients = getMainIngredients(recipe)
  if (ingredients) return `主料：${ingredients}`
  return ''
}

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

// Scroll-triggered fade-up animation
let fadeObserver = null
function setupScrollAnimations() {
  fadeObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')
        }
      })
    },
    { threshold: 0.1 }
  )
  nextTick(() => {
    document.querySelectorAll('.fade-up').forEach(el => fadeObserver.observe(el))
  })
}

function refreshFadeAnimations() {
  nextTick(() => {
    if (!fadeObserver) return
    document.querySelectorAll('.fade-up:not(.visible)').forEach(el => fadeObserver.observe(el))
  })
}

onMounted(async () => {
  await store.fetchAll()
  allFilteredRecipes.value = [...store.recipes]
  setupObserver()
  setupScrollAnimations()
  // Trigger slogan entrance animation
  setTimeout(() => { sloganVisible.value = true }, 100)
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  if (observer) observer.disconnect()
  window.removeEventListener('scroll', handleScroll)
})

// Watch sentinel ref changes
watch(sentinelRef, (el) => {
  if (observer && el) observer.observe(el)
})

// Debounced keyword search only
let searchTimer = null
watch(keyword, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    allFilteredRecipes.value = await store.searchRecipes(keyword.value, selectedTags.value)
    resetPagination()
    refreshFadeAnimations()
  }, 200)
})

// Tag changes apply immediately (local filtering, no API call)
watch(selectedTags, async () => {
  clearTimeout(searchTimer)
  allFilteredRecipes.value = await store.searchRecipes(keyword.value, selectedTags.value)
  resetPagination()
  refreshFadeAnimations()
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
  clearTimeout(searchTimer)
  keyword.value = ''
  selectedTags.value = []
  allFilteredRecipes.value = [...store.recipes]
  resetPagination()
  refreshFadeAnimations()
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
  <div class="magazine-home">
    <!-- Hero Section: Editorial split layout -->
    <section class="hero-section">
      <div class="grid md:grid-cols-12 gap-8 items-end">
        <!-- Left: Editorial headline -->
        <div class="md:col-span-7 lg:col-span-8 fade-up">
          <div class="slogan-block" :class="{ 'slogan-visible': sloganVisible }">
            <div class="slogan-deco-top" aria-hidden="true">
              <span class="slogan-flourish"></span>
              <span class="slogan-label">味之集</span>
              <span class="slogan-flourish"></span>
            </div>
            <h1 class="slogan-cn">{{ currentSlogan.cn }}</h1>
            <p class="slogan-en">{{ currentSlogan.en }}</p>
          </div>
        </div>
        <!-- Right: Search + stats card -->
        <div class="md:col-span-5 lg:col-span-4 fade-up">
          <div class="search-card">
            <label class="search-label">搜索菜谱</label>
            <div class="relative">
              <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <input
                v-model="keyword"
                type="text"
                placeholder="输入菜名、食材…"
                class="search-input"
              />
              <button
                v-if="keyword"
                class="search-clear"
                @click="keyword = ''"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <!-- Stats -->
            <div class="stats-grid">
              <div class="text-center">
                <p class="stat-number text-primary">{{ recipeCount }}</p>
                <p class="stat-label">道菜谱</p>
              </div>
              <div class="text-center">
                <p class="stat-number text-secondary">{{ ingredientCount }}</p>
                <p class="stat-label">种食材</p>
              </div>
              <div class="text-center">
                <p class="stat-number text-accent">{{ tagCount }}</p>
                <p class="stat-label">个分类</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Tag Filters with elegant divider -->
    <section class="tag-section fade-up">
      <div class="elegant-divider mb-8">
        <span>筛选标签</span>
      </div>
      <div class="flex flex-wrap gap-2.5 justify-center">
        <button
          v-for="tag in allTags"
          :key="tag.id"
          class="tag-pill"
          :class="{ active: selectedTags.includes(tag.name) }"
          :style="tag.color && !selectedTags.includes(tag.name) ? { borderColor: tag.color + '40', color: tag.color } : (tag.color && selectedTags.includes(tag.name) ? { background: tag.color, borderColor: tag.color, color: '#fff' } : {})"
          @click="toggleTag(tag.name)"
        >
          {{ tag.name }}
        </button>
      </div>
      <div v-if="hasActiveFilter" class="text-center mt-4">
        <button class="clear-filter-btn" @click="clearFilters">
          清除全部筛选
        </button>
      </div>
    </section>

    <!-- Loading indicator -->
    <div v-if="store.loading" class="flex items-center justify-center py-16">
      <div class="spinner-warm"></div>
      <span class="ml-3 text-sm" style="color: var(--color-text-muted);">加载中...</span>
    </div>

    <!-- Content area -->
    <section v-if="!store.loading" class="content-section">
      <!-- Results count -->
      <div class="results-count fade-up">
        <span class="w-8 h-px" style="background: var(--color-border);"></span>
        <span>共 <strong>{{ allFilteredRecipes.length }}</strong> 道菜谱</span>
        <span class="w-8 h-px" style="background: var(--color-border);"></span>
      </div>

      <!-- Featured Card -->
      <div
        v-if="featuredRecipe && !hasActiveFilter"
        class="featured-card fade-up"
      >
        <router-link :to="`/recipe/${featuredRecipe.id}`" class="no-underline block">
          <div class="grid md:grid-cols-2">
            <div class="relative overflow-hidden aspect-[4/3] md:aspect-auto">
              <img
                :src="getCoverImage(featuredRecipe)"
                :alt="featuredRecipe.name"
                class="w-full h-full object-cover"
              />
              <div v-if="featuredRecipe.calories" class="calorie-badge-featured">
                {{ featuredRecipe.calories }} kcal
              </div>
            </div>
            <div class="featured-content">
              <div class="featured-label">
                <span>本周精选</span>
                <span class="w-8 h-px" style="background: var(--color-accent);"></span>
              </div>
              <h2 class="featured-title">{{ featuredRecipe.name }}</h2>
              <p v-if="getDescription(featuredRecipe)" class="featured-desc drop-cap">
                {{ getDescription(featuredRecipe) }}
              </p>
              <div v-if="featuredRecipe.ingredients" class="featured-ingredients">
                <span
                  v-for="ing in featuredRecipe.ingredients.slice(0, 4)"
                  :key="ing.id || ing.ingredient_name"
                  class="ingredient-pill"
                >
                  {{ ing.ingredient_name || ing.name }}
                </span>
              </div>
              <div class="flex items-center justify-between mt-auto">
                <div class="flex gap-2">
                  <span
                    v-for="tag in featuredRecipe.tags.slice(0, 2)"
                    :key="tag.id"
                    class="featured-tag"
                    :style="tag.color ? { background: tag.color + '1a', color: tag.color } : {}"
                    :class="!tag.color ? (tag.id % 2 === 0 ? 'featured-tag-secondary' : 'featured-tag-primary') : ''"
                  >
                    {{ tag.name }}
                  </span>
                </div>
                <button
                  class="share-circle-btn"
                  title="分享"
                  @click.prevent="handleShare(featuredRecipe)"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </router-link>
      </div>

      <!-- Masonry Grid -->
      <div v-if="gridRecipes.length > 0" class="masonry">
        <RecipeCard
          v-for="recipe in gridRecipes"
          :key="recipe.id"
          :recipe="recipe"
          class="masonry-item fade-up"
          @share="handleShare"
        />
      </div>

      <!-- Load more sentinel -->
      <div v-if="hasMore" ref="sentinelRef" class="load-more-indicator">
        <span class="w-8 h-px" style="background: var(--color-border);"></span>
        <span class="animate-pulse">加载更多菜谱…</span>
        <span class="w-8 h-px" style="background: var(--color-border);"></span>
      </div>

      <!-- All loaded hint -->
      <div v-else-if="displayedRecipes.length > PAGE_SIZE" class="text-center py-6">
        <div class="wavy-divider max-w-xs mx-auto"></div>
        <span class="text-xs mt-2 inline-block" style="color: var(--color-text-muted);">已全部加载</span>
      </div>

      <!-- Empty state -->
      <div v-if="allFilteredRecipes.length === 0" class="empty-state fade-up">
        <svg class="mx-auto mb-6" width="120" height="100" viewBox="0 0 120 100" fill="none">
          <ellipse cx="60" cy="82" rx="38" ry="5" fill="var(--color-border)" opacity="0.4"/>
          <ellipse cx="60" cy="52" rx="32" ry="28" stroke="var(--color-text-muted)" stroke-width="1.5" fill="var(--color-card)" stroke-linecap="round"/>
          <ellipse cx="60" cy="50" rx="22" ry="18" stroke="var(--color-border)" stroke-width="1" fill="none" stroke-dasharray="4 3"/>
          <path d="M48 48Q54 42 60 48Q66 42 72 48" stroke="var(--color-text-muted)" stroke-width="1.2" fill="none" stroke-linecap="round" opacity="0.6"/>
          <path d="M52 56Q60 60 68 56" stroke="var(--color-text-muted)" stroke-width="1.2" fill="none" stroke-linecap="round" opacity="0.4"/>
        </svg>
        <p class="text-lg mb-2" style="color: var(--color-text-muted); font-family: var(--font-heading);">没有找到菜谱</p>
        <p class="text-sm mb-4" style="color: var(--color-text-muted);">试试其他关键词或标签</p>
        <button v-if="hasActiveFilter" class="btn-ghost btn-sm" @click="clearFilters">清除筛选</button>
      </div>
    </section>

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
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/>
          </svg>
        </button>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ===== Hero Section ===== */
.hero-section {
  padding: 2rem 0 3rem;
}

/* ===== Slogan Block ===== */
.slogan-block {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 1s cubic-bezier(.22,.61,.36,1), transform 1s cubic-bezier(.22,.61,.36,1);
  text-align: left;
}
.slogan-block.slogan-visible {
  opacity: 1;
  transform: translateY(0);
}

/* Top decorative row: ── 味之集 ── */
.slogan-deco-top {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.slogan-flourish {
  display: block;
  width: 32px;
  height: 1px;
  background: var(--color-primary);
  opacity: 0;
  transform: scaleX(0);
  transition: opacity 0.6s ease 0.3s, transform 0.6s cubic-bezier(.22,.61,.36,1) 0.3s;
  flex-shrink: 0;
}
.slogan-flourish:first-child {
  transform-origin: right center;
}
.slogan-flourish:last-child {
  transform-origin: left center;
  transition-delay: 0.45s;
}
.slogan-block.slogan-visible .slogan-flourish {
  opacity: 0.5;
  transform: scaleX(1);
}
.slogan-label {
  font-family: var(--font-heading);
  font-size: 0.7rem;
  letter-spacing: 0.3em;
  color: var(--color-primary);
  opacity: 0.6;
  font-weight: 500;
  white-space: nowrap;
}

/* Chinese slogan — hero-level display */
.slogan-cn {
  font-family: var(--font-heading);
  font-size: clamp(2.4rem, 5vw, 4.2rem);
  font-weight: 700;
  letter-spacing: 0.08em;
  line-height: 1.15;
  color: var(--color-text);
  margin-bottom: 1.25rem;
}

/* English subtitle */
.slogan-en {
  font-family: var(--font-ui);
  font-size: clamp(0.75rem, 1.2vw, 0.85rem);
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  opacity: 0;
  font-weight: 400;
  font-style: italic;
  transition: opacity 0.8s ease 0.6s;
}
.slogan-block.slogan-visible .slogan-en {
  opacity: 0.5;
}

/* ===== Search Card ===== */
.search-card {
  background: var(--color-card);
  border-radius: 1rem;
  padding: 1.5rem;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 12px rgba(61, 51, 41, 0.06);
}
.search-label {
  display: block;
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  font-weight: 500;
  margin-bottom: 0.75rem;
  font-family: var(--font-ui);
}
.search-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  width: 1.25rem;
  height: 1.25rem;
  color: var(--color-text-muted);
}
.search-input {
  width: 100%;
  padding: 0.875rem 2.5rem 0.875rem 3rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  font-size: 0.875rem;
  color: var(--color-text);
  font-family: var(--font-ui);
  transition: all 0.25s ease;
  outline: none;
}
.search-input::placeholder {
  color: var(--color-text-muted);
  opacity: 0.6;
}
.search-input:focus {
  box-shadow: 0 0 0 2px rgba(196, 93, 62, 0.2);
  border-color: var(--color-primary);
}
.search-clear {
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}
.search-clear:hover { color: var(--color-text); }

.stats-grid {
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--color-border);
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}
.stat-number {
  font-family: var(--font-heading);
  font-size: 1.5rem;
  font-weight: 700;
}
.stat-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 0.25rem;
  font-family: var(--font-ui);
}
.text-primary { color: var(--color-primary); }
.text-secondary { color: var(--color-secondary); }
.text-accent { color: var(--color-accent); }

/* ===== Tag Section ===== */
.tag-section {
  padding: 0 0 3rem;
}
.elegant-divider {
  display: flex;
  align-items: center;
  gap: 1rem;
  color: var(--color-text-muted);
  font-family: var(--font-heading);
  font-size: 0.8rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
.elegant-divider::before,
.elegant-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--color-border);
}
.tag-pill {
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-size: 0.875rem;
  border: 1px solid var(--color-border);
  background: var(--color-card);
  color: var(--color-text-muted);
  font-weight: 500;
  font-family: var(--font-ui);
  cursor: pointer;
  transition: all 0.2s ease;
}
.tag-pill:hover {
  border-color: var(--color-primary);
  opacity: 0.8;
}
.tag-pill.active {
  background: var(--color-primary);
  color: var(--color-card);
  border-color: var(--color-primary);
  box-shadow: 0 2px 8px rgba(196, 93, 62, 0.3);
}
.clear-filter-btn {
  font-size: 0.8rem;
  color: var(--color-primary);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  font-family: var(--font-ui);
  transition: opacity 0.2s;
}
.clear-filter-btn:hover { opacity: 0.7; }

/* ===== Content Section ===== */
.content-section {
  padding-bottom: 2rem;
}
.results-count {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  font-size: 0.875rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  margin-bottom: 2rem;
}
.results-count strong {
  color: var(--color-text);
}

/* ===== Featured Card ===== */
.featured-card {
  background: var(--color-card);
  border-radius: 1rem;
  border: 1px solid var(--color-border);
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(61, 51, 41, 0.06);
  margin-bottom: 2rem;
  transition: transform 0.35s cubic-bezier(.22,.61,.36,1), box-shadow 0.35s cubic-bezier(.22,.61,.36,1);
  cursor: pointer;
}
.featured-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 50px -12px rgba(61, 51, 41, 0.18);
}
.featured-card img {
  transition: transform 0.6s cubic-bezier(.22,.61,.36,1);
}
.featured-card:hover img {
  transform: scale(1.06);
}
.calorie-badge-featured {
  position: absolute;
  top: 1rem;
  left: 1rem;
  background: rgba(255, 253, 248, 0.8);
  color: var(--color-primary);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.375rem 0.75rem;
  border-radius: 999px;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  font-family: var(--font-ui);
}
.featured-badge {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: var(--color-primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.375rem 0.75rem;
  border-radius: 999px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-family: var(--font-ui);
}
.featured-content {
  padding: 2rem 2.5rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.featured-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--color-accent);
  font-weight: 600;
  margin-bottom: 1rem;
  font-family: var(--font-ui);
}
.featured-title {
  font-family: var(--font-heading);
  font-size: clamp(1.75rem, 3vw, 2.5rem);
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-text);
  margin-bottom: 1rem;
}
.featured-desc {
  color: var(--color-text-muted);
  line-height: 1.7;
  margin-bottom: 1.5rem;
  font-size: 0.9375rem;
}
.featured-ingredients {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.ingredient-pill {
  font-size: 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}
.featured-tag {
  font-size: 0.75rem;
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-weight: 500;
  font-family: var(--font-ui);
}
.featured-tag-primary {
  background: rgba(196, 93, 62, 0.1);
  color: var(--color-primary);
}
.featured-tag-secondary {
  background: rgba(91, 122, 94, 0.1);
  color: var(--color-secondary);
}
.share-circle-btn {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  background: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
.share-circle-btn:hover {
  background: var(--color-primary);
  color: var(--color-card);
  border-color: var(--color-primary);
}

/* ===== Drop Cap ===== */
.drop-cap::first-letter {
  float: left;
  font-family: var(--font-heading);
  font-size: 3.2rem;
  line-height: 0.8;
  padding-right: 0.5rem;
  padding-top: 0.25rem;
  color: var(--color-primary);
  font-weight: 700;
}

/* ===== Masonry Layout ===== */
.masonry {
  columns: 3;
  column-gap: 1.5rem;
}
.masonry-item {
  break-inside: avoid;
  margin-bottom: 1.5rem;
}
@media (max-width: 1023px) {
  .masonry { columns: 2; }
}
@media (max-width: 639px) {
  .masonry { columns: 1; }
}

/* ===== Scroll Fade Animation ===== */
.fade-up {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.fade-up.visible {
  opacity: 1;
  transform: translateY(0);
}

/* ===== Load More ===== */
.load-more-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem 0;
  color: var(--color-text-muted);
  font-size: 0.875rem;
  font-family: var(--font-ui);
}

/* ===== Empty State ===== */
.empty-state {
  text-align: center;
  padding: 6rem 0;
}

/* ===== Mobile ===== */
@media (max-width: 767px) {
  .hero-section { padding: 1rem 0 2rem; }
  .featured-content { padding: 1.5rem; }
  .featured-title { margin-bottom: 0.75rem; }
}
</style>
