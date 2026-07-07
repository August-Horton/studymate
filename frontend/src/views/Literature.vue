<template>
  <div class="literature-view">
    <aside class="library-sidebar">
      <div class="sidebar-header">
        <div class="header-top">
          <div class="logo-icon">📚</div>
          <h2 class="sidebar-title">StudyMate</h2>
        </div>
        <p class="subtitle">文献管理</p>
      </div>
      
      <div class="upload-section">
        <div class="upload-wrapper">
          <input 
            type="file" 
            ref="globalFileInput" 
            accept="application/pdf" 
            style="display: none;" 
            @change="handleGlobalFileUpload" 
          />
          <button class="upload-btn" @click="triggerUpload">
            <span class="btn-icon">+</span>
            <span>上传文献</span>
          </button>
        </div>
      </div>

      <div class="categories-section">
        <div class="section-header">
          <span class="section-title">📁 目录分类</span>
          <button class="add-category-btn" @click="showAddCategoryModal(null)" title="添加文件夹">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
        
        <div class="search-wrapper">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M21 21L15 15M17 10C17 13.866 13.866 17 10 17C6.13401 17 3 13.866 3 10C3 6.13401 6.13401 3 10 3C13.866 3 17 6.13401 17 10Z" stroke="currentColor" stroke-width="2"/>
          </svg>
          <input 
            type="text" 
            v-model="searchQuery" 
            class="search-input" 
            placeholder="搜索标题或正文内容..."
          />
        </div>
        
        <div class="category-tree custom-scroll">
          <div 
            class="category-item all-docs-item" 
            :class="{ active: selectedCategory === null }"
            @click="selectedCategory = null"
          >
            <span class="category-expand">▶</span>
            <span class="category-icon">📋</span>
            <span class="category-name">全部文献</span>
            <span class="category-count">({{ literatureList.length }})</span>
          </div>
          
          <div v-for="cat in categories" :key="cat.id">
            <CategoryItem
              :category="cat"
              :selected-category="selectedCategory"
              :level="0"
              :literature-list="literatureList"
              @select="selectedCategory = $event"
              @add-subcategory="showAddCategoryModal($event)"
              @delete="deleteCategory($event)"
              @drop="handleDropOnCategory"
            />
          </div>
        </div>
      </div>

      <div class="doc-list custom-scroll">
        <div v-if="filteredLiterature.length === 0" class="empty-list">
          <div class="empty-icon">📄</div>
          <p class="empty-title">{{ selectedCategory ? '该文件夹暂无文献' : '还没有文献' }}</p>
          <p class="empty-hint">{{ selectedCategory ? '拖动文档到文件夹中' : '点击上方按钮上传 PDF 文件' }}</p>
        </div>
        
        <div 
          v-else 
          v-for="doc in filteredLiterature" 
          :key="doc.id"
          class="doc-item"
          :class="{ active: currentActiveDoc?.id === doc.id, 'dragging-over': draggingOverDocId === doc.id }"
          draggable="true"
          @dragstart="handleDocDragStart($event, doc)"
          @dragend="handleDocDragEnd"
          @click="openDocument(doc)"
        >
          <div class="doc-icon">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6 2V22H18V6H12V2H6ZM14 8V2H18V8H14Z" fill="currentColor"/>
              <path d="M8 13H16V15H8V13ZM8 17H16V19H8V17Z" fill="currentColor"/>
            </svg>
          </div>
          <div class="doc-info">
            <span class="doc-name">{{ doc.name }}</span>
            <span class="doc-meta">PDF 文档</span>
          </div>
          <div class="doc-actions">
            <button class="download-btn" @click.stop="downloadDocument(doc)" title="下载到本地">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 15V3M5 12l7 7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button class="delete-btn" @click.stop="deleteDocument(doc)" title="删除文献">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M19 7L5 7M12 17V7M14 4H10M16 11V17M8 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <div class="doc-status">
            <div v-if="currentActiveDoc?.id === doc.id" class="status-dot active"></div>
          </div>
        </div>
      </div>
    </aside>

    <main class="reader-container">
      <div v-if="currentActiveDoc" class="reader-wrapper">
        <PdfReader 
          :pdf-path="currentActiveDoc.url"
          :file-name="currentActiveDoc.name"
        />
      </div>
      <div v-else class="empty-reader">
        <div class="empty-content">
          <div class="empty-main-icon">📖</div>
          <p class="welcome-text">开始你的文献阅读</p>
          <p class="welcome-hint">从左侧选择一篇文献，或上传新的 PDF</p>
        </div>
      </div>
    </main>

    <div v-if="showAddCategory" class="modal-overlay" @click="showAddCategory = false">
      <div class="modal-content" @click.stop>
        <h3 class="modal-title">{{ parentCategory ? '添加子文件夹' : '添加文件夹' }}</h3>
        <input 
          v-model="newCategoryName" 
          type="text" 
          class="modal-input" 
          placeholder="输入文件夹名称"
          @keyup.enter="addCategory"
        />
        <div class="modal-actions">
          <button class="modal-btn cancel" @click="showAddCategory = false">取消</button>
          <button class="modal-btn confirm" @click="addCategory">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import PdfReader from '@/components/PdfReader.vue'
import CategoryItem from '@/components/CategoryItem.vue'

const STORAGE_KEY = 'studymate_literature_list'
const CATEGORIES_KEY = 'studymate_categories'

const globalFileInput = ref(null)
const literatureList = ref([])
const currentActiveDoc = ref(null)
const categories = ref([
  { id: 'cat_1', name: '默认分类', icon: '📁', children: [] },
  { id: 'cat_2', name: '学习资料', icon: '📚', children: [] },
  { id: 'cat_3', name: '研究论文', icon: '📝', children: [] }
])
const selectedCategory = ref(null)
const showAddCategory = ref(false)
const newCategoryName = ref('')
const parentCategory = ref(null)
const draggingDoc = ref(null)
const draggingOverDocId = ref(null)

const categoryIcons = ['📁', '📂', '📃', '📄', '📅', '📆', '📇', '📈', '📉', '📊', '📋', '📌']

const filteredLiterature = computed(() => {
  if (!selectedCategory.value) {
    return literatureList.value
  }
  return literatureList.value.filter(doc => doc.categoryId === selectedCategory.value.id)
})

const getCategoryDocCount = (categoryId) => {
  let count = literatureList.value.filter(doc => doc.categoryId === categoryId).length
  const category = findCategoryById(categoryId, categories.value)
  if (category && category.children) {
    for (const child of category.children) {
      count += getCategoryDocCount(child.id)
    }
  }
  return count
}

const findCategoryById = (id, categoryList = categories.value) => {
  for (const cat of categoryList) {
    if (cat.id === id) return cat
    if (cat.children) {
      const found = findCategoryById(id, cat.children)
      if (found) return found
    }
  }
  return null
}

const loadLiteratureList = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      const savedList = JSON.parse(saved)
      literatureList.value = savedList.map(item => {
        if (item.data) {
          const byteString = atob(item.data.split(',')[1])
          const mimeType = item.data.split(',')[0].split(':')[1].split(';')[0]
          const ab = new ArrayBuffer(byteString.length)
          const ia = new Uint8Array(ab)
          for (let i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i)
          }
          const blob = new Blob([ab], { type: mimeType })
          return {
            ...item,
            url: URL.createObjectURL(blob)
          }
        }
        return item
      })
    } catch (e) {
      literatureList.value = []
    }
  }
}

const saveLiteratureList = () => {
  const listToSave = literatureList.value.map(item => {
    return {
      id: item.id,
      name: item.name,
      data: item.data,
      categoryId: item.categoryId
    }
  })
  localStorage.setItem(STORAGE_KEY, JSON.stringify(listToSave))
}

const loadCategories = () => {
  const saved = localStorage.getItem(CATEGORIES_KEY)
  if (saved) {
    try {
      categories.value = JSON.parse(saved)
    } catch (e) {
      categories.value = [
        { id: 'cat_1', name: '默认分类', icon: '📁', children: [] },
        { id: 'cat_2', name: '学习资料', icon: '📚', children: [] },
        { id: 'cat_3', name: '研究论文', icon: '📝', children: [] }
      ]
    }
  }
}

const saveCategories = () => {
  localStorage.setItem(CATEGORIES_KEY, JSON.stringify(categories.value))
}

const showAddCategoryModal = (parent) => {
  parentCategory.value = parent
  newCategoryName.value = ''
  showAddCategory.value = true
}

const addCategory = () => {
  const name = newCategoryName.value.trim()
  if (!name) return
  
  const newCat = {
    id: `cat_${Date.now()}`,
    name,
    icon: categoryIcons[Math.floor(Math.random() * categoryIcons.length)],
    children: []
  }
  
  if (parentCategory.value) {
    const parent = findCategoryById(parentCategory.value.id)
    if (parent) {
      if (!parent.children) parent.children = []
      parent.children.push(newCat)
    }
  } else {
    categories.value.push(newCat)
  }
  
  saveCategories()
  newCategoryName.value = ''
  showAddCategory.value = false
  parentCategory.value = null
}

const deleteCategory = (categoryId) => {
  if (!confirm('确定要删除这个文件夹吗？里面的文献将移动到"全部文献"')) return
  
  const moveToRoot = (catId) => {
    literatureList.value.forEach(doc => {
      if (doc.categoryId === catId) {
        doc.categoryId = null
      }
    })
    const category = findCategoryById(catId)
    if (category && category.children) {
      category.children.forEach(child => moveToRoot(child.id))
    }
  }
  
  moveToRoot(categoryId)
  
  const removeFromList = (list, id) => {
    const index = list.findIndex(c => c.id === id)
    if (index !== -1) {
      list.splice(index, 1)
      return true
    }
    for (const cat of list) {
      if (cat.children && removeFromList(cat.children, id)) {
        return true
      }
    }
    return false
  }
  
  removeFromList(categories.value, categoryId)
  
  if (selectedCategory.value?.id === categoryId) {
    selectedCategory.value = null
  }
  
  saveCategories()
  saveLiteratureList()
}

const triggerUpload = () => {
  globalFileInput.value?.click()
}

const handleGlobalFileUpload = (e) => {
  const file = e.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = async (e) => {
    const dataUrl = e.target.result
    const newDoc = {
      id: `doc_${Date.now()}`,
      name: file.name.replace('.pdf', ''),
      data: dataUrl,
      categoryId: selectedCategory.value?.id || null
    }
    
    if (newDoc.data) {
      const byteString = atob(newDoc.data.split(',')[1])
      const mimeType = newDoc.data.split(',')[0].split(':')[1].split(';')[0]
      const ab = new ArrayBuffer(byteString.length)
      const ia = new Uint8Array(ab)
      for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i)
      }
      const blob = new Blob([ab], { type: mimeType })
      newDoc.url = URL.createObjectURL(blob)
    }
    
    literatureList.value.push(newDoc)
    saveLiteratureList()
    currentActiveDoc.value = newDoc
  }
  reader.readAsDataURL(file)
  e.target.value = ''
}

const openDocument = (doc) => {
  currentActiveDoc.value = doc
}

const downloadDocument = (doc) => {
  if (doc.data) {
    const link = document.createElement('a')
    link.href = doc.data
    link.download = `${doc.name}.pdf`
    link.click()
  }
}

const deleteDocument = (doc) => {
  if (!confirm(`确定要删除《${doc.name}》吗？`)) return
  const index = literatureList.value.findIndex(d => d.id === doc.id)
  if (index !== -1) {
    literatureList.value.splice(index, 1)
    if (currentActiveDoc.value?.id === doc.id) {
      currentActiveDoc.value = null
    }
    saveLiteratureList()
  }
}

const handleDocDragStart = (e, doc) => {
  draggingDoc.value = doc
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', doc.id)
}

const handleDocDragEnd = () => {
  draggingDoc.value = null
  draggingOverDocId.value = null
}

const handleDropOnCategory = (categoryId) => {
  if (!draggingDoc.value) return
  
  const docIndex = literatureList.value.findIndex(d => d.id === draggingDoc.value.id)
  if (docIndex !== -1) {
    literatureList.value[docIndex].categoryId = categoryId
    saveLiteratureList()
  }
}

onMounted(() => {
  loadLiteratureList()
  loadCategories()
})
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.literature-view {
  display: flex;
  height: 100%;
  width: 100%;
  background-color: var(--bg-primary, #f5f5f5);
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
}

.library-sidebar {
  width: 320px;
  background: var(--card-bg, #ffffff);
  border-right: 1px solid var(--border-color, #e2e8f0);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 24px 24px 16px;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  color: white;
}

.header-top {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.logo-icon {
  font-size: 32px;
}

.sidebar-title {
  font-size: 20px;
  font-weight: 700;
}

.subtitle {
  font-size: 13px;
  opacity: 0.9;
  font-weight: 500;
}

.upload-section {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.upload-wrapper {
  position: relative;
}

.upload-btn {
  width: 100%;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  color: white;
  border: none;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}

.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.35);
}

.btn-icon {
  font-size: 18px;
  font-weight: 600;
}

.categories-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--card-bg, #ffffff);
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color, #e2e8f0);
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #374151);
}

.add-category-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-secondary, #64748b);
  transition: all 0.2s;
}

.add-category-btn:hover {
  background: var(--bg-secondary, #f1f5f9);
  color: var(--accent-color, #4f46e5);
  border-color: var(--border-color, #cbd5e1);
}

.search-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--bg-secondary, #f8fafc);
}

.search-icon {
  color: var(--text-tertiary, #94a3b8);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-secondary, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 8px;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: var(--accent-color, #4f46e5);
  background: var(--card-bg, #ffffff);
}

.search-input::placeholder {
  color: var(--text-tertiary, #94a3b8);
}

.category-tree {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 8px;
  overflow-y: auto;
}

.category-tree.custom-scroll::-webkit-scrollbar {
  width: 6px;
}

.category-tree.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.category-tree.custom-scroll::-webkit-scrollbar-thumb {
  background: var(--border-color, #cbd5e1);
  border-radius: 3px;
}

.all-docs-item {
  background: linear-gradient(135deg, var(--accent-light, #EEF2FF) 0%, var(--accent-light, #E0E7FF) 100%);
  color: var(--accent-color, #4f46e5);
  font-weight: 600;
  border-radius: 8px;
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.category-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-secondary, #475569);
}

.category-item:hover {
  background: var(--bg-secondary, #f1f5f9);
}

.category-item.active {
  background: linear-gradient(135deg, var(--accent-light, #EEF2FF) 0%, var(--accent-light, #E0E7FF) 100%);
  color: var(--accent-color, #4f46e5);
}

.category-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.category-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.category-count {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-tertiary, #94a3b8);
  background: var(--bg-secondary, #f1f5f9);
  padding: 2px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}

.category-item.active .category-count {
  background: rgba(79, 70, 229, 0.15);
  color: var(--accent-color, #4f46e5);
}

.category-children {
  margin-left: 16px;
  border-left: 1px dashed var(--border-color, #e2e8f0);
  padding-left: 8px;
}

.category-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.category-item:hover .category-actions {
  opacity: 1;
}

.category-action-btn {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: var(--text-tertiary, #94a3b8);
  transition: all 0.2s;
}

.category-action-btn:hover {
  background: var(--border-color, #e2e8f0);
  color: var(--text-secondary, #475569);
}

.category-drop-zone {
  background: rgba(79, 70, 229, 0.1);
  border: 2px dashed #4F46E5;
}

.doc-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-list {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin-bottom: 6px;
}

.empty-hint {
  font-size: 13px;
  color: var(--text-tertiary, #94a3b8);
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  margin-bottom: 8px;
  position: relative;
}

.doc-item:hover {
  background: var(--bg-secondary, #f8fafc);
  transform: translateX(4px);
}

.doc-item.active {
  background: linear-gradient(135deg, var(--accent-light, #EEF2FF) 0%, var(--accent-light, #E0E7FF) 100%);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.1);
}

.doc-item.dragging-over {
  background: rgba(79, 70, 229, 0.05);
  border: 2px dashed #4F46E5;
}

.doc-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 10px;
  color: white;
  flex-shrink: 0;
}

.doc-icon svg {
  width: 22px;
  height: 22px;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-meta {
  display: block;
  font-size: 12px;
  color: var(--text-tertiary, #94a3b8);
  margin-top: 2px;
}

.doc-actions {
  display: flex;
  gap: 6px;
  opacity: 0;
  transition: opacity 0.25s ease;
}

.doc-item:hover .doc-actions {
  opacity: 1;
}

.download-btn,
.delete-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-tertiary, #94a3b8);
  transition: all 0.2s ease;
}

.download-btn:hover {
  background: #dbeafe;
  color: #3b82f6;
}

.delete-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.doc-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--border-color, #cbd5e1);
  flex-shrink: 0;
}

.status-dot.active {
  background: #10B981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.reader-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  background: var(--bg-secondary, #f1f5f9);
}

.reader-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.empty-reader {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(135deg, var(--bg-secondary, #f8fafc) 0%, var(--bg-secondary, #f1f5f9) 100%);
}

.empty-content {
  text-align: center;
  padding: 40px;
}

.empty-main-icon {
  font-size: 72px;
  margin-bottom: 24px;
  opacity: 0.7;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.welcome-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary, #1e293b);
  margin: 0 0 8px 0;
}

.welcome-hint {
  font-size: 14px;
  color: var(--text-tertiary, #94a3b8);
  margin: 0;
}

.custom-scroll::-webkit-scrollbar {
  width: 6px;
}

.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scroll::-webkit-scrollbar-thumb {
  background: var(--border-color, #cbd5e1);
  border-radius: 4px;
  transition: background 0.2s;
}

.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary, #94a3b8);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--card-bg, #ffffff);
  border-radius: 16px;
  padding: 24px;
  width: 360px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #1e293b);
  margin: 0 0 16px 0;
}

.modal-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary, #374151);
  outline: none;
  transition: all 0.2s;
}

.modal-input:focus {
  border-color: var(--accent-color, #4f46e5);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.modal-input::placeholder {
  color: var(--text-tertiary, #94a3b8);
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.modal-btn.cancel {
  background: var(--bg-secondary, #f1f5f9);
  color: var(--text-secondary, #64748b);
}

.modal-btn.cancel:hover {
  background: var(--border-color, #e2e8f0);
}

.modal-btn.confirm {
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  color: white;
}

.modal-btn.confirm:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
}
</style>
