<template>
  <div class="model-quick-switch">
    <van-dropdown-menu active-color="#4f46e5">
      <van-dropdown-item
        v-model="currentDisplay"
        :options="switchOptions"
        @change="onSwitch"
      />
    </van-dropdown-menu>

    <Teleport to="body">
      <div
        v-if="showMenu"
        class="model-menu-mask"
        @click="showMenu = false"
      >
        <div class="model-menu" @click.stop>
          <div class="menu-header">
            <span>切换 AI 模型</span>
            <van-icon name="cross" @click="showMenu = false" />
          </div>

          <div class="menu-section">
            <div class="section-label">最近使用</div>
            <div
              v-for="item in recentModels"
              :key="`${item.provider}-${item.model}`"
              class="menu-item"
              :class="{ active: isCurrent(item) }"
              @click="switchTo(item)"
            >
              <span class="item-icon">{{ getProvider(item.provider).icon }}</span>
              <div class="item-info">
                <div class="item-name">{{ getModelDisplayName(item) }}</div>
                <div class="item-provider">{{ getProvider(item.provider).name }}</div>
              </div>
              <van-icon v-if="isCurrent(item)" name="success" class="check" />
            </div>
            <div v-if="recentModels.length === 0" class="empty-tip">
              还没有使用记录
            </div>
          </div>

          <div class="menu-footer" @click="openSettings">
            <van-icon name="setting-o" />
            <span>前往 AI 模型配置</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  PROVIDERS,
  getAIConfig,
  getProvider,
  getModelInfo,
  getCurrentModelDisplay,
  getRecentModels,
  switchToModel
} from '../utils/aiConfig'

const emit = defineEmits(['change', 'open-settings'])

// 当前显示
const currentDisplay = ref('')
const showMenu = ref(false)

// 切换选项（用于 van-dropdown）
const switchOptions = computed(() => {
  return [
    { text: `🤖 ${currentDisplay.value || '未配置'}`, value: currentDisplay.value }
  ]
})

// 最近用过的模型
const recentModels = ref([])

// 加载初始数据
const loadData = () => {
  const display = getCurrentModelDisplay()
  currentDisplay.value = display.fullName
  recentModels.value = getRecentModels()
}

const isCurrent = (item) => {
  const config = getAIConfig()
  return config.provider === item.provider && config.model === item.model
}

const switchTo = (item) => {
  switchToModel(item.provider, item.model)
  loadData()
  showMenu.value = false
  emit('change', item)
}

const onSwitch = () => {
  // 点击下拉菜单时弹出自定义菜单
  showMenu.value = true
}

const openSettings = () => {
  showMenu.value = false
  emit('open-settings')
}

const getProvider = (id) => PROVIDERS[id] || PROVIDERS.deepseek

const getModelDisplayName = (item) => {
  const model = getModelInfo(item.provider, item.model)
  return model.name || item.model
}

onMounted(() => {
  loadData()
  // 监听 storage 变化，跨页面同步
  window.addEventListener('storage', loadData)
})

onUnmounted(() => {
  window.removeEventListener('storage', loadData)
})
</script>

<style scoped>
.model-quick-switch {
  display: inline-block;
}

.model-menu-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 999999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.15s ease;
}

.model-menu {
  background: #ffffff;
  border-radius: 12px;
  width: 320px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.2s ease;
}

.menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  font-weight: 600;
}

.menu-section {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.section-label {
  font-size: 11px;
  color: #9ca3af;
  padding: 8px 12px 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s ease;
  margin: 2px 0;
}

.menu-item:hover {
  background: #f3f4f6;
}

.menu-item.active {
  background: rgba(79, 70, 229, 0.08);
  color: #4f46e5;
}

.item-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.item-name {
  font-size: 13px;
  font-weight: 500;
}

.item-provider {
  font-size: 11px;
  color: #9ca3af;
}

.check {
  color: #4f46e5;
}

.empty-tip {
  padding: 20px 12px;
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
}

.menu-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px;
  border-top: 1px solid #e5e7eb;
  font-size: 13px;
  color: #4f46e5;
  cursor: pointer;
  transition: background 0.12s ease;
}

.menu-footer:hover {
  background: rgba(79, 70, 229, 0.05);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
