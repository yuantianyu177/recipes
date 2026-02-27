<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  content: { type: String, default: '' },
})

const html = computed(() => {
  if (!props.content) return ''
  return marked(props.content, { breaks: true })
})
</script>

<template>
  <div class="markdown-content" v-html="html" />
</template>

<style scoped>
.markdown-content {
  line-height: 1.9;
  font-size: 0.9375rem;
  color: var(--color-text, #3d3329);
  font-family: var(--font-body, 'Noto Serif SC', serif);
}
.markdown-content :deep(h1) { font-size: 1.5rem; font-weight: 700; margin: 1em 0 0.5em; font-family: var(--font-heading); }
.markdown-content :deep(h2) { font-size: 1.25rem; font-weight: 600; margin: 1em 0 0.5em; font-family: var(--font-heading); }
.markdown-content :deep(h3) { font-size: 1.1rem; font-weight: 600; margin: 0.75em 0 0.4em; font-family: var(--font-heading); }
.markdown-content :deep(p) { margin-bottom: 0.5em; }
.markdown-content :deep(ul) { list-style-type: disc !important; padding-left: 1.5em !important; margin-bottom: 0.5em; }
.markdown-content :deep(ol) { list-style-type: decimal !important; padding-left: 1.5em !important; margin-bottom: 0.5em; }
.markdown-content :deep(li) { display: list-item !important; margin-bottom: 0.25em; }
.markdown-content :deep(strong) { font-weight: 700; }
.markdown-content :deep(em) { font-style: italic; }
.markdown-content :deep(code) { background: var(--color-bg, #f5f0e8); padding: 0.15em 0.4em; border-radius: 0.25rem; font-size: 0.85em; }
.markdown-content :deep(pre) { background: var(--color-bg, #f5f0e8); padding: 1em; border-radius: 0.5rem; overflow-x: auto; margin-bottom: 0.5em; }
.markdown-content :deep(pre code) { background: none; padding: 0; }
.markdown-content :deep(blockquote) { border-left: 3px solid var(--color-primary, #c45d3e); padding-left: 1em; margin: 0.5em 0; color: var(--color-text-muted); }
.markdown-content :deep(img) { max-width: 100%; border-radius: 0.5rem; margin: 0.5em 0; }
.markdown-content :deep(hr) { border: none; border-top: 1px solid var(--color-border); margin: 1em 0; }
</style>
