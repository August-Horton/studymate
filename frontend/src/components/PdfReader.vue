<template>
  <div class="pdf-workspace">
    <aside class="pdf-sidebar" v-show="isPdfLoaded && !sidebarCollapsed">
      <div class="sidebar-header">
        <div class="header-row">
          <span class="sidebar-title">📋 批注与摘录</span>
          <span v-if="annotationList.length > 0" class="annotation-count">{{ annotationList.length }}</span>
        </div>
      </div>
      
      <div class="sidebar-content custom-scroll">
        <div v-if="annotationList.length === 0" class="empty-state">
          <div class="empty-icon">✏️</div>
          <p>暂无批注</p>
          <p class="hint">划选文献文字即可添加</p>
        </div>
        
        <div v-else class="annotation-list">
          <div 
            v-for="(item, index) in annotationList" 
            :key="item.id || index"
            class="annotation-card"
            :class="`type-${item.type}`"
            @click="jumpToAnnotation(item)"
          >
            <div class="card-header">
              <div class="card-meta">
                <span class="page-badge">P.{{ item.page }}</span>
                <span class="type-label">
                  {{ item.type === 'highlight' ? '🖍️ 高亮' : item.type === 'underline' ? '✍️ 下划线' : '📄 摘录' }}
                </span>
              </div>
              <button class="delete-btn" @click.stop="deleteAnnotation(item.id)" title="删除">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M6 6L18 18M6 18L18 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </button>
            </div>
            
            <div v-if="item.type === 'excerpt'" class="card-content">
              <div class="excerpt-quote">{{ item.content }}</div>
              <textarea 
                v-if="item.note !== undefined"
                v-model="item.note" 
                placeholder="添加你的思考..." 
                class="note-textarea custom-scroll"
                rows="2"
              ></textarea>
            </div>
            
            <div v-else class="card-content highlight-preview">
              <div class="color-dot" :style="{ background: item.color || 'rgba(250, 204, 21, 0.45)' }"></div>
              <span v-if="item.content" class="highlight-content">{{ item.content }}</span>
              <span v-else>在此页添加了标记</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <main class="pdf-main">
      <header class="pdf-toolbar">
        <div class="toolbar-left">
          <button class="icon-btn" @click="sidebarCollapsed = !sidebarCollapsed" title="切换侧边栏">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M4 6H20M4 12H20M4 18H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
          <div class="file-info" v-if="isPdfLoaded">
            <span class="file-icon">📄</span>
            <span class="file-name">{{ fileName || '未命名文件' }}</span>
          </div>
        </div>
        
        <div class="toolbar-center" v-show="isPdfLoaded">
          <button class="nav-btn" @click="prevPage" :disabled="currentPageNum <= 1">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M15 6L9 12L15 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <span class="page-indicator">{{ currentPageNum }} / {{ totalPages }}</span>
          <button class="nav-btn" @click="nextPage" :disabled="currentPageNum >= totalPages">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M9 6L15 12L9 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
        <div class="toolbar-right">
          <div class="zoom-controls" v-show="isPdfLoaded">
            <button class="zoom-btn" @click="zoomOut" :disabled="scale <= 0.5" title="缩小">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
            <span class="zoom-value">{{ Math.round(scale * 100) }}%</span>
            <button class="zoom-btn" @click="zoomIn" :disabled="scale >= 3" title="放大">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
            <button class="zoom-btn fit-btn" @click="fitToWidth" title="自适应宽度">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <path d="M3 4h18M3 20h18M4 4v16M20 4v16M9 4v5M15 4v5M9 15v5M15 15v5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <button class="ai-read-btn" v-show="isPdfLoaded" @click="openAiPanel">
            <span class="ai-icon">✨</span> AI 速读
          </button>
        </div>
      </header>

      <div class="pdf-render-container custom-scroll" @scroll="handleScroll">
        
        <div v-if="isLoading" style="margin-top: 10vh; color: #666; text-align: center;">加载中...</div>
        <div v-else-if="!isPdfLoaded && !props.pdfPath" style="margin-top: 10vh; color: #666; text-align: center;">请点击左上角打开 PDF</div>

        <div v-show="isPdfLoaded" class="pages-container" @click="handleCanvasClick">
          <div 
            v-for="(page, pageIndex) in renderedPages" 
            :key="pageIndex"
            class="page-wrapper"
            :data-page-num="pageIndex + 1"
          >
            <div v-if="!page.loaded" class="page-loading-placeholder">
              <div class="loading-spinner-small"></div>
              <span>加载第 {{ pageIndex + 1 }} 页...</span>
            </div>
            <canvas 
              v-show="page.loaded"
              :ref="el => { if (el) canvasRefs[pageIndex] = el }" 
              class="pdf-canvas"
              :width="page.width"
              :height="page.height"
            ></canvas>
            
            <div 
              class="page-highlight-layer"
              :style="{ width: page.width + 'px', height: page.height + 'px' }"
            >
              <div 
                v-for="(h, hIndex) in getPageHighlights(pageIndex + 1)" 
                :key="hIndex"
                :style="{
                  position: 'absolute',
                  top: (h.top * scale) + 'px',
                  left: (h.left * scale) + 'px',
                  width: (h.width * scale) + 'px',
                  height: h.type === 'underline' ? '2px' : (h.height * scale) + 'px',
                  marginTop: h.type === 'underline' ? ((h.height - 2) * scale) + 'px' : '0',
                  backgroundColor: h.color,
                  mixBlendMode: h.type === 'highlight' ? 'multiply' : 'normal',
                  borderRadius: h.type === 'highlight' ? '3px' : '0',
                  pointerEvents: 'none'
                }"
              ></div>
            </div>

            <div 
              :ref="el => { if (el) textLayerRefs[pageIndex] = el }"
              class="page-text-layer"
              :style="{ width: page.width + 'px', height: page.height + 'px' }"
              @mouseup="handleTextSelection(pageIndex + 1)"
            ></div>
          </div>
        </div>
      </div>

      <div 
        v-show="showSelectionMenu" 
        class="selection-toolbar"
        :style="{ top: menuY + 'px', left: menuX + 'px' }"
      >
        <div class="selection-tools">
          <button class="tool-btn highlight" @mousedown.prevent @click="executeHighlight" title="高亮">
            <span class="tool-icon">🖍️</span>
            <span class="tool-label">高亮</span>
          </button>
          <button class="tool-btn underline" @mousedown.prevent @click="executeUnderline" title="下划线">
            <span class="tool-icon">✍️</span>
            <span class="tool-label">下划线</span>
          </button>
          <div class="tool-divider"></div>
          <button class="tool-btn excerpt" @mousedown.prevent @click="executeExcerpt" title="摘录">
            <span class="tool-icon">📄</span>
            <span class="tool-label">摘录</span>
          </button>
          <div class="tool-divider"></div>
          <button class="tool-btn translate" @mousedown.prevent @click="executeTranslate" title="翻译">
            <span class="tool-icon">🌐</span>
            <span class="tool-label">翻译</span>
          </button>
        </div>
      </div>

      <!-- 翻译结果浮窗 -->
      <div 
        v-if="showTranslation" 
        class="translation-popup"
        :style="{ top: transY + 'px', left: transX + 'px' }"
      >
        <div class="trans-header">
          <span class="trans-title"><span style="margin-right: 6px;">🌐</span>DeepSeek 翻译</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" @click="showTranslation = false" style="cursor: pointer; color: #94a3b8;">
            <path d="M6 18L18 6M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="trans-body custom-scroll">
          <div v-if="isTranslating" class="trans-loading">
            <div class="loading-spinner-small"></div>
            <span>正在请求翻译...</span>
          </div>
          <div v-else class="trans-result">
            {{ translationResult }}
          </div>
        </div>
        <div class="trans-footer" v-if="!isTranslating && translationResult">
          <button class="trans-action-btn" @click="saveTranslationToNotes">
            <span style="font-size: 14px;">📝</span> 存入批注
          </button>
        </div>
      </div>
    </main>

    <div v-if="showAiPanel" class="ai-overlay" @click.self="showAiPanel = false">
      <div class="ai-panel">
        <div class="ai-panel-container custom-scroll">
          <div class="ai-header">
            <h3>✨ AI 智能速读</h3>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" @click="showAiPanel = false" style="cursor: pointer; color: #94a3b8;">
              <path d="M6 18L18 6M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>

          <div v-if="aiStatus === 'idle'" class="ai-empty">
            <div class="ai-sparkle">🤖</div>
            <p style="margin-bottom: 20px; font-weight: 600; color: #334155;">请选择 AI 解析模式：</p>
            
            <div class="ai-mode-buttons">
              <button class="ai-mode-btn summary-mode" @click="generateAiReport('summary')">
                <div class="btn-title"><span class="btn-icon">⚡</span> 提取速读报告</div>
                <div class="btn-desc">快速提炼 4-5 个核心维度，适合文献初筛</div>
              </button>
              
              <button class="ai-mode-btn review-mode" @click="generateAiReport('review')">
                <div class="btn-title"><span class="btn-icon">📚</span> 生成文献综述</div>
                <div class="btn-desc">深度挖掘创新点与研究局限，适合精读梳理</div>
              </button>
            </div>
          </div>

          <div v-else-if="aiStatus === 'loading'" class="ai-loading">
            <div class="loading-spinner"></div>
            <p class="mt-4">正在通读全文并进行深度思考...</p>
            <span style="font-size: 12px; color: #94a3b8;">长文献耗时较长，请耐心等待（15-30秒）</span>
          </div>

          <div v-else-if="aiStatus === 'done' && aiReport" class="ai-report-content">
            <div class="report-module" v-for="(content, title) in aiReport" :key="title">
              <h4 class="module-title">
                <span class="module-icon">{{ getModuleIcon(title) }}</span> {{ title }}
              </h4>
              <p class="module-text">{{ content }}</p>
            </div>
            
            <div class="ai-actions-row">
              <button class="ai-action-btn secondary" @click="resetAiPanel">
                <span style="font-size: 14px; margin-right: 6px;">🔄</span>
                重新生成
              </button>
              
              <button class="ai-action-btn" @click="exportReportToNotes">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style="margin-right: 6px;">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                一键转为摘要笔记
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import pdfWorkerUrl from 'pdfjs-dist/build/pdf.worker.min.js?url'
import { showSuccessToast, showFailToast } from 'vant'
import api from '../api'
import { getAIConfig, getProvider } from '../utils/aiConfig'

const getAIConfigParams = () => {
  const aiConfig = getAIConfig()
  const provider = getProvider(aiConfig.provider)
  return {
    model: aiConfig.model,
    api_key: aiConfig.apiKey,
    base_url: aiConfig.provider === 'custom' ? aiConfig.baseUrl : provider.baseUrl
  }
}

const props = defineProps({
  pdfPath: { type: String, default: '' },
  fileName: { type: String, default: '' },
  initialPage: { type: Number, default: 1 }
})

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl

const isPdfLoaded = ref(false)
const isLoading = ref(false)
const sidebarCollapsed = ref(false)

const currentPageNum = ref(1)
const totalPages = ref(0)
const scale = ref(1.5)

const canvasRefs = ref({})
const textLayerRefs = ref({})
const renderedPages = ref([])

let pdfDocInstance = null
const allHighlights = ref([])

const showAiPanel = ref(false)
const aiStatus = ref('idle')
const aiReport = ref(null)

const openAiPanel = () => {
  showAiPanel.value = true
}

// ================= ✨ 智能图标分配引擎 (已扩容) =================
const getModuleIcon = (title) => {
  if (title.includes('主旨') || title.includes('概括')) return '🎯'
  if (title.includes('背景') || title.includes('缘起') || title.includes('前言')) return '🌍'
  if (title.includes('目的') || title.includes('目标')) return '🎯'
  if (title.includes('方法') || title.includes('步骤') || title.includes('方案')) return '🛠️'
  if (title.includes('结果') || title.includes('数据') || title.includes('成绩')) return '📊'
  if (title.includes('结论') || title.includes('总结') || title.includes('启示')) return '💡'
  
  // 📚 综述专属图标匹配
  if (title.includes('创新') || title.includes('贡献') || title.includes('突破')) return '✨'
  if (title.includes('局限') || title.includes('不足') || title.includes('缺陷')) return '⚠️'
  if (title.includes('未来') || title.includes('方向') || title.includes('展望')) return '�'
  if (title.includes('评价') || title.includes('分析') || title.includes('探讨')) return '⚖️'
  
  return '📌' 
}

// ================= ✨ 动态泛用型 AI 双核引擎 (全文读取版) =================
const aiCurrentMode = ref('summary')

const generateAiReport = async (mode) => {
  aiStatus.value = 'loading'
  aiCurrentMode.value = mode
  
  try {
    let extractedText = ''
    const maxPagesToRead = pdfDocInstance.numPages 
    
    console.log(`开始提取全文，共 ${maxPagesToRead} 页...`)

    for (let i = 1; i <= maxPagesToRead; i++) {
      const page = await pdfDocInstance.getPage(i)
      const textContent = await page.getTextContent()
      extractedText += textContent.items.map(item => item.str).join(' ') + '\n'
    }

    const promptText = extractedText.substring(0, 100000)
    console.log(`提取完毕！正在启动 [${mode === 'review' ? '综述' : '速读'}] 引擎，发送字数:`, promptText.length)

    const res = await api.post('/ai/analyze-pdf', { text: promptText, mode })

    aiReport.value = res
    aiStatus.value = 'done'
    showSuccessToast(mode === 'review' ? '全文综述生成完毕！' : '全文速读解析完成！')

  } catch (error) {
    console.error('AI 请求失败:', error)
    showFailToast('全文解析失败或网络超时，可能字数过多')
    aiStatus.value = 'idle'
  }
}

const exportReportToNotes = () => {
  const reportString = Object.entries(aiReport.value)
    .map(([k, v]) => `**${k}**\n${v}`)
    .join('\n\n')
    
  allHighlights.value.push({
    id: `ai_summary_${Date.now()}`,
    type: 'excerpt', // 安全类型
    page: 1,
    content: '【AI 速读总结】\n' + reportString,
    time: new Date().toLocaleTimeString()
  })
  
  // 💡 修复：使用 Toast 替代 alert
  showSuccessToast('已导入批注列表！')
  showAiPanel.value = false
}

const resetAiPanel = () => {
  aiStatus.value = 'idle'
  aiReport.value = null
  aiCurrentMode.value = 'summary'
}

watch(() => props.fileName, (newName) => {
  if (newName) {
    const savedAnnotations = localStorage.getItem(`studymate_anno_${newName}`)
    if (savedAnnotations) {
      allHighlights.value = JSON.parse(savedAnnotations)
    } else {
      allHighlights.value = []
    }
  }
}, { immediate: true })

watch(allHighlights, (newVal) => {
  if (props.fileName) {
    localStorage.setItem(`studymate_anno_${props.fileName}`, JSON.stringify(newVal))
  }
}, { deep: true })

const showSelectionMenu = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const currentSelectionRects = ref([])

// ================= 🌐 划词翻译引擎 =================
const showTranslation = ref(false)
const isTranslating = ref(false)
const translationResult = ref('')
const transX = ref(0)
const transY = ref(0)
const currentSourceText = ref('')

const executeTranslate = async () => {
  const selection = window.getSelection()
  const text = selection.toString().trim()
  if (!text) return

  currentSourceText.value = text
  
  transX.value = menuX.value
  transY.value = menuY.value + 60 
  
  showSelectionMenu.value = false
  showTranslation.value = true
  isTranslating.value = true
  translationResult.value = ''
  window.getSelection().empty()
  currentSelectionRects.value = []

  try {
    const res = await api.post('/ai/chat', {
      messages: [
        {
          role: 'system',
          content: `你是一个专业的学术翻译引擎。
规则：
1. 若输入英文，请翻译为流畅、符合学术规范的中文。
2. 若输入中文，请翻译为地道、专业的英文。
3. 直接输出翻译结果，**严禁**输出任何多余的解释、寒暄或拼音。`
        },
        {
          role: 'user',
          content: text
        }
      ],
      ...getAIConfigParams()
    })

    if (res && res.content) {
      translationResult.value = res.content
    } else {
      throw new Error('翻译响应异常')
    }

  } catch (error) {
    console.error('翻译出错:', error)
    translationResult.value = '翻译失败，请检查网络或 API Key 配置。'
  } finally {
    isTranslating.value = false
  }
}

const saveTranslationToNotes = () => {
  allHighlights.value.push({
    id: `trans_${Date.now()}`,
    type: 'excerpt',
    page: currentPageNum.value,
    content: `【原文】${currentSourceText.value}\n\n【翻译】${translationResult.value}`,
    note: '',
    time: new Date().toLocaleTimeString()
  })
  showSuccessToast('译文已存入批注列表')
  showTranslation.value = false
}

// 💡 核心修复：防止摘录 (excerpt) 渲染成 NaN 大小的空白块引发崩溃
const getPageHighlights = (pageNum) => {
  return allHighlights.value.filter(h => h.page === pageNum && h.type !== 'excerpt')
}

const annotationList = computed(() => {
  const ids = new Set()
  const result = []
  for (const h of allHighlights.value) {
    if (!ids.has(h.id)) {
      ids.add(h.id)
      result.push(h)
    }
  }
  return result
})

const renderedPages = ref([])
const renderedPageNumbers = ref(new Set())

const loadPdfFromPath = async (path) => {
  try {
    isLoading.value = true
    isPdfLoaded.value = false
    aiReport.value = null
    aiStatus.value = 'idle'
    showAiPanel.value = false
    renderedPageNumbers.value = new Set()
    
    const loadingTask = pdfjsLib.getDocument(path)
    pdfDocInstance = await loadingTask.promise
    totalPages.value = pdfDocInstance.numPages
    currentPageNum.value = props.initialPage || 1
    
    await initPagePlaceholders()
    await renderSinglePage(currentPageNum.value)
    
    isPdfLoaded.value = true
    isLoading.value = false
    
    await nextTick()
    LazyRender(currentPageNum.value)
  } catch (error) {
    isLoading.value = false
    console.error('PDF 加载失败:', error)
  }
}

const initPagePlaceholders = async () => {
  if (!pdfDocInstance) return
  renderedPages.value = []
  
  const firstPage = await pdfDocInstance.getPage(1)
  const viewport = firstPage.getViewport({ scale: scale.value })
  
  for (let i = 1; i <= totalPages.value; i++) {
    renderedPages.value.push({ 
      num: i, 
      width: viewport.width, 
      height: viewport.height,
      loaded: i === currentPageNum.value
    })
  }
}

const LazyRender = async (targetPageNum) => {
  const rangeStart = Math.max(1, targetPageNum - 2)
  const rangeEnd = Math.min(totalPages.value, targetPageNum + 2)
  
  for (let i = rangeStart; i <= rangeEnd; i++) {
    if (!renderedPageNumbers.value.has(i)) {
      renderSinglePage(i)
    }
  }
}

let lazyRenderTimer = null
const scheduleLazyRender = (pageNum) => {
  if (lazyRenderTimer) return
  lazyRenderTimer = setTimeout(() => {
    lazyRenderTimer = null
    LazyRender(pageNum)
  }, 80)
}

const renderAllPages = async () => {
  if (!pdfDocInstance) return
  for (let i = 1; i <= totalPages.value; i++) {
    if (!renderedPageNumbers.value.has(i)) {
      await renderSinglePage(i)
    }
  }
}

const renderSinglePage = async (num) => {
  if (renderedPageNumbers.value.has(num)) return
  
  try {
    const page = await pdfDocInstance.getPage(num)
    const viewport = page.getViewport({ scale: scale.value })
    
    if (renderedPages.value[num - 1]) {
      renderedPages.value[num - 1].width = viewport.width
      renderedPages.value[num - 1].height = viewport.height
      renderedPages.value[num - 1].loaded = true
    }
    
    await nextTick()
    
    const canvas = canvasRefs.value[num - 1]
    if (canvas) {
      const ctx = canvas.getContext('2d')
      await page.render({ canvasContext: ctx, viewport }).promise
    }
    
    const textLayerDiv = textLayerRefs.value[num - 1]
    if (textLayerDiv) {
      try {
        const textContent = await page.getTextContent()
        textLayerDiv.innerHTML = ''
        textLayerDiv.style.setProperty('--scale-factor', viewport.scale)
        await pdfjsLib.renderTextLayer({ textContentSource: textContent, container: textLayerDiv, viewport, textDivs: [] }).promise
      } catch (e) {}
    }
    
    renderedPageNumbers.value.add(num)
  } catch (err) {
    console.error(`渲染页面 ${num} 失败:`, err)
  }
}

const prevPage = () => { 
  if (currentPageNum.value > 1) { 
    currentPageNum.value--
    scrollToPage(currentPageNum.value)
  } 
}

const nextPage = () => { 
  if (currentPageNum.value < totalPages.value) { 
    currentPageNum.value++
    scrollToPage(currentPageNum.value)
  } 
}

const scrollToPage = (pageNum) => {
  const container = document.querySelector('.pdf-render-container')
  const pageElement = document.querySelector(`[data-page-num="${pageNum}"]`)
  if (container && pageElement) {
    container.scrollTo({
      top: pageElement.offsetTop - 50,
      behavior: 'smooth'
    })
  }
}

const zoomIn = () => {
  if (scale.value < 3) {
    scale.value = Math.round((scale.value + 0.1) * 10) / 10
    reRenderLoadedPages()
  }
}

const zoomOut = () => {
  if (scale.value > 0.5) {
    scale.value = Math.round((scale.value - 0.1) * 10) / 10
    reRenderLoadedPages()
  }
}

const fitToWidth = () => {
  const container = document.querySelector('.pdf-render-container')
  if (container && pdfDocInstance) {
    const containerWidth = container.clientWidth - 40
    pdfDocInstance.getPage(1).then(page => {
      const viewport = page.getViewport({ scale: 1 })
      const newScale = containerWidth / viewport.width
      scale.value = Math.round(newScale * 10) / 10
      reRenderLoadedPages()
    })
  }
}

const reRenderLoadedPages = async () => {
  renderedPageNumbers.value = new Set()
  for (let i = 1; i <= totalPages.value; i++) {
    if (renderedPages.value[i - 1] && renderedPages.value[i - 1].loaded) {
      await renderSinglePage(i)
    }
  }
}

const handleTextSelection = (pageNum) => {
  setTimeout(() => {
    const selection = window.getSelection()
    const text = selection.toString().trim()
    if (text.length > 0) {
      currentPageNum.value = pageNum
      const range = selection.getRangeAt(0)
      currentSelectionRects.value = Array.from(range.getClientRects())

      const firstRect = currentSelectionRects.value[0]
      menuX.value = firstRect.left + firstRect.width / 2
      menuY.value = firstRect.top - 70
      showSelectionMenu.value = true
    } else {
      showSelectionMenu.value = false
      currentSelectionRects.value = []
    }
  }, 50)
}

const executeHighlight = () => {
  if (currentSelectionRects.value.length === 0) return
  
  const selection = window.getSelection()
  const text = selection.toString().trim()
  
  const textLayerDiv = textLayerRefs.value[currentPageNum.value - 1]
  if (!textLayerDiv) return
  
  const layerRect = textLayerDiv.getBoundingClientRect()
  const annotationId = `highlight_${Date.now()}`

  currentSelectionRects.value.forEach((rect, index) => {
    allHighlights.value.push({
      id: annotationId,
      type: 'highlight',
      page: currentPageNum.value,
      top: (rect.top - layerRect.top) / scale.value,
      left: (rect.left - layerRect.left) / scale.value,
      width: rect.width / scale.value,
      height: rect.height / scale.value,
      color: 'rgba(250, 204, 21, 0.45)',
      content: index === 0 ? text : '',
      y: (rect.top - layerRect.top) / scale.value
    })
  })

  showSelectionMenu.value = false
  window.getSelection().empty()
  currentSelectionRects.value = []
}

const executeUnderline = () => {
  if (currentSelectionRects.value.length === 0) return
  
  const selection = window.getSelection()
  const text = selection.toString().trim()
  
  const textLayerDiv = textLayerRefs.value[currentPageNum.value - 1]
  if (!textLayerDiv) return
  
  const layerRect = textLayerDiv.getBoundingClientRect()
  const annotationId = `underline_${Date.now()}`

  currentSelectionRects.value.forEach((rect, index) => {
    allHighlights.value.push({
      id: annotationId,
      type: 'underline',
      page: currentPageNum.value,
      top: (rect.top - layerRect.top) / scale.value,
      left: (rect.left - layerRect.left) / scale.value,
      width: rect.width / scale.value,
      height: rect.height / scale.value,
      color: 'rgba(239, 68, 68, 0.8)',
      content: index === 0 ? text : '',
      y: (rect.top - layerRect.top) / scale.value
    })
  })

  showSelectionMenu.value = false
  window.getSelection().empty()
  currentSelectionRects.value = []
}

const executeExcerpt = () => {
  const selection = window.getSelection()
  const text = selection.toString().trim()
  if (!text) return

  allHighlights.value.push({
    id: `excerpt_${Date.now()}`,
    type: 'excerpt',
    page: currentPageNum.value,
    content: text,
    note: '',
    time: new Date().toLocaleTimeString()
  })

  showSelectionMenu.value = false
  window.getSelection().empty()
  currentSelectionRects.value = []
}

const deleteAnnotation = (id) => {
  if (!id) return
  allHighlights.value = allHighlights.value.filter(h => h.id !== id)
}

const jumpToAnnotation = (item) => {
  if (item.page !== currentPageNum.value) {
    currentPageNum.value = item.page
    scrollToPage(item.page)
  }
}

document.addEventListener('mousedown', (e) => {
  if (!e.target.closest('.selection-toolbar') && !e.target.closest('.page-text-layer')) {
    showSelectionMenu.value = false
  }
  if (!e.target.closest('.translation-popup') && !e.target.closest('.page-text-layer') && !e.target.closest('.tool-btn.translate')) {
    showTranslation.value = false
  }
})

const handleScroll = (e) => {
  const container = e.target
  if (!container) return
  
  const containerTop = container.scrollTop
  const containerBottom = containerTop + container.clientHeight
  
  let nearestPage = currentPageNum.value
  let minDist = Infinity
  
  const pageEls = document.querySelectorAll('.page-wrapper')
  for (let i = 0; i < pageEls.length; i++) {
    const el = pageEls[i]
    const elTop = el.offsetTop
    const elBottom = elTop + el.offsetHeight
    const elCenter = elTop + el.offsetHeight / 2
    
    const distToCenter = Math.abs(elCenter - (containerTop + container.clientHeight / 2))
    if (distToCenter < minDist) {
      minDist = distToCenter
      nearestPage = i + 1
    }
    
    if (elBottom > containerTop - 800 && elTop < containerBottom + 800) {
      const pageNum = i + 1
      if (!renderedPageNumbers.value.has(pageNum)) {
        scheduleLazyRender(pageNum)
      }
    }
  }
  
  currentPageNum.value = nearestPage
}

const handleCanvasClick = (e) => {
  const selection = window.getSelection()
  const selectedText = selection.toString().trim()
  if (selectedText.length > 0) return
  
  const target = e.target.closest('.page-wrapper')
  if (!target) return
  const rect = target.getBoundingClientRect()
  const clickX = e.clientX - rect.left
  
  if (clickX < rect.width * 0.3) {
    prevPage()
  } else if (clickX > rect.width * 0.7) {
    nextPage()
  }
}

onMounted(() => {
  if (props.pdfPath) {
    loadPdfFromPath(props.pdfPath)
  }
})

watch(() => props.pdfPath, (newPath) => {
  if (newPath) {
    loadPdfFromPath(newPath)
  }
})
</script>

<style scoped>
* { margin: 0; padding: 0; box-sizing: border-box; }

.pdf-workspace { 
  display: flex; 
  height: 100%; 
  width: 100%; 
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
}

.pdf-sidebar {
  width: 300px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  z-index: 20;
  box-shadow: 2px 0 12px rgba(15, 23, 42, 0.04);
}

.sidebar-header {
  padding: 20px 20px 16px;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  color: white;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sidebar-title { font-size: 15px; font-weight: 600; color: white; }

.annotation-count {
  background: rgba(79, 70, 229, 0.6);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}

.sidebar-content { flex: 1; padding: 16px; overflow-y: auto; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
  color: #94a3b8;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.7; }
.hint { font-size: 12px; margin-top: 4px; opacity: 0.8; }

.annotation-list { display: flex; flex-direction: column; gap: 12px; }

.annotation-card {
  background: white;
  border-radius: 12px;
  padding: 14px;
  border: 1px solid #e2e8f0;
  transition: all 0.25s;
  cursor: pointer;
}
.annotation-card:hover { border-color: #cbd5e1; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05); transform: translateY(-2px); }
.annotation-card:active { transform: scale(0.98); }
.annotation-card.type-excerpt { border-left: 3px solid #4F46E5; }
.annotation-card.type-highlight { border-left: 3px solid #F59E0B; }
.annotation-card.type-underline { border-left: 3px solid #EF4444; }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.card-meta { display: flex; align-items: center; gap: 8px; }
.page-badge { font-size: 11px; font-weight: 700; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: white; padding: 3px 8px; border-radius: 6px; }
.type-label { font-size: 12px; color: #64748b; }
.delete-btn { background: transparent; border: none; color: #cbd5e1; cursor: pointer; padding: 4px; border-radius: 6px; transition: all 0.2s; display: flex; align-items: center; justify-content: center; }
.delete-btn:hover { background: #fee2e2; color: #ef4444; }

.card-content { font-size: 13px; color: #374151; line-height: 1.6; }
.excerpt-quote { padding-left: 10px; border-left: 2px solid #e2e8f0; font-style: italic; color: #475569; margin-bottom: 10px; }
.note-textarea { width: 100%; box-sizing: border-box; border: 1px solid #e2e8f0; background: #f8fafc; border-radius: 8px; padding: 8px 10px; font-size: 13px; color: #1e293b; resize: vertical; transition: all 0.2s; outline: none; font-family: inherit; }
.note-textarea:focus { background: white; border-color: #4F46E5; box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1); }
.note-textarea::placeholder { color: #94a3b8; }
.highlight-preview { display: flex; align-items: flex-start; gap: 8px; color: #64748b; font-size: 12px; }
.color-dot { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; margin-top: 2px; }
.highlight-content { font-size: 13px; color: #374151; line-height: 1.5; word-break: break-all; }

.pdf-main { flex: 1; display: flex; flex-direction: column; position: relative; background: #f1f5f9; }
.pdf-toolbar { display: flex; justify-content: space-between; padding: 12px 20px; background: white; border-bottom: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04); align-items: center; }
.toolbar-left, .toolbar-right, .toolbar-center { display: flex; align-items: center; gap: 12px; }
.icon-btn, .zoom-btn, .nav-btn { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: white; border: 1px solid #e2e8f0; border-radius: 8px; cursor: pointer; color: #475569; transition: all 0.2s; }
.icon-btn:hover, .zoom-btn:hover:not(:disabled), .nav-btn:hover:not(:disabled) { background: #f1f5f9; color: #4F46E5; border-color: #cbd5e1; }
.zoom-btn:disabled, .nav-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.file-info { display: flex; align-items: center; gap: 8px; }
.file-icon { font-size: 18px; }
.file-name { font-size: 14px; font-weight: 600; color: #1e293b; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.zoom-controls { display: flex; align-items: center; gap: 8px; background: #f8fafc; padding: 4px; border-radius: 10px; border: 1px solid #e2e8f0; }
.zoom-value { font-size: 13px; font-weight: 500; color: #475569; min-width: 45px; text-align: center; }
.page-indicator { font-size: 14px; font-weight: 600; color: #374151; min-width: 80px; text-align: center; }

.pdf-render-container { flex: 1; overflow: auto; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 24px; min-height: 0; }
.pages-container { display: flex; flex-direction: column; align-items: center; gap: 20px; }
.page-wrapper { position: relative; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08); border-radius: 8px; overflow: hidden; background: white; }
.pdf-canvas { display: block; background: white; }
.page-loading-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: white;
  z-index: 40;
  color: #94a3b8;
  font-size: 13px;
  gap: 8px;
}
.page-highlight-layer { position: absolute; top: 0; left: 0; pointer-events: none; z-index: 50; }
.page-text-layer { position: absolute; left: 0; top: 0; overflow: hidden; opacity: 1; line-height: 1.0; z-index: 100; pointer-events: auto; user-select: text; }
:deep(.page-text-layer > span), :deep(.page-text-layer br) { color: transparent !important; position: absolute; white-space: pre; cursor: text; transform-origin: 0% 0%; pointer-events: auto; user-select: text; }
.page-text-layer ::selection { background: rgba(79, 70, 229, 0.25) !important; color: transparent !important; }
:deep(.page-text-layer > span)::selection { background: rgba(79, 70, 229, 0.25) !important; color: transparent !important; }

.selection-toolbar { position: fixed; z-index: 999999; transform: translate(-50%, 0); background: white; padding: 8px; border-radius: 12px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15); border: 1px solid #e2e8f0; }
.selection-tools { display: flex; gap: 4px; align-items: center; }
.tool-btn { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 8px 12px; background: transparent; border: none; border-radius: 8px; cursor: pointer; transition: all 0.2s; color: #475569; }
.tool-btn:hover { background: #f1f5f9; }
.tool-btn.highlight:hover { background: linear-gradient(135deg, rgba(250, 204, 21, 0.15) 0%, rgba(245, 158, 11, 0.15) 100%); color: #D97706; }
.tool-btn.underline:hover { background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%); color: #DC2626; }
.tool-btn.excerpt:hover { background: linear-gradient(135deg, rgba(79, 70, 229, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%); color: #4F46E5; }
.tool-icon { font-size: 18px; }
.tool-label { font-size: 11px; font-weight: 600; }
.tool-divider { width: 1px; height: 32px; background: #e2e8f0; margin: 0 4px; }

.custom-scroll::-webkit-scrollbar { width: 8px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; transition: background 0.2s; }
.custom-scroll::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

.ai-read-btn { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; border: none; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 10px rgba(139, 92, 246, 0.3); transition: all 0.2s ease; }
.ai-read-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4); }

.ai-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.3); z-index: 1000; display: flex; justify-content: flex-end; }
.ai-panel { width: 380px; height: 100%; background: #f8fafc; box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1); animation: slideIn 0.3s ease; }
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
.ai-panel-container { padding: 24px; height: 100%; display: flex; flex-direction: column; min-height: 0; }
.ai-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 12px; flex-shrink: 0; }
.ai-header h3 { margin: 0; font-size: 18px; background: linear-gradient(135deg, #4F46E5 0%, #9333ea 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.ai-empty, .ai-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; text-align: center; color: #64748b; font-size: 14px; }
.ai-sparkle { font-size: 48px; margin-bottom: 16px; animation: pulse 2s infinite; }
@keyframes pulse { 0% { transform: scale(1); opacity: 0.8; } 50% { transform: scale(1.1); opacity: 1; text-shadow: 0 0 20px rgba(139, 92, 246, 0.5); } 100% { transform: scale(1); opacity: 0.8; } }
.ai-generate-btn { margin-top: 24px; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); color: white; border: none; padding: 10px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3); transition: all 0.2s; }
.ai-generate-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4); }
.ai-report-content { display: flex; flex-direction: column; gap: 16px; padding-bottom: 30px; overflow-y: auto; flex: 1; min-height: 0; }
.report-module { background: white; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
.module-title { margin: 0 0 8px 0; font-size: 15px; color: #1e293b; display: flex; align-items: center; gap: 8px; }
.module-icon { font-size: 16px; }
.module-text { margin: 0; font-size: 13px; color: #475569; line-height: 1.6; }
.ai-action-btn {
  margin-top: 8px;
  background: white;
  border: 1px solid #cbd5e1;
  color: #4F46E5;
  padding: 10px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-action-btn:hover {
  background: #f8fafc;
  border-color: #4F46E5;
}

.ai-action-btn.secondary {
  border-color: #94a3b8;
  color: #64748b;
}

.ai-action-btn.secondary:hover {
  border-color: #64748b;
  background: #f1f5f9;
  color: #475569;
}

.ai-actions-row {
  display: flex;
  gap: 10px;
  margin-top: 8px;
}

.ai-actions-row .ai-action-btn {
  flex: 1;
  margin-top: 0;
}
.mt-4 { margin-top: 16px; }
.loading-spinner { width: 36px; height: 36px; border: 3px solid #e2e8f0; border-top-color: #8b5cf6; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ================= ✨ AI 双核引擎选择器样式 ================= */
.ai-mode-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  padding: 0 10px;
}

.ai-mode-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: white;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.ai-mode-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.06);
}

.ai-mode-btn.summary-mode:hover {
  border-color: #6366f1;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
}

.ai-mode-btn.review-mode:hover {
  border-color: #10b981;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%);
}

.btn-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-icon {
  font-size: 18px;
}

.btn-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

/* ================= 🌐 划词翻译专属样式 ================= */
.tool-btn.translate:hover {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.1) 0%, rgba(56, 189, 248, 0.1) 100%);
  color: #0284c7;
}

.translation-popup {
  position: fixed;
  z-index: 999999;
  width: 320px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.15);
  border: 1px solid #e2e8f0;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: popup-fade 0.2s ease-out;
}

@keyframes popup-fade {
  from { opacity: 0; transform: translate(-50%, -10px); }
  to { opacity: 1; transform: translate(-50%, 0); }
}

.trans-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.trans-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  display: flex;
  align-items: center;
}

.trans-body {
  padding: 14px;
  max-height: 200px;
  overflow-y: auto;
  font-size: 13px;
  line-height: 1.6;
  color: #1e293b;
}

.trans-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #64748b;
  font-size: 13px;
}

.loading-spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid #e2e8f0;
  border-top-color: #0ea5e9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.trans-result {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.trans-footer {
  padding: 8px 14px;
  border-top: 1px solid #f1f5f9;
  background: #f8fafc;
  display: flex;
  justify-content: flex-end;
}

.trans-action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: white;
  border: 1px solid #cbd5e1;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.trans-action-btn:hover {
  background: #f1f5f9;
  color: #4F46E5;
  border-color: #cbd5e1;
}
</style>
