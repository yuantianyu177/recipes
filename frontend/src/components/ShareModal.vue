<script setup>
import { ref, nextTick, watch, computed } from 'vue'
import { toPng } from 'html-to-image'
import { marked } from 'marked'
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
const coverDataUrl = ref('')

// Get cover image URL from recipe object
function getCoverImageUrl(recipe) {
  if (recipe.images && recipe.images.length > 0) {
    const img = recipe.images[0]
    return typeof img === 'string' ? img : img.image_path
  }
  return ''
}

// Convert remote image to base64 data URL for reliable html-to-image rendering
// Blob URLs can fail on mobile when element is off-screen
async function prefetchCoverAsBase64(url) {
  if (!url) return ''
  try {
    const resp = await fetch(url)
    const blob = await resp.blob()

    // Convert blob to base64 data URL
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => resolve(reader.result)
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
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

watch(() => props.show, async (val) => {
  if (val && props.recipe) {
    imageUrl.value = ''
    generating.value = true
    fullRecipe.value = null
    coverDataUrl.value = ''

    // 1. Fetch recipe data
    const hasFullData = props.recipe.ingredients?.length >= 0 && props.recipe.steps !== undefined
    let recipeData
    if (hasFullData) {
      recipeData = props.recipe
    } else {
      try {
        recipeData = await store.fetchRecipeById(props.recipe.id)
      } catch {
        recipeData = props.recipe
      }
    }

    // 2. Prefetch cover image as base64 data URL
    const coverUrl = getCoverImageUrl(recipeData)
    fullRecipe.value = recipeData
    coverDataUrl.value = await prefetchCoverAsBase64(coverUrl)

    // 3. DOM render — wait for all images in cardRef to decode
    await nextTick()

    // Wait for all images in the render card to be fully decoded
    if (cardRef.value) {
      const imgs = cardRef.value.querySelectorAll('img')
      await Promise.all(
        Array.from(imgs).map(async (img) => {
          if (img.complete && img.naturalHeight > 0) return
          try {
            await img.decode()
          } catch {
            // Ignore decode errors, proceed anyway
          }
        })
      )
    }

    // 4. toPng
    try {
      const dataUrl = await toPng(cardRef.value, {
        pixelRatio: 2,
        backgroundColor: '#fffdf8',
        skipFonts: true,
      })
      imageUrl.value = dataUrl
    } catch (err) {
      imageUrl.value = ''
    } finally {
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

  // 检测是否移动设备
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
  const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent)
  const isWeChat = /MicroMessenger/i.test(navigator.userAgent)

  // iOS 微信内置浏览器特殊处理：引导用户长按保存
  if (isWeChat && isIOS) {
    alert('请长按图片，选择「保存图片」到相册')
    return
  }

  // 尝试使用 Web Share API（支持 iOS Safari、Android Chrome 等）
  const file = new File([blob], fileName, { type: 'image/png' })
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({
        files: [file],
        title: props.recipe?.name || '菜谱分享',
        text: '来自我的菜谱'
      })
      return
    } catch (err) {
      // 用户取消或分享失败，继续尝试其他方式
      if (err.name === 'AbortError') {
        return // 用户主动取消
      }
    }
  }

  // iOS Safari：使用新窗口打开图片，让用户长按保存
  if (isIOS) {
    const url = URL.createObjectURL(blob)
    const newWindow = window.open(url, '_blank')
    if (newWindow) {
      // 提示用户长按保存
      setTimeout(() => {
        alert('请长按图片，选择「存储图像」保存到相册')
      }, 500)
    } else {
      // 弹窗被拦截，使用下载方式
      triggerDownload(blob, fileName)
    }
    URL.revokeObjectURL(url)
    return
  }

  // Android 及其他：尝试使用下载方式
  triggerDownload(blob, fileName)
}

function triggerDownload(blob, fileName) {
  const url = URL.createObjectURL(blob)

  // 优先使用 download 属性
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  a.style.display = 'none'
  document.body.appendChild(a)

  // 兼容某些移动浏览器需要手动触发 click
  if (a.click) {
    a.click()
  } else {
    const event = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      view: window
    })
    a.dispatchEvent(event)
  }

  document.body.removeChild(a)

  // 延迟清理 URL
  setTimeout(() => {
    URL.revokeObjectURL(url)
  }, 1000)
}

function close() {
  imageUrl.value = ''
  fullRecipe.value = null
  coverDataUrl.value = ''
  emit('close')
}

const r = computed(() => fullRecipe.value)
const ingredientGroups = computed(() => r.value ? getIngredientGroups(r.value) : {})
const categoryOrder = ['主料', '辅料', '调料']
const sortedCategories = computed(() => {
  const keys = Object.keys(ingredientGroups.value)
  return categoryOrder.filter((c) => keys.includes(c)).concat(keys.filter((c) => !categoryOrder.includes(c)))
})
const stepsHtml = computed(() => r.value?.steps ? marked(r.value.steps, { breaks: true }) : '')
const descText = computed(() => r.value?.description || '')
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

      <!-- Hidden render card — editorial magazine share card -->
      <div style="position: fixed; left: -9999px; top: 0; width: 420px; z-index: -1;">
        <div ref="cardRef" v-if="r" style="width: 420px; background: #fffdf8; font-family: 'Noto Serif SC', 'PingFang SC', serif; color: #3d3329; overflow: hidden;">

          <!-- Hero cover image — full bleed with overlay -->
          <div v-if="coverDataUrl" style="position: relative; width: 420px; height: 280px; overflow: hidden;">
            <img :src="coverDataUrl" style="width: 100%; height: 100%; object-fit: cover; display: block;" />
            <!-- Dark gradient overlay from bottom -->
            <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 180px; background: linear-gradient(to top, rgba(35, 28, 22, 0.85) 0%, rgba(35, 28, 22, 0.4) 50%, transparent 100%);"></div>
            <!-- Top-left brand watermark on image -->
            <div style="position: absolute; top: 16px; left: 20px; display: flex; align-items: center; gap: 6px;">
              <div style="width: 20px; height: 20px; border-radius: 50%; border: 1.5px solid rgba(255,253,248,0.6); display: flex; align-items: center; justify-content: center;">
                <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
                  <path d="M8 2C8 2 4 5 4 9C4 11 5.5 13 8 14.5" stroke="rgba(255,253,248,0.8)" stroke-width="1.2" stroke-linecap="round" fill="none"/>
                  <path d="M8 2C8 2 12 5 12 9C12 11 10.5 13 8 14.5" stroke="rgba(255,253,248,0.8)" stroke-width="1.2" stroke-linecap="round" fill="none"/>
                </svg>
              </div>
              <span style="font-family: 'Playfair Display', serif; font-size: 11px; color: rgba(255,253,248,0.75); letter-spacing: 0.08em;">味之集</span>
            </div>
            <!-- Recipe title overlaid on image -->
            <div style="position: absolute; bottom: 20px; left: 24px; right: 24px;">
              <div style="font-size: 26px; font-weight: 700; line-height: 1.25; font-family: 'Playfair Display', 'Noto Serif SC', serif; color: #fffdf8; text-shadow: 0 1px 8px rgba(0,0,0,0.2);">{{ r.name }}</div>
            </div>
          </div>

          <!-- Fallback: no cover image — title without hero -->
          <div v-else style="padding: 28px 24px 0;">
            <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 16px;">
              <div style="width: 20px; height: 20px; border-radius: 50%; border: 1.5px solid #e5ddd1; display: flex; align-items: center; justify-content: center;">
                <svg width="10" height="10" viewBox="0 0 16 16" fill="none">
                  <path d="M8 2C8 2 4 5 4 9C4 11 5.5 13 8 14.5" stroke="#c45d3e" stroke-width="1.2" stroke-linecap="round" fill="none"/>
                  <path d="M8 2C8 2 12 5 12 9C12 11 10.5 13 8 14.5" stroke="#5b7a5e" stroke-width="1.2" stroke-linecap="round" fill="none"/>
                </svg>
              </div>
              <span style="font-family: 'Playfair Display', serif; font-size: 11px; color: #8c7e6f; letter-spacing: 0.08em;">味之集</span>
            </div>
            <div style="font-size: 26px; font-weight: 700; line-height: 1.25; font-family: 'Playfair Display', 'Noto Serif SC', serif; color: #3d3329;">{{ r.name }}</div>
          </div>

          <!-- Content body -->
          <div style="padding: 20px 24px 24px;">

            <!-- Tags row -->
            <div v-if="r.tags && r.tags.length" style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px;">
              <span
                v-for="(tag, tIdx) in r.tags"
                :key="tag.id"
                :style="{
                  display: 'inline-flex',
                  alignItems: 'center',
                  fontSize: '10px',
                  padding: '3px 10px',
                  borderRadius: '999px',
                  fontWeight: '500',
                  lineHeight: '1',
                  fontFamily: '\'Noto Sans SC\', sans-serif',
                  letterSpacing: '0.03em',
                  background: tag.color ? tag.color + '1a' : (tIdx % 3 === 0 ? '#e8d5cf' : tIdx % 3 === 1 ? '#d4e3d5' : '#f0e4c8'),
                  color: tag.color || (tIdx % 3 === 0 ? '#c45d3e' : tIdx % 3 === 1 ? '#5b7a5e' : '#d4a853'),
                }"
              >{{ tag.name }}</span>
            </div>

            <!-- Description — editorial quote style -->
            <div v-if="descText" style="position: relative; margin-bottom: 22px; padding: 14px 16px 14px 20px; background: #f5f0e8; border-radius: 8px; border-left: 3px solid #d4a853;">
              <div style="position: absolute; top: 4px; left: 8px; font-family: 'Playfair Display', serif; font-size: 28px; color: #d4a853; opacity: 0.3; line-height: 1;">"</div>
              <div style="font-size: 12.5px; line-height: 1.8; color: #5a4d40; font-family: 'Noto Serif SC', serif;">{{ descText }}</div>
            </div>

            <!-- Elegant section divider -->
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 18px;">
              <div style="flex: 1; height: 1px; background: #e5ddd1;"></div>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M7 1L8.5 5.5L13 7L8.5 8.5L7 13L5.5 8.5L1 7L5.5 5.5L7 1Z" fill="#d4a853" opacity="0.4"/>
              </svg>
              <div style="flex: 1; height: 1px; background: #e5ddd1;"></div>
            </div>

            <!-- Ingredients — refined dotted-leader layout -->
            <div v-if="sortedCategories.length" style="margin-bottom: 22px;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
                <div style="font-size: 14px; font-weight: 700; color: #3d3329; font-family: 'Playfair Display', 'Noto Serif SC', serif;">食材清单</div>
                <div style="flex: 1; height: 1px; background: #e5ddd1;"></div>
              </div>

              <div v-for="(cat, catIdx) in sortedCategories" :key="cat" :style="{ marginBottom: catIdx < sortedCategories.length - 1 ? '14px' : '0' }">
                <!-- Category label with colored accent -->
                <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
                  <div :style="{
                    width: '3px',
                    height: '12px',
                    borderRadius: '2px',
                    background: catIdx === 0 ? '#c45d3e' : catIdx === 1 ? '#5b7a5e' : '#d4a853',
                  }"></div>
                  <span style="font-size: 10.5px; font-weight: 600; color: #8c7e6f; letter-spacing: 0.12em; text-transform: uppercase; font-family: 'Noto Sans SC', sans-serif;">{{ cat }}</span>
                </div>

                <!-- Ingredient rows with dot leaders -->
                <div v-for="item in ingredientGroups[cat]" :key="item.name" style="display: flex; align-items: baseline; gap: 4px; padding: 3px 0 3px 9px;">
                  <span style="font-size: 12px; color: #3d3329; white-space: nowrap; font-family: 'Noto Serif SC', serif;">{{ item.name }}</span>
                  <span style="flex: 1; border-bottom: 1px dotted #d4c9b8; min-width: 12px; margin-bottom: 3px;"></span>
                  <span style="font-size: 11.5px; color: #8c7e6f; white-space: nowrap; font-family: 'Noto Sans SC', sans-serif; font-variant-numeric: tabular-nums;">{{ item.amount }}{{ item.unit }}</span>
                </div>
              </div>
            </div>

            <!-- Steps — editorial column with accent bar -->
            <div v-if="stepsHtml" style="margin-bottom: 22px;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
                <div style="font-size: 14px; font-weight: 700; color: #3d3329; font-family: 'Playfair Display', 'Noto Serif SC', serif;">烹饪步骤</div>
                <div style="flex: 1; height: 1px; background: #e5ddd1;"></div>
              </div>
              <div style="position: relative; background: #f5f0e8; border-radius: 10px; padding: 16px 16px 16px 20px; overflow: hidden;">
                <!-- Left gradient accent bar -->
                <div style="position: absolute; top: 0; left: 0; bottom: 0; width: 4px; background: linear-gradient(to bottom, #c45d3e, #d4a853); border-radius: 4px 0 0 4px;"></div>
                <div style="font-size: 12.5px; line-height: 1.9; color: #3d3329; font-family: 'Noto Serif SC', serif;" v-html="stepsHtml"></div>
              </div>
            </div>

            <!-- Tips — warm accent card -->
            <div v-if="r.tips" style="margin-bottom: 22px;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
                <div style="font-size: 14px; font-weight: 700; color: #3d3329; font-family: 'Playfair Display', 'Noto Serif SC', serif;">小贴士</div>
                <div style="flex: 1; height: 1px; background: #e5ddd1;"></div>
              </div>
              <div style="position: relative; background: linear-gradient(135deg, #f0e4c8 0%, #f7edd6 100%); border-radius: 10px; padding: 16px; border: 1px solid rgba(212, 168, 83, 0.3); overflow: hidden;">
                <!-- Decorative lightbulb icon -->
                <div style="position: absolute; top: 10px; right: 12px; opacity: 0.1;">
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                    <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke="#d4a853" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
                <div style="font-size: 12.5px; line-height: 1.8; color: #5a4d40; font-family: 'Noto Serif SC', serif; position: relative; z-index: 1;">{{ r.tips }}</div>
              </div>
            </div>

            <!-- Bottom flourish -->
            <div style="display: flex; align-items: center; justify-content: center; gap: 12px; padding-top: 6px;">
              <div style="width: 40px; height: 1px; background: linear-gradient(to right, transparent, #d4c9b8);"></div>
              <svg width="16" height="16" viewBox="0 0 28 28" fill="none">
                <path d="M14 4C14 4 8 8 8 14C8 17 10 20 14 22" stroke="#c45d3e" stroke-width="1.5" stroke-linecap="round" fill="none"/>
                <path d="M14 4C14 4 20 8 20 14C20 17 18 20 14 22" stroke="#5b7a5e" stroke-width="1.5" stroke-linecap="round" fill="none"/>
                <path d="M14 22V26" stroke="#d4a853" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <div style="width: 40px; height: 1px; background: linear-gradient(to left, transparent, #d4c9b8);"></div>
            </div>
            <div style="text-align: center; margin-top: 8px; padding-bottom: 4px;">
              <span style="font-family: 'Playfair Display', serif; font-size: 10px; color: #c4b9a8; font-style: italic; letter-spacing: 0.1em;">Crafted with care</span>
            </div>

          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
