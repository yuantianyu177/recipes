<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useRecipeStore } from '../../stores/recipe'
import { apiUploadImage, apiReorderImages, apiCreateRecipe } from '../../api/index'
import MarkdownEditor from '../../components/MarkdownEditor.vue'

const route = useRoute()
const router = useRouter()
const store = useRecipeStore()
const message = useMessage()

const isEdit = computed(() => !!route.params.id)
const submitting = ref(false)

// Fuzzy match helper
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

const form = ref({
  name: '',
  description: '',
  steps: '',
  tips: '',
  images: [],
  ingredients: [],
  tags: [],
})

// Load recipe for editing
onMounted(async () => {
  await store.fetchAll()
  if (isEdit.value) {
    const recipe = await store.fetchRecipeById(route.params.id)
    if (recipe) {
      form.value = {
        name: recipe.name,
        description: recipe.description || '',
        steps: recipe.steps || '',
        tips: recipe.tips || '',
        images: (recipe.images || []).map((img, i) => {
          const url = typeof img === 'string' ? img : img.image_path
          return { url, file: null, id: img.id || null, _key: Date.now() + i }
        }),
        ingredients: (recipe.ingredients || []).map((i) => ({
          id: i.ingredient_id || i.id,
          name: i.ingredient_name || i.name || '',
          amount: i.amount || '',
          unit: i.ingredient_unit || i.unit || '',
          calorie: i.ingredient_calorie ?? i.calorie ?? 0,
        })),
        tags: recipe.tags.map((t) => t.name),
      }
      // Initialize ingredient search text from loaded data
      form.value.ingredients.forEach((item, idx) => {
        ingredientSearch.value[idx] = item.name
      })
    }
  }
})

// ===========================================
// Tag selector with dropdown + search
// ===========================================
const tagDropdownOpen = ref(false)
const tagSearch = ref('')

const filteredAvailableTags = computed(() => {
  let available = store.tags.filter((t) => !form.value.tags.includes(t.name))
  if (tagSearch.value) {
    const kw = tagSearch.value.toLowerCase()
    available = available.filter((t) => fuzzyMatch(t.name, kw))
  }
  return available
})

const filteredTagsByCategory = computed(() => {
  const grouped = {}
  for (const tag of filteredAvailableTags.value) {
    const cat = tag.category || '未分类'
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push(tag)
  }
  return grouped
})

function selectTag(tagName) {
  if (!form.value.tags.includes(tagName)) {
    form.value.tags.push(tagName)
  }
  tagSearch.value = ''
}

function removeSelectedTag(name) {
  form.value.tags = form.value.tags.filter((t) => t !== name)
}

function toggleTagDropdown(e) {
  if (document.activeElement === e.target) {
    tagDropdownOpen.value = !tagDropdownOpen.value
  }
}

function closeTagDropdown() {
  setTimeout(() => { tagDropdownOpen.value = false }, 200)
}

function getTagColor(tagName) {
  const tag = store.tags.find((t) => t.name === tagName)
  return tag?.color || null
}

function getCategoryColor(categoryName) {
  const cat = store.tagCategories.find((c) => c.name === categoryName)
  return cat?.color || null
}

// ===========================================
// Ingredient searchable dropdown
// ===========================================
const ingredientDropdownIdx = ref(-1)
const ingredientSearch = ref({})

function getIngredientFilteredList(idx) {
  const kw = (ingredientSearch.value[idx] || '').toLowerCase()
  if (!kw) return store.ingredients
  return store.ingredients.filter((i) => fuzzyMatch(i.name, kw))
}

function toggleIngredientDropdown(e, idx) {
  if (document.activeElement === e.target) {
    if (ingredientDropdownIdx.value === idx) {
      ingredientDropdownIdx.value = -1
    } else {
      openIngredientDropdown(idx)
    }
  }
}

function openIngredientDropdown(idx) {
  ingredientDropdownIdx.value = idx
  // Don't overwrite search text - preserve current input
  if (ingredientSearch.value[idx] === undefined) {
    ingredientSearch.value[idx] = form.value.ingredients[idx].name || ''
  }
}

function closeIngredientDropdown() {
  setTimeout(() => { ingredientDropdownIdx.value = -1 }, 200)
}

function selectIngredient(idx, ing) {
  form.value.ingredients[idx].name = ing.name
  form.value.ingredients[idx].unit = ing.unit
  form.value.ingredients[idx].calorie = ing.calorie || 0
  form.value.ingredients[idx].id = ing.id
  ingredientSearch.value[idx] = ing.name
  ingredientDropdownIdx.value = -1
}

function onIngredientSearchInput(idx) {
  // Keep dropdown open while typing
  ingredientDropdownIdx.value = idx
  form.value.ingredients[idx].name = ingredientSearch.value[idx] || ''
  // Auto-fill if exact match
  const found = store.ingredients.find((i) => i.name === form.value.ingredients[idx].name)
  if (found) {
    form.value.ingredients[idx].unit = found.unit
    form.value.ingredients[idx].calorie = found.calorie || 0
    form.value.ingredients[idx].id = found.id
  }
}

// ===========================================
// Calories
// ===========================================
const totalCalories = computed(() => {
  let total = 0
  for (const item of form.value.ingredients) {
    const num = parseFloat(item.amount)
    if (!isNaN(num) && item.calorie) total += num * item.calorie
  }
  return Math.round(total)
})

// ===========================================
// Ingredients list management
// ===========================================
function addIngredient() {
  form.value.ingredients.push({ id: 0, name: '', amount: '', unit: '', calorie: 0 })
}

function removeIngredient(idx) {
  form.value.ingredients.splice(idx, 1)
  delete ingredientSearch.value[idx]
}

// ===========================================
// Image upload (upload immediately to server)
// ===========================================
const uploadingImages = ref(new Set())

async function uploadImageImmediately(file) {
  try {
    let recipeId = route.params.id
    if (!recipeId) {
      const draft = await apiCreateRecipe({ name: '草稿-' + Date.now() })
      recipeId = draft.id
      window._draftRecipeId = recipeId
    }
    const uploaded = await apiUploadImage(recipeId, file)
    return {
      url: uploaded.image_path,
      file: null,
      id: uploaded.id,
      _key: Date.now() + Math.random()
    }
  } catch (err) {
    throw err
  }
}

async function triggerFileSelect() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*,.heic,.heif,.avif'
  input.multiple = true
  input.onchange = async (e) => {
    for (const file of e.target.files) {
      const uploadKey = file.name + Date.now()
      uploadingImages.value.add(uploadKey)
      try {
        const imgData = await uploadImageImmediately(file)
        form.value.images.push(imgData)
      } catch (err) {
        message.error('图片上传失败: ' + (err.message || ''))
      } finally {
        uploadingImages.value.delete(uploadKey)
      }
    }
  }
  input.click()
}

function removeImage(idx) {
  form.value.images.splice(idx, 1)
}

function moveImage(idx, dir) {
  const newIdx = idx + dir
  if (newIdx < 0 || newIdx >= form.value.images.length) return
  const arr = form.value.images
  const [item] = arr.splice(idx, 1)
  arr.splice(newIdx, 0, item)
}

// ===========================================
// Submit
// ===========================================
async function handleSubmit() {
  if (!form.value.name.trim()) {
    message.error('请输入菜谱名称')
    return
  }
  if (uploadingImages.value.size > 0) {
    message.warning('请等待图片上传完成')
    return
  }
  submitting.value = true

  try {
    // Build tag_ids from tag names
    const tagIds = form.value.tags
      .map((name) => store.tags.find((t) => t.name === name))
      .filter(Boolean)
      .map((t) => t.id)

    // Build ingredients array (no category_id - it's on the ingredient itself)
    const ingredientsList = form.value.ingredients
      .filter((i) => i.name)
      .map((i) => {
        const found = store.ingredients.find((si) => si.name === i.name)
        return {
          ingredient_id: found ? found.id : i.id,
          amount: i.amount || '',
        }
      })
      .filter((i) => i.ingredient_id)

    const recipeData = {
      name: form.value.name,
      description: form.value.description,
      steps: form.value.steps,
      tips: form.value.tips,
      tag_ids: tagIds,
      ingredients: ingredientsList,
    }

    let recipeId
    if (isEdit.value) {
      await store.updateRecipe(route.params.id, recipeData)
      recipeId = Number(route.params.id)
    } else if (window._draftRecipeId) {
      // Update the draft recipe
      await store.updateRecipe(window._draftRecipeId, recipeData)
      recipeId = window._draftRecipeId
      delete window._draftRecipeId
    } else {
      recipeId = await store.addRecipe(recipeData)
    }

    // All images already uploaded, just reorder them
    const finalImageIds = form.value.images
      .map((img) => img.id)
      .filter(Boolean)

    if (finalImageIds.length > 0) {
      try {
        await apiReorderImages(recipeId, finalImageIds)
      } catch (err) {
        message.warning('图片排序更新失败: ' + (err.message || ''))
      }
    }

    message.success(isEdit.value ? '菜谱已更新' : '菜谱已创建')
    router.push('/admin')
  } catch (err) {
    message.error(err.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

</script>

<template>
  <div class="admin-recipe-edit max-w-3xl mx-auto">
    <!-- Editorial Header -->
    <section class="admin-hero">
      <button class="back-btn" @click="router.back()">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回
      </button>
      <p class="admin-subtitle">{{ isEdit ? 'Edit Recipe' : 'New Recipe' }}</p>
      <div class="deco-line mb-4"></div>
      <h1 class="admin-title">{{ isEdit ? '编辑菜谱' : '新建菜谱' }}</h1>
    </section>

    <!-- Form -->
    <div class="form-sections">
      <!-- Name -->
      <section class="form-section">
        <div class="section-label">
          <span>基本信息</span>
          <span class="w-8 h-px" style="background: var(--color-primary);"></span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <label class="field-label">
            菜谱名称 <span style="color: #b44a3e;">*</span>
          </label>
          <input
            v-model="form.name"
            type="text"
            placeholder="例如：西红柿炒鸡蛋"
            class="input-warm w-full px-4 py-2.5 rounded-xl outline-none transition-all text-sm"
          />
        </div>
      </section>

      <!-- Cover Images -->
      <section class="form-section">
        <div class="section-label">
          <span>封面图片</span>
          <span v-if="uploadingImages.size > 0" class="ml-2 text-xs" style="color: var(--color-accent);">(上传中...)</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <div class="flex flex-wrap gap-3 mb-3">
            <div
              v-for="(img, idx) in form.images"
              :key="img._key || img.id || idx"
              class="image-thumb group"
            >
              <img :src="img.url" class="w-full h-full object-cover" />
              <div class="image-overlay">
                <button v-if="idx > 0" class="img-action-btn" @click="moveImage(idx, -1)">←</button>
                <button class="img-action-btn img-action-delete" @click="removeImage(idx)">✕</button>
                <button v-if="idx < form.images.length - 1" class="img-action-btn" @click="moveImage(idx, 1)">→</button>
              </div>
              <div class="image-index">{{ idx + 1 }}</div>
            </div>
            <button class="image-add" @click="triggerFileSelect">
              <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4v16m8-8H4" />
              </svg>
              <span class="text-xs" style="font-family: var(--font-ui);">添加图片</span>
            </button>
          </div>
          <p class="text-xs" style="color: var(--color-text-muted); font-family: var(--font-ui);">支持 JPG、PNG、HEIC、AVIF 等格式，可上传多张。</p>
        </div>
      </section>

      <!-- Description -->
      <section class="form-section">
        <div class="section-label">
          <span>菜谱简介</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <textarea
            v-model="form.description"
            placeholder="写一段简介..."
            rows="3"
            class="input-warm w-full px-4 py-2.5 rounded-xl outline-none transition-all text-sm resize-none"
          />
        </div>
      </section>

      <!-- Steps -->
      <section class="form-section">
        <div class="section-label">
          <span>烹饪步骤</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <MarkdownEditor v-model="form.steps" placeholder="支持 Markdown 语法，可插入图片..." />
        </div>
      </section>

      <!-- Tips -->
      <section class="form-section">
        <div class="section-label">
          <span>小贴士</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <textarea
            v-model="form.tips"
            placeholder="一些烹饪小技巧..."
            rows="2"
            class="input-warm w-full px-4 py-2.5 rounded-xl outline-none transition-all text-sm resize-none"
          />
        </div>
      </section>

      <!-- Ingredients -->
      <section class="form-section">
        <div class="section-label">
          <span>食材清单</span>
          <span class="ml-auto text-xs" style="color: var(--color-text-muted); font-family: var(--font-ui); letter-spacing: 0;">
            估算总热量：<span class="font-semibold" style="color: var(--color-primary);">{{ totalCalories }} kcal</span>
          </span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <div class="space-y-3">
            <div
              v-for="(item, idx) in form.ingredients"
              :key="idx"
              class="ingredient-row"
            >
              <!-- Name with searchable dropdown -->
              <div class="relative flex-1 min-w-[140px]">
                <input
                  v-model="ingredientSearch[idx]"
                  type="text"
                  placeholder="搜索食材..."
                  class="input-warm w-full px-3 py-2 rounded-lg outline-none text-sm"
                  @focus="openIngredientDropdown(idx)"
                  @mousedown="toggleIngredientDropdown($event, idx)"
                  @blur="closeIngredientDropdown"
                  @input="onIngredientSearchInput(idx)"
                />
                <svg
                  class="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none"
                  style="color: var(--color-text-muted);"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
                <div
                  v-if="ingredientDropdownIdx === idx"
                  class="dropdown-panel"
                >
                  <button
                    v-for="ing in getIngredientFilteredList(idx)"
                    :key="ing.id"
                    class="dropdown-item"
                    :class="{ 'dropdown-selected': ing.name === item.name }"
                    @mousedown.prevent="selectIngredient(idx, ing)"
                  >
                    {{ ing.name }}
                    <span class="text-xs ml-1" style="color: var(--color-text-muted);">({{ ing.unit }}<template v-if="ing.category"> · {{ ing.category }}</template>)</span>
                  </button>
                  <div v-if="getIngredientFilteredList(idx).length === 0" class="dropdown-empty">
                    无匹配食材
                  </div>
                </div>
              </div>

              <!-- Amount -->
              <input
                v-model="item.amount"
                type="text"
                placeholder="用量"
                class="input-warm w-20 px-3 py-2 rounded-lg outline-none text-sm"
              />

              <!-- Unit -->
              <span class="text-xs w-12 text-center" style="color: var(--color-text-muted); font-family: var(--font-ui);">{{ item.unit || '单位' }}</span>

              <!-- Remove -->
              <button class="remove-ingredient" @click="removeIngredient(idx)">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <button class="add-ingredient-btn" @click="addIngredient">
            + 添加食材
          </button>
        </div>
      </section>

      <!-- Tags -->
      <section class="form-section">
        <div class="section-label">
          <span>标签</span>
        </div>
        <div class="card-warm rounded-2xl p-6">
          <!-- Selected tags -->
          <div class="flex flex-wrap gap-2 mb-3 min-h-[2.5rem] items-center">
            <template v-if="form.tags.length">
              <span
                v-for="tag in form.tags"
                :key="tag"
                class="selected-tag"
                :style="getTagColor(tag) ? { background: getTagColor(tag) + '1a', color: getTagColor(tag) } : {}"
              >
                <span>{{ tag }}</span>
                <button class="tag-remove" @click="removeSelectedTag(tag)">×</button>
              </span>
            </template>
            <span v-else class="text-xs" style="color: var(--color-text-muted); font-family: var(--font-ui);">尚未选择标签</span>
          </div>

          <!-- Dropdown trigger -->
          <div class="relative">
            <input
              v-model="tagSearch"
              type="text"
              placeholder="点击选择标签，或输入搜索..."
              class="input-warm w-full px-4 py-2.5 rounded-xl outline-none transition-all text-sm"
              @focus="tagDropdownOpen = true"
              @mousedown="toggleTagDropdown"
              @blur="closeTagDropdown"
            />
            <svg
              class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none transition-transform"
              :class="{ 'rotate-180': tagDropdownOpen }"
              style="color: var(--color-text-muted);"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>

            <div
              v-if="tagDropdownOpen"
              class="dropdown-panel tag-dropdown"
            >
              <template v-if="Object.keys(filteredTagsByCategory).length > 0">
                <div v-for="(catTags, category) in filteredTagsByCategory" :key="category">
                  <div class="dropdown-category-header" :style="getCategoryColor(category) ? { color: getCategoryColor(category) } : {}">
                    {{ category }}
                  </div>
                  <button
                    v-for="tag in catTags"
                    :key="tag.id"
                    class="dropdown-item"
                    :style="tag.color ? { color: tag.color } : {}"
                    @mousedown.prevent="selectTag(tag.name)"
                  >
                    {{ tag.name }}
                  </button>
                </div>
              </template>
              <div v-else class="dropdown-empty py-6">
                没有更多可选标签
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Submit -->
      <div class="flex gap-3 pt-2 pb-12">
        <button
          :disabled="submitting"
          class="btn-primary flex-1 py-3 rounded-xl font-medium text-sm transition-all disabled:opacity-60"
          style="font-family: var(--font-ui);"
          @click="handleSubmit"
        >
          {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '创建菜谱') }}
        </button>
        <button
          class="btn-soft px-8 py-3 rounded-xl text-sm transition-colors"
          style="font-family: var(--font-ui);"
          @click="router.back()"
        >
          取消
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ===== Editorial Header ===== */
.admin-hero { padding: 0 0 1.5rem; }
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
}

/* ===== Form Sections ===== */
.form-sections {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}
.form-section {}
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
.field-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
  font-family: var(--font-ui);
  margin-bottom: 0.5rem;
}

/* ===== Image Thumbnails ===== */
.image-thumb {
  position: relative;
  width: 7rem;
  height: 7rem;
  border-radius: 0.75rem;
  overflow: hidden;
  border: 1px solid var(--color-border);
}
.image-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.5);
  opacity: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  transition: opacity 0.2s ease;
}
.image-thumb:hover .image-overlay { opacity: 1; }
.img-action-btn {
  width: 1.75rem;
  height: 1.75rem;
  border-radius: 50%;
  background: rgba(255,255,255,0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: var(--color-text);
  border: none;
  cursor: pointer;
  transition: background 0.15s;
}
.img-action-btn:hover { background: #fff; }
.img-action-delete {
  background: #b44a3e;
  color: #fff;
}
.img-action-delete:hover { background: #9a3e33; }
.image-index {
  position: absolute;
  top: 0.25rem;
  left: 0.25rem;
  background: rgba(0,0,0,0.5);
  color: #fff;
  font-size: 0.625rem;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.image-add {
  width: 7rem;
  height: 7rem;
  border-radius: 0.75rem;
  border: 2px dashed var(--color-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  color: var(--color-text-muted);
  background: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
.image-add:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* ===== Ingredient Row ===== */
.ingredient-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
  border-radius: 0.75rem;
  padding: 0.625rem 0.75rem;
  background: var(--color-bg);
  transition: background 0.15s;
}
.remove-ingredient {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}
.remove-ingredient:hover {
  color: #b44a3e;
  background: #fdf2f0;
}
.add-ingredient-btn {
  margin-top: 0.75rem;
  width: 100%;
  padding: 0.625rem;
  border-radius: 0.75rem;
  border: 2px dashed var(--color-border);
  font-size: 0.875rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  background: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
.add-ingredient-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* ===== Selected Tag ===== */
.selected-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  padding: 0.375rem 0.75rem;
  border-radius: 999px;
  font-weight: 500;
  font-family: var(--font-ui);
  background: var(--color-primary-light);
  color: var(--color-primary);
  line-height: 1;
}
.tag-remove {
  margin-left: 0.125rem;
  flex-shrink: 0;
  color: inherit;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.875rem;
  transition: color 0.2s;
}
.tag-remove:hover { color: #b44a3e; }

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
  z-index: 20;
  max-height: 12rem;
  overflow-y: auto;
}
.tag-dropdown {
  z-index: 30;
  max-height: min(14rem, 50vh);
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
.dropdown-item:hover { background: var(--color-bg); }
.dropdown-selected {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.dropdown-category-header {
  padding: 0.375rem 0.75rem;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  background: var(--color-bg);
  font-family: var(--font-ui);
  position: sticky;
  top: 0;
  z-index: 10;
}
.dropdown-empty {
  padding: 1rem;
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}
</style>
