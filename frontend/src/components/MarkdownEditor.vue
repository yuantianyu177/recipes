<script setup>
import { ref, watch, computed } from 'vue'
import { marked } from 'marked'
import { apiUploadGeneralImage } from '../api/index'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const text = ref(props.modelValue)
const previewMode = ref(false)
const uploading = ref(false)
const textareaRef = ref(null)

watch(() => props.modelValue, (val) => {
  if (val !== text.value) text.value = val
})

watch(text, (val) => {
  emit('update:modelValue', val)
})

const previewHtml = computed(() => {
  if (!text.value) return ''
  return marked(text.value, { breaks: true })
})

function insertAtCursor(str) {
  const el = textareaRef.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  text.value = text.value.substring(0, start) + str + text.value.substring(end)
  // Restore cursor position after inserted text
  const pos = start + str.length
  requestAnimationFrame(() => {
    el.selectionStart = el.selectionEnd = pos
    el.focus()
  })
}

async function handleImageUpload() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*,.heic,.heif,.avif'
  input.multiple = true
  input.onchange = async (e) => {
    uploading.value = true
    try {
      for (const file of e.target.files) {
        const result = await apiUploadGeneralImage(file)
        insertAtCursor(`![${file.name}](${result.url})\n`)
      }
    } catch (err) {
      alert('Image upload failed: ' + (err.message || ''))
    } finally {
      uploading.value = false
    }
  }
  input.click()
}

async function handlePaste(e) {
  const items = e.clipboardData?.items
  if (!items) return
  const imageFiles = []
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      imageFiles.push(item.getAsFile())
    }
  }
  if (imageFiles.length === 0) return
  e.preventDefault()
  uploading.value = true
  try {
    for (const file of imageFiles) {
      const result = await apiUploadGeneralImage(file)
      insertAtCursor(`![image](${result.url})\n`)
    }
  } catch (err) {
    alert('Image upload failed: ' + (err.message || ''))
  } finally {
    uploading.value = false
  }
}

async function handleDrop(e) {
  const files = e.dataTransfer?.files
  if (!files) return
  const imageFiles = Array.from(files).filter(f => f.type.startsWith('image/'))
  if (imageFiles.length === 0) return
  e.preventDefault()
  uploading.value = true
  try {
    for (const file of imageFiles) {
      const result = await apiUploadGeneralImage(file)
      insertAtCursor(`![${file.name}](${result.url})\n`)
    }
  } catch (err) {
    alert('Image upload failed: ' + (err.message || ''))
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="md-editor-wrap">
    <!-- Toolbar -->
    <div class="md-toolbar">
      <button
        class="md-tab"
        :class="{ active: !previewMode }"
        @click="previewMode = false"
      >编辑</button>
      <button
        class="md-tab"
        :class="{ active: previewMode }"
        @click="previewMode = true"
      >预览</button>
      <div style="flex: 1;" />
      <button
        v-if="!previewMode"
        class="md-btn"
        title="插入图片"
        :disabled="uploading"
        @click="handleImageUpload"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span v-if="uploading" class="text-xs ml-1">上传中...</span>
      </button>
    </div>

    <!-- Edit mode -->
    <textarea
      v-if="!previewMode"
      ref="textareaRef"
      v-model="text"
      :placeholder="placeholder"
      class="md-textarea"
      @paste="handlePaste"
      @drop.prevent="handleDrop"
      @dragover.prevent
    />

    <!-- Preview mode -->
    <div
      v-else
      class="md-preview rich-content"
      v-html="previewHtml"
    />
  </div>
</template>

<style scoped>
.md-editor-wrap {
  border: 1px solid var(--color-border, #e5ddd1);
  border-radius: 0.75rem;
  overflow: hidden;
  background: var(--color-card, #fffdf8);
  transition: all 0.15s;
}
.md-editor-wrap:focus-within {
  border-color: var(--color-primary, #c45d3e);
  box-shadow: 0 0 0 2px rgba(196, 93, 62, 0.12);
}

.md-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 0.375rem 0.5rem;
  border-bottom: 1px solid var(--color-border, #e5ddd1);
  background: var(--color-bg, #f5f0e8);
}

.md-tab {
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-muted, #8c7e6f);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
  font-family: var(--font-ui);
}
.md-tab:hover {
  color: var(--color-text, #3d3329);
}
.md-tab.active {
  background: var(--color-card, #fffdf8);
  color: var(--color-primary, #c45d3e);
  font-weight: 600;
}

.md-btn {
  display: flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  color: var(--color-text-muted, #8c7e6f);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.md-btn:hover {
  background: var(--color-card, #fffdf8);
  color: var(--color-primary, #c45d3e);
}
.md-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.md-textarea {
  width: 100%;
  min-height: 200px;
  padding: 0.75rem 1rem;
  border: none;
  outline: none;
  resize: vertical;
  font-size: 0.875rem;
  line-height: 1.75;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  color: var(--color-text, #3d3329);
  background: transparent;
}
.md-textarea::placeholder {
  color: var(--color-text-muted, #8c7e6f);
  opacity: 0.5;
}

.md-preview {
  min-height: 200px;
  padding: 0.75rem 1rem;
  font-size: 0.9375rem;
  line-height: 1.9;
  font-family: var(--font-body, 'Noto Serif SC', serif);
  color: var(--color-text, #3d3329);
}

/* Markdown rendered content */
.md-preview :deep(h1) { font-size: 1.5rem; font-weight: 700; margin: 1em 0 0.5em; font-family: var(--font-heading); }
.md-preview :deep(h2) { font-size: 1.25rem; font-weight: 600; margin: 1em 0 0.5em; font-family: var(--font-heading); }
.md-preview :deep(h3) { font-size: 1.1rem; font-weight: 600; margin: 0.75em 0 0.4em; font-family: var(--font-heading); }
.md-preview :deep(p) { margin-bottom: 0.5em; }
.md-preview :deep(ul) { list-style-type: disc !important; padding-left: 1.5em !important; margin-bottom: 0.5em; }
.md-preview :deep(ol) { list-style-type: decimal !important; padding-left: 1.5em !important; margin-bottom: 0.5em; }
.md-preview :deep(li) { display: list-item !important; margin-bottom: 0.25em; }
.md-preview :deep(strong) { font-weight: 700; }
.md-preview :deep(em) { font-style: italic; }
.md-preview :deep(code) { background: var(--color-bg, #f5f0e8); padding: 0.15em 0.4em; border-radius: 0.25rem; font-size: 0.85em; }
.md-preview :deep(pre) { background: var(--color-bg, #f5f0e8); padding: 1em; border-radius: 0.5rem; overflow-x: auto; margin-bottom: 0.5em; }
.md-preview :deep(pre code) { background: none; padding: 0; }
.md-preview :deep(blockquote) { border-left: 3px solid var(--color-primary, #c45d3e); padding-left: 1em; margin: 0.5em 0; color: var(--color-text-muted); }
.md-preview :deep(img) { max-width: 100%; border-radius: 0.5rem; margin: 0.5em 0; }
.md-preview :deep(hr) { border: none; border-top: 1px solid var(--color-border); margin: 1em 0; }
</style>
