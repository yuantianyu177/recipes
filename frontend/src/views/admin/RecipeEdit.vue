<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useRecipeStore } from '../../stores/recipe'
import { apiUploadImage, apiReorderImages } from '../../api/index'
import TipTapEditor from '../../components/TipTapEditor.vue'

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

function closeTagDropdown() {
  setTimeout(() => { tagDropdownOpen.value = false }, 200)
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
// Image upload (local files)
// ===========================================
function triggerFileSelect() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.multiple = true
  input.onchange = (e) => {
    for (const file of e.target.files) {
      const url = URL.createObjectURL(file)
      form.value.images.push({ url, file, _key: Date.now() + Math.random() })
    }
  }
  input.click()
}

function removeImage(idx) {
  const img = form.value.images[idx]
  if (img.file) URL.revokeObjectURL(img.url)
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
    } else {
      recipeId = await store.addRecipe(recipeData)
    }

    // Upload new images and collect their IDs in order
    // Build final ordered image ID list preserving user's arrangement
    const finalImageIds = []
    for (const img of form.value.images) {
      if (img.file) {
        // New image: upload and collect returned ID
        try {
          const uploaded = await apiUploadImage(recipeId, img.file)
          finalImageIds.push(uploaded.id)
        } catch (err) {
          message.warning('部分图片上传失败: ' + (err.message || ''))
        }
      } else if (img.id) {
        // Existing image: keep its ID in order
        finalImageIds.push(img.id)
      }
    }

    // Reorder and clean up deleted images on backend
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
  <div class="max-w-3xl mx-auto">
    <!-- Header -->
    <div class="mb-8">
      <button
        class="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-xl transition-colors mb-3"
        @click="router.back()"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        返回
      </button>
      <h1 class="text-2xl font-extrabold text-gray-800">
        {{ isEdit ? '编辑菜谱' : '新建菜谱' }}
      </h1>
    </div>

    <!-- Form -->
    <div class="space-y-6">
      <!-- Name -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100">
        <label class="block text-sm font-semibold text-gray-700 mb-2">
          菜谱名称 <span class="text-red-400">*</span>
        </label>
        <input
          v-model="form.name"
          type="text"
          placeholder="例如：西红柿炒鸡蛋"
          class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-orange-300 focus:ring-2 focus:ring-orange-100 outline-none transition-all text-sm"
        />
      </div>

      <!-- Cover Images -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100">
        <label class="block text-sm font-semibold text-gray-700 mb-3">封面图片</label>
        <div class="flex flex-wrap gap-3 mb-3">
          <div
            v-for="(img, idx) in form.images"
            :key="img._key || img.id || idx"
            class="relative group w-28 h-28 rounded-xl overflow-hidden border border-gray-200"
          >
            <img :src="img.url" class="w-full h-full object-cover" />
            <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-1">
              <button
                v-if="idx > 0"
                class="w-7 h-7 rounded-full bg-white/90 flex items-center justify-center text-xs text-gray-600 hover:bg-white"
                @click="moveImage(idx, -1)"
              >←</button>
              <button
                class="w-7 h-7 rounded-full bg-red-500 flex items-center justify-center text-xs text-white hover:bg-red-600"
                @click="removeImage(idx)"
              >✕</button>
              <button
                v-if="idx < form.images.length - 1"
                class="w-7 h-7 rounded-full bg-white/90 flex items-center justify-center text-xs text-gray-600 hover:bg-white"
                @click="moveImage(idx, 1)"
              >→</button>
            </div>
            <div class="absolute top-1 left-1 bg-black/50 text-white text-[10px] w-5 h-5 rounded-full flex items-center justify-center">
              {{ idx + 1 }}
            </div>
          </div>
          <button
            class="w-28 h-28 rounded-xl border-2 border-dashed border-gray-300 hover:border-orange-400 flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-orange-500 transition-colors"
            @click="triggerFileSelect"
          >
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4v16m8-8H4" />
            </svg>
            <span class="text-xs">添加图片</span>
          </button>
        </div>
        <p class="text-xs text-gray-400">支持 JPG、PNG 格式，可上传多张。保存后将自动上传至服务器。</p>
      </div>

      <!-- Description -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100">
        <label class="block text-sm font-semibold text-gray-700 mb-2">菜谱简介</label>
        <TipTapEditor v-model="form.description" placeholder="写一段简介..." />
      </div>

      <!-- Steps -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100">
        <label class="block text-sm font-semibold text-gray-700 mb-2">烹饪步骤</label>
        <TipTapEditor v-model="form.steps" placeholder="详细描述烹饪步骤..." />
      </div>

      <!-- Tips -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100">
        <label class="block text-sm font-semibold text-gray-700 mb-2">小贴士</label>
        <textarea
          v-model="form.tips"
          placeholder="一些烹饪小技巧..."
          rows="2"
          class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-orange-300 focus:ring-2 focus:ring-orange-100 outline-none transition-all text-sm resize-none"
        />
      </div>

      <!-- Ingredients (no category selector - category is on the ingredient itself) -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <label class="text-sm font-semibold text-gray-700">食材清单</label>
          <span class="text-xs text-gray-400">
            估算总热量：<span class="font-semibold text-orange-500">{{ totalCalories }} kcal</span>
          </span>
        </div>

        <div class="space-y-3">
          <div
            v-for="(item, idx) in form.ingredients"
            :key="idx"
            class="flex gap-2 items-center flex-wrap bg-gray-50 rounded-xl p-3"
          >
            <!-- Name with searchable dropdown -->
            <div class="relative flex-1 min-w-[140px]">
              <input
                v-model="ingredientSearch[idx]"
                type="text"
                placeholder="搜索食材..."
                class="w-full px-3 py-2 rounded-lg border border-gray-200 focus:border-orange-300 outline-none text-sm"
                @focus="openIngredientDropdown(idx)"
                @blur="closeIngredientDropdown"
                @input="onIngredientSearchInput(idx)"
              />
              <svg
                class="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
              <div
                v-if="ingredientDropdownIdx === idx"
                class="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-xl z-20 max-h-48 overflow-y-auto"
              >
                <button
                  v-for="ing in getIngredientFilteredList(idx)"
                  :key="ing.id"
                  class="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-orange-50 hover:text-orange-600 transition-colors"
                  :class="{ 'bg-orange-50 text-orange-600': ing.name === item.name }"
                  @mousedown.prevent="selectIngredient(idx, ing)"
                >
                  {{ ing.name }}
                  <span class="text-gray-400 text-xs ml-1">({{ ing.unit }}<template v-if="ing.category"> · {{ ing.category }}</template>)</span>
                </button>
                <div v-if="getIngredientFilteredList(idx).length === 0" class="px-3 py-3 text-center text-sm text-gray-400">
                  无匹配食材
                </div>
              </div>
            </div>

            <!-- Amount -->
            <input
              v-model="item.amount"
              type="text"
              placeholder="用量"
              class="w-20 px-3 py-2 rounded-lg border border-gray-200 focus:border-orange-300 outline-none text-sm"
            />

            <!-- Unit (auto from ingredient) -->
            <span class="text-xs text-gray-400 w-12 text-center">{{ item.unit || '单位' }}</span>

            <!-- Remove -->
            <button
              class="w-8 h-8 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 flex items-center justify-center transition-colors"
              @click="removeIngredient(idx)"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <button
          class="mt-3 w-full py-2.5 rounded-xl border-2 border-dashed border-gray-300 hover:border-orange-400 text-sm text-gray-400 hover:text-orange-500 transition-colors"
          @click="addIngredient"
        >
          + 添加食材
        </button>
      </div>

      <!-- Tags (searchable dropdown with overflow fix) -->
      <div class="bg-white rounded-2xl p-6 border border-gray-100">
        <label class="block text-sm font-semibold text-gray-700 mb-3">标签</label>

        <!-- Selected tags -->
        <div class="flex flex-wrap gap-2 mb-3" v-if="form.tags.length">
          <span
            v-for="tag in form.tags"
            :key="tag"
            class="inline-flex items-center justify-center gap-1 text-xs px-3 py-1.5 rounded-full bg-orange-50 text-orange-600 font-medium leading-none"
          >
            <span>{{ tag }}</span>
            <button class="hover:text-red-500 ml-0.5 flex-shrink-0" @click="removeSelectedTag(tag)">×</button>
          </span>
        </div>

        <!-- Dropdown trigger -->
        <div class="relative">
          <input
            v-model="tagSearch"
            type="text"
            placeholder="点击选择标签，或输入搜索..."
            class="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:border-orange-300 focus:ring-2 focus:ring-orange-100 outline-none transition-all text-sm"
            @focus="tagDropdownOpen = true"
            @blur="closeTagDropdown"
          />
          <svg
            class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none transition-transform"
            :class="{ 'rotate-180': tagDropdownOpen }"
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>

          <!-- Dropdown panel - use fixed max-height and ensure it doesn't overflow viewport -->
          <div
            v-if="tagDropdownOpen"
            class="absolute left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-xl z-30 max-h-56 overflow-y-auto"
            :class="{ 'bottom-full mb-1': false }"
            style="max-height: min(14rem, 50vh);"
          >
            <template v-if="Object.keys(filteredTagsByCategory).length > 0">
              <div v-for="(catTags, category) in filteredTagsByCategory" :key="category">
                <div class="px-3 py-1.5 text-[10px] font-semibold text-gray-400 uppercase tracking-wider bg-gray-50 sticky top-0 z-10">
                  {{ category }}
                </div>
                <button
                  v-for="tag in catTags"
                  :key="tag.id"
                  class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-orange-50 hover:text-orange-600 transition-colors"
                  @mousedown.prevent="selectTag(tag.name)"
                >
                  {{ tag.name }}
                </button>
              </div>
            </template>
            <div v-else class="px-4 py-6 text-center text-sm text-gray-400">
              没有更多可选标签
            </div>
          </div>
        </div>
      </div>

      <!-- Submit -->
      <div class="flex gap-3 pt-2 pb-12">
        <button
          :disabled="submitting"
          class="flex-1 py-3 rounded-xl bg-gradient-to-r from-orange-400 to-red-500 text-white font-medium text-sm hover:shadow-lg hover:shadow-orange-200 transition-all disabled:opacity-60"
          @click="handleSubmit"
        >
          {{ submitting ? '保存中...' : (isEdit ? '保存修改' : '创建菜谱') }}
        </button>
        <button
          class="px-8 py-3 rounded-xl bg-gray-100 text-gray-600 text-sm hover:bg-gray-200 transition-colors"
          @click="router.back()"
        >
          取消
        </button>
      </div>
    </div>
  </div>
</template>
