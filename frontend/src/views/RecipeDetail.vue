<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRecipeStore } from '../stores/recipe'
import ShareModal from '../components/ShareModal.vue'
import RichContent from '../components/RichContent.vue'

const route = useRoute()
const router = useRouter()
const store = useRecipeStore()

const showShareModal = ref(false)

const recipe = ref(null)
const loadingDetail = ref(true)
const calories = computed(() => recipe.value ? store.calcCalories(recipe.value) : 0)

// --- Auto-rotating carousel ---
const currentSlide = ref(0)
let slideTimer = null

const imageList = computed(() => {
  if (!recipe.value?.images) return []
  return recipe.value.images.map((img) => typeof img === 'string' ? img : img.image_path)
})
const imageCount = computed(() => imageList.value.length)

function startAutoSlide() {
  if (imageCount.value <= 1) return
  slideTimer = setInterval(() => {
    currentSlide.value = (currentSlide.value + 1) % imageCount.value
  }, 4000)
}

function goToSlide(idx) {
  currentSlide.value = idx
  if (slideTimer) clearInterval(slideTimer)
  startAutoSlide()
}

function prevSlide() {
  goToSlide((currentSlide.value - 1 + imageCount.value) % imageCount.value)
}

function nextSlide() {
  goToSlide((currentSlide.value + 1) % imageCount.value)
}

onMounted(async () => {
  loadingDetail.value = true
  recipe.value = await store.fetchRecipeById(route.params.id)
  loadingDetail.value = false
  startAutoSlide()
})
onUnmounted(() => { if (slideTimer) clearInterval(slideTimer) })

// --- Ingredient groups ---
const ingredientGroups = computed(() => {
  if (!recipe.value) return {}
  const groups = {}
  for (const item of recipe.value.ingredients) {
    const cat = item.category || '其他'
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({
      ...item,
      name: item.ingredient_name || item.name || '',
      unit: item.ingredient_unit || item.unit || '',
    })
  }
  return groups
})

const categoryOrder = ['主料', '辅料', '调料']
const sortedCategories = computed(() => {
  const keys = Object.keys(ingredientGroups.value)
  return categoryOrder.filter((c) => keys.includes(c)).concat(keys.filter((c) => !categoryOrder.includes(c)))
})

function handleShare() {
  showShareModal.value = true
}
</script>

<template>
  <div v-if="recipe" class="max-w-3xl mx-auto animate-fade-in-up">
    <!-- Back button -->
    <button class="btn-ghost btn-sm mb-6" @click="router.back()">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      返回
    </button>

    <!-- Image Carousel — photo frame style -->
    <div
      v-if="imageList.length > 0"
      class="relative rounded-xl sm:rounded-2xl overflow-hidden mb-6 sm:mb-8 group carousel-frame"
    >
      <div class="relative aspect-[16/9] rounded-xl overflow-hidden" style="border: 1px solid var(--color-border);">
        <transition name="fade" mode="out-in">
          <img
            :key="currentSlide"
            :src="imageList[currentSlide]"
            :alt="recipe.name"
            class="absolute inset-0 w-full h-full object-cover"
          />
        </transition>
      </div>

      <!-- Arrow buttons -->
      <template v-if="imageCount > 1">
        <button
          class="carousel-arrow left-5"
          @click="prevSlide"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <button
          class="carousel-arrow right-5"
          @click="nextSlide"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </button>

        <!-- Dots -->
        <div class="absolute bottom-5 left-1/2 -translate-x-1/2 flex gap-2">
          <button
            v-for="(_, idx) in imageList"
            :key="idx"
            class="carousel-dot"
            :class="{ 'carousel-dot-active': idx === currentSlide }"
            @click="goToSlide(idx)"
          />
        </div>
      </template>
    </div>

    <!-- Title & Meta -->
    <div class="mb-8">
      <div class="flex items-start justify-between gap-4">
        <h1 class="text-2xl sm:text-3xl md:text-4xl font-bold leading-tight" style="font-family: var(--font-heading); color: var(--color-text);">
          {{ recipe.name }}
        </h1>
        <button class="btn-secondary btn-sm shrink-0 mt-1" @click="handleShare">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
          分享
        </button>
      </div>
      <div class="flex flex-wrap gap-2 mt-4">
        <span v-for="tag in recipe.tags" :key="tag.id" class="tag-secondary">
          {{ tag.name }}
        </span>
        <span v-if="calories > 0" class="tag-accent">
          约 {{ calories }} kcal
        </span>
      </div>
    </div>

    <!-- Wavy divider -->
    <div class="wavy-divider mb-8"></div>

    <!-- Description -->
    <div
      v-if="recipe.description"
      class="card-warm rounded-2xl p-6 mb-8"
      style="font-family: var(--font-body); line-height: 1.9;"
    >
      <RichContent :html="recipe.description" />
    </div>

    <!-- Ingredients -->
    <div class="mb-8">
      <h2 class="section-heading text-xl mb-4">
        <span class="section-icon" style="background: var(--color-secondary-light);">🥬</span>
        食材清单
      </h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        <div
          v-for="category in sortedCategories"
          :key="category"
          class="card-warm rounded-2xl p-5"
        >
          <h3 class="text-sm font-semibold mb-3 uppercase tracking-wide" style="color: var(--color-text-muted); font-family: var(--font-ui);">
            {{ category }}
          </h3>
          <div>
            <div
              v-for="(item, idx) in ingredientGroups[category]"
              :key="item.id"
              class="flex justify-between items-center text-sm py-2"
              :style="idx < ingredientGroups[category].length - 1 ? 'border-bottom: 1px dashed var(--color-border);' : ''"
            >
              <span style="color: var(--color-text);">{{ item.name }}</span>
              <span class="tabular-nums" style="color: var(--color-text-muted);">{{ item.amount }}{{ item.unit }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Steps -->
    <div class="mb-8">
      <h2 class="section-heading text-xl mb-4">
        <span class="section-icon" style="background: var(--color-primary-light);">📝</span>
        烹饪步骤
      </h2>
      <div class="card-warm rounded-2xl p-6 leading-relaxed steps-card" style="font-family: var(--font-body); line-height: 1.9; color: var(--color-text);">
        <RichContent :html="recipe.steps" />
      </div>
    </div>

    <!-- Tips -->
    <div v-if="recipe.tips" class="mb-8">
      <h2 class="section-heading text-xl mb-4">
        <span class="section-icon" style="background: var(--color-accent-light);">💡</span>
        小贴士
      </h2>
      <div class="rounded-2xl p-6 text-sm leading-relaxed" style="background: var(--color-accent-light); border: 1px solid var(--color-accent); color: var(--color-text); font-family: var(--font-body); line-height: 1.9;">
        {{ recipe.tips }}
      </div>
    </div>
  </div>

  <!-- Loading -->
  <div v-else-if="loadingDetail" class="flex items-center justify-center py-24">
    <div class="spinner-warm"></div>
    <span class="ml-3" style="color: var(--color-text-muted);">加载中...</span>
  </div>

  <!-- Not Found -->
  <div v-else class="text-center py-24 animate-fade-in-up">
    <svg class="mx-auto mb-4" width="80" height="70" viewBox="0 0 80 70" fill="none">
      <ellipse cx="40" cy="35" rx="26" ry="22" stroke="var(--color-text-muted)" stroke-width="1.5" fill="var(--color-card)" stroke-linecap="round"/>
      <ellipse cx="40" cy="33" rx="16" ry="12" stroke="var(--color-border)" stroke-width="1" fill="none" stroke-dasharray="4 3"/>
    </svg>
    <p class="text-lg mb-2" style="color: var(--color-text-muted); font-family: var(--font-heading);">菜谱不存在</p>
    <button class="btn-ghost btn-sm mt-4" @click="router.push('/')">
      返回首页
    </button>
  </div>

  <!-- Share Modal -->
  <ShareModal :show="showShareModal" :recipe="recipe" @close="showShareModal = false" />
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.6s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.carousel-frame {
  padding: 0.75rem;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 20px rgba(61, 51, 41, 0.08);
}

.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 253, 248, 0.92);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  opacity: 0;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(61, 51, 41, 0.1);
}
.group:hover .carousel-arrow {
  opacity: 1;
}
.carousel-arrow:hover {
  background: var(--color-card);
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-50%) scale(1.08);
}

.carousel-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: var(--color-border);
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}
.carousel-dot-active {
  background: var(--color-primary);
  width: 1.5rem;
  border-radius: 999px;
}

.section-icon {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.steps-card {
  border-left: 3px solid var(--color-primary);
}
</style>
