import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  apiGetRecipes, apiGetRecipe, apiCreateRecipe, apiUpdateRecipe, apiDeleteRecipe,
  apiGetTags, apiCreateTag, apiDeleteTag,
  apiGetIngredients, apiCreateIngredient, apiUpdateIngredient, apiDeleteIngredient,
  apiSearch,
  apiGetTagCategories, apiCreateTagCategory, apiDeleteTagCategory,
  apiGetIngredientCategories, apiCreateIngredientCategory, apiDeleteIngredientCategory,
} from '../api/index'

export const useRecipeStore = defineStore('recipe', () => {
  const recipes = ref([])
  const tags = ref([])
  const ingredients = ref([])
  const loading = ref(false)

  // API-backed categories
  const tagCategories = ref([])
  const ingredientCategories = ref([])

  // --- Computed ---

  const getRecipeById = computed(() => {
    return (id) => recipes.value.find((r) => r.id === Number(id))
  })

  const getTagsByCategory = computed(() => {
    const grouped = {}
    tags.value.forEach((tag) => {
      const cat = tag.category || '未分类'
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push(tag)
    })
    return grouped
  })

  // --- Fetch data from API ---

  async function fetchRecipes() {
    loading.value = true
    try {
      recipes.value = await apiGetRecipes()
    } catch (err) {
      console.error('Failed to fetch recipes:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchRecipeById(id) {
    try {
      return await apiGetRecipe(id)
    } catch (err) {
      console.error('Failed to fetch recipe:', err)
      return null
    }
  }

  async function fetchTags() {
    try {
      tags.value = await apiGetTags()
    } catch (err) {
      console.error('Failed to fetch tags:', err)
    }
  }

  async function fetchIngredients() {
    try {
      ingredients.value = await apiGetIngredients()
    } catch (err) {
      console.error('Failed to fetch ingredients:', err)
    }
  }

  async function fetchTagCategories() {
    try {
      tagCategories.value = await apiGetTagCategories()
    } catch (err) {
      console.error('Failed to fetch tag categories:', err)
    }
  }

  async function fetchIngredientCategories() {
    try {
      ingredientCategories.value = await apiGetIngredientCategories()
    } catch (err) {
      console.error('Failed to fetch ingredient categories:', err)
    }
  }

  async function fetchAll() {
    await Promise.all([
      fetchRecipes(), fetchTags(), fetchIngredients(),
      fetchTagCategories(), fetchIngredientCategories(),
    ])
  }

  // --- Calorie calculation ---

  function calcCalories(recipe) {
    if (!recipe || !recipe.ingredients) return 0
    let total = 0
    for (const ri of recipe.ingredients) {
      const num = parseFloat(ri.amount)
      const cal = ri.ingredient_calorie ?? ri.calorie ?? 0
      if (!isNaN(num) && cal) {
        total += num * cal
      }
    }
    return Math.round(total)
  }

  // --- Search (via MeiliSearch API) ---

  async function searchRecipes(keyword, selectedTags = []) {
    if (!keyword && selectedTags.length === 0) return [...recipes.value]
    let result = recipes.value
    if (keyword) {
      try {
        const searchResult = await apiSearch(keyword)
        const hitIds = new Set(searchResult.hits.map((h) => h.id))
        result = result.filter((r) => hitIds.has(r.id))
      } catch (err) {
        const kw = keyword.toLowerCase()
        result = result.filter((r) => {
          const t = r.name.toLowerCase()
          let ti = 0
          for (let qi = 0; qi < kw.length; qi++) {
            const idx = t.indexOf(kw[qi], ti)
            if (idx === -1) return false
            ti = idx + 1
          }
          return true
        })
      }
    }
    if (selectedTags.length > 0) {
      result = result.filter((r) =>
        selectedTags.every((t) => r.tags.some((rt) => rt.name === t))
      )
    }
    return result
  }

  // --- Recipe CRUD ---

  async function addRecipe(data) {
    const created = await apiCreateRecipe(data)
    await fetchRecipes()
    return created.id
  }

  async function updateRecipe(id, data) {
    await apiUpdateRecipe(id, data)
    await fetchRecipes()
  }

  async function deleteRecipe(id) {
    await apiDeleteRecipe(id)
    recipes.value = recipes.value.filter((r) => r.id !== Number(id))
  }

  // --- Tag CRUD ---

  async function addTag(tag) {
    const created = await apiCreateTag(tag)
    tags.value.push(created)
    return created
  }

  async function deleteTag(id) {
    await apiDeleteTag(id)
    tags.value = tags.value.filter((t) => t.id !== Number(id))
  }

  // --- Ingredient CRUD ---

  async function addIngredient(ingredient) {
    const created = await apiCreateIngredient(ingredient)
    ingredients.value.push(created)
    return created
  }

  async function updateIngredient(id, data) {
    const updated = await apiUpdateIngredient(id, data)
    const idx = ingredients.value.findIndex((i) => i.id === Number(id))
    if (idx !== -1) ingredients.value[idx] = updated
    return updated
  }

  async function deleteIngredient(id) {
    await apiDeleteIngredient(id)
    ingredients.value = ingredients.value.filter((i) => i.id !== Number(id))
  }

  // --- Tag Category management (API-backed) ---

  async function addTagCategory(name) {
    const created = await apiCreateTagCategory({ name })
    tagCategories.value.push(created)
    return created
  }

  async function deleteTagCategory(id) {
    await apiDeleteTagCategory(id)
    tagCategories.value = tagCategories.value.filter((c) => c.id !== Number(id))
  }

  // --- Ingredient Category management (API-backed) ---

  async function addIngredientCategory(name) {
    const created = await apiCreateIngredientCategory({ name })
    ingredientCategories.value.push(created)
    return created
  }

  async function deleteIngredientCategory(id) {
    await apiDeleteIngredientCategory(id)
    ingredientCategories.value = ingredientCategories.value.filter((c) => c.id !== Number(id))
  }

  return {
    recipes,
    tags,
    ingredients,
    loading,
    ingredientCategories,
    tagCategories,
    getRecipeById,
    getTagsByCategory,
    fetchRecipes,
    fetchRecipeById,
    fetchTags,
    fetchIngredients,
    fetchTagCategories,
    fetchIngredientCategories,
    fetchAll,
    calcCalories,
    searchRecipes,
    addRecipe,
    updateRecipe,
    deleteRecipe,
    addTag,
    deleteTag,
    addIngredient,
    updateIngredient,
    deleteIngredient,
    addTagCategory,
    deleteTagCategory,
    addIngredientCategory,
    deleteIngredientCategory,
  }
})
