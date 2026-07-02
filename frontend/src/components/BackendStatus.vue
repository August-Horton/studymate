<template>
  <div v-if="showNotification" class="backend-status-container">
    <div :class="['backend-status', statusClass]">
      <div class="status-content">
        <span v-if="status === 'unhealthy'" class="status-icon loading">⟳</span>
        <span v-else-if="status === 'healthy'" class="status-icon">✓</span>
        <span v-else-if="status === 'failed'" class="status-icon">✗</span>
        <span v-else class="status-icon">?</span>
        
        <div class="status-text">
          <strong>{{ statusText }}</strong>
          <p v-if="message" class="status-message">{{ message }}</p>
        </div>
        
        <div class="action-buttons">
          <button v-if="status === 'failed'" @click="handleManualRestart" class="action-btn restart-btn">
            重启后端
          </button>
          <button @click="handleRefreshFrontend" class="action-btn refresh-btn" :class="{ loading: isRefreshing }">
            {{ isRefreshing ? '刷新中...' : '刷新页面' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const status = ref('unknown')
const message = ref('')
const showNotification = ref(false)
const isRefreshing = ref(false)
let hideTimeout = null
let lastShowTime = 0
const MIN_SHOW_INTERVAL = 10000 

const statusClass = computed(() => {
  return {
    healthy: status.value === 'healthy',
    unhealthy: status.value === 'unhealthy',
    failed: status.value === 'failed',
    unknown: status.value === 'unknown'
  }
})

const statusText = computed(() => {
  switch (status.value) {
    case 'healthy':
      return '后端服务正常'
    case 'unhealthy':
      return '后端服务异常，正在尝试修复...'
    case 'failed':
      return '后端服务故障'
    default:
      return '正在检查后端状态...'
  }
})

const handleBackendStatus = (data) => {
  const now = Date.now()
  
  if (data.status === 'healthy') {
    const timeSinceLastShow = now - lastShowTime
    if (timeSinceLastShow < MIN_SHOW_INTERVAL) {
      return
    }
    lastShowTime = now
  }
  
  status.value = data.status
  message.value = data.error || ''
  
  showNotification.value = true
  
  if (hideTimeout) {
    clearTimeout(hideTimeout)
  }
  
  if (data.status === 'healthy') {
    hideTimeout = setTimeout(() => {
      showNotification.value = false
    }, 2000)
  }
}

const handleManualRestart = async () => {
  try {
    if (window.electronAPI) {
      await window.electronAPI.restartBackend()
      message.value = '正在重启后端服务...'
      status.value = 'unhealthy'
    }
  } catch (error) {
    console.error('重启后端失败:', error)
    message.value = '重启失败，请手动重启应用'
  }
}

const handleRefreshFrontend = () => {
  isRefreshing.value = true
  setTimeout(() => {
    window.location.reload()
  }, 500)
}

onMounted(() => {
  if (window.electronAPI) {
    window.electronAPI.onBackendStatus(handleBackendStatus)
    
    window.electronAPI.getBackendStatus().then(health => {
      if (health.healthy) {
        status.value = 'healthy'
        showNotification.value = false
      } else {
        status.value = 'unhealthy'
        message.value = health.error
        showNotification.value = true
      }
    }).catch(() => {
      status.value = 'unhealthy'
      message.value = '无法连接到后端服务'
      showNotification.value = true
    })
  }
})

onUnmounted(() => {
  if (window.electronAPI) {
    window.electronAPI.removeBackendStatusListener()
  }
  if (hideTimeout) {
    clearTimeout(hideTimeout)
  }
})
</script>

<style scoped>
.backend-status-container {
  position: fixed;
  top: 80px;
  right: 15px;
  z-index: 9999;
  max-width: 280px;
}

.backend-status {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 10px 14px;
  animation: slideIn 0.3s ease-out;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.backend-status.healthy {
  border-left: 3px solid #52c41a;
}

.backend-status.unhealthy {
  border-left: 3px solid #faad14;
}

.backend-status.failed {
  border-left: 3px solid #ff4d4f;
}

.backend-status.unknown {
  border-left: 3px solid #d9d9d9;
}

.status-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  font-size: 18px;
  line-height: 1;
}

.status-icon.loading {
  animation: spin 1s linear infinite;
}

.status-text {
  flex: 1;
  min-width: 0;
}

.status-text strong {
  display: block;
  margin-bottom: 2px;
  color: #333;
  font-size: 13px;
}

.status-message {
  margin: 0;
  font-size: 11px;
  color: #666;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-left: 8px;
}

.action-btn {
  border: none;
  border-radius: 3px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.2s;
  white-space: nowrap;
}

.restart-btn {
  background: #1890ff;
  color: white;
}

.restart-btn:hover {
  background: #40a9ff;
}

.refresh-btn {
  background: #f5f5f5;
  color: #666;
  border: 1px solid #d9d9d9;
}

.refresh-btn:hover {
  background: #e8e8e8;
  color: #333;
}

.refresh-btn.loading {
  opacity: 0.7;
  cursor: not-allowed;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 0.85;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
