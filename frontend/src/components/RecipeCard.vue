<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  recipe: { type: Object, required: true },
})

const emit = defineEmits(['share'])

const calories = computed(() => props.recipe.calories || 0)

const allImages = computed(() => {
  if (props.recipe.images && props.recipe.images.length > 0) {
    return props.recipe.images.map((img) =>
      typeof img === 'string' ? img : img.image_path
    )
  }
  return ['https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=800&h=600&fit=crop']
})

const hasMultipleImages = computed(() => allImages.value.length > 1)
const currentIndex = ref(0)
let autoplayTimer = null

function startAutoplay() {
  if (!hasMultipleImages.value) return
  stopAutoplay()
  autoplayTimer = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % allImages.value.length
  }, 3000)
}

function stopAutoplay() {
  if (autoplayTimer) {
    clearInterval(autoplayTimer)
    autoplayTimer = null
  }
}

function goTo(index, e) {
  if (e) { e.preventDefault(); e.stopPropagation() }
  currentIndex.value = index
  startAutoplay()
}

// Touch swipe support
let touchStartX = 0
function onTouchStart(e) {
  touchStartX = e.touches[0].clientX
  stopAutoplay()
}
function onTouchEnd(e) {
  const diff = touchStartX - e.changedTouches[0].clientX
  if (Math.abs(diff) > 40) {
    const len = allImages.value.length
    currentIndex.value = diff > 0
      ? (currentIndex.value + 1) % len
      : (currentIndex.value - 1 + len) % len
  }
  startAutoplay()
}

onMounted(() => startAutoplay())
onBeforeUnmount(() => stopAutoplay())

const coverImage = computed(() => allImages.value[0])

const ingredientNames = computed(() => {
  if (!props.recipe.ingredients) return []
  return props.recipe.ingredients
    .map((i) => i.ingredient_name || i.name || '')
    .filter(Boolean)
    .slice(0, 3)
})

const description = computed(() => {
  if (props.recipe.description) return props.recipe.description
  const ings = ingredientNames.value.join('、')
  return ings ? `主料：${ings}` : ''
})

// Alternate drop-cap on some cards for visual variety
const useDropCap = computed(() => {
  return description.value.length > 40 && props.recipe.id % 3 === 0
})

function handleShare(e) {
  e.preventDefault()
  e.stopPropagation()
  emit('share', props.recipe)
}
</script>

<template>
  <router-link :to="`/recipe/${recipe.id}`" class="no-underline block">
    <div class="recipe-card">
      <!-- Cover Image Carousel -->
      <div
        class="relative overflow-hidden"
        @touchstart.passive="hasMultipleImages && onTouchStart($event)"
        @touchend.passive="hasMultipleImages && onTouchEnd($event)"
      >
        <div
          class="carousel-track"
          :style="{ transform: `translateX(-${currentIndex * 100}%)` }"
        >
          <img
            v-for="(img, idx) in allImages"
            :key="idx"
            :src="img"
            :alt="recipe.name"
            class="card-image"
          />
        </div>
        <div v-if="calories > 0" class="calorie-badge">
          {{ calories }} kcal
        </div>
        <!-- Dot indicators -->
        <div v-if="hasMultipleImages" class="carousel-dots">
          <button
            v-for="(_, idx) in allImages"
            :key="idx"
            class="carousel-dot"
            :class="{ active: idx === currentIndex }"
            @click="goTo(idx, $event)"
          />
        </div>
      </div>

      <!-- Content -->
      <div class="card-content">
        <h3 class="card-title">{{ recipe.name }}</h3>
        <p
          v-if="description"
          class="card-desc"
          :class="{ 'drop-cap': useDropCap }"
        >
          {{ description }}
        </p>
        <!-- Ingredient pills -->
        <div v-if="ingredientNames.length" class="ingredient-list">
          <span
            v-for="ing in ingredientNames"
            :key="ing"
            class="ingredient-pill"
          >
            {{ ing }}
          </span>
        </div>
        <!-- Footer: tags + share -->
        <div class="card-footer">
          <div class="flex gap-1.5 flex-wrap">
            <span
              v-for="tag in recipe.tags.slice(0, 2)"
              :key="tag.id"
              class="card-tag"
              :style="tag.color ? { background: tag.color + '1a', color: tag.color } : (tag.id % 2 === 0 ? {} : {})"
              :class="!tag.color ? (tag.id % 2 === 0 ? 'card-tag-secondary' : 'card-tag-primary') : ''"
            >
              {{ tag.name }}
            </span>
          </div>
          <button
            class="share-btn"
            title="分享"
            @click="handleShare"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </router-link>
</template>

<style scoped>
.recipe-card {
  background: var(--color-card);
  border-radius: 1rem;
  border: 1px solid var(--color-border);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(61, 51, 41, 0.04);
  transition: transform 0.35s cubic-bezier(.22,.61,.36,1), box-shadow 0.35s cubic-bezier(.22,.61,.36,1);
  cursor: pointer;
}
.recipe-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 50px -12px rgba(61, 51, 41, 0.18);
}

.card-image {
  width: 100%;
  min-width: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(.22,.61,.36,1);
}
.recipe-card:hover .card-image {
  transform: scale(1.06);
}

.carousel-track {
  display: flex;
  transition: transform 0.45s cubic-bezier(.4, 0, .2, 1);
}

.carousel-dots {
  position: absolute;
  bottom: 0.625rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.375rem;
  z-index: 2;
}
.carousel-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  border: none;
  padding: 0;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.5);
  transition: all 0.25s ease;
}
.carousel-dot.active {
  background: #fff;
  width: 16px;
  border-radius: 3px;
}

.calorie-badge {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  background: rgba(255, 253, 248, 0.8);
  color: var(--color-primary);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  font-family: var(--font-ui);
}

.card-content {
  padding: 1.25rem;
}

.card-title {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: 0.5rem;
  line-height: 1.3;
}

.card-desc {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  line-height: 1.6;
  margin-bottom: 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Drop cap for select cards */
.drop-cap::first-letter {
  float: left;
  font-family: var(--font-heading);
  font-size: 3.2rem;
  line-height: 0.8;
  padding-right: 0.5rem;
  padding-top: 0.25rem;
  color: var(--color-primary);
  font-weight: 700;
}

.ingredient-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 0.75rem;
}
.ingredient-pill {
  font-size: 0.75rem;
  color: rgba(140, 126, 111, 0.7);
  border: 1px solid rgba(229, 221, 209, 0.6);
  border-radius: 999px;
  padding: 0.125rem 0.625rem;
  font-family: var(--font-ui);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(229, 221, 209, 0.5);
}

.card-tag {
  font-size: 0.75rem;
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-weight: 500;
  font-family: var(--font-ui);
}
.card-tag-primary {
  background: rgba(196, 93, 62, 0.1);
  color: var(--color-primary);
}
.card-tag-secondary {
  background: rgba(91, 122, 94, 0.1);
  color: var(--color-secondary);
}

.share-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  background: none;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.share-btn:hover {
  background: var(--color-primary);
  color: var(--color-card);
  border-color: var(--color-primary);
}

@media (max-width: 640px) {
  .recipe-card:hover {
    transform: translateY(-3px);
  }
}
</style>
