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
const coverBlobUrl = ref('')

// Get cover image URL from recipe object
function getCoverImageUrl(recipe) {
  if (recipe.images && recipe.images.length > 0) {
    const img = recipe.images[0]
    return typeof img === 'string' ? img : img.image_path
  }
  return ''
}

// Convert remote image to blob URL to avoid CORS re-download
async function prefetchCoverAsBlob(url) {
  if (!url) return ''
  try {
    const resp = await fetch(url)
    const blob = await resp.blob()
    return URL.createObjectURL(blob)
  } catch {
    return url // fallback to original
  }
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
    console.time('[ShareModal] total')
    imageUrl.value = ''
    generating.value = true
    fullRecipe.value = null
    if (coverBlobUrl.value) {
      URL.revokeObjectURL(coverBlobUrl.value)
      coverBlobUrl.value = ''
    }

    // 1. Fetch recipe data
    console.time('[ShareModal] fetchData')
    const hasFullData = props.recipe.ingredients?.length >= 0 && props.recipe.steps !== undefined
    let recipeData
    if (hasFullData) {
      recipeData = props.recipe
      console.log('[ShareModal] skipped API call (full data available)')
    } else {
      try {
        recipeData = await store.fetchRecipeById(props.recipe.id)
      } catch {
        recipeData = props.recipe
      }
    }
    console.timeEnd('[ShareModal] fetchData')

    // 2. Prefetch cover image as blob
    console.time('[ShareModal] prefetchBlob')
    const coverUrl = getCoverImageUrl(recipeData)
    console.log('[ShareModal] cover URL:', coverUrl)
    const blobPromise = prefetchCoverAsBlob(coverUrl)
    fullRecipe.value = recipeData
    coverBlobUrl.value = await blobPromise
    console.timeEnd('[ShareModal] prefetchBlob')

    // 3. DOM render
    console.time('[ShareModal] domRender')
    await nextTick()
    await new Promise((r) => setTimeout(r, 50))
    console.timeEnd('[ShareModal] domRender')

    // 4. toPng
    console.time('[ShareModal] toPng')
    try {
      const dataUrl = await toPng(cardRef.value, {
        pixelRatio: 2,
        backgroundColor: '#fffdf8',
        skipFonts: true,
      })
      imageUrl.value = dataUrl
    } catch (err) {
      console.error('[ShareModal] toPng error:', err)
      imageUrl.value = ''
    } finally {
      console.timeEnd('[ShareModal] toPng')
      console.timeEnd('[ShareModal] total')
      generating.value = false
    }
  }
})

async function downloadImage() {
  if (!imageUrl.value) return
  const fileName = `${props.recipe?.name || 'recipe'}.png`

  // Convert data URL to blob
  const resp = await fetch(imageUrl.value)
  const blob = await resp.blob()
  const file = new File([blob], fileName, { type: 'image/png' })

  // Use Web Share API on mobile — triggers native share sheet (save to photos, AirDrop, etc.)
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file] })
      return
    } catch {
      // User cancelled or share failed, fall through to download
    }
  }

  // Fallback: traditional download
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.click()
  URL.revokeObjectURL(url)
}

function close() {
  imageUrl.value = ''
  fullRecipe.value = null
  if (coverBlobUrl.value) {
    URL.revokeObjectURL(coverBlobUrl.value)
    coverBlobUrl.value = ''
  }
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
      <div class="rounded-2xl shadow-2xl max-w-md w-full mx-4 max-h-[90vh] sm:max-h-[90vh] flex flex-col overflow-hidden share-modal-card" style="background: var(--color-card);">
        <!-- Modal header -->
        <div class="flex items-center justify-between px-5 py-4" style="border-bottom: 1px solid var(--color-border);">
          <h3 class="text-lg font-bold" style="font-family: var(--font-heading); color: var(--color-text);">分享菜谱</h3>
          <button style="color: var(--color-text-muted);" class="hover:opacity-70 transition-opacity" @click="close">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Preview area -->
        <div class="flex-1 overflow-y-auto p-5">
          <div v-if="generating" class="flex flex-col items-center justify-center py-12">
            <div class="spinner-warm mb-3"></div>
            <span class="text-sm" style="color: var(--color-text-muted);">正在生成图片...</span>
          </div>

          <div v-else-if="imageUrl" class="flex flex-col items-center">
            <img :src="imageUrl" alt="preview" class="w-full rounded-xl shadow-lg" style="border: 1px solid var(--color-border);" />
          </div>

          <div v-else class="text-center text-sm py-12" style="color: var(--color-text-muted);">
            生成失败，请重试
          </div>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 justify-end px-5 py-4" style="border-top: 1px solid var(--color-border);">
          <button class="btn-soft" @click="close">关闭</button>
          <button v-if="imageUrl" class="btn-secondary" @click="downloadImage">保存图片</button>
        </div>
      </div>

      <!-- Hidden render card — refined share card -->
      <div style="position: fixed; left: -9999px; top: 0; width: 420px; z-index: -1;">
        <div ref="cardRef" v-if="r" style="width: 420px; background: #fffdf8; font-family: 'Noto Serif SC', 'PingFang SC', serif; color: #3d3329;">

          <!-- Top decorative bar -->
          <div style="height: 6px; background: linear-gradient(90deg, #c45d3e, #d4a853, #5b7a5e);"></div>

          <div style="padding: 28px 24px 24px;">
            <!-- Logo mark + brand -->
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
              <svg width="24" height="24" viewBox="0 0 28 28" fill="none">
                <path d="M14 4C14 4 8 8 8 14C8 17 10 20 14 22" stroke="#c45d3e" stroke-width="1.8" stroke-linecap="round" fill="none"/>
                <path d="M14 4C14 4 20 8 20 14C20 17 18 20 14 22" stroke="#5b7a5e" stroke-width="1.8" stroke-linecap="round" fill="none"/>
                <path d="M14 22V26" stroke="#d4a853" stroke-width="1.8" stroke-linecap="round"/>
              </svg>
              <span style="font-family: 'Playfair Display', serif; font-size: 13px; color: #8c7e6f; letter-spacing: 0.05em;">My Recipes</span>
            </div>

            <!-- Recipe name -->
            <div style="font-size: 28px; font-weight: 700; line-height: 1.3; font-family: 'Playfair Display', 'Noto Serif SC', serif; color: #3d3329; margin-bottom: 16px;">{{ r.name }}</div>

            <!-- Tags -->
            <div v-if="r.tags && r.tags.length" style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px;">
              <span
                v-for="tag in r.tags"
                :key="tag.id"
                style="display: inline-flex; align-items: center; font-size: 11px; padding: 4px 12px; border-radius: 999px; background: #d4e3d5; color: #5b7a5e; font-weight: 500; line-height: 1;"
              >{{ tag.name }}</span>
            </div>

            <!-- Cover image (using prefetched blob URL — no CORS re-download) -->
            <div v-if="coverBlobUrl" style="border-radius: 12px; overflow: hidden; margin-bottom: 20px; box-shadow: 0 4px 16px rgba(61,51,41,0.1);">
              <img :src="coverBlobUrl" style="width: 100%; height: 240px; object-fit: cover; display: block;" />
            </div>

            <!-- Description -->
            <div v-if="descText" style="background: #f5f0e8; border-radius: 12px; padding: 14px 16px; margin-bottom: 20px; font-size: 13px; line-height: 1.7; color: #8c7e6f;">
              {{ descText }}
            </div>

            <!-- Ingredients — two-column compact layout -->
            <div v-if="sortedCategories.length" style="margin-bottom: 20px;">
              <div style="font-size: 15px; font-weight: 700; color: #3d3329; margin-bottom: 12px; font-family: 'Playfair Display', 'Noto Serif SC', serif;">
                食材清单
              </div>
              <div v-for="cat in sortedCategories" :key="cat" style="margin-bottom: 10px;">
                <div style="font-size: 11px; font-weight: 600; color: #8c7e6f; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px;">{{ cat }}</div>
                <table style="width: 100%; border-collapse: collapse;">
                  <tr v-for="rowIdx in Math.ceil(ingredientGroups[cat].length / 2)" :key="rowIdx">
                    <td style="font-size: 12px; padding: 3px 4px 3px 0; color: #3d3329; width: 25%;">{{ ingredientGroups[cat][(rowIdx - 1) * 2]?.name }}</td>
                    <td style="font-size: 12px; padding: 3px 8px 3px 0; color: #8c7e6f; width: 25%; text-align: right;">{{ ingredientGroups[cat][(rowIdx - 1) * 2]?.amount }}{{ ingredientGroups[cat][(rowIdx - 1) * 2]?.unit }}</td>
                    <td v-if="ingredientGroups[cat][(rowIdx - 1) * 2 + 1]" style="font-size: 12px; padding: 3px 4px 3px 8px; color: #3d3329; width: 25%;">{{ ingredientGroups[cat][(rowIdx - 1) * 2 + 1]?.name }}</td>
                    <td v-if="ingredientGroups[cat][(rowIdx - 1) * 2 + 1]" style="font-size: 12px; padding: 3px 0 3px 0; color: #8c7e6f; width: 25%; text-align: right;">{{ ingredientGroups[cat][(rowIdx - 1) * 2 + 1]?.amount }}{{ ingredientGroups[cat][(rowIdx - 1) * 2 + 1]?.unit }}</td>
                    <td v-else colspan="2"></td>
                  </tr>
                </table>
              </div>
            </div>

            <!-- Steps with numbered dots -->
            <div v-if="stepsText" style="margin-bottom: 20px;">
              <div style="font-size: 15px; font-weight: 700; color: #3d3329; margin-bottom: 12px; font-family: 'Playfair Display', 'Noto Serif SC', serif;">
                烹饪步骤
              </div>
              <div style="background: #f5f0e8; border-radius: 12px; padding: 16px; font-size: 13px; line-height: 1.8; color: #3d3329; white-space: pre-wrap; border-left: 3px solid #c45d3e;">{{ stepsText }}</div>
            </div>

            <!-- Tips -->
            <div v-if="r.tips" style="margin-bottom: 20px;">
              <div style="font-size: 15px; font-weight: 700; color: #3d3329; margin-bottom: 12px; font-family: 'Playfair Display', 'Noto Serif SC', serif;">
                小贴士
              </div>
              <div style="background: #f0e4c8; border-radius: 12px; padding: 14px 16px; font-size: 13px; line-height: 1.7; color: #3d3329; border: 1px solid #d4a853;">{{ r.tips }}</div>
            </div>

            <!-- Wavy divider -->
            <div style="height: 12px; background: url(&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 12'%3E%3Cpath d='M0 6 Q25 0 50 6 T100 6 T150 6 T200 6' fill='none' stroke='%23c4b9a8' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E&quot;) repeat-x center; background-size: 200px 12px; opacity: 0.6; margin-bottom: 12px;"></div>

            <!-- Footer watermark -->
            <div style="text-align: center; font-size: 11px; color: #c4b9a8; font-family: 'Playfair Display', serif; font-style: italic;">
              Crafted with care by nate
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
