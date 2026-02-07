<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRecipeStore } from '../stores/recipe'
import ShareModal from '../components/ShareModal.vue'

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
  // Reset timer on manual navigation
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
    // Normalize field names (backend uses ingredient_name, frontend used name)
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
  <div v-if="recipe" class="max-w-3xl mx-auto">
    <!-- Back button -->
    <button
      class="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 bg-gray-100 hover:bg-gray-200 px-4 py-2 rounded-xl transition-colors mb-6"
      @click="router.back()"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      返回
    </button>

    <!-- Image Carousel -->
    <div
      v-if="imageList.length > 0"
      class="relative rounded-3xl overflow-hidden mb-8 shadow-lg group"
    >
      <!-- Slides -->
      <div class="relative aspect-[16/9] bg-gray-100">
        <transition name="fade" mode="out-in">
          <img
            :key="currentSlide"
            :src="imageList[currentSlide]"
            :alt="recipe.name"
            class="absolute inset-0 w-full h-full object-cover"
          />
        </transition>

        <!-- Gradient overlay bottom -->
        <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
      </div>

      <!-- Arrow buttons (multi-image) -->
      <template v-if="imageCount > 1">
        <button
          class="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 backdrop-blur-sm flex items-center justify-center text-gray-700 hover:bg-white shadow-md opacity-0 group-hover:opacity-100 transition-opacity"
          @click="prevSlide"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </button>
        <button
          class="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/80 backdrop-blur-sm flex items-center justify-center text-gray-700 hover:bg-white shadow-md opacity-0 group-hover:opacity-100 transition-opacity"
          @click="nextSlide"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        </button>

        <!-- Dots -->
        <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
          <button
            v-for="(_, idx) in imageList"
            :key="idx"
            class="w-2 h-2 rounded-full transition-all duration-300"
            :class="idx === currentSlide ? 'bg-white w-6' : 'bg-white/50 hover:bg-white/80'"
            @click="goToSlide(idx)"
          />
        </div>
      </template>
    </div>

    <!-- Title & Meta -->
    <div class="mb-8">
      <div class="flex items-start justify-between gap-4">
        <h1 class="text-3xl md:text-4xl font-extrabold text-gray-800 leading-tight">
          {{ recipe.name }}
        </h1>
        <button
          class="shrink-0 mt-1 px-4 py-2 rounded-xl bg-gradient-to-r from-green-500 to-emerald-500 text-white text-sm font-medium hover:shadow-lg hover:shadow-green-200 transition-all"
          @click="handleShare"
        >
          分享
        </button>
      </div>
      <div class="flex flex-wrap gap-2 mt-4">
        <span
          v-for="tag in recipe.tags"
          :key="tag.id"
          class="inline-block text-xs px-3 py-1 rounded-full bg-orange-50 text-orange-600 font-medium"
        >
          {{ tag.name }}
        </span>
        <span
          v-if="calories > 0"
          class="inline-block text-xs px-3 py-1 rounded-full bg-red-50 text-red-500 font-medium"
        >
          🔥 约 {{ calories }} kcal
        </span>
      </div>
    </div>

    <!-- Description -->
    <div
      v-if="recipe.description"
      class="text-gray-600 leading-relaxed prose mb-8 bg-white rounded-2xl p-6 border border-gray-100"
      v-html="recipe.description"
    />

    <!-- Ingredients -->
    <div class="mb-8">
      <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
        <span class="w-8 h-8 rounded-lg bg-green-50 flex items-center justify-center text-lg">🥬</span>
        食材清单
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          v-for="category in sortedCategories"
          :key="category"
          class="bg-white rounded-2xl p-5 border border-gray-100"
        >
          <h3 class="text-sm font-semibold text-gray-500 mb-3 uppercase tracking-wide">
            {{ category }}
          </h3>
          <div class="space-y-2">
            <div
              v-for="item in ingredientGroups[category]"
              :key="item.id"
              class="flex justify-between items-center text-sm"
            >
              <span class="text-gray-700">{{ item.name }}</span>
              <span class="text-gray-400 tabular-nums">{{ item.amount }}{{ item.unit }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Steps -->
    <div class="mb-8">
      <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
        <span class="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-lg">📝</span>
        烹饪步骤
      </h2>
      <div
        class="bg-white rounded-2xl p-6 border border-gray-100 text-gray-700 leading-relaxed prose"
        v-html="recipe.steps"
      />
    </div>

    <!-- Tips -->
    <div v-if="recipe.tips" class="mb-8">
      <h2 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
        <span class="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-lg">💡</span>
        小贴士
      </h2>
      <div class="bg-gradient-to-r from-amber-50 to-orange-50 rounded-2xl p-6 border border-amber-100 text-sm text-gray-700 leading-relaxed">
        {{ recipe.tips }}
      </div>
    </div>
  </div>

  <!-- Loading -->
  <div v-else-if="loadingDetail" class="flex items-center justify-center py-24">
    <div class="w-8 h-8 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin"></div>
    <span class="ml-3 text-gray-400">加载中...</span>
  </div>

  <!-- Not Found -->
  <div v-else class="text-center py-24">
    <div class="text-6xl mb-4">🍽️</div>
    <p class="text-lg text-gray-500 mb-2">菜谱不存在</p>
    <button
      class="mt-4 px-4 py-2 rounded-xl text-sm text-orange-500 border border-orange-300 hover:bg-orange-50 transition-colors"
      @click="router.push('/')"
    >
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
</style>
