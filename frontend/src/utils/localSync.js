import { ref } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'

const localDirHandle = ref(null)

/**
 * 🛠️ 辅助函数：根据路径字符串（如 "高等数学/微积分"）递归创建并获取嵌套文件夹句柄
 */
const getNestedDirHandle = async (baseHandle, pathStr) => {
  if (!pathStr) return baseHandle
  
  // 按照斜杠分割路径，支持多级目录
  const parts = pathStr.split('/').filter(p => p.trim())
  let currentHandle = baseHandle
  
  for (const part of parts) {
    // 过滤非法字符，防止创建文件夹失败
    const safePart = part.replace(/[\/\\:*?"<>|]/g, '-').trim() || '未分类'
    // 获取或创建下一级文件夹
    currentHandle = await currentHandle.getDirectoryHandle(safePart, { create: true })
  }
  
  return currentHandle
}

/**
 * 将结构化的笔记列表按分类层级同步到本地选定的文件夹
 * @param {Array} notesList 笔记数组流
 */
export const syncNotesToLocalDirectory = async (notesList) => {
  if (!notesList || notesList.length === 0) {
    showFailToast('暂无有效笔记可供同步')
    return
  }

  try {
    // 1. 获取或验证顶级文件夹授权
    if (!localDirHandle.value) {
      localDirHandle.value = await window.showDirectoryPicker({ mode: 'readwrite', startIn: 'documents' })
    } else {
      const permission = await localDirHandle.value.queryPermission({ mode: 'readwrite' })
      if (permission !== 'granted') {
        const request = await localDirHandle.value.requestPermission({ mode: 'readwrite' })
        if (request !== 'granted') {
          localDirHandle.value = null
          showFailToast('未获得本地文件夹读写授权')
          return
        }
      }
    }

    const rootDirHandle = localDirHandle.value
    let syncCount = 0
    const failedNotes = []

    // 2. 遍历笔记，根据层级执行分类写入
    for (const note of notesList) {
      try {
        // 💡 核心逻辑：获取这篇笔记的分类路径（优先用 folder，其次用 course_name，最后用"未分类笔记"）
        let folderPath = note.folder || '未分类笔记'
        
        // 如果没有 folder 但有 course_id，可以用课程名作为分类
        if (folderPath === '未分类笔记' && note.course_name) {
          folderPath = note.course_name
        }
        
        // 自动钻取到目标文件夹（如果本地没有，会自动创建）
        const targetDirHandle = await getNestedDirHandle(rootDirHandle, folderPath)

        // 处理安全文件名
        const safeTitle = note.title 
          ? note.title.replace(/[\/\\:*?"<>|]/g, '-').trim() 
          : `未命名摘录_${note.id || Date.now()}`
        
        const fileName = `${safeTitle}.md`

        // 3. 在对应的【子文件夹】中创建 Markdown 文件
        const fileHandle = await targetDirHandle.getFileHandle(fileName, { create: true })
        
        // 4. 组装 YAML Front Matter 与 Markdown 正文
        const yamlFrontMatter = `---
id: ${note.id || ''}
title: "${safeTitle}"
category: "${folderPath}"
date: ${note.created_at || new Date().toLocaleString()}
source_pdf: "${note.pdf_source || '无'}"
pdf_page: ${note.pdf_page || '无'}
course_id: ${note.course_id || '无'}
tags: "${note.tags || ''}"
---

`
        let markdownBody = `${note.structured_note || note.original_text || note.content || ''}\n\n`
        
        if (note.notes && note.notes.trim()) {
          markdownBody += `### 💡 我的思考与随笔\n\n${note.notes}\n`
        }

        // 5. 写入磁盘
        const writableStream = await fileHandle.createWritable()
        await writableStream.write(yamlFrontMatter + markdownBody)
        await writableStream.close() 
        syncCount++
      } catch (noteError) {
        console.warn(`写入笔记 "${note.title}" 失败:`, noteError)
        failedNotes.push(note.title || '未命名笔记')
      }
    }

    if (failedNotes.length === 0) {
      showSuccessToast(`✨ 已成功同步 ${syncCount} 篇笔记至本地文件夹（按目录结构分类）！`)
    } else {
      showSuccessToast(`✅ 成功同步 ${syncCount} 篇笔记，${failedNotes.length} 篇失败`)
      if (failedNotes.length > 0) {
        console.warn('同步失败的笔记:', failedNotes)
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') return
    console.error('本地同步引擎发生致命错误:', error)
    
    let errorMsg = '本地磁盘写入失败'
    if (error.name === 'QuotaExceededError') {
      errorMsg = '磁盘空间不足，请清理后重试'
    } else if (error.name === 'NotAllowedError') {
      errorMsg = '未获得文件系统访问权限，请重新选择文件夹'
    } else if (error.name === 'SecurityError') {
      errorMsg = '安全限制：请使用 HTTPS 或 localhost 运行'
    } else if (error.name === 'TypeError') {
      errorMsg = '文件句柄已失效，请重新选择同步文件夹'
    } else {
      errorMsg = '本地磁盘写入失败，请检查空间或权限'
    }
    
    showFailToast(errorMsg)
    localDirHandle.value = null
  }
}

export const disconnectLocalDirectory = () => {
  localDirHandle.value = null
  showSuccessToast('已断开本地文件夹连接')
}

export const getLocalSyncStatus = () => {
  return !!localDirHandle.value
}

/**
 * 🛠️ 辅助函数：递归遍历文件夹获取所有 Markdown 文件
 */
const getAllMarkdownFiles = async (dirHandle, rootFolderName = '') => {
  const files = []
  
  for await (const entry of dirHandle.values()) {
    // 将根文件夹名称作为前缀
    const entryPath = rootFolderName 
      ? `${rootFolderName}/${entry.name}` 
      : entry.name
    
    if (entry.kind === 'file' && entry.name.endsWith('.md')) {
      const file = await entry.getFile()
      files.push({
        path: entryPath,
        name: entry.name,
        file: file
      })
    } else if (entry.kind === 'directory') {
      try {
        const subDir = await dirHandle.getDirectoryHandle(entry.name)
        const subFiles = await getAllMarkdownFiles(subDir, entryPath)
        files.push(...subFiles)
      } catch (err) {
        console.warn(`无法访问子目录 ${entry.name}:`, err)
      }
    }
  }
  
  return files
}

/**
 * 🛠️ 辅助函数：解析 YAML Front Matter
 */
const parseFrontMatter = (content) => {
  const frontMatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/
  const match = content.match(frontMatterRegex)
  
  if (!match) {
    return {
      metadata: {},
      body: content.trim()
    }
  }
  
  const yamlStr = match[1]
  const body = match[2].trim()
  const metadata = {}
  
  yamlStr.split('\n').forEach(line => {
    const colonIndex = line.indexOf(':')
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim()
      let value = line.substring(colonIndex + 1).trim()
      
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1)
      }
      
      metadata[key] = value
    }
  })
  
  return { metadata, body }
}

/**
 * 导入本地文件夹中的 Markdown 笔记
 */
export const importNotesFromLocalDirectory = async () => {
  try {
    const dirHandle = await window.showDirectoryPicker({ mode: 'read', startIn: 'documents' })
    
    // 获取选中的根文件夹名称
    const rootFolderName = dirHandle.name
    
    showSuccessToast('正在扫描文件夹...')
    
    const markdownFiles = await getAllMarkdownFiles(dirHandle, rootFolderName)
    
    if (markdownFiles.length === 0) {
      showFailToast('未找到任何 Markdown 文件')
      return
    }
    
    const notes = []
    
    for (const { path, name, file } of markdownFiles) {
      const content = await file.text()
      const { metadata, body } = parseFrontMatter(content)
      
      // 统一路径分隔符（Windows 可能是 \ 或 /）
      const normalizedPath = path.replace(/\\/g, '/')
      const pathParts = normalizedPath.split('/')
      
      // 提取文件夹路径（去掉文件名）
      let folder = ''
      if (pathParts.length > 1) {
        // 取除最后一个（文件名）之外的所有部分作为文件夹路径
        folder = pathParts.slice(0, -1).join('/')
      }
      
      // 如果路径中没有文件夹，尝试使用 metadata.category
      if (!folder && metadata.category) {
        folder = metadata.category
      }
      
      // 清理文件夹名称（移除可能的引号）
      folder = folder.replace(/["']/g, '').trim()
      
      notes.push({
        title: metadata.title || name.replace('.md', ''),
        folder: folder || '默认笔记本', // 如果没有任何文件夹信息，使用默认笔记本
        tags: metadata.tags || '',
        course_id: metadata.course_id && metadata.course_id !== '无' 
          ? parseInt(metadata.course_id) 
          : null,
        original_text: body,
        structured_note: body,
        created_at: metadata.date || new Date().toISOString(),
        pdf_source: metadata.source_pdf || '',
        pdf_page: metadata.pdf_page || null
      })
    }
    
    showSuccessToast(`已扫描到 ${notes.length} 篇笔记，正在导入...`)
    
    const response = await fetch('http://localhost:8000/api/notes/import', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ notes })
    })
    
    if (!response.ok) {
      throw new Error('导入失败')
    }
    
    const result = await response.json()
    showSuccessToast(`✅ 成功导入 ${result.imported || notes.length} 篇笔记！`)
    
    return result.imported || notes.length
  } catch (error) {
    if (error.name === 'AbortError') return
    console.error('导入笔记时发生错误:', error)
    showFailToast('导入失败：' + error.message)
    return 0
  }
}
