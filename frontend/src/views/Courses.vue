<template>
  <div class="courses-view custom-scroll">
    <header class="page-header">
      <div class="header-left">
        <h2 class="page-title">📚 我的课程</h2>
        <span class="course-count">共 {{ courseList.length }} 门课程</span>
      </div>
      <button class="add-btn" @click="openAddForm">
        <span class="add-icon">+</span> 新建课程
      </button>
    </header>

    <div v-if="courseList.length === 0" class="empty-state">
      <div class="empty-icon">📖</div>
      <p class="empty-text">还没有添加课程</p>
      <p class="empty-hint">点击右上角「新建课程」开始吧</p>
    </div>

    <div v-else class="course-grid">
      <div 
        v-for="(course, index) in courseList" 
        :key="course.id" 
        class="course-card"
        @click="openNotesPopup(course)"
      >
        <div class="card-cover" :class="`theme-${themes[index % themes.length]}`">
          <div class="course-icon">{{ themeIcons[index % themeIcons.length] }}</div>
          
          <div class="more-options" @click.stop="toggleMenu(course.id)">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 13a1 1 0 100-2 1 1 0 000 2zM12 6a1 1 0 100-2 1 1 0 000 2zM12 20a1 1 0 100-2 1 1 0 000 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            
            <div class="dropdown-menu" v-show="activeMenuId === course.id">
              <div class="dropdown-item" @click.stop="editCourse(course)">
                <span style="margin-right: 8px;">✏️</span> 编辑信息
              </div>
              <div class="dropdown-divider"></div>
              <div class="dropdown-item text-danger" @click.stop="deleteCourse(course.id)">
                <span style="margin-right: 8px;">🗑️</span> 删除课程
              </div>
            </div>
          </div>
        </div>

        <div class="card-body">
          <h3 class="course-name">{{ course.name }}</h3>
          <p class="course-desc">
            {{ formatKnowledgePoints(course.knowledge_points) || '暂无知识点' }}
          </p>

          <div class="assets-tags">
            <span class="tag" @click.stop="openNotesPopup(course)">
              📄 {{ getCourseNotesCount(course.id) }} 笔记
            </span>
          </div>

          <div class="progress-section">
            <div class="progress-header">
              <span class="progress-text">备考活力值</span>
              <span class="progress-percent" :class="`text-${themes[index % themes.length]}`">
                {{ getCourseProgress(course.id) }}%
              </span>
            </div>
            <div class="progress-bar-bg">
              <div 
                class="progress-bar-fill" 
                :class="`bg-${themes[index % themes.length]}`"
                :style="{ width: `${getCourseProgress(course.id)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <van-popup v-model:show="showAdd" position="bottom" round :style="{ height: '55%' }">
      <div class="form-container">
        <h3 class="form-title">{{ editingCourse ? '编辑课程' : '添加课程' }}</h3>
        <van-field v-model="form.name" label="课程名称" placeholder="如：高等数学" />
        <van-field v-model="form.knowledge_points" label="知识点" placeholder="用逗号分隔，如：导数,积分" type="textarea" rows="4" />
        <van-button 
          block 
          round 
          type="default" 
          style="margin-bottom: 12px;"
          @click="generateKnowledgePoints"
          :loading="isGenerating"
        >
          🤖 AI生成知识点
        </van-button>
        <div class="form-buttons">
          <van-button block round @click="closeAddForm">取消</van-button>
          <van-button block round type="primary" @click="saveCourse">保存</van-button>
        </div>
      </div>
    </van-popup>

    <van-popup v-model:show="showNotesPopup" position="bottom" round :style="{ height: '70%' }">
      <div style="padding: 20px">
        <h3>{{ selectedCourse?.name }} - 笔记管理</h3>
        <van-empty v-if="courseNotes.length === 0" description="该课程暂无笔记" />
        <van-swipe-cell v-for="note in courseNotes" :key="note.id">
          <van-cell :title="getPreview(note.structured_note || note.original_text)"
                    :label="'创建：'+ note.created_at.slice(0,10)"
                    is-link
                    @click="viewNoteDetail(note)" />
          <template #right>
            <van-button square type="danger" text="删除" @click="deleteCourseNote(note.id)" />
          </template>
        </van-swipe-cell>
      </div>
    </van-popup>

    <van-popup v-model:show="showNoteDetail" position="bottom" round :style="{ height: '70%' }">
      <div class="detail-container">
        <h3 class="detail-title">笔记详情</h3>
        <van-tabs v-if="currentNote">
          <van-tab title="结构化笔记">
            <MarkdownViewer :content="currentNote.structured_note || ''" />
          </van-tab>
          <van-tab title="原始文本">
            <div class="original-text">{{ currentNote.original_text || '暂无内容' }}</div>
          </van-tab>
        </van-tabs>
        <div class="detail-buttons">
          <van-button block round @click="showNoteDetail = false">关闭</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { showToast, showConfirmDialog, showSuccessToast, showFailToast } from 'vant'
import api from '../api'
import { getAIConfig, getProvider } from '../utils/aiConfig'
import MarkdownViewer from '../components/MarkdownViewer.vue'

const courseList = ref([])
const showAdd = ref(false)
const editingCourse = ref(null)
const form = reactive({ name: '', knowledge_points: '' })

const showNotesPopup = ref(false)
const selectedCourse = ref(null)
const courseNotes = ref([])

const showNoteDetail = ref(false)
const currentNote = ref(null)

const activeMenuId = ref(null)
const notesCountMap = ref({})
const courseProgressMap = ref({})
const isGenerating = ref(false)

const themes = ['blue', 'orange', 'purple', 'emerald']
const themeIcons = ['📐', '📚', '🧬', '💻', '🎯', '🔬', '🌍', '📊']

const toggleMenu = (id) => {
  activeMenuId.value = activeMenuId.value === id ? null : id
}

const closeMenu = () => {
  activeMenuId.value = null
}

onMounted(() => {
  document.addEventListener('click', closeMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeMenu)
})

const formatKnowledgePoints = (kpStr) => {
  try {
    const arr = JSON.parse(kpStr || '[]')
    return arr.length > 0 ? arr.slice(0, 3).join('、') + (arr.length > 3 ? '...' : '') : ''
  } catch {
    return kpStr || ''
  }
}

const getPreview = (text) => {
  if (!text) return '无标题笔记'
  const clean = text.replace(/\n/g, ' ').replace(/[#*]/g, '')
  return clean.slice(0, 40) + (clean.length > 40 ? '...' : '')
}

const fetchCourses = async () => {
  try {
    const res = await api.get('/courses/')
    courseList.value = res.data || res
    
    for (const course of courseList.value) {
      await fetchCourseStats(course.id)
    }
  } catch (e) {
    console.error('加载课程失败', e)
  }
}

const fetchCourseStats = async (courseId) => {
  try {
    // 获取所有笔记，然后过滤出属于当前课程的笔记
    const res = await api.get('/notes/list')
    const allNotes = res.data || res || []
    // 只统计有归属课程且course_id匹配的笔记
    const courseNotes = allNotes.filter(note => note.course_id === courseId)
    notesCountMap.value[courseId] = courseNotes.length
    
    // 使用字符串类型的 courseId 确保 localStorage 键名一致
    const courseIdStr = String(courseId)
    // 检查是否有备考计划
    const planKey = `study_plan_${courseIdStr}`
    const planData = localStorage.getItem(planKey)
    
    console.log(`[DEBUG Courses] courseId=${courseId}, courseIdStr=${courseIdStr}, planKey=${planKey}, hasPlan=${!!planData}`)
    
    if (!planData) {
      // 没有计划，活力值为0
      courseProgressMap.value[courseId] = 0
      return
    }
    
    // 有计划，计算备考活力值（和Plans.vue相同的逻辑）
    const savedPlan = JSON.parse(planData)
    const detailsKey = `study_plan_details_${courseIdStr}`
    const cachedDetails = JSON.parse(localStorage.getItem(detailsKey) || '{}')
    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
    
    let total = 0
    let completed = 0
    
    if (savedPlan.daily_plan) {
      Object.keys(savedPlan.daily_plan).forEach(dateStr => {
        if (dateStr <= todayStr) {
          const dayCache = cachedDetails[dateStr]
          if (dayCache && dayCache.tasks && dayCache.tasks.length > 0) {
            total += dayCache.tasks.length
            completed += dayCache.tasks.filter(t => t.done).length
          } else {
            total += 1
          }
        }
      })
    }
    
    courseProgressMap.value[courseId] = total === 0 ? 0 : Math.round((completed / total) * 100)
  } catch (e) {
    notesCountMap.value[courseId] = 0
    courseProgressMap.value[courseId] = 0
  }
}

const getCourseNotesCount = (courseId) => {
  return notesCountMap.value[courseId] || 0
}

const getCourseProgress = (courseId) => {
  return courseProgressMap.value[courseId] || 0
}

const openAddForm = () => {
  editingCourse.value = null
  form.name = ''
  form.knowledge_points = ''
  showAdd.value = true
}

const editCourse = (course) => {
  activeMenuId.value = null
  editingCourse.value = course
  form.name = course.name
  try {
    const arr = JSON.parse(course.knowledge_points || '[]')
    form.knowledge_points = arr.join(', ')
  } catch {
    form.knowledge_points = course.knowledge_points || ''
  }
  showAdd.value = true
}

const closeAddForm = () => {
  showAdd.value = false
  editingCourse.value = null
}

const generateKnowledgePoints = async () => {
  if (!form.name) {
    showToast('请先输入课程名称')
    return
  }
  
  isGenerating.value = true
  try {
    const prompt = `请为课程"${form.name}"生成10-15个核心知识点，用中文逗号分隔，不需要序号和其他内容。示例：导数,积分,极限,微分方程`

    // 读取用户配置的 AI 模型
    const aiConfig = getAIConfig()
    if (!aiConfig.apiKey) {
      showFailToast('请先在设置中配置 AI 模型')
      return
    }

    const res = await api.post('/ai/chat', {
      messages: [
        {
          role: 'user',
          content: prompt
        }
      ],
      model: aiConfig.model,
      api_key: aiConfig.apiKey,
      base_url: aiConfig.provider === 'custom' ? aiConfig.baseUrl : getProvider(aiConfig.provider).baseUrl
    })
    
    if (res && res.content) {
      const points = res.content.trim()
      form.knowledge_points = points
      showToast('知识点生成成功！')
    } else {
      showFailToast('生成失败，请重试')
    }
  } catch (e) {
    console.error('生成知识点失败', e)
    showFailToast('生成失败，请重试')
  } finally {
    isGenerating.value = false
  }
}

const saveCourse = async () => {
  if (!form.name) {
    showToast('请输入课程名称')
    return
  }
  try {
    const pointsArray = form.knowledge_points.split(',').map(s => s.trim()).filter(Boolean)
    const payload = { name: form.name, knowledge_points: JSON.stringify(pointsArray) }
    if (editingCourse.value) {
      await api.put(`/courses/${editingCourse.value.id}`, payload)
      showSuccessToast('修改成功')
    } else {
      await api.post('/courses/', payload)
      showSuccessToast('添加成功')
    }
    closeAddForm()
    fetchCourses()
  } catch (e) {
    showFailToast('保存失败')
    console.error(e)
  }
}

const openNotesPopup = async (course) => {
  selectedCourse.value = course
  try {
    // 获取所有笔记，然后过滤出属于当前课程的笔记
    const res = await api.get('/notes/list')
    const allNotes = res.data || res || []
    // 只显示有归属课程且course_id匹配的笔记
    courseNotes.value = allNotes.filter(note => note.course_id === course.id)
  } catch (e) {
    showToast('加载笔记失败')
    return
  }
  showNotesPopup.value = true
}

const deleteCourseNote = async (noteId) => {
  try {
    await api.delete(`/notes/${noteId}`)
    showToast('已删除')
    if (selectedCourse.value) {
      openNotesPopup(selectedCourse.value)
      await fetchCourseStats(selectedCourse.value.id)
    }
  } catch (e) {
    showToast('删除失败')
  }
}

const viewNoteDetail = (note) => {
  currentNote.value = note
  showNoteDetail.value = true
}

const deleteCourse = (id) => {
  activeMenuId.value = null
  showConfirmDialog({
    title: '确认删除',
    message: '删除后该课程下的所有笔记和闪卡也将被移除，确定吗？',
    confirmButtonColor: '#ef4444'
  })
    .then(async () => {
      try {
        await api.delete(`/courses/${id}`)
        showToast('已删除')
        fetchCourses()
      } catch (e) {
        showToast('删除失败')
      }
    })
    .catch(() => {})
}

onMounted(fetchCourses)
</script>

<style scoped>
.courses-view {
  padding: 32px 40px;
  background-color: #f8fafc;
  min-height: calc(100vh - 60px);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.course-count {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
}

.add-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
}

.add-icon {
  font-size: 18px;
  font-weight: 400;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-text {
  font-size: 20px;
  font-weight: 600;
  color: #64748b;
  margin: 0 0 12px 0;
}

.empty-hint {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.course-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
  border: 1px solid #f1f5f9;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
}

.course-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
  border-color: #e2e8f0;
}

.card-cover {
  height: 100px;
  position: relative;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.theme-blue { background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%); }
.theme-orange { background: linear-gradient(135deg, #fb923c 0%, #f97316 100%); }
.theme-purple { background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%); }
.theme-emerald { background: linear-gradient(135deg, #34d399 0%, #10b981 100%); }

.text-blue { color: #3b82f6; }
.text-orange { color: #f97316; }
.text-purple { color: #8b5cf6; }
.text-emerald { color: #10b981; }

.bg-blue { background-color: #3b82f6; }
.bg-orange { background-color: #f97316; }
.bg-purple { background-color: #8b5cf6; }
.bg-emerald { background-color: #10b981; }

.course-icon {
  font-size: 42px;
  filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
  transform: translateY(10px);
}

.more-options {
  position: absolute;
  top: 12px;
  right: 12px;
  color: white;
  opacity: 0.7;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s;
}

.more-options:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.2);
}

.dropdown-menu {
  position: absolute;
  top: 32px;
  right: 0;
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  border: 1px solid #e2e8f0;
  width: 140px;
  z-index: 100;
  overflow: hidden;
  animation: scale-in 0.15s ease-out;
  transform-origin: top right;
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}

.dropdown-item {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 500;
  color: #334155;
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
}

.dropdown-item:hover {
  background: #f8fafc;
}

.dropdown-item.text-danger {
  color: #ef4444;
}

.dropdown-item.text-danger:hover {
  background: #fef2f2;
}

.dropdown-divider {
  height: 1px;
  background: #f1f5f9;
}

.card-body {
  padding: 24px 20px 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.course-name {
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.course-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 16px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.assets-tags {
  display: flex;
  gap: 8px;
  margin-bottom: auto;
  padding-bottom: 20px;
}

.tag {
  background: #f1f5f9;
  color: #475569;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.tag:hover {
  background: #e0e7ff;
  color: #4F46E5;
}

.progress-section {
  width: 100%;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-text {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.progress-percent {
  font-size: 13px;
  font-weight: 700;
}

.progress-bar-bg {
  height: 6px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.form-container,
.notes-container,
.detail-container {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.form-title,
.notes-title,
.detail-title {
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
}

.form-buttons,
.detail-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.original-text {
  background: #f3f4f6;
  padding: 16px;
  border-radius: 12px;
  white-space: pre-wrap;
  line-height: 1.8;
  color: #666;
}

.custom-scroll::-webkit-scrollbar { width: 8px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
</style>
