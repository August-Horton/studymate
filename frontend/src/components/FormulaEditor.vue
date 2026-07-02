<template>
  <div class="formula-editor-container">
    <header class="editor-header">
      <h3 class="title">✨ 可视化公式编辑器</h3>
      <div class="header-actions">
        <van-button size="small" icon="revoke" @click="undo" :disabled="!canUndo">撤销</van-button>
        <van-button size="small" icon="play" @click="redo" :disabled="!canRedo">重做</van-button>
        <van-button size="small" type="primary" icon="success" @click="insertToNote">插入到笔记</van-button>
      </div>
    </header>

    <div class="visual-editor-section">
      <div class="preview-label">可视化交互区 (点击虚线框直接输入)</div>
      <div class="mathlive-wrapper" ref="mathContainerRef">
      </div>
    </div>

    <div class="quick-toolbar">
      <van-tabs v-model:active="activeTab" shrink>
        <van-tab title="常用结构">
          <div class="symbol-grid">
            <button v-for="item in commonSymbols" :key="item.label" class="symbol-btn" @click="insertSymbol(item.value)" :title="item.label">
              <span class="symbol-label" v-html="renderStaticMath(item.display || item.value)"></span>
            </button>
          </div>
        </van-tab>
        <van-tab title="微积分/极限">
          <div class="symbol-grid">
            <button v-for="item in calcSymbols" :key="item.label" class="symbol-btn" @click="insertSymbol(item.value)" :title="item.label">
              <span class="symbol-label" v-html="renderStaticMath(item.display || item.value)"></span>
            </button>
          </div>
        </van-tab>
        <van-tab title="希腊字母">
          <div class="symbol-grid">
            <button v-for="item in greekSymbols" :key="item.label" class="symbol-btn" @click="insertSymbol(item.value)" :title="item.label">
              <span class="symbol-label" v-html="renderStaticMath(item.display || item.value)"></span>
            </button>
          </div>
        </van-tab>
      </van-tabs>
    </div>

    <div class="code-section">
      <div class="preview-label">LaTeX 源码区</div>
      <textarea
        v-model="formula"
        class="latex-textarea custom-scroll"
        placeholder="在此输入 LaTeX 语法，或直接在上方交互区编辑..."
        @input="handleTextareaInput"
      ></textarea>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { MathfieldElement } from 'mathlive'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { showToast } from 'vant'

const emit = defineEmits(['insert', 'close'])

// ================= 核心状态 =================
const formula = ref('')
const activeTab = ref(0)
const mathContainerRef = ref(null)
let mf = null // MathLive 实例

// 历史记录机制
const history = ref([''])
const historyIndex = ref(0)

const recordHistory = (val) => {
  if (history.value[historyIndex.value] === val) return
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1)
  }
  history.value.push(val)
  historyIndex.value = history.value.length - 1
}

const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

const undo = () => {
  if (canUndo.value) {
    historyIndex.value--
    updateBoth(history.value[historyIndex.value])
  }
}

const redo = () => {
  if (canRedo.value) {
    historyIndex.value++
    updateBoth(history.value[historyIndex.value])
  }
}

const updateBoth = (val) => {
  formula.value = val
  if (mf) mf.value = val
}

// ================= 引擎挂载与双向绑定 =================
onMounted(() => {
  // 初始化 MathLive 可视化引擎
  mf = new MathfieldElement()
  
  mf.style.width = '100%'
  mf.style.fontSize = '28px'
  mf.style.padding = '20px'
  mf.style.border = '1px solid transparent'
  mf.style.outline = 'none'
  mf.style.textAlign = 'center'
  mf.style.backgroundColor = 'transparent'
  mf.mathVirtualKeyboardPolicy = 'manual'

  // MathLive -> Vue
  mf.addEventListener('input', () => {
    formula.value = mf.value
    recordHistory(mf.value)
  })

  mathContainerRef.value.appendChild(mf)
})

onBeforeUnmount(() => {
  if (mf) mf.remove()
})

// Vue -> MathLive
const handleTextareaInput = () => {
  if (mf) mf.value = formula.value
  recordHistory(formula.value)
}

// ================= 静态工具栏渲染 (KaTeX) =================
const renderStaticMath = (tex) => {
  try {
    return katex.renderToString(tex, { throwOnError: false })
  } catch (e) {
    return tex
  }
}

// ================= 工具栏插入逻辑 (MathLive) =================
const insertSymbol = (tex) => {
  if (!mf) return
  mf.insert(tex) // MathLive 会自动处理 #? 占位符并聚焦
  mf.focus()
  
  formula.value = mf.value
  recordHistory(mf.value)
}

const insertToNote = () => {
  if (!formula.value.trim()) {
    showToast('公式不能为空')
    return
  }
  // 输出标准的 LaTeX 字符串，外层的 KaTeX 可以完美解析它
  emit('insert', `$$${formula.value}$$`)
}

// ================= 符号库配置 =================
// display: 用于 KaTeX 渲染按钮图标；value: 用于 MathLive 智能插入 (#? 是占位符)
const commonSymbols = [
  { label: '分数', display: '\\frac{x}{y}', value: '\\frac{#?}{#?}' },
  { label: '根号', display: '\\sqrt{x}', value: '\\sqrt{#?}' },
  { label: '上标', display: 'x^2', value: '^{#?}' },
  { label: '下标', display: 'x_i', value: '_{#?}' },
  { label: '括号', display: '\\left( x \\right)', value: '\\left(#?\\right)' },
  { label: '矩阵', display: '\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}', value: '\\begin{bmatrix}#? & #? \\\\ #? & #?\\end{bmatrix}' },
]

const calcSymbols = [
  { label: '求和', display: '\\sum', value: '\\sum_{#?}^{#?}' },
  { label: '积分', display: '\\int', value: '\\int_{#?}^{#?}' },
  { label: '极限', display: '\\lim', value: '\\lim_{#? \\to #?}' },
  { label: '无穷', display: '\\infty', value: '\\infty' },
  { label: '偏导', display: '\\partial', value: '\\frac{\\partial #?}{\\partial #?}' },
]

const greekSymbols = [
  { label: 'alpha', display: '\\alpha', value: '\\alpha' },
  { label: 'beta', display: '\\beta', value: '\\beta' },
  { label: 'gamma', display: '\\gamma', value: '\\gamma' },
  { label: 'theta', display: '\\theta', value: '\\theta' },
  { label: 'lambda', display: '\\lambda', value: '\\lambda' },
  { label: 'mu', display: '\\mu', value: '\\mu' },
  { label: 'pi', display: '\\pi', value: '\\pi' },
  { label: 'Sigma', display: '\\Sigma', value: '\\Sigma' },
]
</script>

<style scoped>
.formula-editor-container {
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
}

.title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.preview-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.visual-editor-section {
  padding: 16px;
  background: #f8fafc;
}

.mathlive-wrapper {
  background: white;
  min-height: 120px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  cursor: text;
}

.mathlive-wrapper:focus-within {
  border-color: #4F46E5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.quick-toolbar {
  background: white;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

:deep(.van-tabs__nav) { background: transparent; }
:deep(.van-tab) { color: #64748b; font-size: 13px; padding: 0 16px; }
:deep(.van-tab--active) { color: #4F46E5; font-weight: 600; }

.symbol-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  background: #f8fafc;
}

.symbol-btn {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.symbol-btn:hover {
  background: #eef2ff;
  border-color: #c7d2fe;
  color: #4F46E5;
}

.symbol-label {
  font-size: 16px;
  pointer-events: none;
}

.code-section {
  padding: 16px;
  background: white;
}

.latex-textarea {
  width: 100%;
  height: 80px;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 14px;
  color: #334155;
  resize: vertical;
  outline: none;
}

.latex-textarea:focus {
  background: white;
  border-color: #4F46E5;
}

.custom-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
.custom-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
</style>
