<script setup>
import { ref, computed, onMounted } from 'vue'
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

function closeCatDropdown() {
  setTimeout(() => { catDropdownOpen.value = false }, 200)
}

const tagsByCategory = computed(() => store.getTagsByCategory)

onMounted(async () => {
  await Promise.all([store.fetchTags(), store.fetchTagCategories()])
})

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
  <div class="max-w-2xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <button class="btn-ghost btn-sm mb-3" @click="router.push('/admin')">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回管理
      </button>
      <h1 class="section-heading text-2xl font-bold" style="color: var(--color-text);">标签管理</h1>
    </div>

    <!-- Manage Tag Categories -->
    <div class="card-warm rounded-2xl p-6 mb-6">
      <h3 class="text-sm font-semibold mb-3 section-heading">标签分类管理</h3>
      <div class="flex flex-wrap gap-2 mb-3">
        <span
          v-for="cat in store.tagCategories"
          :key="cat.id"
          class="inline-flex items-center justify-center text-sm px-3 py-1.5 rounded-full font-medium group"
          style="background: var(--color-secondary-light); color: var(--color-secondary); font-family: var(--font-ui);"
        >
          <span class="mx-1">{{ cat.name }}</span>
          <button
            class="w-4 flex-shrink-0 hover:text-red-500 transition-colors opacity-50 hover:opacity-100"
            style="color: var(--color-secondary);"
            @click="handleDeleteCategory(cat)"
            title="删除分类"
          >
            ×
          </button>
        </span>
      </div>
      <div class="flex gap-2 items-center">
        <input
          v-model="newCategoryName"
          type="text"
          placeholder="新分类名称"
          class="input-warm flex-1 min-w-[120px] px-4 py-2 rounded-xl outline-none text-sm"
          @keyup.enter="handleAddCategory"
        />
        <button
          class="btn-secondary whitespace-nowrap"
          @click="handleAddCategory"
        >
          添加
        </button>
      </div>
    </div>

    <!-- Add Tag -->
    <div class="card-warm rounded-2xl p-6 mb-6">
      <h3 class="text-sm font-semibold mb-3 section-heading">新增标签</h3>
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
            class="card-warm absolute top-full left-0 right-0 mt-1 rounded-xl shadow-xl z-20 max-h-48 overflow-y-auto"
          >
            <button
              v-for="cat in filteredCategories"
              :key="cat.id"
              class="block w-full text-left px-4 py-2 text-sm transition-colors"
              :class="{ 'dropdown-selected': cat.id === newTagCategoryId }"
              style="color: var(--color-text); font-family: var(--font-ui);"
              @mousedown.prevent="selectCategory(cat)"
            >
              {{ cat.name }}
            </button>
            <div v-if="filteredCategories.length === 0" class="px-4 py-3 text-center text-sm" style="color: var(--color-text-muted); font-family: var(--font-ui);">
              无匹配分类
            </div>
          </div>
        </div>

        <button
          class="btn-primary"
          @click="handleAddTag"
        >
          添加
        </button>
      </div>
    </div>

    <!-- Tags by Category -->
    <div class="space-y-4">
      <div
        v-for="(catTags, category) in tagsByCategory"
        :key="category"
        class="card-warm rounded-2xl p-5"
      >
        <h3 class="text-sm font-semibold mb-3" style="color: var(--color-text-muted); font-family: var(--font-ui);">{{ category }}</h3>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tag in catTags"
            :key="tag.id"
            class="inline-flex items-center justify-center text-sm px-3 py-1.5 rounded-full font-medium group leading-none"
            style="background: var(--color-primary-light); color: var(--color-primary); font-family: var(--font-ui);"
          >
            <span class="mx-1">{{ tag.name }}</span>
            <button
              class="w-4 flex-shrink-0 hover:text-red-500 transition-colors opacity-50 hover:opacity-100"
              style="color: var(--color-primary);"
              @click="handleDeleteTag(tag.id)"
            >
              ×
            </button>
          </span>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-if="store.tags.length === 0" class="text-center py-20">
      <div class="text-5xl mb-3">🏷️</div>
      <p style="color: var(--color-text-muted);">暂无标签</p>
    </div>
  </div>
</template>

<style scoped>
.dropdown-selected {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
</style>
