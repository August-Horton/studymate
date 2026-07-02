<template>
  <van-popup
    :show="show"
    position="right"
    :style="{ width: '320px', height: '100%' }"
    @update:show="$emit('update:show', $event)"
  >
    <div class="settings-container">
      <div class="settings-header">
        <h3 class="settings-title">设置</h3>
        <van-icon name="cross" size="20" class="close-btn" @click="closeSettings" />
      </div>

      <div class="settings-content">
        <div class="settings-section">
          <div class="section-title">外观设置</div>

          <div class="theme-options">
            <div
              class="theme-option"
              :class="{ active: currentTheme === 'light' }"
              @click="switchTheme('light')"
            >
              <div class="theme-preview light-preview">
                <van-icon name="sun-o" size="32" color="#f59e0b" />
              </div>
              <div class="theme-label">
                <span class="theme-name">白天模式</span>
                <span class="theme-desc">浅色背景，适合白天使用</span>
              </div>
              <van-icon v-if="currentTheme === 'light'" name="success" class="check-icon" />
            </div>

            <div
              class="theme-option"
              :class="{ active: currentTheme === 'dark' }"
              @click="switchTheme('dark')"
            >
              <div class="theme-preview dark-preview">
                <van-icon name="moon-o" size="32" color="#818cf8" />
              </div>
              <div class="theme-label">
                <span class="theme-name">黑夜模式</span>
                <span class="theme-desc">深色背景，适合夜间使用</span>
              </div>
              <van-icon v-if="currentTheme === 'dark'" name="success" class="check-icon" />
            </div>
          </div>
        </div>

        <div class="settings-section">
          <div class="section-title">AI 模型配置</div>
          <AIConfigPanel />
        </div>

        <div class="settings-section">
          <div class="section-title">关于</div>
          <div class="about-item clickable" @click="showChangelog = true">
            <div class="about-left">
              <span class="about-icon">📋</span>
              <span class="about-label">更新日志</span>
            </div>
            <div class="about-right">
              <span class="about-value">v1.1.0</span>
              <van-icon name="arrow" size="14" class="arrow-icon" />
            </div>
          </div>
          <div class="about-item">
            <div class="about-left">
              <span class="about-icon">📦</span>
              <span class="about-label">产品</span>
            </div>
            <span class="about-value">StudyMate 智学助手</span>
          </div>
        </div>
      </div>
    </div>
  </van-popup>
  <ChangelogModal v-model:show="showChangelog" />
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { getCurrentTheme, applyTheme } from '../utils/theme'
import ChangelogModal from './ChangelogModal.vue'
import AIConfigPanel from './AIConfigPanel.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:show'])

const currentTheme = ref('light')
const showChangelog = ref(false)

onMounted(() => {
  currentTheme.value = getCurrentTheme()
})

const switchTheme = (theme) => {
  currentTheme.value = theme
  applyTheme(theme)
}

const closeSettings = () => {
  emit('update:show', false)
}

watch(() => props.show, (val) => {
  if (val) {
    currentTheme.value = getCurrentTheme()
  }
})
</script>

<style scoped>
.settings-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary, #ffffff);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.settings-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
  margin: 0;
}

.close-btn {
  color: var(--text-secondary, #4b5563);
  cursor: pointer;
  padding: 4px;
}

.settings-content {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
}

.settings-section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary, #9ca3af);
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.theme-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  border: 2px solid var(--border-color, #e5e7eb);
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-tertiary, #f9fafb);
}

.theme-option:hover {
  border-color: var(--accent-color, #4f46e5);
}

.theme-option.active {
  border-color: var(--accent-color, #4f46e5);
  background: var(--accent-light, #eef2ff);
}

.theme-preview {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.light-preview {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
}

.dark-preview {
  background: linear-gradient(135deg, #312e81 0%, #1e1b4b 100%);
}

.theme-label {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.theme-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary, #1f2937);
}

.theme-desc {
  font-size: 12px;
  color: var(--text-tertiary, #9ca3af);
}

.check-icon {
  color: var(--accent-color, #4f46e5);
  font-size: 20px;
}

.about-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.about-item.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 0 -12px;
  padding: 12px;
  border-radius: 8px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.about-item.clickable:hover {
  background: var(--bg-tertiary, #f9fafb);
}

.about-item:last-child {
  border-bottom: none;
}

.about-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.about-icon {
  font-size: 18px;
}

.about-label {
  font-size: 14px;
  color: var(--text-primary, #1f2937);
}

.about-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.arrow-icon {
  color: var(--text-tertiary, #9ca3af);
}

.about-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, #1f2937);
}
</style>
