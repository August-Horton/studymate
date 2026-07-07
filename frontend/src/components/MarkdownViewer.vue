<template>
  <div class="markdown-body" ref="contentRef" @click="handleClick"></div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const props = defineProps({ content: String })
const emit = defineEmits(['link-click'])
const contentRef = ref(null)

// 定义 Obsidian 风格的 Wikilink 扩展
const wikilinkExtension = {
  name: 'wikilink',
  level: 'inline',
  start(src) { return src.match(/\[\[/)?.index; },
  tokenizer(src, tokens) {
    const rule = /^\[\[([^\]]+)\]\]/;
    const match = rule.exec(src);
    if (match) {
      return {
        type: 'wikilink',
        raw: match[0],
        text: match[1].trim()
      };
    }
  },
  renderer(token) {
    return `<span class="internal-link" data-target="${token.text}">${token.text}</span>`;
  }
};

// 挂载到 marked 引擎
marked.use({ extensions: [wikilinkExtension] })

defineExpose({ contentRef })

const handleClick = (event) => {
  if (event.target.classList.contains('internal-link')) {
    const targetTitle = event.target.getAttribute('data-target')
    emit('link-click', targetTitle)
  }
}

function renderContent(rawText) {
  if (!rawText) return ''

  let text = rawText

  // ========== 1. 解码 HTML 实体 ==========
  text = text
    .replace(/&#x([0-9a-fA-F]+);/gi, (_, hex) => String.fromCharCode(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCharCode(parseInt(dec, 10)))
    .replace(/&gt;/g, '>').replace(/&lt;/g, '<')
    .replace(/&amp;/g, '&').replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ')

  // ========== 2. 只清理旧的 KaTeX 错误 HTML 标签（不破坏其他！） ==========
  text = text.replace(/<span[^>]*katex-error[^>]*>.*?<\/span>/gi, '')
  text = text.replace(/<span[^>]*katex[^>]*>(.*?)<\/span>/gi, '$1')
  text = text.replace(/<\/?span[^>]*>/gi, '')

  // ========== 3. 修复损坏的 LaTeX 命令 ==========
  // \frac a b → \frac{a}{b}
  text = text.replace(/\\frac\s+([^\s{]+?)\s+([^\s{]+?)(?=\s|$|[,，、。;；:：])/g, '\\frac{$1}{$2}')
  // \sqrt a → \sqrt{a}
  text = text.replace(/\\sqrt\s+([^\s{]+?)(?=\s|$|[,，、。;；:：])/g, '\\sqrt{$1}')
  // 修复 \left^2 / \right^2
  text = text.replace(/\\left\s*\^(\d+)/g, '^{$1}')
  text = text.replace(/\\right\s*\^(\d+)/g, '^{$1}')
  text = text.replace(/\\left\s*\\frac/g, '\\frac')
  text = text.replace(/\\right\s*\\frac/g, '\\frac')
  text = text.replace(/\\left\s*\(/g, '(').replace(/\\right\s*\)/g, ')')
  text = text.replace(/\\left\s*\[/g, '[').replace(/\\right\s*\]/g, ']')

  // ========== 4. 智能包裹裸的 LaTeX 命令 ==========
  const formulaStore = []
  text = text.replace(/\$[^$]*?\$/g, (m) => {
    formulaStore.push(m)
    return `\x00FORMULA${formulaStore.length - 1}\x00`
  })

  let result = ''
  let i = 0
  while (i < text.length) {
    const cmdIdx = text.indexOf('\\', i)
    if (cmdIdx === -1) {
      result += text.slice(i)
      break
    }

    const before = text.slice(0, cmdIdx)
    const openCount = (before.match(/\x00FORMULA/g) || []).length
    const closeCount = (before.match(/\x00\x00/g) || []).length
    if (openCount !== closeCount) {
      result += text.slice(i, cmdIdx + 1)
      i = cmdIdx + 1
      continue
    }

    result += text.slice(i, cmdIdx)

    let start = cmdIdx
    const lookback = result.slice(Math.max(0, cmdIdx - 20), cmdIdx)
    const varMatch = lookback.match(/([a-zA-Z]\s*[=≠]\s*|[a-zA-Z]\s*(?:[+\-*/]\s*[a-zA-Z]\s*)*)$/)
    if (varMatch) start = cmdIdx - varMatch[0].length

    let end = cmdIdx
    let braceDepth = 0
    let startedBraces = false
    while (end < text.length) {
      const ch = text[end]
      if (ch === '{') { braceDepth++; startedBraces = true }
      else if (ch === '}') {
        braceDepth--
        if (braceDepth < 0) break
      } else if (ch === '\\' && braceDepth === 0 && end > cmdIdx) {
        const nextCmd = text.slice(end).match(/^\\[a-zA-Z]+/)
        if (nextCmd) {
          const prevCh = text[end - 1]
          if (/[\s><=≠±×÷+\-*/]/.test(prevCh)) { end++; continue }
          break
        }
        break
      } else if (braceDepth === 0 && startedBraces && /[\u4e00-\u9fff，。、；：]/.test(ch)) {
        break
      }
      end++
    }

    const expr = text.slice(start, end).trim()
    if (/\\[a-zA-Z]+/.test(expr)) {
      result += `$${expr}$`
    } else {
      result += expr
    }
    i = end
  }
  text = result
  text = text.replace(/\x00FORMULA(\d+)\x00/g, (_, idx) => formulaStore[parseInt(idx)])

  // ========== 5. 【关键修正】先渲染 Markdown（生成基础 HTML） ==========
  // 暂时使用标准渲染，避免版本冲突
  marked.setOptions({ 
    breaks: true, 
    gfm: true
  })
  
  let html = marked.parse(text)

  // ========== 6. 【关键修正】后渲染 LaTeX 公式（在 HTML 中找 $...$） ==========
  // 这样 marked 就不会破坏 KaTeX 生成的 SVG 了！
  const decodeHtml = (str) => {
    return str.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&')
  }

  // 处理 $$...$$ 块公式
  html = html.replace(/\$\$([\s\S]*?)\$\$/g, (_, formula) => {
    try {
      return katex.renderToString(decodeHtml(formula).trim(), { displayMode: true, throwOnError: false })
    } catch (e) {
      return `<div class="math-block">${decodeHtml(formula).trim()}</div>`
    }
  })

  // 处理 $...$ 行内公式
  html = html.replace(/\$([^$]+?)\$/g, (_, formula) => {
    try {
      return katex.renderToString(decodeHtml(formula).trim(), { displayMode: false, throwOnError: false })
    } catch (e) {
      return `<span class="math-inline">${decodeHtml(formula).trim()}</span>`
    }
  })

  // 清理残留的空段落
  html = html.replace(/<p>\s*<\/p>/g, '')

  // ========== 7.5. 【代码块美化】为代码块添加带框样式 ==========
  // 找到所有 <pre><code class="language-xxx"> 结构，包装成带标题栏的代码框
  html = html.replace(
    /<pre><code class="language-([^"]+)">([\s\S]*?)<\/code><\/pre>/g,
    (_, lang, code) => {
      const decodedCode = decodeHtml(code)
      const safeLang = lang || 'text'
      return `<div class="code-block-wrapper" data-lang="${safeLang}">
        <div class="code-block-header">
          <span class="code-lang-label">${safeLang}</span>
          <div class="code-block-actions">
            <button class="code-copy-btn" onclick="window.__copyCode && window.__copyCode(this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              复制
            </button>
          </div>
        </div>
        <pre class="code-block-body"><code class="language-${safeLang}">${decodedCode}</code></pre>
      </div>`
    }
  )

  // 处理没有语言标识的代码块
  html = html.replace(
    /<pre><code>([\s\S]*?)<\/code><\/pre>/g,
    (_, code) => {
      const decodedCode = decodeHtml(code)
      return `<div class="code-block-wrapper" data-lang="text">
        <div class="code-block-header">
          <span class="code-lang-label">text</span>
          <div class="code-block-actions">
            <button class="code-copy-btn" onclick="window.__copyCode && window.__copyCode(this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              复制
            </button>
          </div>
        </div>
        <pre class="code-block-body"><code>${decodedCode}</code></pre>
      </div>`
    }
  )

  // ========== 8. 【图片后缀优化】处理过长的 base64 图片 ==========
  // 替换过长的 base64 图片，只显示图片+缩略信息
  html = html.replace(
    /<img\s+src="(data:image\/([^;]+);base64,)([^"]{40,})"([^>]*)>/g,
    (match, prefix, format, base64Data, rest) => {
      const sizeKB = Math.round((base64Data.length * 0.75) / 1024)
      return `<div class="image-card" data-full-src="${prefix}${base64Data}" data-format="${format}" data-size="${sizeKB}">
        <div class="image-card-preview">
          <img src="${prefix}${base64Data}" loading="lazy" />
          <div class="image-card-overlay">
            <span class="image-format-badge">${format.toUpperCase()}</span>
            <span class="image-size-badge">${sizeKB} KB</span>
            <span class="image-hint">悬停查看完整信息</span>
          </div>
        </div>
      </div>`
    }
  )

  return html
}

onMounted(() => {
  if (contentRef.value) contentRef.value.innerHTML = renderContent(props.content)

  // 全局代码复制函数
  if (!window.__copyCode) {
    window.__copyCode = function(btn) {
      const wrapper = btn.closest('.code-block-wrapper')
      if (!wrapper) return
      const codeEl = wrapper.querySelector('pre code')
      if (!codeEl) return
      const text = codeEl.innerText
      navigator.clipboard.writeText(text).then(() => {
        const originalText = btn.innerHTML
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          已复制
        `
        btn.classList.add('copied')
        setTimeout(() => {
          btn.innerHTML = originalText
          btn.classList.remove('copied')
        }, 2000)
      }).catch(() => {
        // 降级方案
        const textarea = document.createElement('textarea')
        textarea.value = text
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
        const originalText = btn.innerHTML
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          已复制
        `
        btn.classList.add('copied')
        setTimeout(() => {
          btn.innerHTML = originalText
          btn.classList.remove('copied')
        }, 2000)
      })
    }
  }
})

watch(() => props.content, (newVal) => {
  nextTick(() => {
    if (contentRef.value) contentRef.value.innerHTML = renderContent(newVal)
  })
})
</script>

<style scoped>
.markdown-body {
  padding: 24px 40px;
  background: var(--bg-secondary, #ffffff);
  border-radius: 8px;
  line-height: 1.8;
  font-size: 16px;
  color: var(--text-secondary, #374151);
  min-height: 100%;
  width: 100%;
  box-sizing: border-box;
}

/* Markdown 基础样式 */
.markdown-body :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  margin: 20px 0 14px 0;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--border-color, #e8e8ff);
  color: var(--text-primary, #2d3748);
}
.markdown-body :deep(h2) {
  font-size: 19px;
  font-weight: 600;
  margin: 18px 0 12px 0;
  padding-left: 10px;
  border-left: 3px solid var(--accent-color, #4F46E5);
  color: var(--text-primary, #1a202c);
}
.markdown-body :deep(h3), .markdown-body :deep(h4), .markdown-body :deep(h5), .markdown-body :deep(h6) {
  font-size: 16px;
  font-weight: 600;
  margin: 14px 0 10px 0;
  color: var(--text-primary, #2d3748);
}
.markdown-body :deep(p) {
  margin: 10px 0;
  color: var(--text-secondary, #4b5563);
}
.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 28px;
  margin: 10px 0;
  color: var(--text-secondary, #4b5563);
}
.markdown-body :deep(li) {
  margin: 6px 0;
  color: var(--text-secondary, #4b5563);
}
.markdown-body :deep(em) {
  font-style: italic;
}
.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 14px 0;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 10px 14px;
  text-align: center;
}
.markdown-body :deep(th) {
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  font-weight: 600;
}

/* KaTeX 公式样式优化 */
.markdown-body :deep(.katex-display) {
  margin: 16px 0 !important;
  overflow-x: auto;
}

/* 降级公式样式 */
.markdown-body :deep(.math-block) {
  display: block;
  text-align: center;
  padding: 14px 24px;
  margin: 14px 0;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%);
  border-left: 4px solid #4F46E5;
  border-radius: 8px;
  font-family: 'Cambria Math', 'STIX Two Math', 'Latin Modern Math', 'Times New Roman', serif;
  font-size: 17px;
  color: #1a1a2e;
  letter-spacing: 0.3px;
  overflow-x: auto;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.08);
}
.markdown-body :deep(.math-inline) {
  display: inline;
  padding: 3px 9px;
  margin: 0 3px;
  background: linear-gradient(135deg, #f5f7ff 0%, #eef1ff 100%);
  border-radius: 6px;
  font-family: 'Cambria Math', 'STIX Two Math', 'Latin Modern Math', 'Times New Roman', serif;
  font-size: 15px;
  color: #2d2d6b;
}

/* 图片样式 - 限制尺寸并支持点击放大 */
.markdown-body :deep(img) {
  max-width: 100%;
  max-height: 400px;
  height: auto;
  display: block;
  margin: 12px auto;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.markdown-body :deep(img:hover) {
  transform: scale(1.02);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

/* 图片卡片 - 隐藏过长的 base64 后缀 */
.markdown-body :deep(.image-card) {
  position: relative;
  display: inline-block;
  max-width: 100%;
  margin: 12px auto;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
}
.markdown-body :deep(.image-card:hover) {
  transform: scale(1.02);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}
.markdown-body :deep(.image-card-preview) {
  position: relative;
  display: block;
}
.markdown-body :deep(.image-card-preview img) {
  max-width: 100%;
  max-height: 400px;
  height: auto;
  display: block;
  margin: 0;
  border-radius: 0;
  cursor: default;
  transform: none !important;
  box-shadow: none !important;
}
.markdown-body :deep(.image-card-overlay) {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 12px;
  background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}
.markdown-body :deep(.image-card:hover .image-card-overlay) {
  opacity: 1;
}
.markdown-body :deep(.image-format-badge) {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(79, 70, 229, 0.9);
  color: white;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.markdown-body :deep(.image-size-badge) {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(107, 114, 128, 0.9);
  color: white;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}
.markdown-body :deep(.image-hint) {
  margin-left: auto;
  color: rgba(255, 255, 255, 0.85);
  font-size: 11px;
  font-style: italic;
}

/* 代码块 - DeepSeek 风格带框 */
.markdown-body :deep(.code-block-wrapper) {
  margin: 16px 0;
  border-radius: 12px;
  overflow: hidden;
  background: #1e1e1e;
  border: 1px solid #333;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.markdown-body :deep(.code-block-header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #2d2d2d;
  border-bottom: 1px solid #333;
}

.markdown-body :deep(.code-lang-label) {
  font-size: 13px;
  font-weight: 500;
  color: #9cdcfe;
  font-family: 'Fira Code', Consolas, Monaco, monospace;
  text-transform: lowercase;
}

.markdown-body :deep(.code-block-actions) {
  display: flex;
  gap: 8px;
}

.markdown-body :deep(.code-copy-btn) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 12px;
  color: #d4d4d4;
  background: transparent;
  border: 1px solid #555;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.markdown-body :deep(.code-copy-btn:hover) {
  background: #404040;
  border-color: #666;
  color: #fff;
}

.markdown-body :deep(.code-copy-btn.copied) {
  background: rgba(46, 160, 67, 0.2);
  border-color: #2ea043;
  color: #2ea043;
}

.markdown-body :deep(.code-copy-btn svg) {
  width: 14px;
  height: 14px;
}

.markdown-body :deep(.code-block-body) {
  margin: 0;
  padding: 16px 20px;
  background: #1e1e1e;
  overflow-x: auto;
  max-height: 500px;
}

.markdown-body :deep(.code-block-body code) {
  font-family: 'Fira Code', Consolas, Monaco, monospace;
  font-size: 14px;
  line-height: 1.7;
  color: #d4d4d4;
  background: transparent;
  padding: 0;
  border-radius: 0;
}

/* 行内代码 */
.markdown-body :deep(p code),
.markdown-body :deep(li code),
.markdown-body :deep(td code) {
  display: inline;
  padding: 2px 8px;
  font-family: 'Fira Code', Consolas, Monaco, monospace;
  font-size: 13px;
  color: #dc2626;
  background: #fef2f2;
  border-radius: 4px;
}

/* 黑夜模式下的代码块 */
[data-theme="dark"] .markdown-body :deep(.code-block-wrapper) {
  background: #0d1117;
  border-color: #30363d;
}

[data-theme="dark"] .markdown-body :deep(.code-block-header) {
  background: #161b22;
  border-bottom-color: #30363d;
}

[data-theme="dark"] .markdown-body :deep(.code-lang-label) {
  color: #79c0ff;
}

[data-theme="dark"] .markdown-body :deep(.code-block-body) {
  background: #0d1117;
}

[data-theme="dark"] .markdown-body :deep(.code-block-body code) {
  color: #c9d1d9;
}

[data-theme="dark"] .markdown-body :deep(p code),
[data-theme="dark"] .markdown-body :deep(li code),
[data-theme="dark"] .markdown-body :deep(td code) {
  color: #ff7b72;
  background: rgba(248, 81, 73, 0.1);
}
</style>
