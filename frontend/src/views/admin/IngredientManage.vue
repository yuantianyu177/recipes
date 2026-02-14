<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useRecipeStore } from '../../stores/recipe'

const router = useRouter()
const store = useRecipeStore()
const message = useMessage()

const keyword = ref('')
const newName = ref('')
const newUnit = ref('')
const newCalorie = ref('')
const newCategoryId = ref(null)

onMounted(async () => {
  await Promise.all([store.fetchIngredients(), store.fetchIngredientCategories()])
})

// --- Category management ---
const newCategoryName = ref('')

async function handleAddCategory() {
  const name = newCategoryName.value.trim()
  if (!name) return
  if (store.ingredientCategories.some((c) => c.name === name)) {
    message.warning('分类已存在')
    return
  }
  try {
    await store.addIngredientCategory(name)
    newCategoryName.value = ''
    message.success('分类已添加')
  } catch (err) {
    message.error(err.message || '添加失败')
  }
}

async function handleDeleteCategory(cat) {
  try {
    await store.deleteIngredientCategory(cat.id)
  } catch (err) {
    message.error(err.message || '删除失败')
  }
}

// --- Category dropdown for new ingredient ---
const newCatDropdownOpen = ref(false)
const newCatSearchText = ref('')

const filteredNewCats = computed(() => {
  if (!newCatSearchText.value) return store.ingredientCategories
  return store.ingredientCategories.filter((c) => fuzzyMatch(c.name, newCatSearchText.value.trim()))
})

const selectedNewCatName = computed(() => {
  if (!newCategoryId.value) return ''
  const cat = store.ingredientCategories.find((c) => c.id === newCategoryId.value)
  return cat ? cat.name : ''
})

function selectNewCat(cat) {
  newCategoryId.value = cat.id
  newCatSearchText.value = ''
  newCatDropdownOpen.value = false
}

function closeNewCatDropdown() {
  setTimeout(() => { newCatDropdownOpen.value = false }, 200)
}

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

// --- Filtering ---
const filtered = computed(() => {
  if (!keyword.value) return store.ingredients
  const kw = keyword.value.trim()
  if (!kw) return store.ingredients
  return store.ingredients.filter((i) => fuzzyMatch(i.name, kw))
})

// --- Add ---
async function handleAdd() {
  if (!newName.value.trim() || !newUnit.value.trim()) {
    message.error('请输入食材名和单位')
    return
  }
  if (store.ingredients.some((i) => i.name === newName.value.trim())) {
    message.error('该食材已存在')
    return
  }
  try {
    await store.addIngredient({
      name: newName.value.trim(),
      unit: newUnit.value.trim(),
      calorie: parseFloat(newCalorie.value) || 0,
      category_id: newCategoryId.value,
    })
    newName.value = ''
    newUnit.value = ''
    newCalorie.value = ''
    message.success('食材已添加')
  } catch (err) {
    message.error(err.message || '添加失败')
  }
}

// --- Edit ---
const editingId = ref(null)
const editForm = ref({ name: '', unit: '', calorie: '', category_id: null })

// Edit category dropdown
const editCatDropdownOpen = ref(false)
const editCatSearchText = ref('')

const filteredEditCats = computed(() => {
  if (!editCatSearchText.value) return store.ingredientCategories
  return store.ingredientCategories.filter((c) => fuzzyMatch(c.name, editCatSearchText.value.trim()))
})

const selectedEditCatName = computed(() => {
  if (!editForm.value.category_id) return ''
  const cat = store.ingredientCategories.find((c) => c.id === editForm.value.category_id)
  return cat ? cat.name : ''
})

function selectEditCat(cat) {
  editForm.value.category_id = cat.id
  editCatSearchText.value = ''
  editCatDropdownOpen.value = false
}

function closeEditCatDropdown() {
  setTimeout(() => { editCatDropdownOpen.value = false }, 200)
}

function startEdit(item) {
  editingId.value = item.id
  editForm.value = {
    name: item.name,
    unit: item.unit,
    calorie: item.calorie || '',
    category_id: item.category_id || null,
  }
}

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(id) {
  if (!editForm.value.name.trim() || !editForm.value.unit.trim()) {
    message.error('食材名和单位不能为空')
    return
  }
  const dup = store.ingredients.find(
    (i) => i.name === editForm.value.name.trim() && i.id !== id
  )
  if (dup) {
    message.error('该食材名已被使用')
    return
  }
  try {
    await store.updateIngredient(id, {
      name: editForm.value.name.trim(),
      unit: editForm.value.unit.trim(),
      calorie: parseFloat(editForm.value.calorie) || 0,
      category_id: editForm.value.category_id,
    })
    editingId.value = null
    message.success('食材已更新')
  } catch (err) {
    message.error(err.message || '更新失败')
  }
}

function getCategoryName(catId) {
  if (!catId) return '-'
  const cat = store.ingredientCategories.find((c) => c.id === catId)
  return cat ? cat.name : '-'
}

// --- Delete ---
const showDeleteConfirm = ref(false)
const pendingDeleteId = ref(null)

function confirmDelete(id) {
  pendingDeleteId.value = id
  showDeleteConfirm.value = true
}

async function doDelete() {
  if (pendingDeleteId.value) {
    try {
      await store.deleteIngredient(pendingDeleteId.value)
      message.success('食材已删除')
    } catch (err) {
      message.error(err.message || '删除失败')
    }
  }
  showDeleteConfirm.value = false
  pendingDeleteId.value = null
}
</script>

<template>
  <div class="max-w-3xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <button
        class="btn-ghost btn-sm mb-3"
        @click="router.push('/admin')"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回管理
      </button>
      <h1 class="section-heading text-2xl font-bold">食材管理</h1>
      <p class="text-sm mt-0.5" style="color: var(--color-text-muted); font-family: var(--font-ui);">管理全局食材库，包含标准单位、卡路里和分类信息</p>
    </div>

    <!-- Ingredient Category Management -->
    <div class="card-warm rounded-2xl p-6 mb-6">
      <h3 class="text-sm font-semibold mb-3 section-heading">食材分类管理</h3>
      <p class="text-xs mb-3" style="color: var(--color-text-muted); font-family: var(--font-ui);">管理食材的角色分类（如主料、辅料等），新建食材时可选择分类</p>
      <div class="flex flex-wrap gap-2 mb-3">
        <span
          v-for="cat in store.ingredientCategories"
          :key="cat.id"
          class="inline-flex items-center justify-center text-sm px-3 py-1.5 rounded-full font-medium group leading-none"
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

    <!-- Add Ingredient -->
    <div class="card-warm rounded-2xl p-6 mb-6">
      <h3 class="text-sm font-semibold mb-3 section-heading">新增食材</h3>
      <div class="flex gap-2 items-center flex-wrap">
        <input
          v-model="newName"
          type="text"
          placeholder="食材名"
          class="input-warm flex-1 min-w-[120px] px-4 py-2.5 rounded-xl outline-none text-sm"
          @keyup.enter="handleAdd"
        />
        <input
          v-model="newUnit"
          type="text"
          placeholder="单位 (克/个/...)"
          class="input-warm w-28 px-4 py-2.5 rounded-xl outline-none text-sm"
        />
        <input
          v-model="newCalorie"
          type="number"
          placeholder="kcal/单位"
          step="0.1"
          min="0"
          class="input-warm w-28 px-4 py-2.5 rounded-xl outline-none text-sm"
        />
        <!-- Category dropdown -->
        <div class="relative w-28">
          <input
            v-model="newCatSearchText"
            type="text"
            :placeholder="selectedNewCatName || '分类'"
            class="input-warm w-full px-3 py-2.5 rounded-xl outline-none text-sm"
            @focus="newCatDropdownOpen = true"
            @blur="closeNewCatDropdown"
          />
          <div
            v-if="newCatDropdownOpen"
            class="card-warm absolute top-full left-0 right-0 mt-1 rounded-lg shadow-xl z-20 max-h-36 overflow-y-auto min-w-[100px]"
          >
            <button
              v-for="cat in filteredNewCats"
              :key="cat.id"
              class="block w-full text-left px-3 py-1.5 text-sm transition-colors"
              :class="{ 'dropdown-selected': cat.id === newCategoryId }"
              style="color: var(--color-text); font-family: var(--font-ui);"
              @mousedown.prevent="selectNewCat(cat)"
            >
              {{ cat.name }}
            </button>
            <div v-if="filteredNewCats.length === 0" class="px-3 py-2 text-center text-xs" style="color: var(--color-text-muted); font-family: var(--font-ui);">
              无匹配
            </div>
          </div>
        </div>
        <button
          class="btn-primary"
          @click="handleAdd"
        >
          添加
        </button>
      </div>
    </div>

    <!-- Search (full width) -->
    <div class="relative mb-5">
      <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
        <svg class="w-4 h-4" style="color: var(--color-text-muted);" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <input
        v-model="keyword"
        type="text"
        placeholder="搜索食材..."
        class="input-warm w-full pr-4 py-2.5 rounded-xl outline-none transition-all text-sm"
        style="padding-left: 2.5rem;"
      />
    </div>

    <p class="text-xs mb-3" style="color: var(--color-text-muted); font-family: var(--font-ui);">共 {{ filtered.length }} 种食材</p>

    <!-- Ingredient List -->
    <div class="card-warm rounded-2xl overflow-hidden">
      <div
        v-for="(item, idx) in filtered"
        :key="item.id"
        class="px-5 py-3 transition-colors"
        :class="{ 'border-t': idx > 0 }"
        style="border-color: var(--color-bg);"
      >
        <!-- View mode -->
        <div v-if="editingId !== item.id" class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="font-medium text-sm" style="color: var(--color-text); font-family: var(--font-body);">{{ item.name }}</span>
            <span class="text-xs px-2 py-0.5 rounded-full" style="color: var(--color-text-muted); background: var(--color-bg); font-family: var(--font-ui);">{{ item.unit }}</span>
            <span v-if="item.category" class="text-xs px-2 py-0.5 rounded-full" style="color: var(--color-secondary); background: var(--color-secondary-light); font-family: var(--font-ui);">{{ item.category }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs tabular-nums" style="color: var(--color-text-muted); font-family: var(--font-ui);">
              {{ item.calorie ? `${item.calorie} kcal` : '-' }}
            </span>
            <button
              class="text-xs transition-colors"
              style="color: var(--color-primary); font-family: var(--font-ui);"
              @click="startEdit(item)"
            >
              编辑
            </button>
            <button
              class="text-xs hover:text-red-500 transition-colors"
              style="color: var(--color-text-muted); font-family: var(--font-ui);"
              @click="confirmDelete(item.id)"
            >
              删除
            </button>
          </div>
        </div>

        <!-- Edit mode -->
        <div v-else class="flex gap-2 items-center flex-wrap">
          <input
            v-model="editForm.name"
            type="text"
            class="flex-1 min-w-[100px] px-3 py-1.5 rounded-lg outline-none text-sm"
            style="border: 1px solid var(--color-primary); font-family: var(--font-ui);"
          />
          <input
            v-model="editForm.unit"
            type="text"
            placeholder="单位"
            class="w-20 px-3 py-1.5 rounded-lg outline-none text-sm"
            style="border: 1px solid var(--color-primary); font-family: var(--font-ui);"
          />
          <input
            v-model="editForm.calorie"
            type="number"
            placeholder="kcal"
            step="0.1"
            class="w-20 px-3 py-1.5 rounded-lg outline-none text-sm"
            style="border: 1px solid var(--color-primary); font-family: var(--font-ui);"
          />
          <!-- Category dropdown for edit -->
          <div class="relative w-20">
            <input
              v-model="editCatSearchText"
              type="text"
              :placeholder="selectedEditCatName || '分类'"
              class="w-full px-2 py-1.5 rounded-lg outline-none text-sm"
              style="border: 1px solid var(--color-primary); font-family: var(--font-ui);"
              @focus="editCatDropdownOpen = true"
              @blur="closeEditCatDropdown"
            />
            <div
              v-if="editCatDropdownOpen"
              class="card-warm absolute top-full left-0 mt-1 rounded-lg shadow-xl z-20 max-h-36 overflow-y-auto min-w-[100px]"
            >
              <button
                v-for="cat in filteredEditCats"
                :key="cat.id"
                class="block w-full text-left px-3 py-1.5 text-sm transition-colors"
                :class="{ 'dropdown-selected': cat.id === editForm.category_id }"
                style="color: var(--color-text); font-family: var(--font-ui);"
                @mousedown.prevent="selectEditCat(cat)"
              >
                {{ cat.name }}
              </button>
            </div>
          </div>
          <button
            class="btn-primary btn-sm"
            @click="saveEdit(item.id)"
          >
            保存
          </button>
          <button
            class="btn-soft btn-sm"
            @click="cancelEdit"
          >
            取消
          </button>
        </div>
      </div>

      <div v-if="filtered.length === 0" class="text-center py-12">
        <div class="text-4xl mb-2">🥬</div>
        <p class="text-sm" style="color: var(--color-text-muted); font-family: var(--font-ui);">暂无食材</p>
      </div>
    </div>

    <!-- Delete confirmation -->
    <Teleport to="body">
      <div
        v-if="showDeleteConfirm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
        @click.self="showDeleteConfirm = false"
      >
        <div class="rounded-2xl p-6 shadow-2xl max-w-sm w-full mx-4" style="background: var(--color-card);">
          <h3 class="text-lg font-bold mb-2" style="color: var(--color-text); font-family: var(--font-heading);">确认删除</h3>
          <p class="text-sm mb-6" style="color: var(--color-text-muted); font-family: var(--font-ui);">确定要删除这个食材吗？</p>
          <div class="flex gap-3 justify-end">
            <button
              class="btn-soft"
              @click="showDeleteConfirm = false"
            >
              取消
            </button>
            <button
              class="btn-danger"
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

<style scoped>
.dropdown-selected {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
</style>
