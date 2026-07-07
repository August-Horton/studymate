<template>
  <div class="obsidian-workspace">
    
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2 class="sidebar-title">我的知识库</h2>
        <van-button 
          class="graph-button"
          block 
          size="small" 
          type="success" 
          icon="cluster-o" 
          @click="openGraphView"
        >
          🌌 知识图谱
        </van-button>
        <div class="quick-actions">
          <van-button 
            type="default" 
            plain 
            size="small" 
            icon="folder-o" 
            @click="showNewFolderModal = true"
          >
            文件夹
          </van-button>
          <van-button 
            type="success" 
            plain 
            size="small" 
            icon="exchange" 
            @click="handleFolderSync"
          >
            同步
          </van-button>
          <van-button 
            type="warning" 
            plain 
            size="small" 
            icon="down" 
            @click="handleImportNotes"
          >
            导入
          </van-button>
          <van-button 
            type="primary" 
            size="small" 
            icon="plus" 
            @click="openTemplateModal(currentFolder)"
          >
            笔记
          </van-button>
        </div>
      </div>

      <!-- 侧边栏选项卡 -->
      <div class="sidebar-tabs">
        <div 
          class="tab-item" 
          :class="{ 'is-active': activeSidebarTab === 'folder' }"
          @click="activeSidebarTab = 'folder'"
        >
          📁 目录
        </div>
        <div 
          class="tab-item" 
          :class="{ 'is-active': activeSidebarTab === 'outline' }"
          @click="activeSidebarTab = 'outline'"
        >
          📍 大纲
        </div>
        <div 
          class="tab-item" 
          :class="{ 'is-active': activeSidebarTab === 'flashcards' }"
          @click="activeSidebarTab = 'flashcards'; loadFlashcards()"
        >
          🃏 闪卡
        </div>
      </div>

      <!-- 搜索框 -->
      <div class="search-bar">
        <van-search 
          v-model="searchQuery" 
          placeholder="搜索标题或正文内容..." 
          shape="round"
          @update:model-value="handleSearch"
        />
      </div>

      <!-- 搜索结果展示 -->
      <div v-if="searchQuery" class="search-results-list">
        <div v-if="isSearching" style="text-align: center; color: #999; padding: 20px;">
          正在检索中...
        </div>
        
        <div v-else-if="searchResults.length === 0" style="text-align: center; color: #999; padding: 20px;">
          没有找到相关笔记 🧐
        </div>
        
        <div 
          v-else
          v-for="note in searchResults" 
          :key="note.id" 
          class="nav-item"
          :class="{ 'is-active': currentNote?.id === note.id }"
          @click="selectNote(note)"
        >
          <div style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
            <div style="display: flex; align-items: center; overflow: hidden; flex: 1;">
              <van-icon name="search" class="nav-icon" />
              <span class="nav-title" style="flex: 1; margin-right: 8px;">{{ getNoteTitle(note) }}</span>
            </div>
            <div class="note-meta">
              <span class="word-count">{{ formatWordCount(getWordCount(note)) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 目录选项卡内容 -->
      <div v-if="!searchQuery && activeSidebarTab === 'folder'" class="tab-content custom-scroll" 
           @dragover.prevent="handleRootDragOver"
           @dragenter.prevent="isRootDragOver = true"
           @dragleave="isRootDragOver = false"
           @drop.stop="handleRootDrop"
           :class="{ 'is-drag-over': isRootDragOver }">
        <FolderTree 
          v-if="fileTree && (Object.keys(fileTree.children).length > 0 || fileTree.notes.length > 0)"
          :node="fileTree" 
          :currentNoteId="currentNote?.id"
          @select-note="selectNote"
          @open-menu="openNoteMenu"
          @folder-contextmenu="handleFolderContextMenu"
          @move-note="executeNoteMove"
          @move-folder="executeFolderMove"
        />
        <div v-else style="text-align: center; padding: 40px; color: var(--text-tertiary, #9ca3af);">
          暂无笔记，点击上方 + 创建第一篇笔记
        </div>
      </div>

      <!-- 大纲选项卡内容 -->
      <div v-if="!searchQuery && activeSidebarTab === 'outline'" class="tab-content outline-pane custom-scroll">
        <div v-if="tableOfContents.length === 0" class="outline-empty">
          暂无标题层级
        </div>
        <div 
          v-for="(item, index) in tableOfContents" 
          :key="index"
          class="outline-item"
          :class="[`level-${item.level}`, { hidden: isHidden(index) }]"
          @click="scrollToHeading(item)"
        >
          <span 
            v-if="hasChildren(index)" 
            class="collapse-icon"
            :class="{ expanded: expandedSections.includes(index) }"
            @click.stop="toggleSection(index)"
          >
            ▶
          </span>
          <span v-else class="collapse-icon-placeholder">•</span>
          <span class="outline-text">{{ item.text }}</span>
        </div>
      </div>

      <!-- 闪卡选项卡内容 -->
      <div v-if="!searchQuery && activeSidebarTab === 'flashcards'" class="tab-content custom-scroll">
        <div v-if="isLoadingFlashcards" style="text-align: center; padding: 40px; color: #999;">
          <van-loading type="spinner" color="#4F46E5" />
        </div>

        <div v-else-if="flashcards.length === 0" style="text-align: center; padding: 40px; color: #999;">
          <div style="font-size: 56px; margin-bottom: 16px;">🃏</div>
          <div style="font-size: 15px; font-weight: 500; color: var(--text-secondary, #6b7280); margin-bottom: 8px;">还没有闪卡</div>
          <div style="font-size: 12px; color: var(--text-tertiary, #9ca3af);">在笔记中选中文字，点击"制作闪卡"开始吧！</div>
        </div>

        <div v-else>
          <div class="flashcard-section-header">
            <div class="flashcard-count">📚 {{ flashcards.length }} 张闪卡</div>
            <van-button 
              size="small" 
              type="primary" 
              plain 
              icon="play-circle-o"
              @click="startReview"
              :disabled="flashcards.length === 0"
            >
              开始复习
            </van-button>
          </div>

          <div 
            v-for="card in flashcards" 
            :key="card.id" 
            class="flashcard-list-item"
            @click="openSingleCard(card)"
          >
            <div class="flashcard-front">{{ card.front }}</div>
            <div class="flashcard-meta">
              <span style="font-size: 11px; color: var(--text-tertiary, #9ca3af);">
                📄 {{ card.note_title || '未知笔记' }}
              </span>
              <div style="display: flex; gap: 8px; align-items: center;">
                <van-icon 
                  name="eye" 
                  size="14" 
                  color="#4F46E5" 
                  style="cursor: pointer; opacity: 0; transition: opacity 0.2s;"
                  class="flashcard-view"
                  @click.stop="openSingleCard(card)"
                />
                <van-icon 
                  name="cross" 
                  size="14" 
                  color="#ef4444" 
                  style="cursor: pointer; opacity: 0; transition: opacity 0.2s;"
                  class="flashcard-delete"
                  @click.stop="deleteFlashcard(card.id)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="tags-section">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3 class="section-title" style="margin: 0;">🏷️ 标签网络</h3>
          <div style="display: flex; gap: 8px; align-items: center;">
            <span 
              v-if="activeTagFilter" 
              style="font-size: 11px; color: var(--accent-color, #4f46e5); cursor: pointer;" 
              @click="activeTagFilter = ''"
            >
              ❌ 清除筛选
            </span>
            <span 
              v-if="!isDeletingTags"
              style="font-size: 11px; color: #ef4444; cursor: pointer;" 
              @click="isDeletingTags = true"
            >
              🗑️ 删除标签
            </span>
            <span 
              v-else
              style="font-size: 11px; color: var(--accent-color, #4f46e5); cursor: pointer;" 
              @click="isDeletingTags = false"
            >
              ✅ 完成删除
            </span>
          </div>
        </div>
        
        <div class="tags-container">
          <div 
            v-for="tag in presetTags"
            :key="tag.name"
            class="tag-item"
          >
            <van-tag 
              :type="activeTagFilter === tag.name ? tag.type : 'default'"
              :plain="activeTagFilter !== tag.name"
              style="padding: 4px 8px;"
              @click="toggleSidebarFilter(tag.name)"
            >
              #{{ tag.name }}
            </van-tag>
            <van-icon 
              v-if="isDeletingTags"
              name="cross" 
              size="14" 
              color="#ef4444" 
              class="tag-delete-icon"
              @click="deleteTag(tag.name)"
            />
          </div>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <div v-if="currentNote" class="immersive-reader">
        
        <header class="reader-header">
          <div style="display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0;">
            <h1 class="reader-title">{{ getNoteTitle(currentNote) }}</h1>
            <van-icon name="edit" color="#6b7280" size="20" style="cursor: pointer;" @click="openRenameModal" />
          </div>
        
          <div class="reader-actions">
            <van-button 
              v-if="isEditingContent"
              type="warning" 
              plain 
              icon="expand-o" 
              size="small" 
              style="margin-right: 10px;"
              @click="toggleFullscreenMode"
            >
              {{ isFullscreenMode ? '退出全屏' : '全屏模式' }}
            </van-button>
            
            <van-button 
              :type="isEditingContent ? 'success' : 'primary'" 
              plain 
              :icon="isEditingContent ? 'success' : 'edit'" 
              size="small" 
              style="margin-right: 10px;"
              @click="toggleEditMode"
            >
              {{ isEditingContent ? '💾 完成编辑' : '✏️ 编辑正文' }}
            </van-button>

            <van-button 
              type="primary" 
              plain 
              icon="star-o" 
              size="small" 
              style="margin-right: 10px;"
              @click="saveCurrentAsTemplate"
              title="将当前结构存为模板"
            >
              存为模板
            </van-button>
            <van-button type="primary" plain icon="replay" size="small" :loading="isRegenerating" @click="handleRegenerateNote(currentNote.id)">
              AI 重构
            </van-button>
            <van-button type="danger" plain icon="delete-o" size="small" style="margin-left: 10px;" @click="handleDeleteNote(currentNote.id)">
              删除
            </van-button>
          </div>
        </header>

        <article
          v-if="!isEditingContent"
          class="markdown-body custom-scroll"
          @mouseup="handleMouseUp"
          @mouseover="handleArticleMouseOver"
          @mouseout="handleArticleMouseOut"
        >
          <MarkdownViewer :content="currentNote.structured_note" @link-click="handleLinkClick" />

          <div v-if="currentNote.tags" class="note-tags-section">
            <div class="tags-label">🏷️ 标签</div>
            <div class="tags-row">
              <van-tag
                v-for="tag in currentNote.tags.split(',').filter(t => t)"
                :key="tag"
                type="primary"
                size="medium"
                plain
                style="margin-right: 8px; margin-bottom: 8px;"
                @click="toggleSidebarFilter(tag)"
              >
                #{{ tag }}
              </van-tag>
            </div>
          </div>
        </article>

        <div
          v-else-if="isEditingContent"
          class="editor-wrapper"
          :class="{ 'fullscreen-wrapper': isFullscreenMode }"
        >
          <div v-if="isFullscreenMode" class="fullscreen-toolbar">
            <van-button size="small" round :type="isTypewriterMode ? 'primary' : 'default'" icon="ascending" @click="toggleTypewriter">打字机</van-button>
            <van-button size="small" round :type="isTrueFocusMode ? 'primary' : 'default'" icon="eye-o" @click="toggleTrueFocus">专注</van-button>
            <van-button size="small" round icon="cross" @click="toggleFullscreenMode" title="退出全屏 (ESC)" />
          </div>

          <div class="editor-textarea-wrapper">
            <textarea
              ref="mainEditorRef"
              v-model="editingContent"
              class="raw-editor custom-scroll"
              :class="{ 'focus-mask-active': isTrueFocusMode }"
              placeholder="输入 $$ 唤起公式编辑器，输入 [[ 创建双向链接..."
              @input="e => { handleEditorInput(e); handleTypewriterScroll(); }"
              @keyup="handleTypewriterScroll"
              @click="handleTypewriterScroll"
              @scroll="handleEditorScroll"
            ></textarea>

            <!-- 双向链接选择器浮层 - 使用 Teleport 挂载到 body -->
            <Teleport to="body">
              <div
                v-if="showLinkSelector"
                class="link-selector-global"
                :style="{ top: linkSelectorPos.y + 'px', left: linkSelectorPos.x + 'px' }"
              >
                <div class="link-selector-header">
                  <span class="link-selector-title">🔗 选择笔记或输入新标题</span>
                  <span class="link-selector-hint">↑↓ 选择 · Enter 确认 · Esc 关闭</span>
                </div>
                <div class="link-selector-list">
                  <div
                    v-if="filteredNoteTitles.length === 0 && linkSearchQuery.trim()"
                    class="link-selector-item create-new"
                    :class="{ active: true }"
                    @click="selectLinkTitle(linkSearchQuery.trim())"
                  >
                    <span class="create-icon">✨</span>
                    <span>创建新链接："{{ linkSearchQuery.trim() }}"</span>
                  </div>
                  <div
                    v-if="filteredNoteTitles.length === 0 && !linkSearchQuery.trim()"
                    class="link-selector-empty"
                  >
                    暂无笔记，输入文字创建新链接
                  </div>
                  <div
                    v-for="(title, index) in filteredNoteTitles"
                    :key="title"
                    class="link-selector-item"
                    :class="{ active: index === linkSelectedIndex }"
                    @click="selectLinkTitle(title)"
                  >
                    <van-icon name="notes-o" size="14" />
                    <span>{{ title }}</span>
                  </div>
                </div>
              </div>
            </Teleport>
          </div>

          <div class="editor-toolbar">
            <van-button size="small" round icon="photograph" @click="insertImageFromFile" title="插入本地图片">
              图片
            </van-button>
            <van-button size="small" round icon="link" @click="insertImageFromUrl" title="插入网络图片">
              链接图片
            </van-button>
          </div>
        </div>

        <!-- 状态栏 - 显示字数、行数、段落数等信息 -->
        <div v-if="currentNote" class="status-bar">
          <div class="status-left">
            <!-- 字数统计 - 点击可切换统计方式 -->
            <span class="status-item status-clickable" @click.stop="showWordCountMenu = !showWordCountMenu">
              <van-icon name="font-o" size="14" />
              <span>{{ displayCount }} {{ countUnit }}</span>
              <van-icon name="arrow-down" size="10" style="margin-left: 2px;" />
            </span>
            <span class="status-separator">|</span>
            <span class="status-item">
              <van-icon name="list-switch" size="14" />
              {{ getLineCount(currentNote) }} 行
            </span>
            <span class="status-separator">|</span>
            <span class="status-item">
              <van-icon name="notes-o" size="14" />
              {{ getParagraphCount(currentNote) }} 段
            </span>
            <span class="status-separator">|</span>
            <span class="status-item">
              <van-icon name="clock-o" size="14" />
              {{ getReadingTime(currentNote) }} 分钟
            </span>
          </div>
          <div class="status-right">
            <span class="status-item" v-if="isEditingContent">
              <van-icon name="edit" size="14" />
              编辑模式
            </span>
            <span class="status-item" v-else>
              <van-icon name="eye-o" size="14" />
              阅读模式
            </span>
          </div>

          <!-- 字数统计方式下拉菜单 -->
          <div v-if="showWordCountMenu" class="count-menu" @click.stop>
            <div
              class="count-menu-item"
              :class="{ active: countMode === 'words' }"
              @click.stop="setCountMode('words')"
            >
              <span>📝 字数（不含空格标点）</span>
              <span class="menu-count">{{ getWordCount(currentNote) }} 字</span>
            </div>
            <div
              class="count-menu-item"
              :class="{ active: countMode === 'chars' }"
              @click.stop="setCountMode('chars')"
            >
              <span>🔤 字符数（不含空格）</span>
              <span class="menu-count">{{ getCharCount(currentNote, false) }} 字符</span>
            </div>
            <div
              class="count-menu-item"
              :class="{ active: countMode === 'chars-space' }"
              @click.stop="setCountMode('chars-space')"
            >
              <span>⌨️ 字符数（含空格）</span>
              <span class="menu-count">{{ getCharCount(currentNote, true) }} 字符</span>
            </div>
            <div
              class="count-menu-item"
              :class="{ active: countMode === 'all' }"
              @click.stop="setCountMode('all')"
            >
              <span>🌐 全部字符</span>
              <span class="menu-count">{{ getAllCharCount(currentNote) }} 字符</span>
            </div>
          </div>
        </div>
      
      </div>
      
      <div v-else class="empty-state">
        <van-empty image="search" description="从左侧知识库选择一篇笔记，或点击 + 号新建" />
      </div>
    </main>

    <van-overlay :show="loading" @click.stop>
      <div class="loading-container">
        <van-loading type="spinner" size="48px" color="#4F46E5" vertical>
          AI 正在整理笔记...
        </van-loading>
      </div>
    </van-overlay>

    <van-popup v-model:show="showEditNote" position="bottom" round :style="{ height: '70%' }">
      <div class="edit-container">
        <h3 class="edit-title">编辑笔记</h3>
        <van-field v-model="editOriginal" label="原始文本" type="textarea" rows="3" />
        <van-field v-model="editStructured" label="结构化笔记" type="textarea" rows="6" />
        <div class="edit-buttons">
          <van-button block round @click="showEditNote = false">取消</van-button>
          <van-button block round type="primary" :loading="editLoading" @click="saveEditNote">保存</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 新建笔记弹窗 -->
    <van-popup v-model:show="showCreateModal" position="bottom" :style="{ height: '75%' }" round>
      <div style="padding: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <h3 style="margin: 0; font-size: 18px; color: var(--text-primary, #1f2937);">✨ 沉淀新知识</h3>
          <van-icon name="cross" size="20" @click="showCreateModal = false" />
        </div>
        
        <van-field v-model="newNoteTitle" label="标题" placeholder="给这篇笔记起个响亮的名字" border />

        <van-field label="所属课程">
          <template #input>
            <select 
              v-model="newNoteCourseId" 
              style="border: none; width: 100%; outline: none; background: transparent; font-size: 14px;"
            >
              <option value="">不选择课程</option>
              <option 
                v-for="course in courseList" 
                :key="course.id" 
                :value="course.id"
              >
                {{ course.name }}
              </option>
            </select>
          </template>
        </van-field>
        <van-field label="所属文件夹">
          <template #input>
            <input 
              v-model="newNoteFolder" 
              list="existing-folders" 
              placeholder="选择现有文件夹，或输入新路径(用 / 嵌套)" 
              style="border: none; width: 100%; outline: none; background: transparent;"
            />
          </template>
        </van-field>
        
        <div style="margin: 16px 0 8px 16px;">
          <van-uploader :after-read="handleFileUpload" accept=".md,.txt" max-count="1">
            <van-button icon="plus" type="primary" size="small" plain color="#10B981">
              一键导入本地 .md / .txt 文件
            </van-button>
          </van-uploader>
        </div>

        <van-field 
          v-model="newNoteContent" 
          type="textarea" 
          rows="10" 
          placeholder="在此直接粘贴凌乱的草稿、课堂录音文字稿，或者点击上方按钮导入本地文件..." 
          border 
          style="background: #f9fafb; border-radius: 8px;"
        />

        <div style="margin: 16px 0; padding: 0 16px;">
          <p style="font-size: 13px; color: var(--text-secondary, #6b7280); margin-bottom: 8px;">为笔记打上多维标签：</p>
          
          <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;">
            <van-tag 
              v-for="tag in presetTags" 
              :key="tag.name"
              :type="newNoteTags.includes(tag.name) ? tag.type : 'default'"
              :plain="!newNoteTags.includes(tag.name)"
              size="medium"
              style="cursor: pointer; padding: 6px 10px;"
              @click="toggleTagInCreation(tag.name)"
            >
              #{{ tag.name }}
            </van-tag>
          </div>

          <div style="display: flex; gap: 8px; align-items: center;">
            <van-field 
              v-model="customTagInput" 
              placeholder="输入自定义标签" 
              size="small"
              :border="false"
              style="background: #f3f4f6; border-radius: 4px; padding: 4px 8px; width: 160px;"
            />
            <van-button type="primary" size="mini" plain color="#4F46E5" @click="addCustomTag">
              + 添加
            </van-button>
          </div>
        </div>

        <div style="margin-top: 8px; display: flex; gap: 16px;">
          <van-button 
            type="primary" 
            block 
            icon="magic-o" 
            color="#4F46E5"
            :loading="isSaving" 
            @click="saveNewNote(true)"
          >
            AI 智能深度排版
          </van-button>
          <van-button 
            type="default" 
            block 
            plain
            :loading="isSaving" 
            @click="saveNewNote(false)"
          >
            直接保存原文
          </van-button>
        </div>
      </div>
    </van-popup>

    <van-dialog 
      v-model:show="showRenameModal" 
      title="修改笔记标题" 
      show-cancel-button 
      @confirm="confirmRename"
    >
      <div style="padding: 16px;">
        <van-field 
          v-model="editingTitle" 
          placeholder="请输入新的标题..." 
          border
          style="background-color: var(--bg-primary, #f5f5f5); border-radius: 8px;"
        />
      </div>
    </van-dialog>

    <!-- 公式编辑器弹窗 -->
    <van-popup 
      v-model:show="showMathEditor" 
      position="bottom" 
      round 
      :style="{ height: '75%' }"
      @closed="focusMainEditor"
    >
      <FormulaEditor @insert="handleInsertFormula" @close="showMathEditor = false" />
    </van-popup>

    <!-- 笔记操作菜单弹窗 -->
    <van-action-sheet 
      v-model:show="showNoteMenu" 
      :actions="noteMenuActions"
      cancel-text="取消"
      @select="handleNoteMenuSelect"
    />

    <!-- 编辑标签弹窗 -->
    <van-dialog 
      v-model:show="showNewFolderModal" 
      title="新建文件夹" 
      show-cancel-button 
      @confirm="confirmCreateFolder"
    >
      <div style="padding: 16px;">
        <p style="font-size: 12px; color: var(--text-tertiary, #9ca3af); margin-bottom: 12px;">支持多级嵌套，例如：大四/英语/四六级</p>
        <van-field 
          v-model="targetNewFolderName" 
          placeholder="请输入文件夹名称或路径..." 
          border
          style="background-color: var(--bg-primary, #f5f5f5); border-radius: 8px;"
        />
      </div>
    </van-dialog>

    <van-dialog 
      v-model:show="showEditTagsModal" 
      title="编辑笔记属性" 
      show-cancel-button 
      @confirm="saveNoteTags"
    >
      <div style="padding: 16px;">
        <van-field label="所属课程">
          <template #input>
            <select 
              v-model="editingNoteCourseId" 
              style="border: none; width: 100%; outline: none; background: transparent; font-size: 14px;"
            >
              <option value="">不选择课程</option>
              <option 
                v-for="course in courseList" 
                :key="course.id" 
                :value="course.id"
              >
                {{ course.name }}
              </option>
            </select>
          </template>
        </van-field>
        <van-field label="所属文件夹">
          <template #input>
            <input 
              v-model="editingFolder" 
              list="existing-folders" 
              placeholder="选择现有文件夹，或输入新路径(用 / 嵌套)" 
              style="border: none; width: 100%; outline: none; background: transparent;"
            />
          </template>
        </van-field>
        
        <div style="font-size: 13px; color: var(--text-secondary, #6b7280); margin-bottom: 8px;">标签</div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;">
          <van-tag 
            v-for="tag in presetTags" 
            :key="tag.name"
            :type="editingNoteTags.includes(tag.name) ? tag.type : 'default'"
            :plain="!editingNoteTags.includes(tag.name)"
            size="medium"
            style="cursor: pointer; padding: 6px 10px;"
            @click="toggleTagInEdit(tag.name)"
          >
            #{{ tag.name }}
          </van-tag>
        </div>

        <div style="display: flex; gap: 8px; align-items: center;">
          <van-field 
            v-model="customEditTagInput" 
            placeholder="输入自定义标签" 
            size="small"
            :border="false"
            style="background: #f3f4f6; border-radius: 4px; padding: 4px 8px; width: 160px;"
          />
          <van-button type="primary" size="mini" plain color="#4F46E5" @click="addCustomEditTag">
            + 添加
          </van-button>
        </div>

        <div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px;">
          <van-tag 
            v-for="tag in editingNoteTags" 
            :key="tag"
            type="primary"
            size="small"
            closeable
            @close="removeEditTag(tag)"
          >
            #{{ tag }}
          </van-tag>
        </div>
      </div>
    </van-dialog>

    <datalist id="existing-folders">
      <option v-for="folder in uniqueFolders" :key="folder" :value="folder"></option>
    </datalist>

    <div 
      v-show="showContextMenu" 
      class="context-menu shadow-xl" 
      :style="{ top: menuY + 'px', left: menuX + 'px' }"
    >
      <div class="menu-item" @click="handleMenuNewNote">📄 在此处新建笔记</div>
      <div class="menu-item" @click="handleMenuNewFolder">📁 新建子文件夹</div>
      <div class="menu-divider"></div>
      <div class="menu-item" @click="handleMenuRenameFolder">✏️ 重命名文件夹</div>
      <div class="menu-item danger" @click="handleMenuDeleteFolder">🗑️ 删除整个文件夹</div>
    </div>

    <van-dialog 
      v-model:show="showDeleteFolderModal" 
      title="⚠️ 危险操作" 
      show-cancel-button 
      @confirm="confirmDeleteFolder"
    >
      <div style="padding: 20px 16px; text-align: center;">
        <p style="margin: 0 0 16px 0; color: var(--text-primary, #374151); font-size: 15px;">
          确定要彻底删除文件夹 <strong style="color: #ef4444;">[{{ targetFolderNameToDelete }}]</strong> 吗？
        </p>
        
        <div style="display: flex; justify-content: center; background-color: var(--danger-light, #fef2f2); padding: 12px; border-radius: 8px;">
          <van-checkbox v-model="keepNotesOnDelete" shape="square" checked-color="#ef4444">
            保留里面的笔记 (移至上一级目录)
          </van-checkbox>
        </div>

        <p v-if="!keepNotesOnDelete" style="font-size: 12px; color: #ef4444; margin-top: 16px;">
          该文件夹及其子文件夹下的所有笔记将被永久删除！
        </p>
        <p v-else style="font-size: 12px; color: #10b981; margin-top: 16px;">
          笔记安全：子文件将自动归入父文件夹。
        </p>
      </div>
    </van-dialog>

    <!-- 🌍 全局图谱星空 -->
    <van-popup v-model:show="showGraph" position="right" :style="{ width: '100%', height: '100%' }">
      <van-icon name="cross" size="24" color="#6b7280" style="position: absolute; top: 24px; right: 24px; z-index: 999; cursor: pointer;" @click="showGraph = false" />
      <GraphView 
        v-if="showGraph" 
        :notes="notesList" 
        :links="allLinks" 
        @node-click="handleGraphNodeClick" 
      />
    </van-popup>

    <!-- 划词悬浮菜单 -->
    <div 
      v-show="showSelectionMenu" 
      class="selection-toolbar shadow-lg"
      :style="{ top: selectionY + 'px', left: selectionX + 'px' }"
    >
      <van-button size="mini" type="primary" icon="bulb-o" @click="openFlashcardModal">
        制作闪卡
      </van-button>
    </div>

    <!-- 制卡弹窗 -->
    <van-dialog 
      v-model:show="showFlashcardModal" 
      title="✨ 制作记忆闪卡" 
      show-cancel-button 
      @confirm="saveFlashcard"
    >
      <div style="padding: 16px;">
        <van-field 
          v-model="flashcardFront" 
          label="正面(问题)" 
          type="textarea" 
          autosize 
          border 
        />
        
        <div style="display: flex; justify-content: flex-end; margin: 8px 0;">
          <van-button 
            size="mini" 
            type="success" 
            plain 
            icon="play-circle-o" 
            :loading="isGeneratingAnswer"
            @click="generateAnswerWithAI"
          >
            AI 智能生成答案
          </van-button>
        </div>

        <van-field 
          v-model="flashcardBack" 
          label="背面(答案)" 
          type="textarea" 
          autosize 
          border 
          placeholder="请输入答案，或点击上方按钮让 AI 生成..."
          style="background: #f9fafb; border-radius: 8px;"
        />
      </div>
    </van-dialog>

    <!-- 闪卡复习弹窗 -->
    <van-dialog 
      v-model:show="showReviewModal" 
      title="📚 闪卡复习" 
      :show-confirm-button="false"
      :show-cancel-button="false"
      class="review-modal"
    >
      <div class="review-container">
        <div v-if="currentReviewCard" class="review-card" :class="{ 'is-flipped': showAnswer }">
          <div class="card-face card-front">
            <div class="card-content">
              <div style="font-size: 14px; opacity: 0.9; margin-bottom: 16px;">
                {{ currentReviewIndex + 1 }} / {{ flashcards.length }}
              </div>
              <div class="question-text">{{ currentReviewCard.front }}</div>
              <div style="font-size: 12px; opacity: 0.8; margin-top: 20px;">
                👆 点击查看答案
              </div>
            </div>
          </div>
          <div class="card-face card-back">
            <div class="card-content">
              <div style="font-size: 14px; opacity: 0.9; margin-bottom: 16px;">
                {{ currentReviewIndex + 1 }} / {{ flashcards.length }}
              </div>
              <div class="answer-text">{{ currentReviewCard.back }}</div>
              <div style="font-size: 12px; opacity: 0.8; margin-top: 20px;">
                👆 点击返回问题
              </div>
            </div>
          </div>
          <div class="card-click-overlay" @click="showAnswer = !showAnswer"></div>
        </div>

        <div v-if="showAnswer" class="review-actions">
          <van-button 
            type="warning" 
            plain 
            icon="close"
            @click="handleReviewResult('hard')"
          >
            忘记了
          </van-button>
          <van-button 
            type="primary" 
            plain 
            icon="passed"
            @click="handleReviewResult('good')"
          >
            记住了
          </van-button>
          <van-button 
            type="success" 
            plain 
            icon="good-job"
            @click="handleReviewResult('easy')"
          >
            太简单
          </van-button>
        </div>

        <div class="review-progress">
          <van-progress 
            :percentage="((currentReviewIndex + (showAnswer ? 1 : 0)) / flashcards.length) * 100" 
            stroke-width="6"
            color="#4F46E5"
          />
        </div>
      </div>
    </van-dialog>

    <!-- 单独查看闪卡弹窗 -->
    <van-dialog 
      v-model:show="showSingleCardModal" 
      title="🃏 查看闪卡" 
      :show-confirm-button="false"
      :show-cancel-button="false"
      class="single-card-modal"
    >
      <div class="review-container" v-if="selectedCard">
        <div class="review-card" :class="{ 'is-flipped': showSingleCardAnswer }">
          <div class="card-face card-front">
            <div class="card-content">
              <div style="font-size: 14px; opacity: 0.9; margin-bottom: 16px;">
                闪卡详情
              </div>
              <div class="question-text">{{ selectedCard.front }}</div>
              <div style="font-size: 12px; opacity: 0.8; margin-top: 20px;">
                👆 点击查看答案
              </div>
            </div>
          </div>
          <div class="card-face card-back">
            <div class="card-content">
              <div style="font-size: 14px; opacity: 0.9; margin-bottom: 16px;">
                闪卡详情
              </div>
              <div class="answer-text">{{ selectedCard.back }}</div>
              <div style="font-size: 12px; opacity: 0.8; margin-top: 20px;">
                👆 点击返回问题
              </div>
            </div>
          </div>
          <div class="card-click-overlay" @click="showSingleCardAnswer = !showSingleCardAnswer"></div>
        </div>
        
        <div v-if="showSingleCardAnswer" class="review-actions" style="margin-bottom: 16px;">
          <van-button 
            type="warning" 
            plain 
            icon="close"
            @click="handleSingleCardResult('hard')"
          >
            忘记了
          </van-button>
          <van-button 
            type="primary" 
            plain 
            icon="passed"
            @click="handleSingleCardResult('good')"
          >
            记住了
          </van-button>
          <van-button 
            type="success" 
            plain 
            icon="good-job"
            @click="handleSingleCardResult('easy')"
          >
            太简单
          </van-button>
        </div>
        
        <div v-if="!showSingleCardAnswer" class="review-actions" style="margin-bottom: 16px;">
          <van-button 
            type="default" 
            plain 
            @click="showSingleCardModal = false"
          >
            关闭
          </van-button>
        </div>
        
        <div style="font-size: 12px; color: var(--text-tertiary, #9ca3af); text-align: center;">
          📄 {{ selectedCard.note_title || '未知笔记' }}
        </div>
      </div>
    </van-dialog>

    <!-- 🔗 链接悬停预览卡片 -->
    <div 
      v-show="showLinkPreview && previewTargetNote" 
      class="link-preview-card shadow-xl"
      :style="{ top: previewY + 'px', left: previewX + 'px' }"
      @mouseenter="clearPreviewHideTimer"
      @mouseleave="startPreviewHideTimer"
    >
      <div v-if="previewTargetNote">
        <h4 class="preview-title">
          <van-icon name="notes-o" style="margin-right: 4px;" />
          {{ previewTargetNote.title }}
        </h4>
        
        <div class="preview-content" v-html="getPreviewHtml(previewTargetNote.structured_note)"></div>
        
        <div v-if="previewTargetNote.tags" class="preview-tags">
          <van-tag 
            v-for="tag in previewTargetNote.tags.split(',').filter(t => t)" 
            :key="tag" 
            plain 
            type="primary" 
            size="mini"
          >
            {{ tag }}
          </van-tag>
        </div>
      </div>
    </div>

    <van-popup 
      v-model:show="showTemplateModal" 
      position="bottom" 
      round 
      :style="{ height: '65%', background: '#f8fafc' }"
    >
      <div style="padding: 24px; display: flex; flex-direction: column; height: 100%;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <h3 style="margin: 0; font-size: 18px; color: #1e293b;">选择笔记框架</h3>
          <van-icon name="cross" size="20" color="#94a3b8" @click="showTemplateModal = false" style="cursor: pointer;" />
        </div>
        
        <div class="template-grid custom-scroll">
          <div 
            v-for="tpl in allTemplates" 
            :key="tpl.id" 
            class="template-card"
            @click="createNoteFromTemplate(tpl)"
          >
            <div class="tpl-title">{{ tpl.title }}</div>
            <div class="tpl-desc">{{ tpl.desc }}</div>
          </div>
        </div>
      </div>
    </van-popup>

  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { showToast, showSuccessToast, showFailToast, showConfirmDialog, showLoadingToast, closeToast } from 'vant'
import { marked } from 'marked'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import api from '../api'
import { getAIConfig, getProvider } from '../utils/aiConfig'
import MarkdownViewer from '../components/MarkdownViewer.vue'
import FolderTree from '../components/FolderTree.vue'
import GraphView from '../components/GraphView.vue'
import PdfReader from '../components/PdfReader.vue'
import FormulaEditor from '../components/FormulaEditor.vue'
import CollapsibleEditor from '../components/CollapsibleEditor.vue'
import { syncNotesToLocalDirectory, disconnectLocalDirectory, getLocalSyncStatus, importNotesFromLocalDirectory } from '../utils/localSync.js'

// ====== 侧边栏状态 ======
const notesList = ref([])
const isRootDragOver = ref(false)

// ====== 文献管理状态 ======
const showPdfReader = ref(false)
const currentPdfPath = ref('')
const currentPdfInitialPage = ref(1)

// ====== 无限层级文件树引擎 ======
const fileTree = computed(() => {
  const root = { children: {}, notes: [] }
  
  filteredNotesList.value.forEach(note => {
    const pathStr = note.folder || '默认笔记本'
    const parts = pathStr.split('/').map(p => p.trim()).filter(p => p)
    
    let currentLevel = root
    
    parts.forEach(part => {
      if (!currentLevel.children[part]) {
        currentLevel.children[part] = { children: {}, notes: [] }
      }
      currentLevel = currentLevel.children[part]
    })
    
    currentLevel.notes.push(note)
  })
  
  return root
})

// 【新增】：自动提取所有已存在的唯一文件夹路径
const uniqueFolders = computed(() => {
  const folders = new Set()
  notesList.value.forEach(note => {
    if (note.folder) {
      folders.add(note.folder)
    }
  })
  return Array.from(folders)
})

// ====== 本地文件夹同步 ======
const isDirConnected = computed(() => getLocalSyncStatus())

const handleFolderSync = async () => {
  await syncNotesToLocalDirectory(notesList.value)
}

const handleImportNotes = async () => {
  const count = await importNotesFromLocalDirectory()
  if (count && count > 0) {
    await loadNotes()
    showToast({ message: `✅ 已导入 ${count} 篇笔记`, position: 'top' })
  }
}

const handleDisconnect = () => {
  disconnectLocalDirectory()
  showToast('已断开本地文件夹连接')
}

// ====== 当前选中的笔记 ======
const currentNote = ref(null)
const isRegenerating = ref(false)
const loading = ref(false)

// ====== 侧边栏选项卡状态 ======
const activeSidebarTab = ref('folder') // 'folder' 或 'outline'

// ====== 正文编辑状态 ======
const isEditingContent = ref(false)
const editingContent = ref('') // 临时存放输入框里的纯文本

// 切换：编辑 / 保存并预览
const toggleEditMode = async () => {
  if (!currentNote.value) return

  if (isEditingContent.value) {
    // 1. 当前是编辑状态，点击意味着【保存并退出编辑】
    // 先记录编辑器的滚动比例
    let scrollRatio = 0
    const editor = mainEditorRef.value
    if (editor) {
      const scrollTop = editor.scrollTop
      const scrollHeight = editor.scrollHeight
      const clientHeight = editor.clientHeight
      const maxScroll = scrollHeight - clientHeight
      scrollRatio = maxScroll > 0 ? scrollTop / maxScroll : 0
    }

    try {
      // 还原真实内容（把占位符替换回 base64）
      const realContent = unfoldImagesInContent(editingContent.value, imagePlaceholderMap.value)

      // 发送 PUT 请求更新正文 (保持其他字段不变)
      const res = await api.put(`/notes/${currentNote.value.id}`, {
        title: currentNote.value.title,
        structured_note: realContent, // 保存真实内容（含 base64）
        tags: currentNote.value.tags || '',
        folder: currentNote.value.folder || '默认笔记本'
      })

      if (res.success) {
        // 更新成功后，将真实内容同步到当前笔记，并切换回只读模式
        currentNote.value.structured_note = realContent
        editingContent.value = realContent
        imagePlaceholderMap.value = new Map()
        isEditingContent.value = false
        showToast({ message: '💾 笔记已保存', position: 'top' })

        // 按比例恢复阅读模式的滚动位置
        await nextTick()
        setTimeout(() => {
          const article = document.querySelector('.main-content .markdown-body')
          if (article) {
            const maxScroll = article.scrollHeight - article.clientHeight
            article.scrollTop = maxScroll * scrollRatio
          }
        }, 50)
      } else {
        showFailToast(res?.message || '保存失败')
      }
    } catch (e) {
      console.error(e)
      showFailToast('网络异常，保存失败')
    }
  } else {
    // 2. 当前是只读状态，点击意味着【进入编辑模式】
    // 先记录阅读模式的滚动比例
    let scrollRatio = 0
    const article = document.querySelector('.main-content .markdown-body')
    if (article) {
      const scrollTop = article.scrollTop
      const scrollHeight = article.scrollHeight
      const clientHeight = article.clientHeight
      const maxScroll = scrollHeight - clientHeight
      scrollRatio = maxScroll > 0 ? scrollTop / maxScroll : 0
    }

    const rawContent = currentNote.value.structured_note || currentNote.value.content || ''
    // 折叠长 base64 图片为占位符
    const { display, map } = foldImagesInContent(rawContent)
    editingContent.value = display
    imagePlaceholderMap.value = map
    realEditorContent.value = rawContent
    isEditingContent.value = true

    // 按比例恢复编辑器的滚动位置
    await nextTick()
    setTimeout(() => {
      const editor = mainEditorRef.value
      if (editor) {
        const maxScroll = editor.scrollHeight - editor.clientHeight
        editor.scrollTop = maxScroll * scrollRatio
      }
    }, 50)
  }
}

// ====== 大纲提取引擎（DOM 扫描绝对定位法）======
const tableOfContents = ref([])

// ====== 编辑器图片折叠：维护真实内容与显示内容的双向映射 ======
// 真实内容（保存到数据库）
const realEditorContent = ref('')
// 图片占位符的映射：占位符 -> 真实 base64
const imagePlaceholderMap = ref(new Map())

// 替换长 base64 为短占位符
const foldImagesInContent = (content) => {
  if (!content) return { display: '', map: new Map() }
  const map = new Map()
  let counter = 0
  const display = content.replace(
    /!\[([^\]]*)\]\(([^)]{60,})\)/g,
    (match, alt, url) => {
      const isBase64 = url.startsWith('data:image/')
      if (isBase64) {
        const sizeKB = Math.round((url.split(',')[1]?.length || 0) * 0.75 / 1024)
        const format = (url.match(/data:image\/([^;]+)/)?.[1] || 'png').toUpperCase()
        const placeholder = `![${alt || '图片'}](🖼️_${format}_${sizeKB}KB_图${counter})`
        map.set(placeholder, match)
        counter++
        return placeholder
      }
      return match
    }
  )
  return { display, map }
}

// 从显示内容还原为真实内容（恢复占位符为原 base64）
const unfoldImagesInContent = (displayContent, map) => {
  if (!displayContent) return ''
  let result = displayContent
  for (const [placeholder, original] of map.entries()) {
    result = result.split(placeholder).join(original)
  }
  return result
}

watch(
  [() => currentNote.value?.structured_note, isEditingContent],
  async ([newContent, isEditing]) => {
    // 1. 如果进入编辑模式，或者没有内容，直接清空大纲
    if (isEditing || !newContent) {
      tableOfContents.value = []
      return
    }

    // 2. 核心保护：等待 Vue 本轮数据更新完成
    await nextTick()

    // 3. 核心保护：加入 50ms 的微小延迟，彻底避开 v-html 的异步渲染时差
    setTimeout(() => {
      const article = document.querySelector('.main-content .markdown-body')
      if (!article) return

      const headings = article.querySelectorAll('h1, h2, h3, h4, h5, h6')
      const toc = []

      headings.forEach((headingEl, index) => {
        // 给真实 DOM 强行注入唯一 ID
        const uniqueId = `toc-heading-${index}`
        headingEl.id = uniqueId

        const text = headingEl.innerText.trim()
        // 过滤空标题，避免大纲中出现空行
        if (!text) return

        toc.push({
          level: parseInt(headingEl.tagName.substring(1)),
          text: text,
          id: uniqueId
        })
      })

      tableOfContents.value = toc
      console.log('[DEBUG] 大纲已更新:', toc)
    }, 50)
  },
  // 4. 终极保护：强制该监听器在 Vue 的 DOM 彻底挂载完毕后 (post) 才触发
  { immediate: true, flush: 'post' }
)

// 平滑滚动函数
const scrollToHeading = (item) => {
  console.log('[DEBUG] 滚动到标题 ID:', item.id)
  const element = document.getElementById(item.id)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    element.style.transition = 'background-color 0.3s'
    element.style.backgroundColor = '#eef2ff'
    setTimeout(() => {
      element.style.backgroundColor = ''
    }, 2000)
  } else {
    console.log('[DEBUG] 未找到元素:', item.id)
  }
}

// 大纲折叠功能
const expandedSections = ref([])

const hasChildren = (index) => {
  if (index >= tableOfContents.value.length - 1) return false
  const currentLevel = tableOfContents.value[index].level
  for (let i = index + 1; i < tableOfContents.value.length; i++) {
    const childLevel = tableOfContents.value[i].level
    if (childLevel > currentLevel) {
      return true
    }
    if (childLevel <= currentLevel) {
      return false
    }
  }
  return false
}

const toggleSection = (index) => {
  const idx = expandedSections.value.indexOf(index)
  if (idx > -1) {
    expandedSections.value.splice(idx, 1)
  } else {
    expandedSections.value.push(index)
  }
}

const isHidden = (index) => {
  const currentLevel = tableOfContents.value[index].level
  for (let i = index - 1; i >= 0; i--) {
    const parentLevel = tableOfContents.value[i].level
    if (parentLevel < currentLevel) {
      // 找到父标题
      if (!expandedSections.value.includes(i) && hasChildren(i)) {
        return true
      }
      return false
    }
  }
  return false
}

// ====== 标签删除模式 ======
const isDeletingTags = ref(false)

// ====== 编辑相关 ======
const showEditNote = ref(false)
const editOriginal = ref('')
const editStructured = ref('')
const editLoading = ref(false)

// ====== 新建笔记弹窗 ======
const showCreateModal = ref(false)
const newNoteTitle = ref('')
const newNoteContent = ref('')
const newNoteFolder = ref('默认笔记本')
const isSaving = ref(false)

// ====== 当前课程 ======
const selectedCourseId = ref(1)
const courseList = ref([])
const newNoteCourseId = ref('') // 新建笔记时选择的课程ID
const editingNoteCourseId = ref('') // 编辑笔记属性时选择的课程ID

// ====== 知识图谱状态 ======
const showGraph = ref(false)
const allLinks = ref([])

// 打开图谱时拉取全库链接
const openGraphView = async () => {
  console.log('点击知识图谱按钮')
  try {
    console.log('正在请求 links 接口...')
    const res = await api.get('/notes/links')
    console.log('links 接口响应:', res)
    if (res.success) {
      allLinks.value = res.data
      console.log('✅ 成功加载链接数据:', allLinks.value)
    } else {
      console.log('接口返回不是 success，使用空列表')
      allLinks.value = []
    }
  } catch (e) {
    console.error('拉取图谱失败', e)
    allLinks.value = []
    showToast('图谱加载失败')
  } finally {
    console.log('打开图谱弹窗')
    showGraph.value = true
  }
}

// 图谱点击穿梭
const handleGraphNodeClick = (noteId) => {
  const target = notesList.value.find(n => n.id === noteId)
  if (target) {
    showGraph.value = false
    selectNote(target)
  }
}

// ====== 闪卡与划词引擎 ======
const showSelectionMenu = ref(false)
const selectionX = ref(0)
const selectionY = ref(0)

const showFlashcardModal = ref(false)
const flashcardFront = ref('')
const flashcardBack = ref('')
const isGeneratingAnswer = ref(false)

const handleMouseUp = (e) => {
  if (isEditingContent.value || showFlashcardModal.value) return
  
  setTimeout(() => {
    const selection = window.getSelection()
    const text = selection.toString().trim()
    
    if (text.length > 0) {
      const range = selection.getRangeAt(0)
      const rect = range.getBoundingClientRect()
      
      selectionX.value = rect.left + rect.width / 2
      selectionY.value = rect.top
      
      flashcardFront.value = text
      showSelectionMenu.value = true
    } else {
      showSelectionMenu.value = false
    }
  }, 50)
}

const openFlashcardModal = () => {
  showSelectionMenu.value = false
  flashcardBack.value = ''
  showFlashcardModal.value = true
}

const generateAnswerWithAI = async () => {
  if (!currentNote.value) return
  isGeneratingAnswer.value = true

  try {
    console.log('📡 发送 AI 生成请求...')

    // 读取用户配置的 AI 模型
    const aiConfig = getAIConfig()
    if (!aiConfig.apiKey) {
      showFailToast('请先在设置中配置 AI 模型')
      return
    }

    const res = await api.post('/notes/ai/generate-flashcard', {
      question: flashcardFront.value,
      context: currentNote.value.structured_note || currentNote.value.content || '',
      model: aiConfig.model,
      api_key: aiConfig.apiKey,
      base_url: aiConfig.provider === 'custom' ? aiConfig.baseUrl : getProvider(aiConfig.provider).baseUrl
    })
    console.log('📡 收到响应:', res)

    if (res.success) {
      flashcardBack.value = res.answer
      showToast('AI 生成完毕')
    } else {
      showFailToast('AI 生成失败')
    }
  } catch (e) {
    console.error('❌ 请求失败:', e)
    showFailToast('网络请求失败')
  } finally {
    isGeneratingAnswer.value = false
  }
}

const saveFlashcard = async () => {
  if (!flashcardFront.value || !flashcardBack.value) {
    showToast('正面和背面都不能为空哦')
    return
  }
  
  try {
    const res = await api.post(`/notes/${currentNote.value.id}/flashcards`, {
      note_id: currentNote.value.id,
      question: flashcardFront.value,
      answer: flashcardBack.value
    })
    if (res.success) {
      showToast('✨ 闪卡已收入牌组')
      // 自动切换到闪卡标签页并刷新
      activeSidebarTab.value = 'flashcards'
      loadFlashcards()
    }
  } catch (e) {
    console.error(e)
  }
}

// ====== 闪卡列表与复习 ======
const flashcards = ref([])
const isLoadingFlashcards = ref(false)

const loadFlashcards = async () => {
  isLoadingFlashcards.value = true
  try {
    const res = await api.get('/notes/flashcards')
    if (res.success) {
      flashcards.value = res.data
    }
  } catch (e) {
    console.error('加载闪卡失败', e)
    showFailToast('加载闪卡失败')
  } finally {
    isLoadingFlashcards.value = false
  }
}

const deleteFlashcard = async (cardId) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这张闪卡吗？'
    })
    const res = await api.delete(`/notes/flashcards/${cardId}`)
    if (res.success) {
      showToast('闪卡已删除')
      loadFlashcards()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error(e)
    }
  }
}

// 复习模式
const showReviewModal = ref(false)
const currentReviewIndex = ref(0)
const currentReviewCard = ref(null)
const showAnswer = ref(false)

// 单独查看闪卡模式
const showSingleCardModal = ref(false)
const selectedCard = ref(null)
const showSingleCardAnswer = ref(false)

const openSingleCard = (card) => {
  selectedCard.value = card
  showSingleCardAnswer.value = false
  showSingleCardModal.value = true
}

const handleSingleCardResult = (result) => {
  const resultMessages = {
    'hard': '💪 已标记为需要加强复习',
    'good': '✅ 已记住，下次复习间隔增加',
    'easy': '🌟 太简单了，稍后复习'
  }
  showToast(resultMessages[result] || '已记录')
  showSingleCardModal.value = false
}

const startReview = () => {
  if (flashcards.value.length === 0) return
  currentReviewIndex.value = 0
  currentReviewCard.value = flashcards.value[0]
  showAnswer.value = false
  showReviewModal.value = true
}

const handleReviewResult = (result) => {
  if (currentReviewIndex.value < flashcards.value.length - 1) {
    currentReviewIndex.value++
    currentReviewCard.value = flashcards.value[currentReviewIndex.value]
    showAnswer.value = false
  } else {
    showSuccessToast('🎉 复习完成！')
    showReviewModal.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', (e) => {
    if (!e.target.closest('.selection-toolbar')) {
      showSelectionMenu.value = false
    }
  })
})

// ====== 标签系统 ======
const presetTags = ref([
  { name: '重点', type: 'primary' },
  { name: '错题', type: 'danger' },
  { name: '公式', type: 'success' },
  { name: '易错点', type: 'warning' }
])

const newNoteTags = ref([])
const customTagInput = ref('')
const activeTagFilter = ref('')

const toggleTagInCreation = (tagName) => {
  if (newNoteTags.value.includes(tagName)) {
    newNoteTags.value = newNoteTags.value.filter(t => t !== tagName)
  } else {
    newNoteTags.value.push(tagName)
  }
}

const addCustomTag = () => {
  const tag = customTagInput.value.trim()
  if (tag && !newNoteTags.value.includes(tag)) {
    newNoteTags.value.push(tag)
    if (!presetTags.value.some(p => p.name == tag)) {
      presetTags.value.push({ name: tag, type: 'primary' })
    }
  }
  customTagInput.value = ''
}

const toggleSidebarFilter = (tagName) => {
  activeTagFilter.value = activeTagFilter.value === tagName ? '' : tagName
  console.log('[DEBUG] 筛选标签:', activeTagFilter.value)
  console.log('[DEBUG] 筛选后的列表:', filteredNotesList.value)
}

// ====== 搜索系统 ======
const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)
let searchTimeout = null

const handleSearch = () => {
  // 清除上一次的定时器
  if (searchTimeout) clearTimeout(searchTimeout)
  
  const keyword = searchQuery.value.trim()
  if (!keyword) {
    searchResults.value = []
    isSearching.value = false
    return
  }

  isSearching.value = true
  
  // 设置 500ms 的延迟
  searchTimeout = setTimeout(async () => {
    try {
      const res = await api.get(`/notes/search?keyword=${encodeURIComponent(keyword)}`)
      if (res.success) {
        searchResults.value = res.data
      }
    } catch (e) {
      console.error("搜索请求失败", e)
    } finally {
      isSearching.value = false
    }
  }, 500)
}

const deleteTag = (tagName) => {
  if (activeTagFilter.value === tagName) {
    activeTagFilter.value = ''
  }
  presetTags.value = presetTags.value.filter(t => t.name !== tagName)
  showToast({ message: `已删除标签 #${tagName}`, position: 'top' })
}

// ====== 笔记操作菜单 ======
const showNoteMenu = ref(false)
const showEditTagsModal = ref(false)
const currentMenuNote = ref(null)
const editingNoteTags = ref([])
const editingFolder = ref('')
const customEditTagInput = ref('')

// 新建文件夹相关状态
const showNewFolderModal = ref(false)
const targetNewFolderName = ref('')

// 核心：创建文件夹（通过生成初始化占位笔记来实现）
const confirmCreateFolder = async () => {
  const folderPath = targetNewFolderName.value.trim()
  if (!folderPath) {
    showToast('文件夹名称不能为空')
    return
  }

  try {
    // 伪造一篇极简的占位笔记，用来把文件夹的“地基”打好
    const res = await api.post('/notes', {
      course_id: selectedCourseId.value || 1,
      title: '📁 文件夹初始化',
      content: '这个文件夹已经建好啦，快往里面添加你的笔记吧！\n\n(这条初始化记录随时可以删除)',
      folder: folderPath
    })

    if (res.id) {  // 检查返回的笔记对象有 id 属性
      showToast('文件夹创建成功！')
      targetNewFolderName.value = '' // 清空输入框
      await loadNotes() // 重新拉取列表，左侧目录树会瞬间长出这个新文件夹！
    }
  } catch (e) {
    showFailToast('创建失败')
    console.error(e)
  }
}

// ================= 删除弹窗相关状态 =================
const showDeleteFolderModal = ref(false)
const keepNotesOnDelete = ref(true) // 默认勾选，保护用户数据

// 提取当前要删除的文件夹的"短名字" (例如 "大三/数学" -> "数学")
const targetFolderNameToDelete = computed(() => {
  return contextTargetFolder.value ? contextTargetFolder.value.split('/').pop() : ''
})

// 原来的右键菜单点击删除时，改为弹出自定义 Modal
const handleMenuDeleteFolder = () => {
  keepNotesOnDelete.value = true // 每次打开默认选择保留
  showDeleteFolderModal.value = true
}

// ================= 核心执行：删除或降级保留 =================
const confirmDeleteFolder = async () => {
  const targetPath = contextTargetFolder.value
  
  // 计算父级路径 (例如 target:"考研/数学" -> parent:"考研")
  const pathParts = targetPath.split('/')
  pathParts.pop() // 砍掉最后一级
  const parentPath = pathParts.join('/') 

  // 找出所有受影响的笔记（该文件夹及所有子文件夹里的笔记）
  const notesToProcess = notesList.value.filter(n => 
    n.folder === targetPath || n.folder?.startsWith(`${targetPath}/`)
  )
  
  console.log('[调试] 目标文件夹:', targetPath)
  console.log('[调试] 父级文件夹:', parentPath)
  console.log('[调试] 受影响笔记总数:', notesToProcess.length, notesToProcess)
  console.log('[调试] 是否保留笔记:', keepNotesOnDelete.value)
  
  if (notesToProcess.length === 0) {
    showToast('该文件夹没有笔记')
    return
  }

  showLoadingToast({ message: '处理中...', forbidClick: true })

  try {
    if (!keepNotesOnDelete.value) {
      // 🚨 毁灭模式：全军覆没
      console.log('[调试] 删除模式：删除所有笔记')
      await Promise.all(notesToProcess.map(note => api.delete(`/notes/${note.id}`)))
      if (currentNote.value && (currentNote.value.folder === targetPath || currentNote.value.folder?.startsWith(`${targetPath}/`))) {
        currentNote.value = null // 清空右侧正在看的笔记
      }
    } else {
      // 🛡️ 保护模式：降级移至父目录
      console.log('[调试] 保留模式：移动笔记到父目录')
      
      // 1. 找出占位用的"初始化笔记"，这个必须删掉，否则空文件夹依然存在
      const dummyNote = notesToProcess.find(n => n.folder === targetPath && (n.title === '📁 文件夹初始化' || n.title === '未命名笔记'))
      console.log('[调试] 找到初始化笔记:', dummyNote)
      
      if (dummyNote) {
        try {
          await api.delete(`/notes/${dummyNote.id}`)
        } catch (e) {
          console.warn('[调试] 删除初始化笔记失败（可能已不存在）:', e)
        }
      }

      // 2. 将剩下的真实笔记，批量更新路径
      const notesToMove = notesToProcess.filter(n => n.id !== dummyNote?.id)
      console.log('[调试] 待移动笔记:', notesToMove)
      
      // 逐个更新，避免 Promise.all 出错导致全部失败
      for (const note of notesToMove) {
        let newFolder = note.folder
        
        if (!parentPath) {
          // 如果删除的是顶级目录(例如 "数学")，则移入 "默认笔记本"
          const remainder = note.folder.substring(targetPath.length) // 如 "/高数" 或 ""
          newFolder = remainder.startsWith('/') ? remainder.substring(1) : remainder
          if (!newFolder) newFolder = '默认笔记本'
        } else {
          // 如果删除的是子目录(例如 target:"大三/数学", parent:"大三")
          // note.folder 为 "大三/数学/高数" 时，直接替换成 "大三/高数"
          newFolder = note.folder.replace(targetPath, parentPath)
        }
        
        console.log(`[调试] 笔记 ${note.id} 从 ${note.folder} 迁移到 ${newFolder}`)

        // 调用更新接口，只更新 folder 字段
        try {
          await api.put(`/notes/${note.id}`, {
            folder: newFolder
          })
          console.log(`[调试] 笔记 ${note.id} 更新成功`)
        } catch (e) {
          console.error(`[调试] 笔记 ${note.id} 更新失败:`, e)
        }
      }
    }

    // 重新拉取数据，左侧目录树会自动重新排版
    await loadNotes()
    showToast('操作完成')
    
  } catch (e) {
    console.error("删除/迁移失败", e)
    showFailToast('网络异常，操作失败')
  }
}

// ================= 右键菜单逻辑 =================
// 菜单状态
const showContextMenu = ref(false)
const menuX = ref(0)
const menuY = ref(0)
const contextTargetFolder = ref('') // 记录你当前右键点击的是哪个绝对路径

// 1. 唤醒菜单
const handleFolderContextMenu = (payload) => {
  const { event, folderName, currentPath } = payload
  // 拼装出这根树枝的绝对路径 (如：大三/数学/高数)
  contextTargetFolder.value = currentPath ? `${currentPath}/${folderName}` : folderName
  
  menuX.value = event.clientX
  menuY.value = event.clientY
  showContextMenu.value = true
}

// 全局监听：点击任意地方关闭菜单
const closeMenu = () => showContextMenu.value = false
onMounted(() => window.addEventListener('click', closeMenu))
onUnmounted(() => window.removeEventListener('click', closeMenu))

// ================= 核心操作管线 =================

// 操作 1：在此处新建笔记
const handleMenuNewNote = () => {
  showContextMenu.value = false
  openTemplateModal(contextTargetFolder.value)
}

// 操作 2：新建子文件夹
const handleMenuNewFolder = () => {
  targetNewFolderName.value = `${contextTargetFolder.value}/` // 预填路径并加上斜杠，等你打字
  showNewFolderModal.value = true
  showContextMenu.value = false
}

// 操作 3：重命名文件夹 (硬核：批量修改路径前缀)
const handleMenuRenameFolder = () => {
  showContextMenu.value = false
  const oldPath = contextTargetFolder.value
  const folderName = oldPath.split('/').pop() // 提取最后一段名字

  showConfirmDialog({
    title: `重命名: ${folderName}`,
    message: '警告：这将会修改该路径下所有笔记的所属位置。由于是批量操作，可能需要几秒钟。',
    beforeClose: async (action) => {
      if (action === 'confirm') {
        // 这里为了体验，直接弹一个原生 prompt。也可以自己再写个 dialog
        const newName = window.prompt("请输入新的文件夹名称:", folderName)
        if (!newName || newName === folderName) return true
        
        const newPath = oldPath.substring(0, oldPath.lastIndexOf(folderName)) + newName
        
        // 找出所有属于这个文件夹及子文件夹的笔记
        const notesToUpdate = notesList.value.filter(n => n.folder === oldPath || n.folder?.startsWith(`${oldPath}/`))
        
        showLoadingToast({ message: '批量迁移中...', forbidClick: true })
        // 并发进行批量更新 (调用我们已有的 update 接口)
        await Promise.all(notesToUpdate.map(note => {
          const updatedFolder = note.folder.replace(oldPath, newPath)
          return api.put(`/notes/${note.id}`, { folder: updatedFolder })
        }))
        
        closeToast()
        await loadNotes()
        showToast('重命名完成')
      }
      return true
    }
  })
}

// ================= 拖拽重组：静默迁移引擎 =================
const executeNoteMove = async ({ note, targetPath }) => {
  // 可以在右上角给个静默提示
  showToast({ message: '正在移动...', position: 'top' })
  
  try {
    // 调用现有的修改接口，仅修改 folder 字段
    const res = await api.put(`/notes/${note.id}`, {
      title: note.title,
      content: note.content,
      tags: note.tags,
      folder: targetPath
    })

    // API 拦截器返回 response.data，所以直接检查 res.success
    if (res.success) {
      showToast({ message: '✨ 移动成功', position: 'top' })
      // 如果当前正在阅读这篇笔记，同步更新内存里的路径
      if (currentNote.value?.id === note.id) {
        currentNote.value.folder = targetPath
      }
      // 重新拉取列表，左侧目录树会自动重新渲染折叠状态
      await loadNotes() 
    } else {
      showFailToast('移动失败: ' + (res.message || '未知错误'))
    }
  } catch (e) {
    showFailToast('移动失败')
    console.error('移动笔记失败:', e)
  }
}

const executeFolderMove = async ({ sourcePath, targetPath }) => {
  showToast({ message: '正在移动文件夹...', position: 'top' })
  
  try {
    const res = await api.post('/notes/move-folder', {
      source_path: sourcePath,
      target_path: targetPath
    })

    if (res.success) {
      showToast({ message: `✨ ${res.message}`, position: 'top' })
      await loadNotes() 
    } else {
      showFailToast('移动失败: ' + (res.message || '未知错误'))
    }
  } catch (e) {
    showFailToast('移动文件夹失败')
    console.error('移动文件夹失败:', e)
  }
}

// ====== 根目录拖放处理 ======
const handleRootDragOver = (event) => {
  event.preventDefault()
}

const handleRootDrop = async (event) => {
  isRootDragOver.value = false
  
  try {
    const data = event.dataTransfer.getData('application/json')
    if (!data) return
    
    const droppedData = JSON.parse(data)
    
    if (droppedData.type === 'folder') {
      // 文件夹移动到根目录
      const sourcePath = droppedData.currentPath 
        ? `${droppedData.currentPath}/${droppedData.folderName}` 
        : droppedData.folderName
      
      // 不能把根目录的文件夹再移到根目录（源路径等于文件夹名称，说明已经在根目录）
      if (sourcePath !== droppedData.folderName) {
        await executeFolderMove({ sourcePath, targetPath: '' })
      }
    } else if (droppedData.folder !== undefined && droppedData.folder !== '') {
      // 笔记移动到根目录
      await executeNoteMove({ note: droppedData, targetPath: '' })
    }
  } catch (e) {
    console.error("根目录拖放解析失败", e)
  }
}

const noteMenuActions = computed(() => [
  { name: '编辑属性', icon: 'setting-o' },
  { name: 'AI 重构', icon: 'refresh' },
  { name: '删除笔记', icon: 'delete-o', color: '#ee0a24' }
])

const openNoteMenu = (note) => {
  currentMenuNote.value = note
  editingNoteTags.value = note.tags ? note.tags.split(',').filter(t => t) : []
  editingFolder.value = note.folder || '默认笔记本'
  editingNoteCourseId.value = note.course_id ? String(note.course_id) : ''
  showNoteMenu.value = true
}

const handleNoteMenuSelect = (action) => {
  if (!currentMenuNote.value) return
  
  switch (action.name) {
    case '编辑属性':
      showNoteMenu.value = false
      showEditTagsModal.value = true
      break
    case 'AI 重构':
      showNoteMenu.value = false
      handleRegenerateNote(currentMenuNote.value.id)
      break
    case '删除笔记':
      showNoteMenu.value = false
      handleDeleteNote(currentMenuNote.value.id)
      break
  }
}

const toggleTagInEdit = (tagName) => {
  if (editingNoteTags.value.includes(tagName)) {
    editingNoteTags.value = editingNoteTags.value.filter(t => t !== tagName)
  } else {
    editingNoteTags.value.push(tagName)
  }
}

const addCustomEditTag = () => {
  const tag = customEditTagInput.value.trim()
  if (tag && !editingNoteTags.value.includes(tag)) {
    editingNoteTags.value.push(tag)
    if (!presetTags.value.some(p => p.name == tag)) {
      presetTags.value.push({ name: tag, type: 'primary' })
    }
  }
  customEditTagInput.value = ''
}

const removeEditTag = (tag) => {
  editingNoteTags.value = editingNoteTags.value.filter(t => t !== tag)
}

const saveNoteTags = async () => {
  if (!currentMenuNote.value) return
  
  try {
    // 获取用户选择的课程ID（如果没有选择则为null）
    const courseId = editingNoteCourseId.value ? parseInt(editingNoteCourseId.value) : null
    console.log('[DEBUG] 保存属性:', { 
      tags: editingNoteTags.value.join(','), 
      folder: editingFolder.value,
      course_id: courseId 
    })
    const res = await api.put(`/notes/${currentMenuNote.value.id}`, {
      title: currentMenuNote.value.title,
      tags: editingNoteTags.value.join(','),
      folder: editingFolder.value || '默认笔记本',
      course_id: courseId
    })
    console.log('[DEBUG] 保存响应:', res)
    
    showEditTagsModal.value = false
    await loadNotes()
    
    const updatedNote = notesList.value.find(n => n.id === currentMenuNote.value.id)
    if (updatedNote) {
      currentMenuNote.value = { ...updatedNote }
      if (currentNote.value?.id === updatedNote.id) {
        currentNote.value = { ...updatedNote }
      }
    }
    
    showSuccessToast('属性已更新')
  } catch (e) {
    console.error('[ERROR] 更新属性失败:', e)
    showFailToast('更新失败')
  }
}

const filteredNotesList = computed(() => {
  if (!activeTagFilter.value) return notesList.value
  
  return notesList.value.filter(note => {
    if (!note.tags) return false
    const tagsArray = note.tags.split(',').map(t => t.trim()).filter(t => t)
    return tagsArray.includes(activeTagFilter.value)
  })
})

// ====== 渲染内容 ======
const renderNoteContent = computed(() => {
  if (!currentNote.value?.structured_note) return ''
  return currentNote.value.structured_note
})

// ====== 获取笔记标题 ======
const getNoteTitle = (note) => {
  if (!note) return '未命名笔记'
  if (note.title && note.title.trim()) return note.title.trim()
  const content = note.structured_note || note.original_text || ''
  const match = content.match(/^#\s+(.+)$/m)
  if (match) return match[1].trim()
  const firstLine = content.split('\n')[0] || ''
  return firstLine.slice(0, 30) + (firstLine.length > 30 ? '...' : '') || '未命名笔记'
}

// ====== 状态栏字数统计模式 ======
const countMode = ref(localStorage.getItem('wordCountMode') || 'words')
const showWordCountMenu = ref(false)

// 当前显示的计数
const displayCount = computed(() => {
  if (!currentNote.value) return 0
  switch (countMode.value) {
    case 'words':
      return getWordCount(currentNote.value)
    case 'chars':
      return getCharCount(currentNote.value, false)
    case 'chars-space':
      return getCharCount(currentNote.value, true)
    case 'all':
      return getAllCharCount(currentNote.value)
    default:
      return getWordCount(currentNote.value)
  }
})

// 计数单位
const countUnit = computed(() => {
  switch (countMode.value) {
    case 'words': return '字'
    case 'chars': return '字符'
    case 'chars-space': return '字符'
    case 'all': return '字符'
    default: return '字'
  }
})

// 设置统计模式
const setCountMode = (mode) => {
  countMode.value = mode
  localStorage.setItem('wordCountMode', mode)
  showWordCountMenu.value = false
}

// 点击外部关闭菜单
const handleDocumentClick = (e) => {
  // 如果点击的是状态栏或菜单内部，不关闭
  if (e.target.closest('.status-bar')) return
  showWordCountMenu.value = false
}

onMounted(() => {
  // 使用 setTimeout 延后注册，避免初始化时的点击事件干扰
  setTimeout(() => {
    document.addEventListener('click', handleDocumentClick)
  }, 0)
})

onUnmounted(() => {
  document.removeEventListener('click', handleDocumentClick)
})

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

// 计算笔记行数
const getLineCount = (note) => {
  if (!note) return 0
  const content = note.structured_note || note.original_text || ''
  if (!content.trim()) return 0
  return content.split('\n').length
}

// 计算笔记段落数
const getParagraphCount = (note) => {
  if (!note) return 0
  const content = note.structured_note || note.original_text || ''
  if (!content.trim()) return 0
  // 按空行分隔段落
  return content.split(/\n\s*\n/).filter(p => p.trim()).length
}

// 计算阅读时间（分钟）
const getReadingTime = (note) => {
  if (!note) return 0
  const count = getWordCount(note)
  // 中文阅读速度约 300 字/分钟，英文约 200 词/分钟
  // 取平均值，至少 1 分钟
  return Math.max(1, Math.ceil(count / 300))
}

// 计算字符数
const getCharCount = (note, includeSpace = false) => {
  if (!note) return 0
  const content = note.structured_note || note.original_text || ''
  if (!content) return 0
  if (includeSpace) {
    return content.length
  }
  return content.replace(/\s/g, '').length
}

// 计算全部字符数（包括 Markdown 语法、空格、换行等）
const getAllCharCount = (note) => {
  if (!note) return 0
  const content = note.structured_note || note.original_text || ''
  return content.length
}

// ====== 重命名弹窗状态 ======
const showRenameModal = ref(false)
const editingTitle = ref('')

// 打开弹窗，自动填入当前标题
const openRenameModal = () => {
  if (!currentNote.value) return
  editingTitle.value = currentNote.value.title || ''
  showRenameModal.value = true
}

// 核心：确认修改并保存
const confirmRename = async () => {
  if (!currentNote.value || !editingTitle.value.trim()) {
    showToast('标题不能为空哦')
    return
  }

  const newTitle = editingTitle.value.trim()
  const noteId = currentNote.value.id

  try {
    const res = await api.put(`/notes/${noteId}`, {
      title: newTitle,
      content: currentNote.value.content,
      tags: currentNote.value.tags || ''
    })

    if (res.success || res?.error === undefined) {
      showRenameModal.value = false
      
      await loadNotes()
      
      const updatedNote = notesList.value.find(n => n.id === noteId)
      if (updatedNote) {
        currentNote.value = { ...updatedNote }
      }
      
      showSuccessToast('✨ 标题已更新')
    } else {
      showFailToast(res?.message || '保存失败')
    }
  } catch (e) {
    console.error('[ERROR] 修改标题失败:', e)
    showFailToast('网络异常，未能保存')
  }
}

// ================= 🔗 链接悬停预览引擎 =================
const showLinkPreview = ref(false)
const previewTargetNote = ref(null)
const previewX = ref(0)
const previewY = ref(0)

let previewHoverTimer = null
let previewHideTimer = null

const getPreviewText = (markdownStr) => {
  if (!markdownStr) return '这里是一片荒芜，还没有写内容...'
  let stripped = markdownStr.replace(/[#*`_\[\]>=-]/g, '').trim()
  return stripped.length > 120 ? stripped.substring(0, 120) + '...' : stripped
}

const getPreviewHtml = (markdownStr) => {
  if (!markdownStr) return '<span style="color: var(--text-tertiary, #9ca3af);">这里是一片荒芜，还没有写内容...</span>'
  
  let text = markdownStr
  
  text = text.replace(/```[\s\S]*?```/g, '')
  text = text.replace(/`([^`]+)`/g, '$1')
  text = text.replace(/^\s*#+\s*/gm, '')
  text = text.replace(/[*_]{2}([^*_]+)[*_]{2}/g, '$1')
  text = text.replace(/[*_]([^*_]+)[*_]/g, '$1')
  text = text.replace(/\[{2}([^\]]+)\]{2}/g, '$1')
  
  const formulas = []
  let formulaIndex = 0
  
  text = text.replace(/\$\$(.*?)\$\$/g, (match, formula) => {
    formulas.push({ type: 'block', content: formula.trim() })
    return `__FORMULA_BLOCK_${formulaIndex++}__`
  })
  
  text = text.replace(/\$(.*?)\$/g, (match, formula) => {
    formulas.push({ type: 'inline', content: formula.trim() })
    return `__FORMULA_INLINE_${formulaIndex++}__`
  })
  
  text = text.replace(/\n+/g, ' ')
  
  if (text.length > 180) {
    text = text.substring(0, 180) + '...'
  }
  
  for (let i = 0; i < formulas.length; i++) {
    const formula = formulas[i]
    try {
      const rendered = katex.renderToString(formula.content, {
        displayMode: formula.type === 'block',
        throwOnError: false
      })
      text = text.replace(`__FORMULA_${formula.type.toUpperCase()}_${i}__`, rendered)
    } catch (e) {
      text = text.replace(`__FORMULA_${formula.type.toUpperCase()}_${i}__`, formula.content)
    }
  }
  
  return `<p style="margin: 0; line-height: 1.6;">${text}</p>`
}

const handleArticleMouseOver = (e) => {
  const target = e.target
  if (target.classList && target.classList.contains('internal-link')) {
    clearPreviewHideTimer()
    
    const targetTitle = target.getAttribute('data-target')
    const note = notesList.value.find(n => n.title === targetTitle)
    
    if (note) {
      previewHoverTimer = setTimeout(() => {
        previewTargetNote.value = note
        
        const rect = target.getBoundingClientRect()
        previewX.value = rect.left + rect.width / 2
        previewY.value = rect.bottom + 12 
        
        showLinkPreview.value = true
      }, 200)
    }
  }
}

const handleArticleMouseOut = (e) => {
  const target = e.target
  if (target.classList && target.classList.contains('internal-link')) {
    clearTimeout(previewHoverTimer) 
    startPreviewHideTimer()
  }
}

const startPreviewHideTimer = () => {
  previewHideTimer = setTimeout(() => {
    showLinkPreview.value = false
    previewTargetNote.value = null
  }, 300)
}

const clearPreviewHideTimer = () => {
  if (previewHideTimer) clearTimeout(previewHideTimer)
}

// ================= 📝 模板化笔记引擎 =================
const showTemplateModal = ref(false)
const targetFolderForNewNote = ref('默认笔记本')

const defaultTemplates = [
  { 
    id: 'blank', 
    title: '📄 空白笔记', 
    desc: '自由发挥，从零开始',
    content: '' 
  },
  { 
    id: 'math', 
    title: '📐 数学定理笔记', 
    desc: '专业的数学知识记录结构',
    content: '# 📐 定理/公式名称\n\n## 📌 核心定义\n\n> 定理的正式、准确表述\n\n---\n\n## 🔍 关键概念解析\n\n- **概念1**: 解释说明\n- **概念2**: 解释说明\n- **前置知识**: 需要掌握的基础知识\n\n---\n\n## 📝 完整证明过程\n\n### 证明思路\n\n（简述证明的核心思路和策略）\n\n### 详细步骤\n\n```\n1. 第一步：\n2. 第二步：\n3. 第三步：\n...\n```\n\n---\n\n## 💡 经典例题\n\n### 例题 1\n\n**题目**: \n\n**解答**:\n\n### 例题 2\n\n**题目**: \n\n**解答**:\n\n---\n\n## ⚠️ 常见误区与易错点\n\n- ❌ 错误做法：\n- ✅ 正确做法：\n\n---\n\n## 🔗 相关定理与公式\n\n- [[相关定理1]]\n- [[相关定理2]]\n\n---\n\n## 📚 参考资料\n\n- 教材/课程章节：\n- 视频/文章链接：\n'
  },
  { 
    id: 'bug', 
    title: '🐛 问题/故障排查记录', 
    desc: '专业的问题分析与解决模板',
    content: '# 🐛 问题/故障记录\n\n## 📋 基本信息\n\n| 项目 | 内容 |\n|------|------|\n| **问题ID** | BUG-YYYYMMDD-001 |\n| **发现时间** | 202X-XX-XX |\n| **发现人** | |\n| **优先级** | 🔴 严重 / 🟡 中等 / 🟢 轻微 |\n| **状态** | 🟡 处理中 / ✅ 已解决 / ⏸️ 挂起 |\n\n---\n\n## 🎯 问题现象\n\n### 现象描述\n\n（清晰、具体地描述发生了什么）\n\n### 截图/日志\n\n```\n（粘贴错误日志或报错信息）\n```\n\n---\n\n## 🔍 复现步骤\n\n1. 第一步：\n2. 第二步：\n3. 第三步：\n\n---\n\n## 🕵️ 根因分析\n\n### 初步排查\n\n| 排查项 | 结果 | 说明 |\n|--------|------|------|\n| 检查项1 | ❌/✅ | |\n| 检查项2 | ❌/✅ | |\n\n### 根本原因\n\n> 真正的问题根源是什么？\n\n---\n\n## ✅ 解决方案\n\n### 方案对比\n\n| 方案 | 优点 | 缺点 | 实施难度 |\n|------|------|------|----------|\n| 方案A | | | |\n| 方案B | | | |\n\n### 最终方案\n\n（详细说明具体怎么做）\n\n---\n\n## 📊 验证结果\n\n### 测试用例\n\n- [ ] 测试1：\n- [ ] 测试2：\n\n### 结果确认\n\n✅ 问题已修复，验证通过\n\n---\n\n## 📝 经验总结\n\n### 学到了什么\n\n### 如何预防\n\n- [ ] 预防措施1：\n- [ ] 预防措施2：\n\n---\n\n## 🔗 相关问题\n\n- [[相关问题1]]\n'
  },
  { 
    id: 'cornell', 
    title: '📝 康奈尔笔记法', 
    desc: '世界公认的高效笔记法（升级版）',
    content: '# 📝 课程/讲座主题\n\n## 📌 基本信息\n\n| 项目 | 内容 |\n|------|------|\n| **课程/讲座** | |\n| **日期** | 202X-XX-XX |\n| **页码** | 第 ___ 页 / 共 ___ 页 |\n| **讲师/来源** | |\n\n---\n\n| 🎯 线索栏 (25%) | 💡 笔记栏 (75%) |\n|----------------|----------------|\n| \n**❓ 问题区**   | \n**📝 笔记提示**<br>• 用项目符号或编号<br>• 善用缩写与箭头<br>• 每段后留一行空白<br>• 🔴🔵⚫ 用颜色区分主次<br> |\n| Q1?           |  |\n| Q2?           |  |\n| Q3?           |  |\n|               |  |\n| **🔑 关键词/符号** | \n**📌 疑难标签**<br>❓ 没听懂<br>⭐ 很重要<br>🔗 可关联其他章节 |\n| - 关键词1     |  |\n| - 关键词2     |  |\n| - 关键词3     |  |\n| ⚡⚡⚡ 高频考点  |  |\n\n---\n\n## 📊 总结与反思\n\n### 📝 一句话摘要\n\n（10字以内，电梯演讲式）\n\n---\n\n### 🎯 核心三点\n\n1. **核心点1**：\n2. **核心点2**：\n3. **核心点3**：\n\n---\n\n### 🤔 合上笔记问自己\n\n- 我今天学到了哪 3 个关键点？\n  1. \n  2. \n  3. \n- 哪个概念最容易混淆？\n- 我能举出一个反例吗？\n\n---\n\n| ❓ 疑问与困惑 | 🎯 行动计划（含产出） |\n|-------------|---------------------|\n| ❓ 问题1：  | □ 立即：___________<br>  [ ] 思维导图<br>  [ ] 写自测题<br>  [ ] 讲给别人听<br>  [ ] 与旧知识关联 |\n| ❓ 问题2：  | □ 近期：___________<br>  [ ] 思维导图<br>  [ ] 写自测题<br>  [ ] 讲给别人听<br>  [ ] 与旧知识关联 |\n| ❓ 问题3：  | |\n\n---\n\n## ⏰ 复习打卡\n\n| 复习时间 | 状态 | 日期 | 自测正确率 |\n|---------|------|------|-----------|\n| □ 24h   | ⏳   |      | ___%      |\n| □ 7d    | ⏳   |      | ___%      |\n| □ 30d   | ⏳   |      | ___%      |\n\n---\n\n## 📝 使用示例（光合作用）\n\n| 线索栏 | 笔记栏 |\n|--------|--------|\n| Q: 光合作用是什么？ | • 绿色植物利用阳光能量，将CO₂和H₂O转化为有机物<br>• ⭐ 公式：6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂ |\n| Q: 两个阶段？ | 1. **光反应**（类囊体）→ 产生ATP和NADPH<br>2. **暗反应**（基质）→ 合成葡萄糖 |\n| 关键词：叶绿体<br>类囊体<br>基质<br>叶绿素 |  |\n\n---\n\n💡 **提示**：\n- 左侧用疑问句式，方便后续主动回忆\n- 右侧用 ⭐❓🔗 标记重点/疑点/关联\n- 复习时遮住右侧，尝试回答左侧问题\n'
  },
  {
    id: 'meeting',
    title: '📋 高效会议纪要',
    desc: '结构化的会议记录与跟进模板',
    content: '# 📋 会议纪要\n\n## 📌 基本信息\n\n| 项目 | 内容 |\n|------|------|\n| **会议主题** | |\n| **时间** | 202X-XX-XX XX:XX |\n| **地点** | 线上/线下 |\n| **主持人** | |\n| **参会人员** | |\n| **缺席人员** | |\n| **记录人** | |\n\n---\n\n## 🎯 会议目标\n\n### 本次会议要解决的问题\n\n1. [ ] 目标1：\n2. [ ] 目标2：\n3. [ ] 目标3：\n\n---\n\n## 📝 讨论要点\n\n### 议题一\n\n**讨论内容**：\n\n**达成共识**：\n\n**待决议**：\n\n---\n\n### 议题二\n\n**讨论内容**：\n\n**达成共识**：\n\n**待决议**：\n\n---\n\n## ✅ 行动项与跟进\n\n| 序号 | 行动项 | 负责人 | 截止时间 | 状态 | 备注 |\n|------|--------|--------|----------|------|------|\n| 1 | | | | ⏳ 待开始 | |\n| 2 | | | | 🔄 进行中 | |\n| 3 | | | | ✅ 已完成 | |\n\n---\n\n## 📌 重要决议\n\n- **决议1**: \n- **决议2**: \n\n---\n\n## 📅 下次会议\n\n| 项目 | 内容 |\n|------|------|\n| **时间** | |\n| **地点** | |\n| **待准备** | |\n| **待讨论议题** | |\n'
  },
  {
    id: 'reading',
    title: '📖 深度读书笔记',
    desc: '系统的书籍阅读与知识内化',
    content: '# 📖 书籍/文章信息\n\n## 基本信息\n\n| 项目 | 内容 |\n|------|------|\n| **书名/文章标题** | |\n| **作者** | |\n| **译者** | |\n| **出版社/来源** | |\n| **阅读时间** | 202X-XX-XX |\n| **阅读类型** | 📕 精读 / 📗 通读 / 📙 速读 |\n\n---\n\n## 🎯 阅读目标\n\n> 我想从这本书里获得什么？\n\n- 目标1：\n- 目标2：\n\n---\n\n## 📊 核心观点\n\n### 核心观点一\n\n**原文引用**：\n> \n\n**我的理解**：\n\n**启发与应用**：\n\n---\n\n### 核心观点二\n\n**原文引用**：\n> \n\n**我的理解**：\n\n**启发与应用**：\n\n---\n\n## 💡 金句摘录\n\n> "经典语录1"\n> \n> —— 出处\n\n---\n\n## 🤔 我的思考\n\n### 认同的观点\n\n- ✅ 观点1：\n- ✅ 观点2：\n\n### 不同看法\n\n- ❓ 疑问1：\n- 💭 思考1：\n\n---\n\n## 🎬 行动清单\n\n| 行动项 | 优先级 | 计划时间 | 状态 |\n|--------|--------|----------|------|\n| 行动1 | 🔴 高 | | ⏳ |\n| 行动2 | 🟡 中 | | ⏳ |\n\n---\n\n## 🔗 相关资料\n\n- [[相关书籍1]]\n- [推荐文章](url)\n'
  },
  {
    id: 'project',
    title: '🚀 项目管理文档',
    desc: '完整的项目规划与管理',
    content: '# 🚀 项目名称\n\n## 📋 项目概述\n\n### 项目背景\n\n（为什么要做这个项目？）\n\n### 项目目标\n\n- **总体目标**: \n- **成功标准**: \n\n---\n\n## 📊 时间规划\n\n| 阶段 | 开始时间 | 结束时间 | 关键里程碑 | 负责人 |\n|------|----------|----------|------------|--------|\n| 1. 立项 | | | | |\n| 2. 设计 | | | | |\n| 3. 开发 | | | | |\n| 4. 测试 | | | | |\n| 5. 上线 | | | | |\n\n---\n\n## 👥 团队与分工\n\n| 角色 | 人员 | 职责 |\n|------|------|------|\n| 项目经理 | | |\n| 开发/执行 | | |\n| 设计/支持 | | |\n\n---\n\n## 📝 任务清单\n\n### 阶段一：立项\n\n- [ ] 任务1：\n- [ ] 任务2：\n\n### 阶段二：实施\n\n- [ ] 任务1：\n- [ ] 任务2：\n\n---\n\n## ⚠️ 风险与应对\n\n| 风险 | 发生概率 | 影响 | 应对措施 | 负责人 |\n|------|----------|------|----------|--------|\n| 风险1 | 🟡 中 | 🟡 中 | | |\n| 风险2 | 🔴 高 | 🔴 高 | | |\n\n---\n\n## 📈 进度跟踪\n\n### 本周进度\n\n- ✅ 已完成：\n- 🔄 进行中：\n- ❌ 阻塞项：\n\n### 下周计划\n\n- \n- \n'
  },
  {
    id: 'daily',
    title: '☀️ 每日复盘与规划',
    desc: '专业的每日反思与成长记录',
    content: '# ☀️ 每日复盘 - YYYY-MM-DD\n\n---\n\n## ✅ 今日完成\n\n### 核心成果\n\n- [ ] 任务1：\n- [ ] 任务2：\n\n### 时间记录\n\n| 时间段 | 活动 | 产出 |\n|--------|------|------|\n| 上午 | | |\n| 下午 | | |\n| 晚上 | | |\n\n---\n\n## 🤔 反思与改进\n\n### 做得好的地方\n\n- 👍 亮点1：\n- 👍 亮点2：\n\n### 需要改进\n\n- ⚠️ 不足1：\n- 💡 改进方案：\n\n---\n\n## 💡 今日收获\n\n### 学到了什么\n\n- 知识1：\n- 技能1：\n\n### 重要感悟\n\n> \n\n---\n\n## 📋 明日规划\n\n### Top 3 优先级\n\n1. 🔴 重要紧急：\n2. 🟡 重要不紧急：\n3. 🟢 一般：\n\n### 详细计划\n\n| 时间 | 任务 | 预计时长 |\n|------|------|----------|\n| | | |\n| | | |\n\n---\n\n## ✨ 感恩与小确幸\n\n- 感谢1：\n- 小确幸：\n'
  },
  {
    id: 'code',
    title: '💻 技术/API文档',
    desc: '专业的技术文档结构',
    content: '# 💻 功能/组件/API文档\n\n## 📝 概述\n\n### 功能说明\n\n（这个功能是做什么的？）\n\n### 应用场景\n\n- 场景1：\n- 场景2：\n\n---\n\n## 🏗️ 架构与设计\n\n### 系统架构图\n\n```\n（架构图或模块关系）\n```\n\n### 核心流程\n\n```mermaid\nflowchart LR\n    A[开始] --> B[处理]\n    B --> C[结束]\n```\n\n---\n\n## 📋 API 接口\n\n### 接口一\n\n| 项目 | 内容 |\n|------|------|\n| **URL** | `/api/xxx` |\n| **方法** | GET/POST/PUT/DELETE |\n| **描述** | |\n\n**请求参数**：\n\n| 参数名 | 类型 | 必填 | 说明 |\n|--------|------|------|------|\n| param1 | string | ✅ | |\n\n**响应示例**：\n\n```json\n{\n  \"code\": 200,\n  \"data\": {}\n}\n```\n\n---\n\n## 💾 数据结构\n\n### Schema 定义\n\n```typescript\ninterface DataType {\n  id: string;\n  name: string;\n  createdAt: Date;\n}\n```\n\n---\n\n## 🚀 使用示例\n\n### 基础用法\n\n```javascript\n// 代码示例\n```\n\n### 高级用法\n\n```javascript\n// 代码示例\n```\n\n---\n\n## ⚠️ 注意事项\n\n- 注意1：\n- 注意2：\n\n---\n\n## 🔗 相关链接\n\n- [[相关组件1]]\n- 外部文档：\n'
  },
  {
    id: 'lesson',
    title: '🎓 课程学习笔记',
    desc: '系统化的课程学习与知识管理',
    content: '# 🎓 课程/讲座名称\n\n## 📌 基本信息\n\n| 项目 | 内容 |\n|------|------|\n| **课程名称** | |\n| **讲师/来源** | |\n| **学习时间** | 202X-XX-XX |\n| **课程类型** | 🎥 视频 / 📖 阅读 / 🎤 讲座 |\n\n---\n\n## 🎯 学习目标\n\n### 本课目标\n\n- [ ] 掌握1：\n- [ ] 理解2：\n- [ ] 学会3：\n\n---\n\n## 📝 核心内容\n\n### 知识点一\n\n**核心要点**：\n\n**详细解释**：\n\n---\n\n### 知识点二\n\n**核心要点**：\n\n**详细解释**：\n\n---\n\n## 🎯 重点与难点\n\n### 重点\n\n- ⭐ 重点1：\n- ⭐ 重点2：\n\n### 难点\n\n- 🤔 难点1：\n- 💡 理解：\n\n---\n\n## 📝 练习与作业\n\n### 课堂练习\n\n- [ ] 练习1：\n- [ ] 练习2：\n\n### 课后作业\n\n- [ ] 作业1：\n- [ ] 作业2：\n\n---\n\n## ❓ 疑问与思考\n\n### 不懂的地方\n\n- ❓ 问题1：\n- ❓ 问题2：\n\n### 我的思考\n\n- 💭 思考1：\n\n---\n\n## 📚 相关资料\n\n- 推荐阅读：\n- 视频链接：\n- [[相关知识点]]\n'
  },
  {
    id: 'recipe',
    title: '🍳 美食食谱',
    desc: '专业的食谱记录与创新',
    content: '# 🍳 菜品名称\n\n## 📸 成品展示\n\n---\n\n## 📋 基本信息\n\n| 项目 | 内容 |\n|------|------|\n| **菜系** | 川菜/粤菜/西餐/日料... |\n| **难度** | ⭐ 简单 / ⭐⭐ 中等 / ⭐⭐⭐ 困难 |\n| **准备时间** | 30分钟 |\n| **烹饪时间** | 45分钟 |\n| **份量** | 2-3人份 |\n| **口味** | 咸鲜/麻辣/酸甜/清淡 |\n\n---\n\n## 🥬 食材清单\n\n### 主料\n\n| 食材 | 用量 | 备注 |\n|------|------|------|\n| 主食材1 | 500g | |\n| 主食材2 | 200g | |\n\n### 辅料\n\n| 食材 | 用量 | 备注 |\n|------|------|------|\n| 配料1 | 适量 | |\n| 配料2 | 少许 | |\n\n### 调料\n\n| 调料 | 用量 |\n|------|------|\n| 盐 | 5g |\n| 生抽 | 2勺 |\n\n---\n\n## 👩‍🍳 制作步骤\n\n### 准备工作\n\n1. 处理食材：\n2. 备料：\n\n### 烹饪过程\n\n```\n1️⃣ 第一步：\n   （详细说明操作要点）\n\n2️⃣ 第二步：\n   （关键技巧和注意事项）\n\n3️⃣ 第三步：\n   （火候控制、时间把握）\n```\n\n---\n\n## 💡 小贴士与技巧\n\n- 💡 技巧1：\n- 💡 技巧2：\n\n---\n\n## 🔄 变通与创新\n\n### 可以替换的食材\n\n- 可替换为：\n\n### 个人创新\n\n- 我的改动：\n\n---\n\n## 📊 营养信息\n\n| 营养成分 | 每份含量 |\n|----------|----------|\n| 热量 | kcal |\n| 蛋白质 | g |\n| 碳水 | g |\n\n---\n\n## 📝 制作记录\n\n| 日期 | 评价 | 改进建议 |\n|------|------|----------|\n| 202X-XX-XX | ⭐⭐⭐ | |\n'
  },
  {
    id: 'travel',
    title: '✈️ 旅行攻略与游记',
    desc: '完整的旅行规划与回忆记录',
    content: '# ✈️ 目的地 - 旅行时间\n\n---\n\n## 📋 旅行概览\n\n| 项目 | 内容 |\n|------|------|\n| **目的地** | |\n| **时间** | 202X-XX-XX ~ 202X-XX-XX |\n| **天数** | X天Y晚 |\n| **同行人** | |\n| **旅行类型** | 🏖️ 休闲 / 🎒 徒步 / 🏛️ 文化 / 🍜 美食 |\n| **总预算** | ￥XXX |\n\n---\n\n## 📅 行程安排\n\n### Day 1 - 日期\n\n**上午**：\n- 地点：\n- 交通：\n- 门票/费用：\n\n**下午**：\n- 地点：\n- 活动：\n\n**晚上**：\n- 晚餐：\n- 住宿：\n\n---\n\n### Day 2 - 日期\n\n**上午**：\n- 地点：\n- 交通：\n\n---\n\n## 🏨 住宿记录\n\n| 日期 | 酒店/民宿 | 位置 | 评分 | 备注 |\n|------|-----------|------|------|------|\n| | | | ⭐⭐⭐⭐⭐ | |\n\n---\n\n## 🍜 美食记录\n\n### 推荐餐厅\n\n| 店名 | 位置 | 推荐菜品 | 人均 | 评分 |\n|------|------|----------|------|------|\n| | | | | ⭐⭐⭐⭐⭐ |\n\n### 必吃美食\n\n- ✅ 美食1：\n- ✅ 美食2：\n\n---\n\n## 📸 精彩瞬间\n\n### 最佳照片\n\n---\n\n## 💡 旅行贴士\n\n### 行前准备\n\n- [ ] 证件：\n- [ ] 物品：\n\n### 当地注意\n\n- 交通：\n- 文化习俗：\n\n---\n\n## 💰 费用记录\n\n| 项目 | 金额 | 备注 |\n|------|------|------|\n| 交通 | | |\n| 住宿 | | |\n| 餐饮 | | |\n| 门票 | | |\n| 购物 | | |\n| **总计** | | |\n\n---\n\n## ✨ 旅行感悟\n\n### 最难忘的经历\n\n### 学到了什么\n\n### 下次计划\n\n- [ ] 还想再来：\n- [ ] 想尝试：\n'
  }
]

const customTemplates = ref(JSON.parse(localStorage.getItem('studyMateCustomTemplates') || '[]'))

const allTemplates = computed(() => [...defaultTemplates, ...customTemplates.value])

const openTemplateModal = (folder = '默认笔记本') => {
  targetFolderForNewNote.value = folder
  showTemplateModal.value = true
}

const createNoteFromTemplate = async (template) => {
  showTemplateModal.value = false
  
  // 如果是空白笔记，则打开原来的新建笔记窗口
  if (template.id === 'blank') {
    newNoteTitle.value = ''
    newNoteContent.value = ''
    newNoteFolder.value = targetFolderForNewNote.value
    showCreateModal.value = true
    return
  }
  
  // 其他模板继续按原逻辑创建
  showLoadingToast({ message: '创建中...', forbidClick: true })
  
  try {
    let newTitle = template.title.replace(/[\uD800-\uDBFF][\uDC00-\uDFFF]|\s/g, '').replace(/[📄📐🐛📝⭐]/g, '')
    
    console.log('📝 创建笔记，标题:', newTitle)
    console.log('📝 内容:', template.content)
    
    const res = await api.post('/notes/', {
      title: newTitle,
      content: template.content,
      course_id: 1,
      user_id: 1,
      folder: targetFolderForNewNote.value,
      tags: []
    })
    
    console.log('✅ 后端返回:', res)
    
    await loadNotes()
    
    if (notesList.value.length > 0) {
      console.log('📋 笔记列表:', notesList.value)
      const newNote = notesList.value[0]
      console.log('📖 选中笔记:', newNote)
      console.log('📖 structured_note:', newNote.structured_note)
      selectNote(newNote)
      // 编辑模式下需要设置 editingContent
      editingContent.value = newNote.structured_note || ''
      isEditingContent.value = true
      showToast('✨ 模板加载完毕，开始记录吧！')
    }
  } catch (e) {
    console.error(e)
    showFailToast('创建失败')
  }
}

const saveCurrentAsTemplate = async () => {
  if (!currentNote.value || !currentNote.value.structured_note) return
  
  try {
    const name = await showConfirmDialog({
      title: '保存为模板',
      message: '给你的专属笔记骨架起个名字吧：',
      showCancelButton: true,
      showConfirmButton: true,
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      showInput: true,
      inputPlaceholder: '输入模板名称',
    })
    
    if (!name) return
    
    const newTemplate = {
      id: `custom_${Date.now()}`,
      title: `⭐ ${name}`,
      desc: '自定义模板',
      content: currentNote.value.structured_note
    }
    
    customTemplates.value.push(newTemplate)
    localStorage.setItem('studyMateCustomTemplates', JSON.stringify(customTemplates.value))
    showToast('模板保存成功！')
  } catch {
    // 用户取消
  }
}

// ================= 实时公式编辑器引擎 =================
const showMathEditor = ref(false)
const mainEditorRef = ref(null)
const savedCursorPosition = ref(0)
const skipMathTrigger = ref(false) // 用于跳过触发

// ================= 双向链接选择器引擎 =================
const showLinkSelector = ref(false)
const linkSearchQuery = ref('')
const linkSelectorPos = ref({ x: 0, y: 0 })
const linkCursorStart = ref(0) // 记录 [[ 开始的位置
const linkSelectedIndex = ref(0)

// 过滤后的笔记标题列表
const filteredNoteTitles = computed(() => {
  const query = linkSearchQuery.value.trim().toLowerCase()
  if (!query) return notesList.value.map(n => getNoteTitle(n))
  return notesList.value
    .map(n => getNoteTitle(n))
    .filter(title => title.toLowerCase().includes(query))
})

// 处理双向链接输入
const handleLinkInput = (e) => {
  const val = editingContent.value
  const cursor = e.target.selectionStart

  // 检测是否刚输入了 [[
  if (val.substring(cursor - 2, cursor) === '[[') {
    // 使用镜像 div 方法精确计算光标位置
    updateLinkSelectorPosition(cursor)
    linkCursorStart.value = cursor
    linkSearchQuery.value = ''
    linkSelectedIndex.value = 0
    showLinkSelector.value = true
  }
}

// 计算光标在屏幕上的位置（用于 fixed 定位的浮层）
const updateLinkSelectorPosition = (cursorPos) => {
  const textarea = mainEditorRef.value
  if (!textarea) return

  // 创建或获取镜像 div
  let mirror = document.getElementById('link-selector-mirror')
  if (!mirror) {
    mirror = document.createElement('div')
    mirror.id = 'link-selector-mirror'
    document.body.appendChild(mirror)
  }

  // 复制 textarea 的所有相关样式
  const styles = window.getComputedStyle(textarea)
  const propList = [
    'boxSizing', 'width',
    'borderTopWidth', 'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth',
    'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft',
    'fontStyle', 'fontVariant', 'fontWeight', 'fontStretch', 'fontSize',
    'lineHeight', 'fontFamily', 'textAlign', 'textTransform', 'textIndent',
    'textDecoration', 'letterSpacing', 'wordSpacing', 'whiteSpace',
    'wordWrap', 'overflowWrap'
  ]

  // 设置镜像 div 样式
  mirror.style.position = 'absolute'
  mirror.style.top = '0'
  mirror.style.left = '-9999px'
  mirror.style.visibility = 'hidden'
  mirror.style.overflow = 'visible'
  mirror.style.height = 'auto'
  mirror.style.minHeight = 'auto'
  mirror.style.maxHeight = 'none'
  mirror.style.wordBreak = 'break-word'

  propList.forEach(prop => {
    mirror.style[prop] = styles[prop]
  })

  // 放入光标前的文本 + 一个标记 span
  const textBeforeCursor = editingContent.value.substring(0, cursorPos)
  mirror.innerHTML = ''
  mirror.appendChild(document.createTextNode(textBeforeCursor))

  const marker = document.createElement('span')
  marker.id = 'cursor-marker-span'
  marker.textContent = '\u200b'
  mirror.appendChild(marker)

  // 获取 textarea 的屏幕位置
  const textareaRect = textarea.getBoundingClientRect()

  // 获取标记的位置（相对于视口）
  const markerRect = marker.getBoundingClientRect()
  const mirrorRect = mirror.getBoundingClientRect()

  // 计算光标相对于 textarea 内容区的位置
  const markerOffsetY = markerRect.top - mirrorRect.top
  const markerOffsetX = markerRect.left - mirrorRect.left

  // 考虑 textarea 的滚动
  const scrollTop = textarea.scrollTop
  const scrollLeft = textarea.scrollLeft

  // 光标在 textarea 可视区域中的位置
  const relativeY = markerOffsetY - scrollTop + markerRect.height
  const relativeX = markerOffsetX - scrollLeft

  // 浮层估算宽度
  const selectorWidth = 320 // 浮层 min-width 是 280，max-width 是 360

  // 屏幕坐标计算
  let x = textareaRect.left + relativeX
  let y = textareaRect.top + relativeY

  // 边界检测：右边界
  const viewportWidth = window.innerWidth
  if (x + selectorWidth > viewportWidth - 10) {
    // 超出右边界，改成向左边显示
    // 让浮层右边对齐到光标左边
    x = x - selectorWidth - 10
    // 如果左边也不够，就贴着视口左边
    if (x < 10) {
      x = 10
    }
  }

  // 边界检测：下边界
  const selectorHeight = 280 // 浮层最大高度约 280
  const viewportHeight = window.innerHeight
  if (y + selectorHeight > viewportHeight - 10) {
    // 超出下边界，浮层显示在光标上方
    y = y - selectorHeight - parseFloat(styles.lineHeight || 28)
    // 如果上方也不够，就贴着视口上边
    if (y < 10) {
      y = 10
    }
  }

  linkSelectorPos.value = { x, y }
}

// 选择笔记标题插入
const selectLinkTitle = (title) => {
  if (!title) return
  const editor = mainEditorRef.value
  if (!editor) return

  const content = editingContent.value
  // linkCursorStart 是 [[ 之后的位置
  // 替换范围：从 [[ 之后到当前光标位置
  const start = linkCursorStart.value
  const currentCursor = editor.selectionStart

  // 构建新内容：
  // - 保留 [[ 之前的内容
  // - 添加 [[标题]]
  // - 保留原 [光标之后] 的内容
  const before = content.substring(0, start - 2) // 包含 [[ 之前的部分
  const after = content.substring(currentCursor)  // 光标之后的部分
  editingContent.value = before + '[[' + title + ']]' + after

  showLinkSelector.value = false
  linkSearchQuery.value = ''

  nextTick(() => {
    // 将光标移到 ]] 之后
    const newPos = start - 2 + 2 + title.length + 2 // before + [[ + title + ]]
    editor.selectionStart = newPos
    editor.selectionEnd = newPos
    editor.focus()
  })
}

// 关闭链接选择器
const closeLinkSelector = () => {
  showLinkSelector.value = false
  linkSearchQuery.value = ''
}

// 处理链接选择器的键盘事件
const handleLinkSelectorKeydown = (e) => {
  if (!showLinkSelector.value) return

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      linkSelectedIndex.value = (linkSelectedIndex.value + 1) % Math.max(filteredNoteTitles.value.length, 1)
      break
    case 'ArrowUp':
      e.preventDefault()
      linkSelectedIndex.value = (linkSelectedIndex.value - 1 + Math.max(filteredNoteTitles.value.length, 1)) % Math.max(filteredNoteTitles.value.length, 1)
      break
    case 'Enter':
      e.preventDefault()
      if (filteredNoteTitles.value.length > 0) {
        selectLinkTitle(filteredNoteTitles.value[linkSelectedIndex.value])
      } else if (linkSearchQuery.value.trim()) {
        // 如果没有匹配的，使用输入的内容作为新标题
        selectLinkTitle(linkSearchQuery.value.trim())
      }
      break
    case 'Escape':
      e.preventDefault()
      e.stopPropagation()
      closeLinkSelector()
      // 恢复焦点到编辑器
      nextTick(() => {
        mainEditorRef.value?.focus()
      })
      break
  }
}

// 点击外部关闭链接选择器（使用 mousedown 避免与 click 输入冲突）
const handleLinkSelectorOutsideClick = (e) => {
  if (!showLinkSelector.value) return
  // 检查点击目标是否在链接选择器内部
  if (e.target.closest('.link-selector')) return
  // 检查点击目标是否是编辑器（允许在编辑器中操作）
  if (e.target === mainEditorRef.value || e.target.closest('.editor-textarea-wrapper')) return
  // 其他情况关闭选择器
  closeLinkSelector()
}

// 监听输入更新搜索查询
const updateLinkSearch = (e) => {
  if (!showLinkSelector.value) return

  const cursor = e.target.selectionStart
  const content = editingContent.value

  // 提取 [[ 之后的输入内容
  if (cursor >= linkCursorStart.value) {
    linkSearchQuery.value = content.substring(linkCursorStart.value, cursor)
    linkSelectedIndex.value = 0
    // 同步更新浮层位置
    updateLinkSelectorPosition(cursor)
  }
}

// 编辑器滚动时更新浮层位置
const handleEditorScroll = () => {
  if (!showLinkSelector.value) return
  const editor = mainEditorRef.value
  if (!editor) return
  updateLinkSelectorPosition(editor.selectionStart)
}

// 使用 FormulaEditor 组件时的插入处理
const handleInsertFormula = (formula) => {
  // formula 已经是 `$$...$$` 格式
  const val = editingContent.value
  const pos = savedCursorPosition.value
  
  const mathBlock = `\n${formula}\n`
  
  editingContent.value = val.substring(0, pos) + mathBlock + val.substring(pos)
  showMathEditor.value = false
  
  nextTick(() => {
    mainEditorRef.value?.focus()
  })
}

const handleEditorInput = (e) => {
  const val = editingContent.value
  const cursor = e.target.selectionStart

  if (skipMathTrigger.value) {
    skipMathTrigger.value = false
    return
  }

  // 检测双向链接 [[ 触发（优先检测，即使在选择器打开时也可以触发新的 [[）
  if (val.substring(cursor - 2, cursor) === '[[') {
    // 如果已有选择器打开，先关闭它
    if (showLinkSelector.value) {
      closeLinkSelector()
    }
    handleLinkInput(e)
    return
  }

  // 如果链接选择器已打开，更新搜索查询
  if (showLinkSelector.value) {
    updateLinkSearch(e)
    return
  }

  if (val.substring(cursor - 2, cursor) === '$$') {
    editingContent.value = val.substring(0, cursor - 2) + val.substring(cursor)
    savedCursorPosition.value = cursor - 2
    showMathEditor.value = true
  }
}

const insertImageFromFile = async () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    const reader = new FileReader()
    reader.onload = (evt) => {
      const base64 = evt.target.result
      const markdown = `![图片](${base64})`
      insertTextAtCursor(markdown)
    }
    reader.readAsDataURL(file)
  }
  input.click()
}

const insertImageFromUrl = async () => {
  try {
    const url = await showConfirmDialog({
      title: '插入网络图片',
      message: '请输入图片网址：',
      showCancelButton: true,
      showConfirmButton: true,
      confirmButtonText: '插入',
      cancelButtonText: '取消',
      showInput: true,
      inputPlaceholder: 'https://example.com/image.png',
    })
    
    if (!url || !url.trim()) return
    
    const markdown = `![](${url.trim()})`
    insertTextAtCursor(markdown)
  } catch {
    // 用户取消
  }
}

const insertTextAtCursor = (text) => {
  const editor = mainEditorRef.value
  if (!editor) return
  
  const start = editor.selectionStart
  const end = editor.selectionEnd
  const content = editingContent.value
  editingContent.value = content.substring(0, start) + text + content.substring(end)
  
  nextTick(() => {
    const newPos = start + text.length
    editor.selectionStart = newPos
    editor.selectionEnd = newPos
    editor.focus()
  })
}

const focusMainEditor = () => {
  nextTick(() => {
    mainEditorRef.value?.focus()
  })
}

// ================= 沉浸式引擎状态 =================
const isFullscreenMode = ref(false) // 外壳：全屏模式 (原 focus mode)
const isTypewriterMode = ref(true)  // 核心 1：打字机模式 (默认开启)
const isTrueFocusMode = ref(false)  // 核心 2：真正的专注模式 (聚光灯)

// 1. 切换全屏模式
const toggleFullscreenMode = () => {
  isFullscreenMode.value = !isFullscreenMode.value
  if (isFullscreenMode.value) {
    isEditingContent.value = true
    nextTick(() => mainEditorRef.value?.focus())
  }
}

// 2. 切换打字机
const toggleTypewriter = () => {
  isTypewriterMode.value = !isTypewriterMode.value
  if (isTypewriterMode.value) handleTypewriterScroll() // 开启时立刻居中一次
}

// 3. 切换专注聚光灯
const toggleTrueFocus = () => {
  isTrueFocusMode.value = !isTrueFocusMode.value
  // 💡 极客联动：专注模式的聚光灯在屏幕正中央，所以必须强制绑定打字机模式！
  if (isTrueFocusMode.value) {
    isTypewriterMode.value = true
    handleTypewriterScroll()
  }
}

// ESC 键退出处理
const handleKeyDown = (e) => {
  if (e.key === 'Escape' && isFullscreenMode.value) {
    toggleFullscreenMode()
  }
}

// 生命周期钩子：添加和移除 ESC 监听
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

// ⌨️ 终极打字机算法：基于行数计算
const handleTypewriterScroll = () => {
  // 只有在全屏且开启了打字机模式时才生效
  if (!isFullscreenMode.value || !isTypewriterMode.value) return
  
  const textarea = mainEditorRef.value
  if (!textarea) return

  // 截取光标之前的文本，计算有多少个换行符 \n
  const textBeforeCursor = textarea.value.substring(0, textarea.selectionStart)
  const currentLine = textBeforeCursor.split('\n').length
  const totalLines = textarea.value.split('\n').length || 1
  
  // 用行数比例代替字符比例，精准度大幅提升
  const ratio = currentLine / totalLines
  const scrollHeight = textarea.scrollHeight
  const clientHeight = textarea.clientHeight
  
  const targetScroll = (scrollHeight * ratio) - (clientHeight / 2)
  
  // 加上 behavior: 'smooth'，让打字机的滚动充满呼吸感
  if (targetScroll > 0) {
    textarea.scrollTo({ top: targetScroll, behavior: 'smooth' })
  } else {
    textarea.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

// ====== 选择笔记 ======
const selectNote = (note) => {
  if (!note.title) note.title = ''
  currentNote.value = note
  editOriginal.value = note.original_text || ''
  editStructured.value = note.structured_note || ''
  
  // 切换笔记时强制退出编辑模式，防止误操作
  isEditingContent.value = false
}

// ====== 处理内部链接点击 ======
const handleLinkClick = (targetTitle) => {
  const targetNote = notesList.value.find(n => n.title === targetTitle)
  
  if (targetNote) {
    selectNote(targetNote)
  } else {
    showToast('知识荒原：该笔记尚未创建 🌵')
  }
}

// ====== 新建笔记 ======
const handleCreateNote = () => {
  newNoteTitle.value = ''
  newNoteContent.value = ''
  showCreateModal.value = true
}

// 读取本地文件
const handleFileUpload = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    newNoteContent.value = e.target.result
    if (!newNoteTitle.value) {
      newNoteTitle.value = file.file.name.replace(/\.[^/.]+$/, "")
    }
    showToast('文件解析成功！')
  }
  reader.readAsText(file.file)
}

// 保存新笔记
const saveNewNote = async (useAi) => {
  if (!newNoteTitle.value || !newNoteContent.value) {
    showToast('标题和内容都不能为空哦')
    return
  }
  
  isSaving.value = true
  try {
    // 获取用户选择的课程ID（如果没有选择则使用默认值1）
    const courseId = newNoteCourseId.value ? parseInt(newNoteCourseId.value) : 1
    
    let res
    if (useAi) {
      // 使用 AI 智能排版
      res = await api.post('/notes/upload-json', {
        text: newNoteContent.value,
        course_id: courseId,
        user_id: 1,
        tags: newNoteTags.value,
        folder: newNoteFolder.value || '默认笔记本'
      })
      
      // 保存标题
      if (res.id) {
        await api.put(`/notes/${res.id}`, {
          title: newNoteTitle.value
        })
      }
    } else {
      // 直接保存原文 - 使用新的直接创建接口
      res = await api.post('/notes/', {
        title: newNoteTitle.value,
        content: newNoteContent.value,
        course_id: courseId,
        user_id: 1,
        tags: newNoteTags.value,
        folder: newNoteFolder.value || '默认笔记本'
      })
    }
    
    showSuccessToast(useAi ? '✨ AI 排版完成！' : '保存成功')
    
    showCreateModal.value = false
    newNoteTitle.value = ''
    newNoteContent.value = ''
    newNoteFolder.value = '默认笔记本'
    newNoteTags.value = []
    await loadNotes()
    
    if (notesList.value.length > 0) {
      selectNote(notesList.value[0])
    }
  } catch (e) {
    console.error(e)
    showFailToast('网络拥堵，保存失败')
  } finally {
    isSaving.value = false
  }
}

// ====== 加载课程列表 ======
const loadCourses = async () => {
  try {
    const res = await api.get('/courses/')
    courseList.value = res.data || res || []
    console.log('[DEBUG] 课程列表:', courseList.value)
  } catch (e) {
    console.error('加载课程失败', e)
  }
}

// ====== 加载笔记列表 ======
const loadNotes = async () => {
  try {
    // 加载所有课程的笔记（不传 course_id 参数）
    const res = await api.get('/notes/list')
    notesList.value = res.data || res || []
    
    // 为笔记添加 course_name 字段（如果有 course_id）
    if (courseList.value && courseList.value.length > 0) {
      notesList.value = notesList.value.map(note => {
        if (note.course_id) {
          const course = courseList.value.find(c => c.id === note.course_id)
          if (course) {
            return { ...note, course_name: course.name }
          }
        }
        return note
      })
    }
    
    console.log('[DEBUG] 笔记列表:', notesList.value)
    if (notesList.value.length > 0 && !currentNote.value) {
      selectNote(notesList.value[0])
    }
  } catch (e) {
    console.error('加载笔记失败', e)
  }
}

// ====== 删除笔记 ======
const handleDeleteNote = (noteId) => {
  showConfirmDialog({
    title: '🗑️ 确认删除笔记？',
    message: '笔记删除后将无法恢复，相关的闪卡复习进度也会一并清除。是否确定？',
    confirmButtonColor: '#ee0a24',
    confirmButtonText: '确认删除',
    cancelButtonText: '留着吧'
  }).then(async () => {
    try {
      const res = await api.delete(`/notes/${noteId}`)
      showSuccessToast('笔记已安全删除')
      notesList.value = notesList.value.filter(n => n.id !== noteId)
      if (currentNote.value?.id === noteId) {
        currentNote.value = notesList.value[0] || null
      }
    } catch (e) {
      console.error("[前端 ERROR] 删除笔记失败:", e)
      showFailToast('网络拥堵，删除失败')
    }
  }).catch(() => {
    // 用户取消
  })
}

// ====== 重新生成笔记 ======
const handleRegenerateNote = (noteId) => {
  showConfirmDialog({
    title: '✨ 重新生成笔记？',
    message: 'AI 导师将重新梳理并生成一份全新的笔记。当前内容将被永久覆盖，是否继续？',
    confirmButtonText: '重新生成',
    confirmButtonColor: '#4F46E5',
    cancelButtonText: '再看看'
  }).then(async () => {
    isRegenerating.value = true
    try {
      const res = await api.post(`/notes/${noteId}/regenerate`)
      
      if (res.success) {
        if (currentNote.value) {
          currentNote.value.structured_note = res.data?.content || res.data?.structured_note
          currentNote.value.mindmap_json = res.data?.mindmap || res.data?.mindmap_json
        }
        
        showToast({ message: '✨ 笔记已焕然一新！', position: 'top' })
        loadNotes()
      } else {
        showFailToast(res.message || '生成失败，请稍后再试')
      }
    } catch (e) {
      console.error("[前端 ERROR] 重新生成失败:", e)
      showFailToast('网络连接超时，AI 导师可能太累了')
    } finally {
      isRegenerating.value = false
    }
  }).catch(() => {
    // 用户取消
  })
}

// ====== 保存编辑 ======
const saveEditNote = async () => {
  if (!currentNote.value) return
  editLoading.value = true
  try {
    await api.put(`/notes/${currentNote.value.id}`, {
      original_text: editOriginal.value,
      structured_note: editStructured.value
    })
    showSuccessToast('保存成功')
    currentNote.value.original_text = editOriginal.value
    currentNote.value.structured_note = editStructured.value
    showEditNote.value = false
    loadNotes()
  } catch (e) {
    showFailToast('保存失败')
  } finally {
    editLoading.value = false
  }
}

onMounted(async () => {
  await loadCourses() // 先加载课程
  await loadNotes()  // 再加载笔记

  // 注册全局键盘和点击事件（用于双向链接选择器）
  document.addEventListener('keydown', handleLinkSelectorKeydown)
  document.addEventListener('mousedown', handleLinkSelectorOutsideClick)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleLinkSelectorKeydown)
  document.removeEventListener('mousedown', handleLinkSelectorOutsideClick)
})
</script>

<style scoped>
/* 🪟 链接悬停预览卡片专属样式 */
.link-preview-card {
  position: fixed;
  z-index: 999999;
  width: 320px;
  background: var(--card-bg, rgba(255, 255, 255, 0.95));
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 10px 30px var(--shadow-color, rgba(0, 0, 0, 0.1));
  transform: translateX(-50%);
  transition: opacity 0.2s ease, transform 0.2s ease;
  pointer-events: auto;
}

.link-preview-card::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 12px;
  height: 12px;
  background: var(--card-bg, #ffffff);
  border-left: 1px solid var(--border-color, #e5e7eb);
  border-top: 1px solid var(--border-color, #e5e7eb);
}

.preview-title {
  margin: 0 0 8px 0;
  font-size: 15px;
  color: var(--text-primary, #1f2937);
  font-weight: 600;
  display: flex;
  align-items: center;
}

.preview-content {
  margin: 0 0 12px 0;
  font-size: 13px;
  color: var(--text-secondary, #6b7280);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.preview-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding-top: 8px;
  border-top: 1px dashed var(--border-color, #e5e7eb);
}

/* 🗂️ 模板网格布局 */
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  overflow-y: auto;
  padding-bottom: 20px;
}

.template-card {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px var(--shadow-color, rgba(0,0,0,0.02));
}

.template-card:hover {
  border-color: var(--accent-color, #4f46e5);
  box-shadow: 0 8px 16px var(--shadow-color, rgba(79, 70, 229, 0.08));
  transform: translateY(-2px);
}

.tpl-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #334155);
  margin-bottom: 6px;
}

.tpl-desc {
  font-size: 12px;
  color: var(--text-secondary, #64748b);
  line-height: 1.5;
}

/* ====== 🧠 Obsidian 工作区布局 ====== */
.obsidian-workspace {
  display: flex;
  height: 100%;
  background-color: var(--bg-tertiary, #f9fafb);
  overflow: hidden;
}

/* 👈 左侧导航 */
.sidebar {
  width: 300px;
  background-color: var(--bg-primary, #f5f5f5);
  border-right: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px 18px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.sidebar-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary, #1f2937);
  margin: 0;
  text-align: center;
  letter-spacing: 0.5px;
}

.graph-button {
  font-weight: 600;
  height: 40px !important;
  border-radius: 8px !important;
}

.quick-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.quick-actions .van-button {
  flex: 1;
  font-weight: 500;
  height: 38px !important;
  border-radius: 8px !important;
}

/* 📑 侧边栏选项卡样式 */
.sidebar-tabs {
  display: flex;
  padding: 16px 18px;
  gap: 10px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 10px 8px;
  font-size: 14px;
  color: var(--text-secondary, #6b7280);
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.tab-item.is-active {
  background-color: var(--bg-secondary, #ffffff);
  color: var(--accent-color, #4f46e5);
  box-shadow: 0 2px 4px var(--shadow-color, rgba(0,0,0,0.05));
  font-weight: 600;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
}

.tab-content.is-drag-over {
  background-color: var(--accent-light, rgba(79, 70, 229, 0.1));
  border: 2px dashed var(--accent-color, #4f46e5);
  border-radius: 8px;
}

/* 📍 大纲专属样式 */
.outline-pane {
  padding: 20px 16px;
}

.outline-item {
  padding: 4px 8px;
  font-size: 13px;
  color: var(--text-secondary, #4b5563);
  cursor: pointer;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-left: 2px solid transparent;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.outline-item:hover {
  background-color: var(--accent-light, #eef2ff);
  color: var(--accent-color, #4f46e5);
}

.outline-item.hidden {
  display: none;
}

.collapse-icon {
  width: 14px;
  height: 14px;
  font-size: 10px;
  line-height: 14px;
  text-align: center;
  color: var(--text-tertiary, #9ca3af);
  cursor: pointer;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.collapse-icon:hover {
  color: var(--accent-color, #4f46e5);
}

.collapse-icon.expanded {
  transform: rotate(90deg);
}

.collapse-icon-placeholder {
  width: 14px;
  height: 14px;
  font-size: 8px;
  line-height: 14px;
  text-align: center;
  color: #d1d5db;
  flex-shrink: 0;
}

.outline-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 根据标题层级缩进，形成树状结构 */
.level-1 { 
  font-weight: 700; 
  margin-top: 12px; 
  font-size: 16px; 
  padding-left: 8px; 
  color: var(--text-primary, #1f2937);
  background-color: var(--bg-primary, #f5f5f5);
  padding: 6px 8px;
  border-radius: 4px;
}
.level-2 { padding-left: 28px; opacity: 0.95; font-size: 14px; }
.level-3 { padding-left: 48px; opacity: 0.9; font-size: 13px; }
.level-4 { padding-left: 68px; opacity: 0.8; font-size: 12px; }
.level-5 { padding-left: 88px; opacity: 0.7; font-size: 12px; }
.level-6 { padding-left: 108px; opacity: 0.6; font-size: 11px; }

.outline-empty {
  text-align: center;
  color: var(--text-tertiary, #9ca3af);
  margin-top: 40px;
  font-size: 13px;
}

/* 搜索栏 */
.search-bar {
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.search-results-list {
  padding: 14px;
  overflow-y: auto;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #374151);
}

.add-btn {
  cursor: pointer;
  padding: 4px;
  transition: opacity 0.2s;
}
.add-btn:hover { opacity: 0.7; }

/* 侧边栏菜单项 */
.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  margin: 6px 10px;
  border-radius: 8px;
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
  font-weight: 500;
}

.nav-icon {
  margin-right: 8px;
  font-size: 16px;
}

.nav-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  background: #f3f4f6;
  border-radius: 10px;
  white-space: nowrap;
}

.nav-item.is-active .word-count {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.9);
}

/* 标签网络 */
.tags-section {
  padding: 24px 18px;
}

.section-title {
  font-size: 12px;
  color: var(--text-tertiary, #9ca3af);
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-item {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.tag-delete-icon {
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  transition: all 0.2s;
}

.tag-delete-icon:hover {
  color: #ef4444;
  background-color: var(--danger-light, #fef2f2);
}

/* 👉 右侧沉浸区 */
.main-content {
  flex: 1;
  background-color: var(--bg-secondary, #ffffff);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.immersive-reader {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.reader-header {
  padding: 30px 50px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reader-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #1f2937);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reader-actions {
  flex-shrink: 0;
  display: flex;
}

/* 状态栏 - 类似 Word 的底部状态栏 */
.status-bar {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 24px;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  font-size: 12px;
  color: var(--text-secondary, #64748b);
  flex-shrink: 0;
  height: 32px;
}

.status-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-right {
  display: flex;
  align-items: center;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s ease;
}

.status-item:hover {
  color: var(--accent-color, #4f46e5);
}

.status-separator {
  color: #cbd5e1;
  font-weight: 300;
}

/* 可点击的状态栏项目 */
.status-clickable {
  cursor: pointer;
  padding: 2px 6px;
  margin: -2px -6px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.status-clickable:hover {
  background: rgba(79, 70, 229, 0.1);
  color: var(--accent-color, #4f46e5);
}

/* 字数统计下拉菜单 */
.count-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 16px;
  background: #ffffff;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  padding: 6px;
  min-width: 240px;
  z-index: 100;
  animation: fadeInUp 0.2s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.count-menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s ease;
  color: var(--text-primary, #334155);
}

.count-menu-item:hover {
  background: #f1f5f9;
}

.count-menu-item.active {
  background: rgba(79, 70, 229, 0.1);
  color: var(--accent-color, #4f46e5);
  font-weight: 500;
}

.count-menu-item.active::before {
  content: '✓';
  color: var(--accent-color, #4f46e5);
  font-weight: bold;
  margin-right: 6px;
}

.menu-count {
  font-size: 12px;
  color: var(--text-tertiary, #94a3b8);
  font-weight: 400;
}

.count-menu-item.active .menu-count {
  color: #6366f1;
}

/* 编辑模式下的状态栏 */
.editor-wrapper + .status-bar {
  background: #f1f5f9;
  border-top-color: #cbd5e1;
}

/* 选中状态栏 */
.status-bar .status-item.is-active {
  color: var(--accent-color, #4f46e5);
  font-weight: 500;
}

.markdown-body {
  flex: 1;
  padding: 50px;
  overflow-y: auto;
  line-height: 1.9;
  font-size: 16px;
  color: var(--text-primary, #374151);
}

/* Markdown 样式 */
.markdown-body :deep(h1) { font-size: 22px; font-weight: 700; margin: 20px 0 14px 0; padding-bottom: 6px; border-bottom: 2px solid #e8e8ff; color: #2d3748; }
.markdown-body :deep(h2) { font-size: 19px; font-weight: 600; margin: 18px 0 12px 0; padding-left: 10px; border-left: 3px solid #4F46E5; color: #1a202c; }
.markdown-body :deep(h3), .markdown-body :deep(h4), .markdown-body :deep(h5), .markdown-body :deep(h6) { font-size: 16px; font-weight: 600; margin: 14px 0 10px 0; color: #2d3748; }
.markdown-body :deep(p) { margin: 10px 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 28px; margin: 10px 0; }
.markdown-body :deep(li) { margin: 6px 0; }
.markdown-body :deep(strong) { font-weight: 700; color: #1a202c; }
.markdown-body :deep(.katex-display) { margin: 16px 0 !important; overflow-x: auto; }

/* 🔗 双向链接专属外观 */
.markdown-body :deep(.internal-link) {
  color: var(--accent-color, #4f46e5);
  background-color: var(--accent-light, #eef2ff);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 0 2px;
}

.markdown-body :deep(.internal-link)::before {
  content: '🔗';
  font-size: 12px;
  margin-right: 4px;
}

.markdown-body :deep(.internal-link):hover {
  background-color: var(--accent-color, #4f46e5);
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(79, 70, 229, 0.3);
}

/* 极客纯文本编辑器样式 */
.editor-container {
  flex: 1;
  display: flex;
  position: relative;
}

.zen-mode-container {
  position: static;
}

/* 🧱 编辑器基础包装器 */
.editor-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 🧱 全屏不透明底座 (彻底阻断透视) */
.fullscreen-wrapper {
  position: fixed !important;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 99999;
  background-color: var(--bg-tertiary, #f9fafb); /* 背景颜色交由包装盒负责 */
  display: flex;
  flex-direction: column;
}

/* 🎛️ 悬浮控制台 */
.fullscreen-toolbar {
  position: absolute; /* 改为相对于包装盒定位 */
  top: 24px;
  right: 32px;
  z-index: 999999;
  display: flex;
  gap: 12px;
  background: rgba(255, 255, 255, 0.9);
  padding: 8px;
  border-radius: 40px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}

/* 🖥️ 全屏时的输入框本体 */
.fullscreen-wrapper .raw-editor {
  flex: 1;
  width: 100vw !important;
  height: 100vh !important;
  max-width: 100% !important;
  /* 上下留出巨大的打字机滚动空间 */
  padding: 40vh 20vw 40vh 20vw !important; 
  /* 核心修复：输入框本身必须透明，防止被 mask 导致背景也变透明 */
  background-color: transparent !important; 
  border: none !important;
  font-size: 18px; line-height: 2.2;
}

/* 🎯 专注模式魔法：聚光灯遮罩 (现在只会遮罩文字) */
.raw-editor.focus-mask-active {
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

/* 在全屏模式下隐藏滚动条 */
.fullscreen-wrapper .raw-editor::-webkit-scrollbar {
  display: none;
}

.raw-editor {
  flex: 1;
  width: 100%;
  padding: 50px;
  font-family: 'Fira Code', Consolas, Monaco, monospace; /* 程序员等宽字体优先 */
  font-size: 15px;
  line-height: 1.9;
  color: var(--text-primary, #374151);
  background-color: var(--bg-tertiary, #f9fafb); /* 淡淡的灰色背景，区别于阅读模式 */
  border: none;
  outline: none;
  resize: none;
}

.raw-editor::placeholder {
  color: var(--text-tertiary, #9ca3af);
}

/* 编辑器文字层（包裹 textarea） */
.editor-textarea-wrapper {
  position: relative;
  flex: 1;
  display: flex;
  overflow: visible;
}

/* 双向链接选择器浮层 */
.link-selector {
  position: absolute;
  z-index: 99999;
  background: #ffffff;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  min-width: 280px;
  max-width: 360px;
  overflow: hidden;
  animation: fadeInUp 0.15s ease;
}

.link-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(135deg, var(--bg-tertiary, #f8fafc) 0%, var(--bg-primary, #f1f5f9) 100%);
  border-bottom: 1px solid #e2e8f0;
}

.link-selector-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #334155);
}

.link-selector-hint {
  font-size: 11px;
  color: var(--text-tertiary, #94a3b8);
}

.link-selector-list {
  max-height: 240px;
  overflow-y: auto;
  padding: 4px;
}

.link-selector-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary, #475569);
  transition: all 0.12s ease;
  margin: 2px 0;
}

.link-selector-item:hover,
.link-selector-item.active {
  background: var(--accent-light, rgba(79, 70, 229, 0.08));
  color: var(--accent-color, #4f46e5);
}

.link-selector-item.active {
  font-weight: 500;
}

.link-selector-item.create-new {
  color: #059669;
  background: rgba(5, 150, 105, 0.05);
}

.link-selector-item.create-new:hover,
.link-selector-item.create-new.active {
  background: rgba(5, 150, 105, 0.1);
  color: #047857;
}

.create-icon {
  font-size: 14px;
}

.link-selector-empty {
  padding: 20px 16px;
  text-align: center;
  font-size: 13px;
  color: var(--text-tertiary, #94a3b8);
}

/* 编辑器内图片占位符的高亮（虽然 textarea 不能直接设置子元素样式，但占位符文本会通过等宽字体显示） */
.raw-editor {
  font-variant-ligatures: none;
}

.editor-toolbar {
  display: flex;
  gap: 8px;
  padding: 12px 50px;
  background-color: var(--bg-primary, #f5f5f5);
  border-top: 1px solid var(--border-color, #e5e7eb);
}

/* 笔记标签区域样式 */
.note-tags-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px dashed var(--border-color, #e5e7eb);
}

.tags-label {
  font-size: 13px;
  color: var(--text-secondary, #6b7280);
  margin-bottom: 12px;
  font-weight: 500;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
}

.tags-row :deep(.van-tag) {
  cursor: pointer;
  transition: all 0.2s;
}

.tags-row :deep(.van-tag:hover) {
  opacity: 0.8;
  transform: translateY(-1px);
}

/* 隐藏部分滚动条，保持视觉洁癖 */
.custom-scroll::-webkit-scrollbar { width: 6px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 覆盖 Vant 组件的默认背景 */
:deep(.van-collapse-item__content) {
  padding: 4px 0;
  background-color: transparent;
}

/* 加载遮罩 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: rgba(255, 255, 255, 0.95);
}

/* 编辑弹窗 */
.edit-container {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.edit-title {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
}

.edit-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

/* 🖱️ 右键悬浮菜单样式 */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: var(--card-bg, #ffffff);
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  padding: 8px 0;
  min-width: 180px;
  border: 1px solid var(--border-color, #e5e7eb);
}
.menu-item {
  padding: 10px 16px;
  font-size: 13px;
  color: var(--text-primary, #374151);
  cursor: pointer;
  transition: background 0.2s;
}
.menu-item:hover { background-color: var(--bg-primary, #f5f5f5); color: var(--accent-color, #4f46e5); }
.menu-item.danger:hover { background-color: var(--danger-light, #fef2f2); color: #ef4444; }
.menu-divider { border-top: 1px solid var(--border-color, #e5e7eb); margin: 4px 0; }

/* 鍒掕瘝鎮诞鑿滃崟 */
.selection-toolbar {
  position: fixed;
  z-index: 999999;
  transform: translate(-50%, -120%);
  background: var(--card-bg, #ffffff);
  padding: 4px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  border: 1px solid var(--border-color, #e5e7eb);
}

/* 馃幆 闈炲父閲嶈锛氱殗鍗曠墖闈欐劅 */
.review-modal {
  padding: 0 !important;
}

.review-container {
  padding: 30px 20px;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.review-card {
  width: 100%;
  max-width: 360px;
  height: 260px;
  position: relative;
  perspective: 1000px;
  cursor: pointer;
  margin-bottom: 30px;
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 30px rgba(79, 70, 229, 0.15);
}

.card-front {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.card-back {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  transform: rotateY(180deg);
}

.card-click-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  cursor: pointer;
  z-index: 10;
}

.review-card.is-flipped .card-front {
  transform: rotateY(-180deg);
}

.review-card.is-flipped .card-back {
  transform: rotateY(0deg);
}

.card-content {
  padding: 30px;
  text-align: center;
  color: white;
}

.question-text {
  font-size: 18px;
  font-weight: 500;
  line-height: 1.6;
  margin-bottom: 16px;
}

.answer-text {
  font-size: 16px;
  font-weight: 400;
  line-height: 1.7;
  margin-bottom: 16px;
}

.review-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.review-actions :deep(.van-button) {
  flex: 1;
  min-width: 80px;
}

.review-progress {
  width: 100%;
  max-width: 300px;
}

/* 馃幆 闈炲父閲嶈锛氱殗鍗曠墖鍒楄〃鏍峰紡 */
.flashcard-list-item {
  background: var(--card-bg, #ffffff);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: all 0.2s ease;
  border: 1px solid #f3f4f6;
}

.flashcard-list-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.flashcard-front {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary, #374151);
  line-height: 1.5;
  margin-bottom: 8px;
}

.flashcard-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flashcard-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.flashcard-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #374151);
}

.flashcard-list-item:hover .flashcard-delete,
.flashcard-list-item:hover .flashcard-view {
  opacity: 1;
}

.flashcard-delete:hover,
.flashcard-view:hover {
  transform: scale(1.1);
}

</style>

<style>
/* 全局样式：双向链接选择器浮层（Teleport 到 body，需要全局样式） */
.link-selector-global {
  position: fixed;
  z-index: 999999;
  background: #ffffff;
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  min-width: 280px;
  max-width: 360px;
  overflow: hidden;
  animation: fadeInUp 0.15s ease;
}

.link-selector-global .link-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: linear-gradient(135deg, var(--bg-tertiary, #f8fafc) 0%, var(--bg-primary, #f1f5f9) 100%);
  border-bottom: 1px solid #e2e8f0;
}

.link-selector-global .link-selector-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary, #334155);
}

.link-selector-global .link-selector-hint {
  font-size: 11px;
  color: var(--text-tertiary, #94a3b8);
}

.link-selector-global .link-selector-list {
  max-height: 240px;
  overflow-y: auto;
  padding: 4px;
}

.link-selector-global .link-selector-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary, #475569);
  transition: all 0.12s ease;
  margin: 2px 0;
}

.link-selector-global .link-selector-item:hover,
.link-selector-global .link-selector-item.active {
  background: var(--accent-light, rgba(79, 70, 229, 0.08));
  color: var(--accent-color, #4f46e5);
}

.link-selector-global .link-selector-item.active {
  font-weight: 500;
}

.link-selector-global .link-selector-item.create-new {
  color: #059669;
  background: rgba(5, 150, 105, 0.05);
}

.link-selector-global .link-selector-item.create-new:hover,
.link-selector-global .link-selector-item.create-new.active {
  background: rgba(5, 150, 105, 0.1);
  color: #047857;
}

.link-selector-global .create-icon {
  font-size: 14px;
}

.link-selector-global .link-selector-empty {
  padding: 20px 16px;
  text-align: center;
  font-size: 13px;
  color: var(--text-tertiary, #94a3b8);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>