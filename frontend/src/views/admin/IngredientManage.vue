<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
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

function toggleNewCatDropdown(e) {
  if (document.activeElement === e.target) {
    newCatDropdownOpen.value = !newCatDropdownOpen.value
  }
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

function toggleEditCatDropdown(e) {
  if (document.activeElement === e.target) {
    editCatDropdownOpen.value = !editCatDropdownOpen.value
  }
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

function getCategoryColor(catId) {
  if (!catId) return null
  const cat = store.ingredientCategories.find((c) => c.id === catId)
  return cat?.color || null
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
  <div class="admin-ingredient max-w-3xl mx-auto">
    <!-- Editorial Header -->
    <section class="admin-hero fade-up">
      <button class="back-btn" @click="router.push('/admin')">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回
      </button>
      <p class="admin-subtitle">Ingredient Library</p>
      <div class="deco-line mb-4"></div>
      <h1 class="admin-title">食材管理</h1>
      <p class="admin-desc">管理全局食材库，包含标准单位、卡路里和分类信息。</p>
    </section>

    <!-- Ingredient Category Management -->
    <section class="manage-section fade-up">
      <div class="section-label">
        <span>食材分类</span>
        <span class="w-8 h-px" style="background: var(--color-secondary);"></span>
      </div>
      <div class="card-warm rounded-2xl p-6">
        <p class="text-xs mb-3" style="color: var(--color-text-muted); font-family: var(--font-ui);">管理食材的角色分类（如主料、辅料等），新建食材时可选择分类</p>
        <div class="flex flex-wrap gap-2 mb-4">
          <span
            v-for="cat in store.ingredientCategories"
            :key="cat.id"
            class="category-pill"
            :style="cat.color ? { background: cat.color + '1a', color: cat.color } : {}"
          >
            <span>{{ cat.name }}</span>
            <button class="pill-delete" @click="handleDeleteCategory(cat)" title="删除分类">×</button>
          </span>
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

    <!-- Add Ingredient -->
    <section class="manage-section fade-up" style="z-index: 10;">
      <div class="section-label">
        <span>新增食材</span>
        <span class="w-8 h-px" style="background: var(--color-primary);"></span>
      </div>
      <div class="card-warm rounded-2xl p-6">
        <div class="flex gap-2 items-center flex-wrap">
          <input v-model="newName" type="text" placeholder="食材名" class="input-warm flex-1 min-w-[120px] px-4 py-2.5 rounded-xl outline-none text-sm" @keyup.enter="handleAdd" />
          <input v-model="newUnit" type="text" placeholder="单位 (克/个/...)" class="input-warm w-28 px-4 py-2.5 rounded-xl outline-none text-sm" />
          <input v-model="newCalorie" type="number" placeholder="kcal/单位" step="0.1" min="0" class="input-warm w-28 px-4 py-2.5 rounded-xl outline-none text-sm" />
          <!-- Category dropdown -->
          <div class="relative w-28">
            <input
              v-model="newCatSearchText"
              type="text"
              :placeholder="selectedNewCatName || '分类'"
              class="input-warm w-full px-3 py-2.5 rounded-xl outline-none text-sm"
              @focus="newCatDropdownOpen = true"
              @mousedown="toggleNewCatDropdown"
              @blur="closeNewCatDropdown"
            />
            <div v-if="newCatDropdownOpen" class="dropdown-panel">
              <button
                v-for="cat in filteredNewCats"
                :key="cat.id"
                class="dropdown-item"
                :class="{ 'dropdown-selected': cat.id === newCategoryId }"
                :style="cat.color ? { color: cat.color } : {}"
                @mousedown.prevent="selectNewCat(cat)"
              >
                {{ cat.name }}
              </button>
              <div v-if="filteredNewCats.length === 0" class="dropdown-empty">无匹配</div>
            </div>
          </div>
          <button class="btn-primary" @click="handleAdd">添加</button>
        </div>
      </div>
    </section>

    <!-- Search -->
    <section class="manage-section fade-up">
      <div class="elegant-divider mb-4">
        <span>食材列表</span>
      </div>
      <div class="relative mb-4">
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索食材..."
          class="search-input"
        />
      </div>
      <p class="text-xs mb-3" style="color: var(--color-text-muted); font-family: var(--font-ui);">共 <strong style="color: var(--color-text);">{{ filtered.length }}</strong> 种食材</p>
    </section>

    <!-- Ingredient List -->
    <div class="card-warm rounded-2xl fade-up" style="position: relative; z-index: 5;">
      <div
        v-for="(item, idx) in filtered"
        :key="item.id"
        class="ingredient-row"
        :class="{ 'border-t': idx > 0 }"
      >
        <!-- View mode -->
        <div v-if="editingId !== item.id" class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="ingredient-name">{{ item.name }}</span>
            <span class="ingredient-unit">{{ item.unit }}</span>
            <span v-if="item.category" class="ingredient-cat" :style="getCategoryColor(item.category_id) ? { background: getCategoryColor(item.category_id) + '1a', color: getCategoryColor(item.category_id) } : {}">{{ item.category }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="ingredient-calorie">
              {{ item.calorie ? `${item.calorie} kcal` : '-' }}
            </span>
            <button class="row-action-edit" @click="startEdit(item)">编辑</button>
            <button class="row-action-delete" @click="confirmDelete(item.id)">删除</button>
          </div>
        </div>

        <!-- Edit mode -->
        <div v-else class="flex gap-2 items-center flex-wrap">
          <input v-model="editForm.name" type="text" class="edit-input flex-1 min-w-[100px]" />
          <input v-model="editForm.unit" type="text" placeholder="单位" class="edit-input w-20" />
          <input v-model="editForm.calorie" type="number" placeholder="kcal" step="0.1" class="edit-input w-20" />
          <!-- Category dropdown for edit -->
          <div class="relative w-20">
            <input
              v-model="editCatSearchText"
              type="text"
              :placeholder="selectedEditCatName || '分类'"
              class="edit-input w-full"
              @focus="editCatDropdownOpen = true"
              @mousedown="toggleEditCatDropdown"
              @blur="closeEditCatDropdown"
            />
            <div v-if="editCatDropdownOpen" class="dropdown-panel">
              <button
                v-for="cat in filteredEditCats"
                :key="cat.id"
                class="dropdown-item"
                :class="{ 'dropdown-selected': cat.id === editForm.category_id }"
                :style="cat.color ? { color: cat.color } : {}"
                @mousedown.prevent="selectEditCat(cat)"
              >
                {{ cat.name }}
              </button>
            </div>
          </div>
          <button class="btn-primary btn-sm" @click="saveEdit(item.id)">保存</button>
          <button class="btn-soft btn-sm" @click="cancelEdit">取消</button>
        </div>
      </div>

      <div v-if="filtered.length === 0" class="empty-state-inline">
        <svg class="mx-auto mb-2" width="48" height="48" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="16" stroke="var(--color-border)" stroke-width="1.5" fill="none" />
          <path d="M18 24h12" stroke="var(--color-border)" stroke-width="1.5" stroke-linecap="round" />
        </svg>
        <p class="text-sm" style="color: var(--color-text-muted); font-family: var(--font-ui);">暂无食材</p>
      </div>
    </div>

    <!-- Delete confirmation -->
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
            <p class="modal-desc">确定要删除这个食材吗？</p>
            <div class="flex gap-3 justify-end">
              <button class="btn-soft" @click="showDeleteConfirm = false">取消</button>
              <button class="btn-danger" @click="doDelete">确认删除</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* ===== Editorial Header ===== */
.admin-hero { padding: 0 0 2rem; }
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
.deco-line { width: 48px; height: 1px; background: var(--color-primary); }
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
.manage-section { margin-bottom: 2rem; position: relative; z-index: 1; }
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
  padding: 0.75rem 1rem 0.75rem 2.75rem;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 0.75rem;
  font-size: 0.875rem;
  color: var(--color-text);
  font-family: var(--font-ui);
  transition: all 0.25s ease;
  outline: none;
}
.search-input::placeholder { color: var(--color-text-muted); opacity: 0.6; }
.search-input:focus {
  box-shadow: 0 0 0 2px rgba(196, 93, 62, 0.15);
  border-color: var(--color-primary);
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
.pill-delete:hover { opacity: 1; color: #b44a3e; }

/* ===== Ingredient Row ===== */
.ingredient-row {
  padding: 0.875rem 1.25rem;
  transition: background 0.15s;
  border-color: var(--color-bg);
}
.ingredient-row:hover {
  background: rgba(245, 240, 232, 0.5);
}
.ingredient-name {
  font-weight: 500;
  font-size: 0.875rem;
  color: var(--color-text);
  font-family: var(--font-body);
}
.ingredient-unit {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  color: var(--color-text-muted);
  background: var(--color-bg);
  font-family: var(--font-ui);
}
.ingredient-cat {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  color: var(--color-secondary);
  background: var(--color-secondary-light);
  font-family: var(--font-ui);
}
.ingredient-calorie {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  font-variant-numeric: tabular-nums;
}
.row-action-edit {
  font-size: 0.75rem;
  color: var(--color-primary);
  background: none;
  border: none;
  cursor: pointer;
  font-family: var(--font-ui);
  transition: opacity 0.2s;
}
.row-action-edit:hover { opacity: 0.7; }
.row-action-delete {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  font-family: var(--font-ui);
  transition: color 0.2s;
}
.row-action-delete:hover { color: #b44a3e; }

/* ===== Edit Input ===== */
.edit-input {
  padding: 0.375rem 0.625rem;
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-family: var(--font-ui);
  color: var(--color-text);
  border: 1px solid var(--color-primary);
  outline: none;
  background: var(--color-card);
  transition: box-shadow 0.2s;
}
.edit-input:focus {
  box-shadow: 0 0 0 2px rgba(196, 93, 62, 0.15);
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
  max-height: 9rem;
  overflow-y: auto;
  min-width: 100px;
}
.dropdown-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 0.375rem 0.75rem;
  font-size: 0.8125rem;
  color: var(--color-text);
  font-family: var(--font-ui);
  background: none;
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.dropdown-item:hover { background: var(--color-bg); }
.dropdown-selected {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.dropdown-empty {
  padding: 0.75rem;
  text-align: center;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}

/* ===== Empty ===== */
.empty-state-inline {
  text-align: center;
  padding: 3rem 0;
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
}
.modal-deco { width: 40px; height: 2px; background: var(--color-primary); margin-bottom: 1.25rem; }
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
</style>
