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
      class: 'prose max-w-none focus:outline-none min-h-[120px] px-4 py-3 text-sm',
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
  <div class="border border-gray-200 rounded-xl overflow-hidden focus-within:border-orange-300 focus-within:ring-2 focus-within:ring-orange-100 transition-all">
    <!-- Toolbar -->
    <div v-if="editor" class="flex flex-wrap gap-0.5 p-2 border-b border-gray-100 bg-gray-50/50">
      <button
        v-for="item in [
          { action: () => editor.chain().focus().toggleBold().run(), active: editor.isActive('bold'), label: 'B', title: '加粗' },
          { action: () => editor.chain().focus().toggleItalic().run(), active: editor.isActive('italic'), label: 'I', title: '斜体', italic: true },
          { action: () => editor.chain().focus().toggleUnderline().run(), active: editor.isActive('underline'), label: 'U', title: '下划线', underline: true },
        ]"
        :key="item.label"
        :title="item.title"
        class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold transition-colors"
        :class="item.active ? 'bg-orange-100 text-orange-600' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'"
        @click="item.action()"
      >
        <span :class="{ italic: item.italic, underline: item.underline }">{{ item.label }}</span>
      </button>

      <div class="w-px h-6 bg-gray-200 mx-1 self-center" />

      <button
        v-for="item in [
          { action: () => editor.chain().focus().toggleHeading({ level: 2 }).run(), active: editor.isActive('heading', { level: 2 }), label: 'H2' },
          { action: () => editor.chain().focus().toggleHeading({ level: 3 }).run(), active: editor.isActive('heading', { level: 3 }), label: 'H3' },
        ]"
        :key="item.label"
        class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold transition-colors"
        :class="item.active ? 'bg-orange-100 text-orange-600' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'"
        @click="item.action()"
      >
        {{ item.label }}
      </button>

      <div class="w-px h-6 bg-gray-200 mx-1 self-center" />

      <button
        v-for="item in [
          { action: () => editor.chain().focus().toggleBulletList().run(), active: editor.isActive('bulletList'), label: '•', title: '无序列表' },
          { action: () => editor.chain().focus().toggleOrderedList().run(), active: editor.isActive('orderedList'), label: '1.', title: '有序列表' },
        ]"
        :key="item.label"
        :title="item.title"
        class="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold transition-colors"
        :class="item.active ? 'bg-orange-100 text-orange-600' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'"
        @click="item.action()"
      >
        {{ item.label }}
      </button>
    </div>

    <!-- Editor -->
    <EditorContent :editor="editor" />
  </div>
</template>
