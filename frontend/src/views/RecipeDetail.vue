<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRecipeStore } from '../stores/recipe'
import ShareModal from '../components/ShareModal.vue'
import MarkdownContent from '../components/MarkdownContent.vue'

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
  <!-- ===== RECIPE LOADED ===== -->
  <div v-if="recipe" class="recipe-detail">

    <!-- Floating top bar: back + share -->
    <div class="detail-topbar animate-fade-in-up">
      <button class="topbar-btn" @click="router.back()">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        <span>返回</span>
      </button>
      <button class="topbar-btn" @click="handleShare">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
        </svg>
        <span>分享</span>
      </button>
    </div>

    <!-- ===== HERO: Full-width image carousel ===== -->
    <section
      v-if="imageList.length > 0"
      class="hero-carousel group animate-fade-in-up"
    >
      <div class="hero-carousel-inner">
        <transition name="fade" mode="out-in">
          <img
            :key="currentSlide"
            :src="imageList[currentSlide]"
            :alt="recipe.name"
            class="hero-carousel-img"
          />
        </transition>

        <!-- Gradient overlay for text legibility -->
        <div class="hero-gradient-bottom"></div>

        <!-- Carousel arrows -->
        <template v-if="imageCount > 1">
          <button class="carousel-arrow carousel-arrow-left" @click="prevSlide">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
          </button>
          <button class="carousel-arrow carousel-arrow-right" @click="nextSlide">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          </button>
        </template>

        <!-- Image counter + dots -->
        <div class="hero-carousel-controls">
          <span v-if="imageCount > 1" class="image-counter">
            {{ currentSlide + 1 }} / {{ imageCount }}
          </span>
          <div v-if="imageCount > 1" class="flex gap-2">
            <button
              v-for="(_, idx) in imageList"
              :key="idx"
              class="carousel-dot"
              :class="{ 'carousel-dot-active': idx === currentSlide }"
              @click="goToSlide(idx)"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- ===== EDITORIAL HEADER ===== -->
    <section class="editorial-header animate-fade-in-up">
      <!-- Category label -->
      <div class="editorial-label">
        <span class="deco-line"></span>
        <span class="label-text">菜谱详情</span>
        <span class="deco-line"></span>
      </div>

      <!-- Recipe title -->
      <h1 class="editorial-title">{{ recipe.name }}</h1>

      <!-- Tags + calories row -->
      <div class="meta-row">
        <span
          v-for="tag in recipe.tags"
          :key="tag.id"
          class="meta-tag"
          :style="tag.color ? { background: tag.color + '1a', color: tag.color } : {}"
          :class="!tag.color ? (tag.id % 2 === 0 ? 'meta-tag-secondary' : 'meta-tag-primary') : ''"
        >
          {{ tag.name }}
        </span>
        <span v-if="calories > 0" class="meta-tag meta-tag-accent">
          {{ calories }} kcal
        </span>
      </div>
    </section>

    <!-- Elegant divider -->
    <div class="elegant-divider">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <path d="M12 4L14.5 9.5L20 12L14.5 14.5L12 20L9.5 14.5L4 12L9.5 9.5L12 4Z" fill="var(--color-primary)" opacity="0.3"/>
      </svg>
    </div>

    <!-- ===== DESCRIPTION — drop-cap editorial style ===== -->
    <section v-if="recipe.description" class="description-section animate-fade-in-up">
      <div class="description-card">
        <p class="description-text drop-cap">{{ recipe.description }}</p>
      </div>
    </section>

    <!-- ===== INGREDIENTS — Magazine spread ===== -->
    <section class="ingredients-section animate-fade-in-up">
      <div class="section-label">
        <span class="section-label-line"></span>
        <h2 class="section-label-text">食材清单</h2>
        <span class="section-label-line"></span>
      </div>

      <div class="ingredients-grid">
        <div
          v-for="(category, catIdx) in sortedCategories"
          :key="category"
          class="ingredient-group"
          :class="[
            catIdx === 0 ? 'ingredient-group-primary' : '',
            catIdx === 1 ? 'ingredient-group-secondary' : '',
            catIdx >= 2 ? 'ingredient-group-accent' : ''
          ]"
        >
          <!-- Category header with decorative number -->
          <div class="ingredient-group-header">
            <span class="ingredient-group-number">{{ String(catIdx + 1).padStart(2, '0') }}</span>
            <h3 class="ingredient-group-title">{{ category }}</h3>
          </div>

          <!-- Ingredient rows -->
          <div class="ingredient-rows">
            <div
              v-for="(item, idx) in ingredientGroups[category]"
              :key="item.id"
              class="ingredient-row"
            >
              <span class="ingredient-name">{{ item.name }}</span>
              <span class="ingredient-dots"></span>
              <span class="ingredient-amount">{{ item.amount }}{{ item.unit }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Wavy divider -->
    <div class="wavy-divider mx-auto" style="max-width: 200px;"></div>

    <!-- ===== STEPS — Editorial column ===== -->
    <section class="steps-section animate-fade-in-up">
      <div class="section-label">
        <span class="section-label-line"></span>
        <h2 class="section-label-text">烹饪步骤</h2>
        <span class="section-label-line"></span>
      </div>

      <div class="steps-card">
        <div class="steps-accent-bar"></div>
        <div class="steps-content">
          <MarkdownContent :content="recipe.steps" />
        </div>
      </div>
    </section>

    <!-- ===== TIPS — Pull-quote style ===== -->
    <section v-if="recipe.tips" class="tips-section animate-fade-in-up">
      <div class="tips-card">
        <div class="tips-icon-wrapper">
          <svg class="tips-icon" viewBox="0 0 24 24" fill="none">
            <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke="var(--color-accent)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="tips-label">小贴士</div>
        <p class="tips-text">{{ recipe.tips }}</p>
      </div>
    </section>

    <!-- Bottom flourish -->
    <div class="bottom-flourish animate-fade-in-up">
      <div class="flourish-line"></div>
      <span class="flourish-text">Bon Appetit</span>
      <div class="flourish-line"></div>
    </div>
  </div>

  <!-- ===== LOADING ===== -->
  <div v-else-if="loadingDetail" class="loading-state">
    <div class="spinner-warm"></div>
    <span class="loading-text">加载中...</span>
  </div>

  <!-- ===== NOT FOUND ===== -->
  <div v-else class="not-found-state animate-fade-in-up">
    <svg class="mx-auto mb-6" width="100" height="85" viewBox="0 0 100 85" fill="none">
      <ellipse cx="50" cy="70" rx="35" ry="5" fill="var(--color-border)" opacity="0.4"/>
      <ellipse cx="50" cy="42" rx="30" ry="26" stroke="var(--color-text-muted)" stroke-width="1.5" fill="var(--color-card)" stroke-linecap="round"/>
      <ellipse cx="50" cy="40" rx="20" ry="16" stroke="var(--color-border)" stroke-width="1" fill="none" stroke-dasharray="4 3"/>
      <path d="M40 38Q48 32 50 38Q52 32 60 38" stroke="var(--color-text-muted)" stroke-width="1.2" fill="none" stroke-linecap="round" opacity="0.6"/>
      <path d="M42 48Q50 52 58 48" stroke="var(--color-text-muted)" stroke-width="1.2" fill="none" stroke-linecap="round" opacity="0.4"/>
    </svg>
    <p class="not-found-title">菜谱不存在</p>
    <p class="not-found-desc">可能已被删除或链接有误</p>
    <button class="btn-ghost btn-sm mt-5" @click="router.push('/')">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0h4"/>
      </svg>
      返回首页
    </button>
  </div>

  <!-- Share Modal -->
  <ShareModal :show="showShareModal" :recipe="recipe" @close="showShareModal = false" />
</template>

<style scoped>
/* ===== Page Container ===== */
.recipe-detail {
  max-width: 52rem;
  margin: 0 auto;
  padding-bottom: 4rem;
}

/* ===== Top Bar ===== */
.detail-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
}
.topbar-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-size: 0.8125rem;
  font-weight: 500;
  font-family: var(--font-ui);
  color: var(--color-text-muted);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.topbar-btn:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: 0 2px 10px rgba(196, 93, 62, 0.12);
  transform: translateY(-1px);
}

/* ===== Hero Carousel ===== */
.hero-carousel {
  margin-bottom: 3rem;
  border-radius: 1.25rem;
  overflow: hidden;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  box-shadow: 0 8px 40px rgba(61, 51, 41, 0.1);
  padding: 0.25rem;
}
.hero-carousel-inner {
  position: relative;
  border-radius: 0.875rem;
  overflow: hidden;
  aspect-ratio: 16 / 10;
}
.hero-carousel-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 8s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.hero-carousel:hover .hero-carousel-img {
  transform: scale(1.04);
}
.hero-gradient-bottom {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: linear-gradient(to top, rgba(61, 51, 41, 0.35), transparent);
  pointer-events: none;
}

/* Carousel arrows */
.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 253, 248, 0.9);
  color: var(--color-text);
  border: 1px solid rgba(229, 221, 209, 0.6);
  opacity: 0;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 16px rgba(61, 51, 41, 0.12);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.carousel-arrow-left { left: 1.25rem; }
.carousel-arrow-right { right: 1.25rem; }
.group:hover .carousel-arrow { opacity: 1; }
.carousel-arrow:hover {
  background: var(--color-card);
  border-color: var(--color-primary);
  color: var(--color-primary);
  transform: translateY(-50%) scale(1.1);
}

/* Carousel controls */
.hero-carousel-controls {
  position: absolute;
  bottom: 1.25rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 253, 248, 0.85);
  border-radius: 999px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(229, 221, 209, 0.4);
}
.image-counter {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  letter-spacing: 0.05em;
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

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.6s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ===== Editorial Header ===== */
.editorial-header {
  text-align: center;
  padding: 0 1rem 2.5rem;
}
.editorial-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.label-text {
  font-size: 0.7rem;
  letter-spacing: 0.3em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  font-weight: 500;
  font-family: var(--font-ui);
}
.deco-line {
  width: 40px;
  height: 1px;
  background: var(--color-primary);
  opacity: 0.5;
}
.editorial-title {
  font-family: var(--font-heading);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--color-text);
  margin-bottom: 1.5rem;
}
.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}
.meta-tag {
  display: inline-flex;
  align-items: center;
  font-size: 0.75rem;
  padding: 0.3rem 0.875rem;
  border-radius: 999px;
  font-weight: 500;
  font-family: var(--font-ui);
  transition: transform 0.2s ease;
}
.meta-tag:hover { transform: translateY(-1px); }
.meta-tag-primary {
  background: rgba(196, 93, 62, 0.1);
  color: var(--color-primary);
}
.meta-tag-secondary {
  background: rgba(91, 122, 94, 0.1);
  color: var(--color-secondary);
}
.meta-tag-accent {
  background: var(--color-accent-light);
  color: var(--color-accent);
}

/* ===== Elegant Divider ===== */
.elegant-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 1rem 0 2.5rem;
}
.elegant-divider::before,
.elegant-divider::after {
  content: '';
  flex: 1;
  max-width: 120px;
  height: 1px;
  background: var(--color-border);
}

/* ===== Description ===== */
.description-section {
  max-width: 40rem;
  margin: 0 auto 3rem;
  padding: 0 1rem;
}
.description-card {
  position: relative;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
  padding: 2rem 2.5rem;
  box-shadow: 0 2px 12px rgba(61, 51, 41, 0.04);
}
.description-card::before {
  content: '\201C';
  position: absolute;
  top: -0.25rem;
  left: 1.25rem;
  font-family: var(--font-heading);
  font-size: 4rem;
  line-height: 1;
  color: var(--color-primary);
  opacity: 0.15;
}
.description-text {
  font-family: var(--font-body);
  font-size: 1rem;
  line-height: 2;
  color: var(--color-text);
}
.drop-cap::first-letter {
  float: left;
  font-family: var(--font-heading);
  font-size: 3.5rem;
  line-height: 0.75;
  padding-right: 0.625rem;
  padding-top: 0.3rem;
  color: var(--color-primary);
  font-weight: 700;
}

/* ===== Section Label ===== */
.section-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.25rem;
  margin-bottom: 2rem;
}
.section-label-line {
  flex: 1;
  max-width: 80px;
  height: 1px;
  background: var(--color-border);
}
.section-label-text {
  font-family: var(--font-heading);
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: 0.05em;
}

/* ===== Ingredients ===== */
.ingredients-section {
  margin-bottom: 3rem;
}
.ingredients-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.25rem;
}
.ingredient-group {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
  padding: 1.75rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.ingredient-group::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
}
.ingredient-group-primary::before { background: var(--color-primary); }
.ingredient-group-secondary::before { background: var(--color-secondary); }
.ingredient-group-accent::before { background: var(--color-accent); }
.ingredient-group:hover {
  box-shadow: 0 8px 30px rgba(61, 51, 41, 0.08);
  transform: translateY(-3px);
}
.ingredient-group-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border);
}
.ingredient-group-number {
  font-family: var(--font-heading);
  font-size: 1.75rem;
  font-weight: 700;
  opacity: 0.12;
  line-height: 1;
}
.ingredient-group-title {
  font-size: 0.8125rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}
.ingredient-rows {
  display: flex;
  flex-direction: column;
}
.ingredient-row {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  padding: 0.5rem 0;
}
.ingredient-name {
  font-size: 0.875rem;
  color: var(--color-text);
  font-family: var(--font-body);
  white-space: nowrap;
}
.ingredient-dots {
  flex: 1;
  border-bottom: 1px dotted var(--color-border);
  min-width: 1rem;
  margin-bottom: 0.25rem;
}
.ingredient-amount {
  font-size: 0.8125rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* ===== Steps ===== */
.steps-section {
  margin: 3rem 0;
}
.steps-card {
  position: relative;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(61, 51, 41, 0.04);
}
.steps-accent-bar {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(to bottom, var(--color-primary), var(--color-accent));
  border-radius: 4px 0 0 4px;
}
.steps-content {
  padding: 2.5rem 2.5rem 2.5rem 3rem;
  font-family: var(--font-body);
  line-height: 2;
  color: var(--color-text);
}

/* ===== Tips ===== */
.tips-section {
  margin-bottom: 3rem;
  max-width: 40rem;
  margin-left: auto;
  margin-right: auto;
}
.tips-card {
  position: relative;
  text-align: center;
  padding: 2.5rem 2rem;
  background: linear-gradient(135deg, var(--color-accent-light), rgba(240, 228, 200, 0.3));
  border: 1px solid var(--color-accent);
  border-radius: 1rem;
  overflow: hidden;
}
.tips-card::before {
  content: '';
  position: absolute;
  top: -30px;
  right: -30px;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--color-accent);
  opacity: 0.06;
}
.tips-card::after {
  content: '';
  position: absolute;
  bottom: -20px;
  left: -20px;
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: var(--color-accent);
  opacity: 0.04;
}
.tips-icon-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}
.tips-icon {
  width: 2rem;
  height: 2rem;
}
.tips-label {
  font-size: 0.7rem;
  letter-spacing: 0.25em;
  text-transform: uppercase;
  color: var(--color-accent);
  font-weight: 600;
  font-family: var(--font-ui);
  margin-bottom: 1rem;
}
.tips-text {
  font-family: var(--font-body);
  font-size: 0.9375rem;
  line-height: 2;
  color: var(--color-text);
  position: relative;
  z-index: 1;
}

/* ===== Bottom Flourish ===== */
.bottom-flourish {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  padding: 2rem 0 1rem;
}
.flourish-line {
  width: 60px;
  height: 1px;
  background: var(--color-border);
}
.flourish-text {
  font-family: var(--font-heading);
  font-size: 0.875rem;
  font-style: italic;
  color: var(--color-text-muted);
  opacity: 0.5;
  letter-spacing: 0.1em;
}

/* ===== Loading State ===== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8rem 0;
  gap: 1rem;
}
.loading-text {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  font-family: var(--font-ui);
}

/* ===== Not Found ===== */
.not-found-state {
  text-align: center;
  padding: 6rem 0;
}
.not-found-title {
  font-size: 1.25rem;
  color: var(--color-text-muted);
  font-family: var(--font-heading);
  margin-bottom: 0.5rem;
}
.not-found-desc {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  font-family: var(--font-ui);
}

/* ===== Mobile Responsive ===== */
@media (max-width: 767px) {
  .recipe-detail {
    padding-bottom: 2rem;
  }
  .hero-carousel {
    margin-left: -0.5rem;
    margin-right: -0.5rem;
    border-radius: 0.75rem;
    padding: 0.1875rem;
  }
  .hero-carousel-inner {
    aspect-ratio: 4 / 3;
    border-radius: 0.5rem;
  }
  .editorial-header {
    padding: 0 0 2rem;
  }
  .editorial-title {
    font-size: 1.75rem;
  }
  .description-card {
    padding: 1.5rem;
  }
  .description-card::before {
    font-size: 3rem;
    left: 0.75rem;
  }
  .ingredients-grid {
    grid-template-columns: 1fr;
  }
  .ingredient-group {
    padding: 1.25rem;
  }
  .steps-content {
    padding: 1.5rem 1.5rem 1.5rem 2rem;
  }
  .tips-card {
    padding: 2rem 1.5rem;
  }
  .carousel-arrow {
    width: 2rem;
    height: 2rem;
  }
  .carousel-arrow-left { left: 0.75rem; }
  .carousel-arrow-right { right: 0.75rem; }
  .hero-carousel-controls {
    padding: 0.375rem 0.75rem;
    gap: 0.75rem;
  }
}

@media (max-width: 480px) {
  .detail-topbar {
    margin-bottom: 1.25rem;
  }
  .topbar-btn span {
    display: none;
  }
  .topbar-btn {
    padding: 0.5rem;
    border-radius: 50%;
  }
  .editorial-title {
    font-size: 1.5rem;
  }
  .section-label-text {
    font-size: 1.125rem;
  }
}
</style>
