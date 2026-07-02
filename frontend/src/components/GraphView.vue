<template>
  <div class="graph-wrapper">
    <div class="graph-toolbar">
      <div class="stats">
        <span class="stat-item"><span class="dot connected"></span> 核心节点: {{ connectedCount }}</span>
        <span class="stat-item"><span class="dot orphan"></span> 孤立节点: {{ orphanCount }}</span>
        <span class="stat-item"><span class="dot ghost"></span> 待建节点: {{ ghostCount }}</span>
      </div>
      <van-search 
        v-model="searchKeyword" 
        placeholder="检索节点..." 
        shape="round" 
        style="padding: 0; width: 200px; background: transparent;" 
      />
      <van-button size="small" @click="resetLayout" type="primary">重置布局</van-button>
    </div>
    
    <div class="graph-container" ref="graphContainer">
      <svg 
        ref="svgRef"
        class="graph-svg" 
        @mousedown="onMouseDown"
        @mousemove="onMouseMove"
        @mouseup="onMouseUp"
        @mouseleave="onMouseUp"
        @wheel="onWheel"
      >
        <g :transform="`translate(${viewBox.x}, ${viewBox.y}) scale(${viewBox.scale})`">
          <line
            v-for="(link, index) in visibleLinks"
            :key="`link-${index}`"
            :x1="link.source.x"
            :y1="link.source.y"
            :x2="link.target.x"
            :y2="link.target.y"
            class="graph-link"
            :class="{ 'is-highlighted': link.isHighlighted }"
          />
          
          <g
            v-for="node in visibleNodes"
            :key="node.id"
            class="graph-node"
            :class="{ 
              'is-orphan': node.isOrphan, 
              'is-ghost': node.isGhost,
              'is-highlighted': node.isHighlighted,
              'is-dragging': draggingNode === node.id
            }"
            @mousedown.stop="startDrag($event, node)"
            @click.stop="handleNodeClick(node)"
          >
            <circle
              :cx="node.x"
              :cy="node.y"
              :r="node.radius"
              :fill="node.color"
              class="node-circle"
            />
            <text
              :x="node.x"
              :y="node.y + node.radius + 16"
              text-anchor="middle"
              class="node-label"
              :class="{ 'is-ghost': node.isGhost }"
            >
              {{ node.name }}
            </text>
          </g>
        </g>
      </svg>
    </div>
    
    <div class="zoom-controls">
      <van-button size="small" icon="plus" @click="zoomIn" />
      <van-button size="small" icon="minus" @click="zoomOut" />
      <van-button size="small" @click="resetView">1:1</van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'

const props = defineProps({
  notes: { type: Array, required: true },
  links: { type: Array, required: true }
})

const emit = defineEmits(['node-click'])

const graphContainer = ref(null)
const svgRef = ref(null)
const searchKeyword = ref('')
const nodes = ref([])
const graphLinks = ref([])

const viewBox = ref({
  x: 0,
  y: 0,
  scale: 1
})

const isDragging = ref(false)
const isPanning = ref(false)
const draggingNode = ref(null)
const lastMouseX = ref(0)
const lastMouseY = ref(0)

const nodeData = computed(() => {
  console.log('📊 解析节点数据:', { notesCount: props.notes.length, linksCount: props.links.length })
  
  const nodeMap = new Map()
  const existingTitles = new Set(props.notes.map(n => n.title))
  const linkedTitles = new Set()

  props.links.forEach(link => {
    const sourceNote = props.notes.find(n => n.id === link.source_id)
    if (sourceNote) {
      linkedTitles.add(sourceNote.title)
      linkedTitles.add(link.target_title)
    }
  })

  props.notes.forEach((note, index) => {
    const isOrphan = !linkedTitles.has(note.title)
    nodeMap.set(note.title, {
      id: `note-${note.id}`,
      name: note.title,
      noteId: note.id,
      isOrphan,
      isGhost: false,
      color: isOrphan ? '#ef4444' : '#4F46E5',
      radius: isOrphan ? 20 : 25,
      x: 0,
      y: 0,
      vx: 0,
      vy: 0,
      isHighlighted: false
    })
  })

  props.links.forEach(link => {
    if (!existingTitles.has(link.target_title)) {
      if (!nodeMap.has(link.target_title)) {
        nodeMap.set(link.target_title, {
          id: `ghost-${link.target_title}`,
          name: link.target_title,
          noteId: null,
          isOrphan: false,
          isGhost: true,
          color: '#9ca3af',
          radius: 15,
          x: 0,
          y: 0,
          vx: 0,
          vy: 0,
          isHighlighted: false
        })
      }
    }
  })

  const result = Array.from(nodeMap.values())
  console.log('✅ 节点数据解析完成:', result.length, '个节点')
  return result
})

const connectedCount = computed(() => nodeData.value.filter(n => !n.isOrphan && !n.isGhost).length)
const orphanCount = computed(() => nodeData.value.filter(n => n.isOrphan).length)
const ghostCount = computed(() => nodeData.value.filter(n => n.isGhost).length)

const filteredNodes = computed(() => {
  if (!searchKeyword.value) return nodeData.value
  return nodeData.value.filter(n => 
    n.name.toLowerCase().includes(searchKeyword.value.toLowerCase()))
})

const initLayout = () => {
  console.log('🎨 初始化布局')
  
  const centerX = 400
  const centerY = 300
  const filtered = filteredNodes.value
  
  if (filtered.length === 0) {
    console.log('⚠️ 没有节点可显示')
    return
  }
  
  filtered.forEach((node, i) => {
    const angle = (i / filtered.length) * Math.PI * 2
    const distance = 150 + (i % 3) * 80
    node.x = centerX + Math.cos(angle) * distance
    node.y = centerY + Math.sin(angle) * distance
    node.vx = 0
    node.vy = 0
    node.isHighlighted = false
  })
  
  nodes.value = [...filtered]
  
  graphLinks.value = []
  const nodeMap = new Map(nodes.value.map(n => [n.name, n]))
  
  props.links.forEach(link => {
    const sourceNote = props.notes.find(n => n.id === link.source_id)
    if (sourceNote) {
      const source = nodeMap.get(sourceNote.title)
      const target = nodeMap.get(link.target_title)
      if (source && target) {
        graphLinks.value.push({ source, target, isHighlighted: false })
        console.log('🔗 添加连接:', source.name, '->', target.name)
      }
    }
  })
  
  console.log('✅ 布局完成，节点数:', nodes.value.length, '连接数:', graphLinks.value.length)
}

const simulate = () => {
  if (nodes.value.length === 0) {
    requestAnimationFrame(simulate)
    return
  }
  
  const damping = 0.9
  const repulsion = 12000
  const attraction = 0.005
  const centerPull = 0.001
  const centerX = 400
  const centerY = 300
  
  for (let i = 0; i < nodes.value.length; i++) {
    const node = nodes.value[i]
    if (draggingNode.value === node.id) continue
    
    let fx = 0
    let fy = 0
    
    for (let j = 0; j < nodes.value.length; j++) {
      if (i === j) continue
      const other = nodes.value[j]
      const dx = node.x - other.x
      const dy = node.y - other.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = repulsion / (dist * dist)
      fx += (dx / dist) * force
      fy += (dy / dist) * force
    }
    
    graphLinks.value.forEach(link => {
      if (link.source === node) {
        const dx = link.target.x - node.x
        const dy = link.target.y - node.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        fx += dx * attraction
        fy += dy * attraction
      } else if (link.target === node) {
        const dx = link.source.x - node.x
        const dy = link.source.y - node.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        fx += dx * attraction
        fy += dy * attraction
      }
    })
    
    fx += (centerX - node.x) * centerPull
    fy += (centerY - node.y) * centerPull
    
    node.vx = (node.vx + fx) * damping
    node.vy = (node.vy + fy) * damping
    node.x += node.vx
    node.y += node.vy
  }
  
  requestAnimationFrame(simulate)
}

const visibleNodes = computed(() => nodes.value)
const visibleLinks = computed(() => graphLinks.value)

const onMouseDown = (e) => {
  lastMouseX.value = e.clientX
  lastMouseY.value = e.clientY
  isPanning.value = true
  console.log('🖱️ 开始平移')
}

const startDrag = (e, node) => {
  e.stopPropagation()
  isDragging.value = true
  draggingNode.value = node.id
  lastMouseX.value = e.clientX
  lastMouseY.value = e.clientY
  console.log('🖱️ 开始拖拽节点:', node.name)
}

const onMouseMove = (e) => {
  const dx = e.clientX - lastMouseX.value
  const dy = e.clientY - lastMouseY.value
  
  if (isPanning.value) {
    viewBox.value.x += dx
    viewBox.value.y += dy
    console.log('📍 平移:', viewBox.value.x, viewBox.value.y)
  } else if (isDragging.value && draggingNode.value) {
    const node = nodes.value.find(n => n.id === draggingNode.value)
    if (node) {
      node.x += dx / viewBox.value.scale
      node.y += dy / viewBox.value.scale
      node.vx = 0
      node.vy = 0
    }
  }
  
  lastMouseX.value = e.clientX
  lastMouseY.value = e.clientY
}

const onMouseUp = () => {
  isPanning.value = false
  isDragging.value = false
  draggingNode.value = null
  console.log('🖱️ 结束拖拽/平移')
}

const onWheel = (e) => {
  e.preventDefault()
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.max(0.3, Math.min(3, viewBox.value.scale * delta))
  console.log('🔍 缩放:', newScale)
  viewBox.value.scale = newScale
}

const zoomIn = () => {
  viewBox.value.scale = Math.min(viewBox.value.scale * 1.2, 3)
  console.log('🔍 放大:', viewBox.value.scale)
}

const zoomOut = () => {
  viewBox.value.scale = Math.max(viewBox.value.scale / 1.2, 0.3)
  console.log('🔍 缩小:', viewBox.value.scale)
}

const resetView = () => {
  viewBox.value.scale = 1
  console.log('🔍 重置视图')
}

const resetLayout = () => {
  viewBox.value.x = 0
  viewBox.value.y = 0
  viewBox.value.scale = 1
  initLayout()
}

const handleNodeClick = (node) => {
  console.log('👆 点击节点:', node.name)
  
  nodes.value.forEach(n => n.isHighlighted = false)
  graphLinks.value.forEach(l => l.isHighlighted = false)
  
  node.isHighlighted = true
  
  graphLinks.value.forEach(link => {
    if (link.source === node || link.target === node) {
      link.isHighlighted = true
      link.source.isHighlighted = true
      link.target.isHighlighted = true
    }
  })
  
  if (node.noteId) {
    emit('node-click', node.noteId)
  }
}

onMounted(() => {
  nextTick(() => {
    initLayout()
    simulate()
  })
})

watch(() => [props.notes, props.links], () => {
  console.log('🔄 数据更新，重新初始化布局')
  nextTick(() => {
    initLayout()
  })
}, { deep: true })
</script>

<style scoped>
.graph-wrapper { 
  position: relative; 
  width: 100%; 
  height: 100%; 
  background: linear-gradient(135deg, #f0f4ff 0%, #f8fafc 100%);
  overflow: hidden;
}

.graph-toolbar { 
  position: absolute; 
  top: 20px; 
  left: 20px; 
  right: 20px;
  z-index: 10; 
  display: flex; 
  gap: 20px; 
  align-items: center; 
  background: rgba(255,255,255,0.95); 
  padding: 12px 24px; 
  border-radius: 16px; 
  box-shadow: 0 4px 20px rgba(0,0,0,0.08); 
  backdrop-filter: blur(10px); 
}

.stats { 
  display: flex; 
  gap: 20px; 
  font-size: 13px; 
  color: #475569; 
  font-weight: 500; 
}

.dot { 
  display: inline-block; 
  width: 10px; 
  height: 10px; 
  border-radius: 50%; 
  margin-right: 6px; 
}

.dot.connected { 
  background: #4F46E5; 
  box-shadow: 0 0 8px #4F46E5; 
}

.dot.orphan { 
  background: #ef4444; 
  box-shadow: 0 0 8px #ef4444; 
}

.dot.ghost { 
  background: #9ca3af; 
}

.graph-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 100%;
  cursor: grab;
}

.graph-svg:active {
  cursor: grabbing;
}

.graph-link {
  stroke: #cbd5e1;
  stroke-width: 2;
  fill: none;
  transition: stroke 0.3s;
}

.graph-link.is-highlighted {
  stroke: #4F46E5;
  stroke-width: 3;
}

.graph-node {
  cursor: pointer;
  transition: transform 0.2s;
}

.graph-node:hover .node-circle {
  filter: brightness(1.1);
}

.graph-node.is-highlighted .node-circle {
  filter: drop-shadow(0 0 10px currentColor);
}

.graph-node.is-dragging {
  cursor: grabbing;
}

.node-circle {
  transition: all 0.2s;
}

.node-label {
  font-size: 13px;
  font-weight: 500;
  fill: #374151;
  pointer-events: none;
}

.node-label.is-ghost {
  fill: #9ca3af;
  font-style: italic;
}

.zoom-controls {
  position: absolute;
  bottom: 24px;
  right: 24px;
  display: flex;
  gap: 8px;
  z-index: 10;
}

.zoom-controls .van-button {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>
