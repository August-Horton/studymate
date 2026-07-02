<template>
  <div class="folder-node">
    <div v-for="(subNode, folderName) in node.children" :key="folderName" class="sub-folder">
      
      <div class="folder-header" 
           @click="toggleFolder(folderName)"
           @contextmenu.prevent="$emit('folder-contextmenu', { event: $event, folderName, currentPath: props.currentPath })"
           draggable="true"
           @dragstart.stop="handleFolderDragStart($event, folderName)"
           @dragover.prevent
           @dragenter.prevent="dragOverFolder = folderName"
           @dragleave="dragOverFolder = null"
           @drop.stop="handleDrop($event, folderName)"
           :class="{ 'is-drag-over': dragOverFolder === folderName, 'is-dragging': isDraggingFolder === folderName }"
      >
        <van-icon :name="openFolders[folderName] ? 'arrow-down' : 'arrow'" class="toggle-icon" />
        <van-icon name="folder-o" color="#4F46E5" class="folder-icon" />
        <span class="folder-name">{{ folderName }}</span>
        <span class="folder-count" v-if="getNoteCount(subNode) > 0">({{ getNoteCount(subNode) }})</span>
      </div>

      <div v-show="openFolders[folderName]" class="folder-content">
        <FolderTree 
          v-if="Object.keys(subNode.children).length > 0 || subNode.notes.length > 0"
          :node="subNode" 
          :currentNoteId="currentNoteId"
          :currentPath="props.currentPath ? `${props.currentPath}/${folderName}` : folderName"
          @select-note="$emit('select-note', $event)"
          @open-menu="$emit('open-menu', $event)"
          @folder-contextmenu="$emit('folder-contextmenu', $event)"
          @move-note="$emit('move-note', $event)"
          @move-folder="$emit('move-folder', $event)"
        />
      </div>

    </div>

    <div 
      v-for="note in node.notes" 
      :key="note.id" 
      class="nav-item"
      :class="{ 'is-active': currentNoteId === note.id }"
      draggable="true"
      @dragstart.stop="handleDragStart($event, note)"
      @click.stop="$emit('select-note', note)"
    >
      <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
        <div style="display: flex; align-items: center; overflow: hidden; flex: 1;">
          <van-icon name="notes-o" class="nav-icon" />
          <span class="nav-title">{{ getNoteTitle(note) || '未命名笔记' }}</span>
        </div>
        <div class="note-meta">
          <span class="word-count" :title="`${getWordCount(note)} 字`">{{ formatWordCount(getWordCount(note)) }}</span>
          <van-icon name="more-o" class="more-icon" @click.stop="$emit('open-menu', note)" />
        </div>
      </div>
      <div v-if="note.tags" class="note-tags">
        <van-tag v-for="tag in note.tags.split(',').filter(t => t)" :key="tag" plain type="primary" size="mini">
          {{ tag }}
        </van-tag>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  currentNoteId: { type: [Number, String], default: null },
  // 【新增】：追踪当前所处的绝对路径
  currentPath: { type: String, default: '' }
})

// 【新增】：向外暴露 folder-contextmenu 和 move-note 事件
const emit = defineEmits(['select-note', 'open-menu', 'folder-contextmenu', 'move-note', 'move-folder'])

// 控制拖拽悬停时的高亮状态
const dragOverFolder = ref(null)
// 控制当前正在拖拽的文件夹
const isDraggingFolder = ref(null)

// 当抓起笔记时：把笔记的核心数据打包进事件里
const handleDragStart = (event, note) => {
  // 将笔记对象转为字符串存入 dataTransfer
  event.dataTransfer.setData('application/json', JSON.stringify(note))
  event.dataTransfer.effectAllowed = 'move'
}

// 当抓起文件夹时：
const handleFolderDragStart = (event, folderName) => {
  const folderData = {
    type: 'folder',
    folderName: folderName,
    currentPath: props.currentPath
  }
  event.dataTransfer.setData('application/json', JSON.stringify(folderData))
  event.dataTransfer.effectAllowed = 'move'
  isDraggingFolder.value = folderName
}

// 当笔记或文件夹松手掉进文件夹时：
const handleDrop = (event, folderName) => {
  dragOverFolder.value = null // 清除高亮
  isDraggingFolder.value = null
  
  try {
    const data = event.dataTransfer.getData('application/json')
    if (!data) return
    
    const droppedData = JSON.parse(data)
    
    // 计算目标文件夹的绝对路径
    const targetPath = props.currentPath ? `${props.currentPath}/${folderName}` : folderName
    
    // 判断是笔记还是文件夹
    if (droppedData.type === 'folder') {
      // 文件夹移动
      const sourcePath = droppedData.currentPath 
        ? `${droppedData.currentPath}/${droppedData.folderName}` 
        : droppedData.folderName
      
      // 不能把文件夹拖到自己内部或拖到自己本身
      if (sourcePath !== targetPath && !targetPath.startsWith(sourcePath + '/')) {
        emit('move-folder', { sourcePath, targetPath })
      }
    } else if (droppedData.folder !== undefined) {
      // 笔记移动（保持原有逻辑）
      if (droppedData.folder !== targetPath) {
        emit('move-note', { note: droppedData, targetPath })
      }
    }
  } catch (e) {
    console.error("拖拽解析失败", e)
  }
}

const openFolders = ref({})

const toggleFolder = (folderName) => {
  openFolders.value[folderName] = !openFolders.value[folderName]
}

const getNoteCount = (node) => {
  let count = node.notes ? node.notes.length : 0
  if (node.children) {
    Object.values(node.children).forEach(child => {
      count += getNoteCount(child)
    })
  }
  return count
}

const getNoteTitle = (note) => {
  if (!note) return '未命名笔记'
  if (note.title && note.title.trim()) return note.title.trim()
  const content = note.structured_note || note.original_text || ''
  const match = content.match(/^#\s+(.+)$/m)
  if (match) return match[1].trim()
  const firstLine = content.split('\n')[0] || ''
  return firstLine.slice(0, 30) + (firstLine.length > 30 ? '...' : '') || '未命名笔记'
}

// 计算笔记字数
const getWordCount = (note) => {
  if (!note) return 0
  const content = note.structured_note || note.original_text || ''
  // 移除 markdown 语法符号
  const cleanText = content
    .replace(/```[\s\S]*?```/g, '') // 移除代码块
    .replace(/`[^`]*`/g, '') // 移除行内代码
    .replace(/!\[.*?\]\(.*?\)/g, '') // 移除图片
    .replace(/\[.*?\]\(.*?\)/g, '') // 移除链接
    .replace(/#{1,6}\s/g, '') // 移除标题符号
    .replace(/[*_~`]/g, '') // 移除强调符号
    .replace(/^\s*[-*+]\s/gm, '') // 移除列表符号
    .replace(/^\s*\d+\.\s/gm, '') // 移除有序列表符号
    .replace(/>\s/g, '') // 移除引用符号
    .trim()
  // 中文字符
  const chineseChars = (cleanText.match(/[\u4e00-\u9fa5]/g) || []).length
  // 英文单词
  const englishWords = (cleanText.match(/[a-zA-Z]+/g) || []).join(' ')
  const englishCharCount = englishWords.replace(/\s/g, '').length
  // 数字
  const numbers = (cleanText.match(/\d+/g) || []).join('')
  const numberCount = numbers.length
  return chineseChars + englishCharCount + numberCount
}

// 格式化字数显示
const formatWordCount = (count) => {
  if (count === 0) return ''
  if (count < 1000) return `${count}字`
  if (count < 10000) return `${(count / 1000).toFixed(1)}k`
  return `${(count / 10000).toFixed(1)}w`
}
</script>

<style scoped>
.folder-node {
  width: 100%;
}

.sub-folder {
  margin-bottom: 4px;
}

.folder-header {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  color: var(--text-primary, #374151);
  border-radius: 6px;
  transition: background 0.2s;
  user-select: none;
}

.folder-header:hover {
  background-color: var(--border-color, #e5e7eb);
}

/* 当笔记悬停在文件夹上方的魔法光晕效果 */
.folder-header.is-drag-over {
  background-color: var(--accent-light, #eef2ff);
  border: 1px dashed var(--accent-color, #4f46e5);
  border-radius: 6px;
}

.folder-header.is-dragging {
  opacity: 0.5;
  background-color: var(--bg-primary, #f5f5f5);
}

.toggle-icon {
  font-size: 12px;
  margin-right: 6px;
  color: var(--text-tertiary, #9ca3af);
  transition: transform 0.2s;
}

.folder-icon {
  font-size: 16px;
  margin-right: 8px;
}

.folder-name {
  font-size: 14px;
  font-weight: 600;
}

.folder-count {
  font-size: 12px;
  color: var(--text-tertiary, #9ca3af);
  margin-left: 4px;
}

.folder-content {
  padding-left: 16px;
  border-left: 1px solid var(--border-color, #e5e7eb);
  margin-left: 16px;
}

.nav-item {
  padding: 8px 12px;
  margin: 4px 0;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary, #4b5563);
  transition: all 0.2s;
}

.nav-item:hover {
  background-color: var(--border-color, #e5e7eb);
}

.nav-item.is-active {
  background-color: var(--accent-color, #4f46e5);
  color: #ffffff;
}

.nav-icon {
  margin-right: 8px;
  font-size: 14px;
}

.nav-title {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.more-icon {
  padding: 4px;
  color: inherit;
  opacity: 0.6;
}

.more-icon:hover {
  opacity: 1;
}

.note-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 4px;
  padding-left: 22px;
}

.note-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.word-count {
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  font-weight: 500;
  padding: 2px 6px;
  background: var(--bg-secondary, #f3f4f6);
  border-radius: 10px;
  white-space: nowrap;
}

.nav-item.is-active .word-count {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
}
</style>
