<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Placeholder from '@tiptap/extension-placeholder'
import { watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '请输入内容...' },
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    Underline,
    Placeholder.configure({ placeholder: props.placeholder }),
  ],
  editorProps: {
    attributes: {
      class: 'tiptap-body',
    },
  },
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

watch(
  () => props.modelValue,
  (val) => {
    if (editor.value && val !== editor.value.getHTML()) {
      editor.value.commands.setContent(val, false)
    }
  }
)
</script>

<template>
  <div class="tiptap-wrap">
    <!-- Toolbar -->
    <div v-if="editor" class="tiptap-toolbar">
      <button
        v-for="item in [
          { action: () => editor.chain().focus().toggleBold().run(), active: editor.isActive('bold'), label: 'B', title: '加粗' },
          { action: () => editor.chain().focus().toggleItalic().run(), active: editor.isActive('italic'), label: 'I', title: '斜体', italic: true },
          { action: () => editor.chain().focus().toggleUnderline().run(), active: editor.isActive('underline'), label: 'U', title: '下划线', underline: true },
        ]"
        :key="item.label"
        :title="item.title"
        class="tiptap-btn"
        :class="{ active: item.active }"
        @click="item.action()"
      >
        <span :class="{ italic: item.italic, underline: item.underline }">{{ item.label }}</span>
      </button>

      <div class="tiptap-sep" />

      <button
        v-for="item in [
          { action: () => editor.chain().focus().toggleHeading({ level: 2 }).run(), active: editor.isActive('heading', { level: 2 }), label: 'H2' },
          { action: () => editor.chain().focus().toggleHeading({ level: 3 }).run(), active: editor.isActive('heading', { level: 3 }), label: 'H3' },
        ]"
        :key="item.label"
        class="tiptap-btn small"
        :class="{ active: item.active }"
        @click="item.action()"
      >
        {{ item.label }}
      </button>

      <div class="tiptap-sep" />

      <button
        v-for="item in [
          { action: () => editor.chain().focus().toggleBulletList().run(), active: editor.isActive('bulletList'), label: '•', title: '无序列表' },
          { action: () => editor.chain().focus().toggleOrderedList().run(), active: editor.isActive('orderedList'), label: '1.', title: '有序列表' },
        ]"
        :key="item.label"
        :title="item.title"
        class="tiptap-btn small"
        :class="{ active: item.active }"
        @click="item.action()"
      >
        {{ item.label }}
      </button>
    </div>

    <!-- Editor -->
    <EditorContent :editor="editor" />
  </div>
</template>

<style scoped>
.tiptap-wrap {
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  overflow: hidden;
  transition: all 0.15s;
}
.tiptap-wrap:focus-within {
  border-color: #fdba74;
  box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.15);
}

/* Toolbar */
.tiptap-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  padding: 0.5rem;
  border-bottom: 1px solid #f3f4f6;
  background: rgba(249, 250, 251, 0.5);
}
.tiptap-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  transition: all 0.15s;
  cursor: pointer;
  border: none;
  background: none;
}
.tiptap-btn:hover {
  background: #f3f4f6;
  color: #374151;
}
.tiptap-btn.active {
  background: #fff7ed;
  color: #ea580c;
}
.tiptap-btn.small {
  font-size: 0.75rem;
  font-weight: 700;
}
.tiptap-sep {
  width: 1px;
  height: 1.5rem;
  background: #e5e7eb;
  margin: 0 0.25rem;
  align-self: center;
}

/* Editor body */
.tiptap-wrap :deep(.tiptap-body) {
  max-width: none;
  outline: none;
  min-height: 120px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  line-height: 1.75;
}

/* Placeholder */
.tiptap-wrap :deep(p.is-editor-empty:first-child::before) {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

/* Paragraphs */
.tiptap-wrap :deep(p) {
  margin-bottom: 0.5em;
}

/* Headings */
.tiptap-wrap :deep(h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1em;
  margin-bottom: 0.5em;
}
.tiptap-wrap :deep(h3) {
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 0.75em;
  margin-bottom: 0.4em;
}

/* Unordered list */
.tiptap-wrap :deep(ul) {
  list-style-type: disc !important;
  padding-left: 1.5em !important;
  margin-bottom: 0.5em;
}

/* Ordered list */
.tiptap-wrap :deep(ol) {
  list-style-type: decimal !important;
  padding-left: 1.5em !important;
  margin-bottom: 0.5em;
}

/* List items */
.tiptap-wrap :deep(li) {
  display: list-item !important;
  margin-bottom: 0.25em;
}
.tiptap-wrap :deep(li p) {
  margin-bottom: 0.1em;
}

/* Nested lists */
.tiptap-wrap :deep(ul ul) {
  list-style-type: circle !important;
}
.tiptap-wrap :deep(ol ol) {
  list-style-type: lower-alpha !important;
}

/* Inline formatting */
.tiptap-wrap :deep(strong) {
  font-weight: 700;
}
.tiptap-wrap :deep(em) {
  font-style: italic;
}
.tiptap-wrap :deep(u) {
  text-decoration: underline;
}
</style>
