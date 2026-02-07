/**
 * API client for backend communication.
 * All requests are proxied via Vite dev server -> FastAPI backend.
 */

const BASE = '/api'

function getAuthHeaders() {
  const token = localStorage.getItem('recipe_admin_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request(url, options = {}) {
  const resp = await fetch(BASE + url, {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options.headers,
    },
    ...options,
  })
  if (!resp.ok) {
    // Auto-redirect to login on 401
    if (resp.status === 401) {
      localStorage.removeItem('recipe_admin_token')
      if (window.location.pathname.startsWith('/admin')) {
        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname)
      }
    }
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    const error = new Error(err.detail || 'Request failed')
    error.status = resp.status
    throw error
  }
  if (resp.status === 204) return null
  return resp.json()
}

// ============== Auth ==============

export async function apiLogin(username, password) {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

// ============== Recipes ==============

export async function apiGetRecipes() {
  return request('/recipes')
}

export async function apiGetRecipe(id) {
  return request(`/recipes/${id}`)
}

export async function apiCreateRecipe(data) {
  return request('/recipes', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function apiUpdateRecipe(id, data) {
  return request(`/recipes/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function apiDeleteRecipe(id) {
  return request(`/recipes/${id}`, { method: 'DELETE' })
}

// ============== Tags ==============

export async function apiGetTags() {
  return request('/tags')
}

export async function apiCreateTag(data) {
  return request('/tags', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function apiUpdateTag(id, data) {
  return request(`/tags/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function apiDeleteTag(id) {
  return request(`/tags/${id}`, { method: 'DELETE' })
}

// ============== Ingredients ==============

export async function apiGetIngredients(q = '') {
  const params = q ? `?q=${encodeURIComponent(q)}` : ''
  return request(`/ingredients${params}`)
}

export async function apiCreateIngredient(data) {
  return request('/ingredients', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function apiUpdateIngredient(id, data) {
  return request(`/ingredients/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function apiDeleteIngredient(id) {
  return request(`/ingredients/${id}`, { method: 'DELETE' })
}

// ============== Tag Categories ==============

export async function apiGetTagCategories() {
  return request('/tags/categories')
}

export async function apiCreateTagCategory(data) {
  return request('/tags/categories', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function apiDeleteTagCategory(id) {
  return request(`/tags/categories/${id}`, { method: 'DELETE' })
}

// ============== Ingredient Categories ==============

export async function apiGetIngredientCategories() {
  return request('/ingredients/categories')
}

export async function apiCreateIngredientCategory(data) {
  return request('/ingredients/categories', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function apiDeleteIngredientCategory(id) {
  return request(`/ingredients/categories/${id}`, { method: 'DELETE' })
}

// ============== Search ==============

export async function apiSearch(q = '', tag = '', limit = 20) {
  const params = new URLSearchParams()
  if (q) params.set('q', q)
  if (tag) params.set('tag', tag)
  params.set('limit', limit)
  return request(`/search?${params}`)
}

// ============== Upload ==============

export async function apiUploadImage(recipeId, file) {
  const formData = new FormData()
  formData.append('file', file)
  const token = localStorage.getItem('recipe_admin_token')
  const resp = await fetch(`${BASE}/recipes/${recipeId}/images`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || 'Upload failed')
  }
  return resp.json()
}

export async function apiDeleteImage(imageId) {
  return request(`/images/${imageId}`, { method: 'DELETE' })
}

export async function apiReorderImages(recipeId, imageIds) {
  return request(`/recipes/${recipeId}/images/reorder`, {
    method: 'PUT',
    body: JSON.stringify({ image_ids: imageIds }),
  })
}

// ============== Import/Export ==============

export async function apiExportRecipeBatch(recipeIds) {
  const token = localStorage.getItem('recipe_admin_token')
  const resp = await fetch(`${BASE}/recipes/export-batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ recipe_ids: recipeIds }),
  })
  if (!resp.ok) throw new Error('Export failed')
  return resp.blob()
}

export async function apiImportRecipes(file) {
  const formData = new FormData()
  formData.append('file', file)
  const token = localStorage.getItem('recipe_admin_token')
  const resp = await fetch(`${BASE}/recipes/import`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || 'Import failed')
  }
  return resp.json()
}

// ============== Search Settings ==============

export async function apiSetupSearchIndex() {
  return request('/search/setup', { method: 'POST' })
}

export async function apiGetSynonyms() {
  return request('/search/synonyms')
}

export async function apiSetSynonyms(synonyms) {
  return request('/search/synonyms', {
    method: 'PUT',
    body: JSON.stringify(synonyms),
  })
}

// ============== Password ==============

export async function apiChangePassword(oldPassword, newPassword) {
  return request('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  })
}
