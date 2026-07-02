<template>
  <div class="collapsible-editor-container">
    <div class="editor-scroll-wrapper custom-scroll">
      <div 
        ref="editorRef"
        class="editor-content"
        :class="{ 'focus-mask-active': isFocusMode }"
        contenteditable="true"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '输入内容...'
  },
  isFocusMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const editorRef = ref(null)
const isInternalUpdate = ref(false)
const collapsedImages = ref(new Set())

const imageRegex = /!\[([^\]]*)\]\((data:image\/[^)]+)\)/g

const renderContent = (content) => {
  let html = ''
  let lastIndex = 0
  let match
  
  while ((match = imageRegex.exec(content)) !== null) {
    const beforeText = content.substring(lastIndex, match.index)
    if (beforeText) {
      html += escapeHtml(beforeText).replace(/\n/g, '<br>')
    }
    
    const altText = match[1]
    const imageData = match[2]
    const imageId = `img_${lastIndex}`
    
    const isCollapsed = collapsedImages.value.has(imageId)
    
    html += `<span class="image-wrapper" data-image-id="${imageId}" data-alt="${escapeHtml(altText)}" data-url="${escapeHtml(imageData)}">`
    html += `<span class="collapse-btn" contenteditable="false">${isCollapsed ? '▶' : '▼'}</span>`
    html += `<span class="image-alt">![${escapeHtml(altText)}]</span>`
    if (!isCollapsed) {
      html += `<span class="image-url">(${escapeHtml(imageData)})</span>`
    }
    html += `</span>`
    
    lastIndex = match.index + match[0].length
  }
  
  const remainingText = content.substring(lastIndex)
  if (remainingText) {
    html += escapeHtml(remainingText).replace(/\n/g, '<br>')
  }
  
  return html || `<span class="placeholder">${escapeHtml(props.placeholder)}</span>`
}

const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

const getContentFromHtml = () => {
  const editor = editorRef.value
  if (!editor) return ''
  
  let text = ''
  const walkNodes = (node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      text += node.textContent
    } else if (node.classList?.contains('image-wrapper')) {
      const alt = node.getAttribute('data-alt')
      const url = node.getAttribute('data-url')
      text += `![${alt}](${url})`
    } else if (node.nodeName === 'BR') {
      text += '\n'
    } else if (node.childNodes) {
      for (let child of node.childNodes) {
        walkNodes(child)
      }
    }
  }
  
  walkNodes(editor)
  
  return text.replace(/\n\n/g, '\n')
}

const handleInput = () => {
  if (isInternalUpdate.value) return
  
  const content = getContentFromHtml()
  emit('update:modelValue', content)
}

const handleFocus = () => {
  const placeholder = editorRef.value?.querySelector('.placeholder')
  if (placeholder) {
    placeholder.remove()
  }
}

const handleBlur = () => {
  if (editorRef.value && !editorRef.value.textContent.trim()) {
    editorRef.value.innerHTML = `<span class="placeholder">${escapeHtml(props.placeholder)}</span>`
  }
}

const updateEditorContent = () => {
  const editor = editorRef.value
  if (!editor) return
  
  isInternalUpdate.value = true
  
  const selection = window.getSelection()
  let savedRange = null
  if (selection.rangeCount > 0) {
    try {
      savedRange = selection.getRangeAt(0).cloneRange()
    } catch (e) {}
  }
  
  editor.innerHTML = renderContent(props.modelValue)
  
  const collapseBtns = editor.querySelectorAll('.collapse-btn')
  collapseBtns.forEach(btn => {
    btn.removeEventListener('click', toggleImageCollapse)
    btn.addEventListener('click', toggleImageCollapse)
  })
  
  nextTick(() => {
    isInternalUpdate.value = false
  })
}

const toggleImageCollapse = (e) => {
  e.stopPropagation()
  const wrapper = e.target.closest('.image-wrapper')
  if (!wrapper) return
  
  const imageId = wrapper.getAttribute('data-image-id')
  if (collapsedImages.value.has(imageId)) {
    collapsedImages.value.delete(imageId)
  } else {
    collapsedImages.value.add(imageId)
  }
  
  updateEditorContent()
}

watch(() => props.modelValue, (newVal) => {
  const currentContent = getContentFromHtml()
  if (newVal !== currentContent) {
    updateEditorContent()
  }
})

watch(() => props.isFocusMode, () => {
  updateEditorContent()
})

onMounted(() => {
  updateEditorContent()
})

const focus = () => {
  editorRef.value?.focus()
}

const getSelectionStart = () => {
  const selection = window.getSelection()
  if (!selection.rangeCount || !editorRef.value) return 0
  
  const range = selection.getRangeAt(0)
  const preRange = document.createRange()
  preRange.selectNodeContents(editorRef.value)
  preRange.setEnd(range.endContainer, range.endOffset)
  return preRange.toString().length
}

const getValue = () => {
  return getContentFromHtml()
}

const getScrollHeight = () => {
  return editorRef.value?.parentElement?.scrollHeight || 0
}

const getClientHeight = () => {
  return editorRef.value?.parentElement?.clientHeight || 0
}

const scrollTo = (options) => {
  editorRef.value?.parentElement?.scrollTo(options)
}

defineExpose({ focus, getSelectionStart, getValue, getScrollHeight, getClientHeight, scrollTo })
</script>

<style scoped>
.collapsible-editor-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.editor-scroll-wrapper {
  flex: 1;
  overflow: auto;
  position: relative;
}

.editor-content {
  min-height: 100%;
  padding: 50px;
  font-family: 'Fira Code', Consolas, Monaco, monospace;
  font-size: 15px;
  line-height: 1.9;
  color: var(--text-primary, #374151);
  background-color: var(--bg-tertiary, #f9fafb);
  outline: none;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.editor-content:focus {
  outline: none;
}

.custom-scroll::-webkit-scrollbar {
  width: 6px;
}

.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scroll::-webkit-scrollbar-thumb {
  background: var(--border-color, #d1d5db);
  border-radius: 4px;
}

.editor-content.focus-mask-active {
  -webkit-mask-image: linear-gradient(
    to bottom,
    rgba(0,0,0, 0.05) 0%,
    rgba(0,0,0, 0.05) 35%,
    rgba(0,0,0, 1) 45%,
    rgba(0,0,0, 1) 55%,
    rgba(0,0,0, 0.05) 65%,
    rgba(0,0,0, 0.05) 100%
  );
}

.placeholder {
  color: var(--text-tertiary, #9ca3af);
  pointer-events: none;
}

.image-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: linear-gradient(135deg, var(--accent-light, #eff6ff) 0%, var(--accent-light, #dbeafe) 100%);
  border-radius: 6px;
  margin: 0 2px;
  vertical-align: middle;
}

.collapse-btn {
  font-size: 10px;
  color: #60a5fa;
  cursor: pointer;
  user-select: none;
  padding: 0 2px;
  min-width: 14px;
  text-align: center;
}

.collapse-btn:hover {
  color: #2563eb;
}

.image-alt {
  color: var(--accent-color, #2563eb);
  font-weight: 500;
}

.image-url {
  color: var(--text-secondary, #6b7280);
  font-size: 13px;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>