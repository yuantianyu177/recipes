<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useRecipeStore } from '../../stores/recipe'

const router = useRouter()
const store = useRecipeStore()
const message = useMessage()

const newTagName = ref('')
const newTagCategoryId = ref(null)
const newCategoryName = ref('')

// Category searchable dropdown state
const catDropdownOpen = ref(false)
const catSearch = ref('')

// --- Fuzzy match helper ---
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

const filteredCategories = computed(() => {
  if (!catSearch.value) return store.tagCategories
  const kw = catSearch.value.trim()
  if (!kw) return store.tagCategories
  return store.tagCategories.filter((c) => fuzzyMatch(c.name, kw))
})

const selectedCategoryName = computed(() => {
  if (!newTagCategoryId.value) return ''
  const cat = store.tagCategories.find((c) => c.id === newTagCategoryId.value)
  return cat ? cat.name : ''
})

function selectCategory(cat) {
  newTagCategoryId.value = cat.id
  catSearch.value = ''
  catDropdownOpen.value = false
}

function toggleCatDropdown(e) {
  if (document.activeElement === e.target) {
    catDropdownOpen.value = !catDropdownOpen.value
  }
}

function closeCatDropdown() {
  setTimeout(() => { catDropdownOpen.value = false }, 200)
}

function getCategoryColor(categoryName) {
  const cat = store.tagCategories.find((c) => c.name === categoryName)
  return cat?.color || null
}

const tagsByCategory = computed(() => store.getTagsByCategory)

onMounted(async () => {
  await Promise.all([store.fetchTags(), store.fetchTagCategories()])
  setupScrollAnimations()
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

async function handleAddTag() {
  if (!newTagName.value.trim()) return
  if (!newTagCategoryId.value) {
    message.warning('请选择标签分类')
    return
  }
  if (store.tags.some((t) => t.name === newTagName.value.trim())) {
    message.warning('标签已存在')
    return
  }
  try {
    await store.addTag({ name: newTagName.value.trim(), category_id: newTagCategoryId.value })
    newTagName.value = ''
    message.success('标签已添加')
  } catch (err) {
    message.error(err.message || '添加失败')
  }
}

async function handleDeleteTag(id) {
  try {
    await store.deleteTag(id)
  } catch (err) {
    message.error(err.message || '删除失败')
  }
}

async function handleAddCategory() {
  const name = newCategoryName.value.trim()
  if (!name) return
  if (store.tagCategories.some((c) => c.name === name)) {
    message.warning('分类已存在')
    return
  }
  try {
    await store.addTagCategory(name)
    newCategoryName.value = ''
    message.success('分类已添加')
  } catch (err) {
    message.error(err.message || '添加失败')
  }
}

async function handleDeleteCategory(cat) {
  try {
    await store.deleteTagCategory(cat.id)
  } catch (err) {
    message.error(err.message || '删除失败')
  }
}
</script>

<template>
  <div class="admin-tag-manage max-w-2xl mx-auto">
    <!-- Editorial Header -->
    <section class="admin-hero fade-up">
      <button class="back-btn" @click="router.push('/admin')">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回
      </button>
      <p class="admin-subtitle">Tag Management</p>
      <div class="deco-line mb-4"></div>
      <h1 class="admin-title">标签管理</h1>
      <p class="admin-desc">管理菜谱标签与分类，让你的菜谱更易于检索。</p>
    </section>

    <!-- Category Management -->
    <section class="manage-section fade-up">
      <div class="section-label">
        <span>分类管理</span>
        <span class="w-8 h-px" style="background: var(--color-accent);"></span>
      </div>
      <div class="card-warm rounded-2xl p-6">
        <div class="flex flex-wrap gap-2 mb-4">
          <span
            v-for="cat in store.tagCategories"
            :key="cat.id"
            class="category-pill"
            :style="cat.color ? { background: cat.color + '1a', color: cat.color } : {}"
          >
            <span>{{ cat.name }}</span>
            <button class="pill-delete" @click="handleDeleteCategory(cat)" title="删除分类">×</button>
          </span>
          <span v-if="store.tagCategories.length === 0" class="text-xs" style="color: var(--color-text-muted); font-family: var(--font-ui);">暂无分类</span>
        </div>
        <div class="flex gap-2 items-center">
          <input
            v-model="newCategoryName"
            type="text"
            placeholder="新分类名称"
            class="input-warm flex-1 min-w-[120px] px-4 py-2.5 rounded-xl outline-none text-sm"
            @keyup.enter="handleAddCategory"
          />
          <button class="btn-secondary" @click="handleAddCategory">添加</button>
        </div>
      </div>
    </section>

    <!-- Add Tag -->
    <section class="manage-section fade-up" style="z-index: 10;">
      <div class="section-label">
        <span>新增标签</span>
        <span class="w-8 h-px" style="background: var(--color-primary);"></span>
      </div>
      <div class="card-warm rounded-2xl p-6">
        <div class="flex gap-2 items-center flex-wrap">
          <input
            v-model="newTagName"
            type="text"
            placeholder="标签名称"
            class="input-warm flex-1 min-w-[140px] px-4 py-2.5 rounded-xl outline-none text-sm"
            @keyup.enter="handleAddTag"
          />
          <!-- Custom searchable category dropdown -->
          <div class="relative min-w-[160px]">
            <input
              v-model="catSearch"
              type="text"
              :placeholder="selectedCategoryName || '选择分类...'"
              class="input-warm w-full px-4 py-2.5 rounded-xl outline-none transition-all text-sm"
              @focus="catDropdownOpen = true"
              @mousedown="toggleCatDropdown"
              @blur="closeCatDropdown"
            />
            <svg
              class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none transition-transform"
              :class="{ 'rotate-180': catDropdownOpen }"
              style="color: var(--color-text-muted);"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            <div
              v-if="catDropdownOpen"
              class="dropdown-panel"
            >
              <button
                v-for="cat in filteredCategories"
                :key="cat.id"
                class="dropdown-item"
                :class="{ 'dropdown-selected': cat.id === newTagCategoryId }"
                :style="cat.color ? { color: cat.color } : {}"
                @mousedown.prevent="selectCategory(cat)"
              >
                {{ cat.name }}
              </button>
              <div v-if="filteredCategories.length === 0" class="dropdown-empty">
                无匹配分类
              </div>
            </div>
          </div>
          <button class="btn-primary" @click="handleAddTag">添加</button>
        </div>
      </div>
    </section>

    <!-- Tags by Category -->
    <section class="manage-section fade-up">
      <div class="elegant-divider mb-6">
        <span>全部标签</span>
      </div>
      <div class="space-y-4">
        <div
          v-for="(catTags, category) in tagsByCategory"
          :key="category"
          class="card-warm rounded-2xl p-5"
        >
          <h3 class="cat-heading" :style="getCategoryColor(category) ? { color: getCategoryColor(category) } : {}">{{ category }}</h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="tag in catTags"
              :key="tag.id"
              class="tag-pill-admin"
              :style="tag.color ? { background: tag.color + '1a', color: tag.color } : {}"
            >
              <span>{{ tag.name }}</span>
              <button class="pill-delete-primary" @click="handleDeleteTag(tag.id)">×</button>
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- Empty -->
    <div v-if="store.tags.length === 0" class="empty-state fade-up">
      <svg class="mx-auto mb-5" width="80" height="60" viewBox="0 0 80 60" fill="none">
        <rect x="10" y="15" width="28" height="14" rx="7" stroke="var(--color-border)" stroke-width="1.5" fill="var(--color-card)" />
        <rect x="42" y="15" width="28" height="14" rx="7" stroke="var(--color-border)" stroke-width="1.5" fill="var(--color-card)" />
        <rect x="20" y="35" width="40" height="14" rx="7" stroke="var(--color-border)" stroke-width="1.5" fill="var(--color-card)" />
      </svg>
      <p class="text-lg mb-1" style="color: var(--color-text-muted); font-family: var(--font-heading);">暂无标签</p>
      <p class="text-sm" style="color: var(--color-text-muted);">在上方添加你的第一个标签</p>
    </div>
  </div>
</template>

<style scoped>
/* ===== Editorial Header ===== */
.admin-hero {
  padding: 0 0 2rem;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  font-family: var(--font-ui);
  margin-bottom: 1.25rem;
  padding: 0.375rem 0.75rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}
.back-btn:hover {
  color: var(--color-primary);
  background: var(--color-primary-light);
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

/* ===== Section ===== */
.manage-section {
  margin-bottom: 2rem;
  position: relative;
  z-index: 1;
}
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

/* ===== Category Pill ===== */
.category-pill {
  display: inline-flex;
  align-items: center;
  font-size: 0.8125rem;
  padding: 0.375rem 0.75rem;
  border-radius: 999px;
  font-weight: 500;
  font-family: var(--font-ui);
  background: var(--color-secondary-light);
  color: var(--color-secondary);
  transition: all 0.2s ease;
}
.pill-delete {
  margin-left: 0.25rem;
  width: 1rem;
  flex-shrink: 0;
  color: inherit;
  opacity: 0.4;
  cursor: pointer;
  background: none;
  border: none;
  font-size: 1rem;
  line-height: 1;
  transition: all 0.2s;
}
.pill-delete:hover {
  opacity: 1;
  color: #b44a3e;
}

/* ===== Tag Pill ===== */
.tag-pill-admin {
  display: inline-flex;
  align-items: center;
  font-size: 0.8125rem;
  padding: 0.375rem 0.75rem;
  border-radius: 999px;
  font-weight: 500;
  font-family: var(--font-ui);
  background: var(--color-primary-light);
  color: var(--color-primary);
  transition: all 0.2s ease;
}
.pill-delete-primary {
  margin-left: 0.25rem;
  width: 1rem;
  flex-shrink: 0;
  color: inherit;
  opacity: 0.4;
  cursor: pointer;
  background: none;
  border: none;
  font-size: 1rem;
  line-height: 1;
  transition: all 0.2s;
}
.pill-delete-primary:hover {
  opacity: 1;
  color: #b44a3e;
}

.cat-heading {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}

/* ===== Dropdown ===== */
.dropdown-panel {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 0.25rem;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  box-shadow: 0 8px 24px rgba(61, 51, 41, 0.12);
  z-index: 50;
  max-height: 12rem;
  overflow-y: auto;
}
.dropdown-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  color: var(--color-text);
  font-family: var(--font-ui);
  background: none;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.dropdown-item:hover {
  background: var(--color-bg);
}
.dropdown-selected {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.dropdown-empty {
  padding: 1rem;
  text-align: center;
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}

/* ===== Empty State ===== */
.empty-state {
  text-align: center;
  padding: 4rem 0;
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
