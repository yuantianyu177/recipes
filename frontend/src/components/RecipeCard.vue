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
    <div class="bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-500 h-full border border-gray-100 hover:border-gray-200 hover:-translate-y-1">
      <!-- Cover Image -->
      <div class="relative overflow-hidden aspect-[16/10]">
        <img
          :src="coverImage"
          :alt="recipe.name"
          class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 ease-out"
        />
        <!-- Gradient overlay -->
        <div class="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />

        <!-- Calorie badge -->
        <div
          v-if="calories > 0"
          class="absolute top-3 right-3 bg-white/90 backdrop-blur-sm text-orange-600 text-xs font-semibold px-2.5 py-1 rounded-full shadow-sm"
        >
          🔥 {{ calories }} kcal
        </div>

        <!-- Image count badge -->
        <div
          v-if="recipe.images && recipe.images.length > 1"
          class="absolute top-3 left-3 bg-black/50 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full"
        >
          📷 {{ recipe.images.length }}
        </div>

        <!-- Title on image -->
        <div class="absolute bottom-0 left-0 right-0 p-4">
          <h3 class="text-lg font-bold text-white drop-shadow-lg leading-tight">
            {{ recipe.name }}
          </h3>
        </div>
      </div>

      <!-- Info -->
      <div class="p-4">
        <p v-if="mainIngredients" class="text-xs text-gray-400 mb-3 truncate">
          {{ mainIngredients }}
        </p>
        <div class="flex items-center gap-1.5">
          <div class="flex flex-wrap gap-1.5 flex-1">
            <span
              v-for="tag in recipe.tags.slice(0, 3)"
              :key="tag.id"
              class="inline-block text-xs px-2.5 py-0.5 rounded-full bg-orange-50 text-orange-600 font-medium"
            >
              {{ tag.name }}
            </span>
          </div>
          <button
            class="shrink-0 inline-flex items-center gap-1 text-xs text-green-600 hover:text-green-700 bg-green-50 hover:bg-green-100 px-2.5 py-1 rounded-full transition-colors"
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
