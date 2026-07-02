export const changelogData = [
  {
    version: 'v1.1.0',
    date: '2026-06-23',
    title: '主题系统 & 代码美化',
    type: 'major',
    changes: [
      { type: 'feature', icon: '🌙', title: '新增白天/黑夜模式切换', desc: '支持一键切换白天和黑夜主题，自动保存用户偏好' },
      { type: 'feature', icon: '⚙️', title: '新增设置面板', desc: '右上角设置按钮，可打开系统设置抽屉' },
      { type: 'feature', icon: '💻', title: '代码块美化', desc: '代码块采用 DeepSeek 风格，带语言标识和一键复制功能' },
      { type: 'feature', icon: '📝', title: '行内代码高亮', desc: '正文中的行内代码增加红色背景高亮' },
      { type: 'feature', icon: '📋', title: '更新日志功能', desc: '新增更新日志页面，记录每次版本更新内容' }
    ]
  },
  {
    version: 'v1.0.3',
    date: '2026-06-22',
    title: '编辑器优化',
    type: 'minor',
    changes: [
      { type: 'feature', icon: '🖼️', title: '长图片自动折叠', desc: '编辑模式下 base64 长图片自动折叠为占位符，减少滚动' },
      { type: 'fix', icon: '🐛', title: '修复保存失败问题', desc: '修复课程 ID 为空导致的 422 错误' },
      { type: 'fix', icon: '🐛', title: '修复同步失败提示', desc: '本地同步增加详细错误分类提示' }
    ]
  },
  {
    version: 'v1.0.2',
    date: '2026-06-21',
    title: '阅读体验优化',
    type: 'minor',
    changes: [
      { type: 'feature', icon: '🖼️', title: '图片卡片化显示', desc: '长 base64 图片以卡片形式展示，显示格式和大小信息' },
      { type: 'feature', icon: '🔗', title: '双向链接支持', desc: '支持 [[笔记标题]] 形式的内部链接' },
      { type: 'feature', icon: '📐', title: 'LaTeX 公式渲染', desc: '支持行内和块级 LaTeX 数学公式渲染' }
    ]
  },
  {
    version: 'v1.0.1',
    date: '2026-06-20',
    title: '功能完善',
    type: 'patch',
    changes: [
      { type: 'feature', icon: '🏷️', title: '标签系统', desc: '笔记支持多标签分类管理' },
      { type: 'feature', icon: '📂', title: '文件夹管理', desc: '支持文件夹树形结构组织笔记' },
      { type: 'feature', icon: '💾', title: '本地同步', desc: '支持将笔记同步到本地文件夹' }
    ]
  },
  {
    version: 'v1.0.0',
    date: '2026-06-18',
    title: '初始版本发布',
    type: 'major',
    changes: [
      { type: 'feature', icon: '📝', title: '笔记管理', desc: '支持 Markdown 编辑、预览、全文搜索' },
      { type: 'feature', icon: '🃏', title: '闪卡复习', desc: '基于 SM-2 算法的记忆卡片系统' },
      { type: 'feature', icon: '📊', title: '备考计划', desc: 'AI 生成个性化学习计划' },
      { type: 'feature', icon: '📄', title: '论文助手', desc: '学术论文润色与分析' },
      { type: 'feature', icon: '📚', title: '课程管理', desc: '多课程笔记分类管理' },
      { type: 'feature', icon: '📖', title: '文献管理', desc: '文献导入、PDF 阅读、笔记关联' }
    ]
  }
]

export default changelogData
