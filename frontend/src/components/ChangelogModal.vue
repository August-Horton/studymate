<template>
  <van-popup
    :show="show"
    position="center"
    round
    :style="{ width: '90%', maxWidth: '560px', maxHeight: '80vh' }"
    @update:show="$emit('update:show', $event)"
  >
    <div class="changelog-container">
      <div class="changelog-header">
        <div class="header-content">
          <h3 class="changelog-title">更新日志</h3>
          <p class="changelog-subtitle">记录每一次进步 ✨</p>
        </div>
        <van-icon name="cross" size="20" class="close-btn" @click="close" />
      </div>

      <div class="changelog-content custom-scroll">
        <div
          v-for="(release, index) in changelogData"
          :key="release.version"
          class="release-item"
        >
          <div class="release-header">
            <div class="version-tag" :class="release.type">
              {{ release.version }}
            </div>
            <div class="release-info">
              <div class="release-title">{{ release.title }}</div>
              <div class="release-date">{{ formatDate(release.date) }}</div>
            </div>
            <div v-if="index === 0" class="latest-badge">最新</div>
          </div>

          <div class="release-changes">
            <div
              v-for="(change, idx) in release.changes"
              :key="idx"
              class="change-item"
            >
              <div class="change-icon">{{ change.icon }}</div>
              <div class="change-content">
                <div class="change-title">{{ change.title }}</div>
                <div class="change-desc">{{ change.desc }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="changelog-footer">
        <van-button type="primary" round block @click="close">
          我知道了
        </van-button>
      </div>
    </div>
  </van-popup>
</template>

<script setup>
import { changelogData } from '../data/changelog'

defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:show'])

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}年${month}月${day}日`
}

const close = () => {
  emit('update:show', false)
}
</script>

<style scoped>
.changelog-container {
  display: flex;
  flex-direction: column;
  max-height: 80vh;
  background: var(--bg-secondary, #ffffff);
  border-radius: 16px;
  overflow: hidden;
}

.changelog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

.header-content {
  flex: 1;
}

.changelog-title {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 4px 0;
}

.changelog-subtitle {
  font-size: 13px;
  opacity: 0.85;
  margin: 0;
}

.close-btn {
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  padding: 4px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  color: white;
  transform: rotate(90deg);
}

.changelog-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.release-item {
  margin-bottom: 28px;
}

.release-item:last-child {
  margin-bottom: 0;
}

.release-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  position: relative;
}

.version-tag {
  flex-shrink: 0;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  font-family: 'Fira Code', Consolas, Monaco, monospace;
}

.version-tag.major {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
}

.version-tag.minor {
  background: linear-gradient(135deg, #10b981 0%, #14b8a6 100%);
  color: white;
}

.version-tag.patch {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
  color: white;
}

.release-info {
  flex: 1;
  min-width: 0;
}

.release-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
  margin-bottom: 2px;
}

.release-date {
  font-size: 12px;
  color: var(--text-tertiary, #9ca3af);
}

.latest-badge {
  flex-shrink: 0;
  padding: 2px 10px;
  background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
  color: white;
  font-size: 11px;
  font-weight: 600;
  border-radius: 12px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.release-changes {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-left: 8px;
}

.change-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: var(--bg-tertiary, #f9fafb);
  border-radius: 10px;
  border-left: 3px solid var(--accent-color, #4f46e5);
  transition: all 0.2s ease;
}

.change-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px var(--shadow-color, rgba(0, 0, 0, 0.08));
}

.change-icon {
  flex-shrink: 0;
  font-size: 20px;
  line-height: 1.2;
}

.change-content {
  flex: 1;
  min-width: 0;
}

.change-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
  margin-bottom: 4px;
}

.change-desc {
  font-size: 13px;
  color: var(--text-secondary, #6b7280);
  line-height: 1.5;
}

.changelog-footer {
  padding: 16px 24px 20px;
  border-top: 1px solid var(--border-color, #e5e7eb);
}

.custom-scroll::-webkit-scrollbar {
  width: 6px;
}

.custom-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scroll::-webkit-scrollbar-thumb {
  background: var(--text-tertiary, #d1d5db);
  border-radius: 3px;
}

.custom-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary, #9ca3af);
}
</style>
