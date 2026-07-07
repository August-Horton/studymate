<template>
  <div id="app">
    <BackendStatus />
    <van-nav-bar title="StudyMate 智学助手" fixed>
      <template #left>
        <div class="brand-tag">
          <span class="brand-dot"></span>
          <span class="brand-text">智学</span>
        </div>
      </template>
      <template #right>
        <van-icon name="setting-o" size="20" class="settings-btn" @click="showSettings = true" />
      </template>
    </van-nav-bar>
    <div class="content">
      <van-tabs v-model:active="active" @change="onTabChange" sticky offset-top="46" :border="false" title-active-color="var(--accent-color)">
        <van-tab title="📝 笔记管理" to="/notes"></van-tab>
        <van-tab title="📖 文献管理" to="/literature"></van-tab>
        <van-tab title="📅 备考计划" to="/plans"></van-tab>
        <van-tab title="📚 课程管理" to="/courses"></van-tab>
      </van-tabs>
      <div class="page-container">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
    <SettingsDrawer v-model:show="showSettings" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BackendStatus from './components/BackendStatus.vue'
import SettingsDrawer from './components/SettingsDrawer.vue'
import { initTheme, getCurrentTheme } from './utils/theme'

const router = useRouter()
const route = useRoute()
const active = ref(0)
const showSettings = ref(false)
const currentTheme = ref('light')

onMounted(() => {
  initTheme()
  currentTheme.value = getCurrentTheme()
})

const routeToIndex = {
  '/notes': 0,
  '/literature': 1,
  '/plans': 2,
  '/courses': 3
}

if (routeToIndex[route.path] !== undefined) {
  active.value = routeToIndex[route.path]
}

const onTabChange = (index) => {
  const paths = ['/notes', '/literature', '/plans', '/courses']
  router.push(paths[index])
}

watch(() => route.path, (newPath) => {
  if (routeToIndex[newPath] !== undefined) {
    active.value = routeToIndex[newPath]
  }
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-primary, #f5f5f5);
}

.brand-tag {
  display: flex;
  align-items: center;
  gap: 6px;
}

.brand-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-color, #4f46e5);
  box-shadow: 0 0 8px var(--accent-color, #4f46e5);
}

.brand-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary, #9ca3af);
  letter-spacing: 1px;
}

.settings-btn {
  color: var(--text-primary, #1f2937);
  cursor: pointer;
  padding: 4px;
  transition: transform 0.3s ease;
}

.settings-btn:hover {
  transform: rotate(60deg);
}

.content {
  height: calc(100vh - 46px);
  margin-top: 46px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content .van-tabs {
  flex-shrink: 0;
}

.page-container {
  flex: 1;
  overflow: hidden;
}

/* 页面过渡动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* Vant Tabs 样式覆盖 */
.van-tabs {
  background: var(--bg-secondary, #ffffff);
}

.van-tabs__nav {
  background: var(--bg-secondary, #ffffff);
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.van-tabs__line {
  background-color: var(--accent-color, #4f46e5) !important;
  border-radius: 2px;
  height: 3px !important;
}

.van-tab--active {
  font-weight: 600;
}
</style>
