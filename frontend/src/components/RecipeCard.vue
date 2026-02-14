<script setup>
import { computed } from 'vue'

const props = defineProps({
  recipe: { type: Object, required: true },
})

const emit = defineEmits(['share'])

const calories = computed(() => props.recipe.calories || 0)

const coverImage = computed(() => {
  if (props.recipe.images && props.recipe.images.length > 0) {
    const img = props.recipe.images[0]
    return typeof img === 'string' ? img : img.image_path
  }
  return 'https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=800&h=600&fit=crop'
})

const mainIngredients = computed(() => {
  if (!props.recipe.ingredients) return ''
  return props.recipe.ingredients
    .filter((i) => i.category === '主料')
    .map((i) => i.ingredient_name || i.name || '')
    .filter(Boolean)
    .join(' · ')
})

function handleShare(e) {
  e.preventDefault()
  e.stopPropagation()
  emit('share', props.recipe)
}
</script>

<template>
  <router-link :to="`/recipe/${recipe.id}`" class="no-underline block group">
    <div class="recipe-card card-warm rounded-2xl overflow-hidden h-full">
      <!-- Cover Image with photo frame feel -->
      <div class="p-2.5 pb-0">
        <div class="relative overflow-hidden rounded-xl aspect-[16/10] photo-frame">
          <img
            :src="coverImage"
            :alt="recipe.name"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
          />

          <!-- Calorie badge -->
          <div v-if="calories > 0" class="badge-overlay top-2.5 right-2.5">
            {{ calories }} kcal
          </div>

          <!-- Image count badge -->
          <div
            v-if="recipe.images && recipe.images.length > 1"
            class="absolute top-2.5 left-2.5 text-xs px-2 py-0.5 rounded-full"
            style="background: rgba(61,51,41,0.55); color: white; backdrop-filter: blur(4px);"
          >
            {{ recipe.images.length }} 张
          </div>
        </div>
      </div>

      <!-- Info -->
      <div class="p-4 pt-3">
        <h3 class="text-base font-bold leading-tight mb-1" style="font-family: var(--font-heading); color: var(--color-text);">
          {{ recipe.name }}
        </h3>
        <p v-if="mainIngredients" class="text-xs mb-3 truncate" style="color: var(--color-text-muted);">
          {{ mainIngredients }}
        </p>
        <div class="flex items-center gap-1.5">
          <div class="flex flex-wrap gap-1.5 flex-1">
            <span
              v-for="tag in recipe.tags.slice(0, 3)"
              :key="tag.id"
              class="tag-secondary"
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
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            分享
          </button>
        </div>
      </div>
    </div>
  </router-link>
</template>

<style scoped>
.recipe-card {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.recipe-card:hover {
  transform: translateY(-5px) rotate(-0.4deg);
  box-shadow: 0 16px 40px rgba(61, 51, 41, 0.12);
  border-color: var(--color-border-hover);
}

.photo-frame {
  border: 1px solid var(--color-border);
  transition: border-color 0.3s ease;
}
.recipe-card:hover .photo-frame {
  border-color: var(--color-primary-light);
}

.badge-overlay {
  position: absolute;
  font-size: 0.7rem;
  font-weight: 600;
  font-family: var(--font-ui);
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: rgba(255, 253, 248, 0.92);
  color: var(--color-primary);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(229, 221, 209, 0.5);
}

.share-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.7rem;
  font-family: var(--font-ui);
  padding: 0.3rem 0.6rem;
  border-radius: 999px;
  color: var(--color-accent);
  background: var(--color-accent-light);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.25s ease;
  flex-shrink: 0;
}
.share-btn:hover {
  background: var(--color-accent);
  color: white;
  transform: scale(1.05);
}

@media (max-width: 640px) {
  .recipe-card:hover {
    transform: translateY(-3px);
  }
}
</style>
