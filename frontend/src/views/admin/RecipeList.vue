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
  setupScrollAnimations()
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

// Scroll-triggered fade-up animation
function setupScrollAnimations() {
  const fadeObserver = new IntersectionObserver(
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
  <div class="admin-recipe-list">
    <!-- Editorial Header -->
    <section class="admin-hero fade-up">
      <div class="grid md:grid-cols-12 gap-6 items-end">
        <div class="md:col-span-7">
          <p class="admin-subtitle">Recipe Management</p>
          <div class="deco-line mb-4"></div>
          <h1 class="admin-title">菜谱管理</h1>
          <p class="admin-desc">在这里管理你的所有菜谱，创建、编辑或删除。</p>
        </div>
        <div class="md:col-span-5">
          <div class="admin-actions-card">
            <div class="flex gap-2 flex-wrap mb-4">
              <button class="btn-primary" @click="router.push('/admin/recipe/new')">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                新建菜谱
              </button>
              <button class="btn-ghost" @click="router.push('/admin/tags')">标签管理</button>
              <button class="btn-ghost" @click="router.push('/admin/ingredients')">食材管理</button>
            </div>
            <!-- Search -->
            <div class="relative">
              <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <input
                v-model="keyword"
                type="text"
                placeholder="搜索菜谱..."
                class="search-input"
              />
              <button v-if="keyword" class="search-clear" @click="keyword = ''">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Results count divider -->
    <div class="results-divider fade-up">
      <span></span>
      <span>共 <strong>{{ allFilteredRecipes.length }}</strong> 道菜谱</span>
      <span></span>
    </div>

    <!-- Recipe Cards Grid -->
    <div
      v-if="displayedRecipes.length > 0"
      class="recipe-grid"
    >
      <div
        v-for="(recipe, idx) in displayedRecipes"
        :key="recipe.id"
        class="recipe-admin-card fade-up"
        :style="{ animationDelay: `${(idx % 6) * 0.06}s` }"
      >
        <!-- Cover -->
        <div class="card-cover">
          <img :src="getCover(recipe)" :alt="recipe.name" />
          <div class="card-cover-overlay" />
          <div class="card-cover-content">
            <h3>{{ recipe.name }}</h3>
            <div class="flex gap-1 mt-1.5">
              <span
                v-for="tag in recipe.tags.slice(0, 2)"
                :key="tag.id"
                class="card-tag"
                :style="tag.color ? { background: tag.color + '33', color: '#fff' } : {}"
              >
                {{ tag.name }}
              </span>
            </div>
          </div>
          <div v-if="recipe.calories" class="card-calorie">
            {{ recipe.calories }} kcal
          </div>
        </div>

        <!-- Actions -->
        <div class="card-actions">
          <span class="card-date">{{ formatDate(recipe.updated_at) }}</span>
          <div class="flex gap-1.5">
            <button class="action-edit" @click="router.push(`/admin/recipe/${recipe.id}/edit`)">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              编辑
            </button>
            <button class="action-delete" @click="confirmDelete(recipe.id)">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              删除
            </button>
          </div>
        </div>
      </div>
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

    <!-- Empty -->
    <div v-if="allFilteredRecipes.length === 0" class="empty-state fade-up">
      <svg class="mx-auto mb-6" width="100" height="80" viewBox="0 0 100 80" fill="none">
        <rect x="15" y="10" width="70" height="50" rx="6" stroke="var(--color-border)" stroke-width="1.5" fill="var(--color-card)" />
        <path d="M15 25h70" stroke="var(--color-border)" stroke-width="1" />
        <rect x="25" y="32" width="20" height="3" rx="1.5" fill="var(--color-border)" />
        <rect x="25" y="40" width="35" height="3" rx="1.5" fill="var(--color-border)" opacity="0.5" />
        <rect x="25" y="48" width="15" height="3" rx="1.5" fill="var(--color-border)" opacity="0.3" />
        <circle cx="65" cy="42" r="8" stroke="var(--color-text-muted)" stroke-width="1.5" fill="none" opacity="0.4" />
        <path d="M70 47l4 4" stroke="var(--color-text-muted)" stroke-width="1.5" stroke-linecap="round" opacity="0.4" />
      </svg>
      <p class="text-lg mb-2" style="color: var(--color-text-muted); font-family: var(--font-heading);">暂无菜谱</p>
      <p class="text-sm mb-4" style="color: var(--color-text-muted);">点击上方按钮创建你的第一道菜谱</p>
    </div>

    <!-- Delete confirmation dialog -->
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
          v-if="showDeleteConfirm"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          @click.self="showDeleteConfirm = false"
        >
          <div class="modal-card">
            <div class="modal-deco"></div>
            <h3 class="modal-title">确认删除</h3>
            <p class="modal-desc">确定要删除这道菜谱吗？此操作不可撤销。</p>
            <div class="flex gap-3 justify-end">
              <button class="btn-soft" @click="showDeleteConfirm = false">取消</button>
              <button class="btn-danger" @click="doDelete">确认删除</button>
            </div>
          </div>
        </div>
      </transition>
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
          class="btn-back-top fixed bottom-8 right-8 z-40"
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
/* ===== Editorial Header ===== */
.admin-hero {
  padding: 1rem 0 2.5rem;
}
.admin-subtitle {
  color: var(--color-text-muted);
  font-size: 0.7rem;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
  font-weight: 500;
  font-family: var(--font-ui);
}
.deco-line {
  width: 48px;
  height: 1px;
  background: var(--color-primary);
}
.admin-title {
  font-family: var(--font-heading);
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
  color: var(--color-text);
  margin-bottom: 0.75rem;
}
.admin-desc {
  color: var(--color-text-muted);
  font-size: 0.9375rem;
  line-height: 1.6;
  font-family: var(--font-body);
  max-width: 28rem;
}

/* ===== Actions Card ===== */
.admin-actions-card {
  background: var(--color-card);
  border-radius: 1rem;
  padding: 1.25rem;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 12px rgba(61, 51, 41, 0.06);
}

/* ===== Search ===== */
.search-icon {
  position: absolute;
  left: 0.875rem;
  top: 50%;
  transform: translateY(-50%);
  width: 1.125rem;
  height: 1.125rem;
  color: var(--color-text-muted);
}
.search-input {
  width: 100%;
  padding: 0.75rem 2.25rem 0.75rem 2.75rem;
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
  box-shadow: 0 0 0 2px rgba(196, 93, 62, 0.15);
  border-color: var(--color-primary);
}
.search-clear {
  position: absolute;
  right: 0.625rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}
.search-clear:hover { color: var(--color-text); }

/* ===== Results Divider ===== */
.results-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  margin-bottom: 2rem;
  letter-spacing: 0.05em;
}
.results-divider span:first-child,
.results-divider span:last-child {
  flex: 1;
  height: 1px;
  background: var(--color-border);
  max-width: 80px;
}
.results-divider strong {
  color: var(--color-text);
  font-family: var(--font-heading);
  font-size: 1rem;
}

/* ===== Recipe Grid ===== */
.recipe-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}
@media (max-width: 1023px) {
  .recipe-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 639px) {
  .recipe-grid { grid-template-columns: 1fr; }
}

/* ===== Recipe Card ===== */
.recipe-admin-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
  overflow: hidden;
  transition: all 0.35s cubic-bezier(.22,.61,.36,1);
}
.recipe-admin-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px -8px rgba(61, 51, 41, 0.15);
}

.card-cover {
  position: relative;
  aspect-ratio: 16/10;
  overflow: hidden;
}
.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s cubic-bezier(.22,.61,.36,1);
}
.recipe-admin-card:hover .card-cover img {
  transform: scale(1.06);
}
.card-cover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.5) 0%, transparent 60%);
}
.card-cover-content {
  position: absolute;
  bottom: 0.875rem;
  left: 1rem;
  right: 1rem;
}
.card-cover-content h3 {
  color: #fff;
  font-family: var(--font-heading);
  font-weight: 700;
  font-size: 1.0625rem;
  text-shadow: 0 1px 4px rgba(0,0,0,0.3);
  line-height: 1.3;
}
.card-tag {
  font-size: 0.625rem;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.2);
  color: #fff;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  font-family: var(--font-ui);
  letter-spacing: 0.03em;
}
.card-calorie {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: rgba(255, 253, 248, 0.85);
  color: var(--color-primary);
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  font-family: var(--font-ui);
}

/* ===== Card Actions ===== */
.card-actions {
  padding: 0.875rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-date {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}
.action-edit {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-primary);
  background: var(--color-primary-light);
  border: none;
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all 0.2s ease;
}
.action-edit:hover {
  background: var(--color-primary);
  color: #fff;
}
.action-delete {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: #b44a3e;
  background: #fdf2f0;
  border: none;
  cursor: pointer;
  font-family: var(--font-ui);
  transition: all 0.2s ease;
}
.action-delete:hover {
  background: #b44a3e;
  color: #fff;
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
  padding: 5rem 0;
}

/* ===== Modal ===== */
.modal-card {
  background: var(--color-card);
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 25px 60px -12px rgba(61, 51, 41, 0.25);
  max-width: 24rem;
  width: 100%;
  margin: 0 1rem;
  position: relative;
  overflow: hidden;
}
.modal-deco {
  width: 40px;
  height: 2px;
  background: var(--color-primary);
  margin-bottom: 1.25rem;
}
.modal-title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}
.modal-desc {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  margin-bottom: 1.5rem;
  line-height: 1.6;
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

/* ===== Mobile ===== */
@media (max-width: 767px) {
  .admin-hero { padding: 0.5rem 0 1.5rem; }
  .admin-title { margin-bottom: 0.5rem; }
}
</style>
