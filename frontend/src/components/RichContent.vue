<script setup>
defineProps({
  html: { type: String, default: '' },
})
</script>

<template>
  <div class="rich-content" v-html="html" />
</template>

<style scoped>
.rich-content {
  line-height: 1.9;
  font-size: 0.9375rem;
  color: var(--color-text, #3d3329);
  font-family: var(--font-body, 'Noto Serif SC', serif);
}

/* Paragraphs */
.rich-content :deep(p) {
  margin-bottom: 0.5em;
}

/* Headings */
.rich-content :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0.5em;
  font-family: var(--font-heading, 'Playfair Display', serif);
}
.rich-content :deep(h3) {
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 0.75em;
  margin-bottom: 0.4em;
  font-family: var(--font-heading, 'Playfair Display', serif);
}

/* Unordered list */
.rich-content :deep(ul) {
  list-style-type: disc !important;
  padding-left: 1.5em !important;
  margin-bottom: 0.5em;
}

/* Ordered list */
.rich-content :deep(ol) {
  list-style-type: decimal !important;
  padding-left: 1.5em !important;
  margin-bottom: 0.5em;
}

/* List items */
.rich-content :deep(li) {
  display: list-item !important;
  margin-bottom: 0.25em;
}

/* Nested lists */
.rich-content :deep(ul ul) {
  list-style-type: circle !important;
}
.rich-content :deep(ul ul ul) {
  list-style-type: square !important;
}
.rich-content :deep(ol ol) {
  list-style-type: lower-alpha !important;
}

/* Inline formatting */
.rich-content :deep(strong) {
  font-weight: 700;
}
.rich-content :deep(em) {
  font-style: italic;
}
.rich-content :deep(u) {
  text-decoration: underline;
}
</style>
