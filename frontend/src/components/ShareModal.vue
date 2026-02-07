<script setup>
import { ref, nextTick, watch, computed } from 'vue'
import { toPng } from 'html-to-image'
import { useRecipeStore } from '../stores/recipe'

const props = defineProps({
  recipe: { type: Object, default: null },
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])
const store = useRecipeStore()

const cardRef = ref(null)
const imageUrl = ref('')
const generating = ref(false)
const fullRecipe = ref(null)

// Get cover image from recipe
function getCoverImage(recipe) {
  if (recipe.images && recipe.images.length > 0) {
    const img = recipe.images[0]
    return typeof img === 'string' ? img : img.image_path
  }
  return ''
}

// Group ingredients by category
function getIngredientGroups(recipe) {
  if (!recipe.ingredients || !recipe.ingredients.length) return {}
  const groups = {}
  for (const item of recipe.ingredients) {
    const cat = item.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({
      name: item.ingredient_name || item.name || '',
      amount: item.amount || '',
      unit: item.ingredient_unit || item.unit || '',
    })
  }
  return groups
}

// Strip HTML tags to plain text for rendering
function stripHtml(html) {
  if (!html) return ''
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

watch(() => props.show, async (val) => {
  if (val && props.recipe) {
    imageUrl.value = ''
    generating.value = true
    fullRecipe.value = null

    // Always fetch full recipe data (card only has summary)
    try {
      const full = await store.fetchRecipeById(props.recipe.id)
      fullRecipe.value = full
    } catch {
      fullRecipe.value = props.recipe
    }

    await nextTick()
    // Wait for DOM rendering and image loading
    await new Promise((r) => setTimeout(r, 600))
    try {
      const dataUrl = await toPng(cardRef.value, {
        pixelRatio: 2,
        backgroundColor: '#ffffff',
      })
      imageUrl.value = dataUrl
    } catch {
      imageUrl.value = ''
    } finally {
      generating.value = false
    }
  }
})

function downloadImage() {
  if (!imageUrl.value) return
  const a = document.createElement('a')
  a.href = imageUrl.value
  a.download = `${props.recipe?.name || 'recipe'}.png`
  a.click()
}

function close() {
  imageUrl.value = ''
  fullRecipe.value = null
  emit('close')
}

const r = computed(() => fullRecipe.value)
const ingredientGroups = computed(() => r.value ? getIngredientGroups(r.value) : {})
const categoryOrder = ['主料', '辅料', '调料']
const sortedCategories = computed(() => {
  const keys = Object.keys(ingredientGroups.value)
  return categoryOrder.filter((c) => keys.includes(c)).concat(keys.filter((c) => !categoryOrder.includes(c)))
})
const stepsText = computed(() => r.value ? stripHtml(r.value.steps) : '')
const descText = computed(() => r.value ? stripHtml(r.value.description) : '')
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      @click.self="close"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 max-h-[90vh] flex flex-col overflow-hidden">
        <!-- Modal header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h3 class="text-lg font-bold text-gray-800">分享菜谱</h3>
          <button class="text-gray-400 hover:text-gray-600 transition-colors" @click="close">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Preview area -->
        <div class="flex-1 overflow-y-auto p-5">
          <div v-if="generating" class="flex flex-col items-center justify-center py-12">
            <div class="w-8 h-8 border-4 border-green-200 border-t-green-500 rounded-full animate-spin mb-3"></div>
            <span class="text-sm text-gray-400">正在生成图片...</span>
          </div>

          <div v-else-if="imageUrl" class="flex flex-col items-center">
            <img :src="imageUrl" alt="preview" class="w-full rounded-xl shadow-lg border border-gray-100" />
          </div>

          <div v-else class="text-center text-sm text-gray-400 py-12">
            生成失败，请重试
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 justify-end px-5 py-4 border-t border-gray-100">
          <button
            class="px-4 py-2 rounded-xl text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 transition-colors"
            @click="close"
          >
            关闭
          </button>
          <button
            v-if="imageUrl"
            class="px-5 py-2 rounded-xl text-sm text-white bg-gradient-to-r from-green-500 to-emerald-500 hover:shadow-lg hover:shadow-green-200 transition-all font-medium"
            @click="downloadImage"
          >
            保存图片
          </button>
        </div>
      </div>

      <!-- Hidden render card -->
      <div style="position: fixed; left: -9999px; top: 0; width: 420px; z-index: -1;">
        <div ref="cardRef" v-if="r" style="width: 420px; padding: 24px; background: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #374151;">

          <!-- Header with gradient -->
          <div style="background: linear-gradient(135deg, #f97316, #ef4444); border-radius: 16px; padding: 24px; margin-bottom: 20px; color: white;">
            <div style="font-size: 12px; opacity: 0.85; margin-bottom: 8px;">🍳 我的菜谱</div>
            <div style="font-size: 26px; font-weight: 800; line-height: 1.3;">{{ r.name }}</div>
          </div>

          <!-- Cover image -->
          <div v-if="getCoverImage(r)" style="border-radius: 14px; overflow: hidden; margin-bottom: 20px;">
            <img :src="getCoverImage(r)" crossorigin="anonymous" style="width: 100%; height: 240px; object-fit: cover; display: block;" />
          </div>

          <!-- Tags -->
          <div v-if="r.tags && r.tags.length" style="margin-bottom: 20px;">
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              <span
                v-for="tag in r.tags"
                :key="tag.id"
                style="display: inline-flex; align-items: center; justify-content: center; font-size: 12px; padding: 6px 14px; border-radius: 999px; background: #fff7ed; color: #ea580c; font-weight: 500; line-height: 1;"
              >{{ tag.name }}</span>
            </div>
          </div>

          <!-- Description -->
          <div v-if="descText" style="background: #f9fafb; border-radius: 14px; padding: 16px; margin-bottom: 20px; font-size: 13px; line-height: 1.7; color: #6b7280;">
            {{ descText }}
          </div>

          <!-- Ingredients by category -->
          <div v-if="sortedCategories.length" style="margin-bottom: 20px;">
            <div style="font-size: 16px; font-weight: 700; color: #374151; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
              <span style="display: inline-flex; width: 28px; height: 28px; border-radius: 8px; background: #f0fdf4; align-items: center; justify-content: center; font-size: 16px;">🥬</span>
              食材清单
            </div>
            <div v-for="cat in sortedCategories" :key="cat" style="background: #f9fafb; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;">
              <div style="font-size: 12px; font-weight: 600; color: #9ca3af; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;">{{ cat }}</div>
              <div v-for="(item, i) in ingredientGroups[cat]" :key="i" style="display: flex; justify-content: space-between; font-size: 13px; padding: 5px 0; color: #4b5563; border-bottom: 1px solid #f3f4f6;">
                <span>{{ item.name }}</span>
                <span style="color: #9ca3af;">{{ item.amount }}{{ item.unit }}</span>
              </div>
            </div>
          </div>

          <!-- Steps -->
          <div v-if="stepsText" style="margin-bottom: 20px;">
            <div style="font-size: 16px; font-weight: 700; color: #374151; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
              <span style="display: inline-flex; width: 28px; height: 28px; border-radius: 8px; background: #eff6ff; align-items: center; justify-content: center; font-size: 16px;">📝</span>
              烹饪步骤
            </div>
            <div style="background: #f9fafb; border-radius: 14px; padding: 16px; font-size: 13px; line-height: 1.8; color: #4b5563; white-space: pre-wrap;">{{ stepsText }}</div>
          </div>

          <!-- Tips -->
          <div v-if="r.tips" style="margin-bottom: 20px;">
            <div style="font-size: 16px; font-weight: 700; color: #374151; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
              <span style="display: inline-flex; width: 28px; height: 28px; border-radius: 8px; background: #fffbeb; align-items: center; justify-content: center; font-size: 16px;">💡</span>
              小贴士
            </div>
            <div style="background: linear-gradient(135deg, #fffbeb, #fff7ed); border-radius: 14px; padding: 16px; font-size: 13px; line-height: 1.7; color: #4b5563;">{{ r.tips }}</div>
          </div>

          <!-- Footer watermark -->
          <div style="text-align: center; font-size: 11px; color: #d1d5db; padding-top: 12px; margin-top: 8px; border-top: 1px solid #f3f4f6;">
            Designed by nate · Recipes
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
