<template>
  <div>
    <div 
      class="category-item"
      :class="{ active: isActive, 'category-drop-zone': isDraggingOver }"
      @click="handleSelect"
      @dragenter.prevent="isDraggingOver = true"
      @dragover.prevent
      @dragleave="isDraggingOver = false"
      @drop="handleDrop"
    >
      <span class="expand-toggle" @click.stop="toggleExpand">
        {{ hasChildren ? (isExpanded ? '▼' : '▶') : ' ' }}
      </span>
      <span class="category-icon">{{ category.icon }}</span>
      <span class="category-name">{{ category.name }}</span>
      <span class="category-count">{{ totalCount }}</span>
      <div class="category-actions">
        <button class="category-action-btn add-btn" @click.stop="handleAddSubcategory" title="添加子文件夹">+</button>
        <button class="category-action-btn delete-btn" @click.stop="handleDelete" title="删除文件夹">×</button>
      </div>
    </div>
    
    <div v-if="isExpanded && hasChildren" class="category-children">
      <CategoryItem
        v-for="child in category.children"
        :key="child.id"
        :category="child"
        :selected-category="selectedCategory"
        :level="level + 1"
        :literature-list="literatureList"
        @select="$emit('select', $event)"
        @add-subcategory="$emit('add-subcategory', $event)"
        @delete="$emit('delete', $event)"
        @drop="$emit('drop', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  category: {
    type: Object,
    required: true
  },
  selectedCategory: {
    type: Object,
    default: null
  },
  level: {
    type: Number,
    default: 0
  },
  literatureList: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select', 'add-subcategory', 'delete', 'drop'])

const isExpanded = ref(true)
const isDraggingOver = ref(false)

const hasChildren = computed(() => {
  return props.category.children && props.category.children.length > 0
})

const isActive = computed(() => {
  return props.selectedCategory?.id === props.category.id
})

const totalCount = computed(() => {
  return getCategoryTotalCount(props.category)
})

const getCategoryTotalCount = (cat) => {
  let count = props.literatureList.filter(d => d.categoryId === cat.id).length
  if (cat.children) {
    for (const child of cat.children) {
      count += getCategoryTotalCount(child)
    }
  }
  return count
}

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const handleSelect = () => {
  emit('select', props.category)
}

const handleAddSubcategory = () => {
  emit('add-subcategory', props.category)
}

const handleDelete = () => {
  emit('delete', props.category.id)
}

const handleDrop = (e) => {
  e.preventDefault()
  e.stopPropagation()
  isDraggingOver.value = false
  emit('drop', props.category.id)
}
</script>

<style scoped>
.category-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  color: #374151;
  font-size: 13px;
}

.category-item:hover {
  background: #f1f5f9;
}

.category-item:hover .category-menu-btn {
  opacity: 1;
}

.category-item.active {
  background: #EEF2FF;
  color: #4F46E5;
}

.expand-toggle {
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #94a3b8;
  flex-shrink: 0;
  transition: transform 0.2s;
}

.expand-toggle.expanded {
  transform: rotate(90deg);
}

.category-icon {
  font-size: 14px;
  flex-shrink: 0;
  margin-right: 6px;
}

.category-name {
  flex: 1;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.category-count {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  flex-shrink: 0;
  margin-left: 4px;
}

.category-item.active .category-count {
  color: #4F46E5;
}

.category-menu-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #94a3b8;
  opacity: 0;
  transition: all 0.2s;
}

.category-menu-btn:hover {
  background: #e2e8f0;
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
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.category-action-btn:hover {
  background: #e2e8f0;
  color: #475569;
}

.category-action-btn.add-btn:hover {
  background: #dbeafe;
  color: #3b82f6;
}

.category-action-btn.delete-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.category-drop-zone {
  background: rgba(79, 70, 229, 0.1);
  border: 2px dashed #4F46E5;
}

.category-children {
  margin-left: 20px;
  border-left: 1px dashed #e2e8f0;
  padding-left: 8px;
}
</style>
