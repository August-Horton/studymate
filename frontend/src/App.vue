<template>
  <div id="app">
    <BackendStatus />
    <van-nav-bar title="StudyMate 智学助手" fixed>
      <template #right>
        <van-icon name="setting-o" size="20" class="settings-btn" @click="showSettings = true" />
      </template>
    </van-nav-bar>
    <div class="content">
      <van-tabs v-model:active="active" @change="onTabChange">
        <van-tab title="笔记管理" to="/notes"></van-tab>
        <van-tab title="文献管理" to="/literature"></van-tab>
        <van-tab title="备考计划" to="/plans"></van-tab>
        <van-tab title="课程管理" to="/courses"></van-tab>
      </van-tabs>
      <div class="page-container">
        <router-view />
      </div>
    </div>
    <SettingsDrawer v-model:show="showSettings" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BackendStatus from './components/BackendStatus.vue'
import SettingsDrawer from './components/SettingsDrawer.vue'
import { initTheme } from './utils/theme'

const router = useRouter()
const route = useRoute()
const active = ref(0)
const showSettings = ref(false)

onMounted(() => {
  initTheme()
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

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  height: 100vh;
  overflow: hidden;
  background-color: var(--bg-primary, #f5f5f5);
  transition: background-color 0.3s ease;
}

/* Vant 导航栏主题适配 */
:root {
  --van-nav-bar-background: var(--nav-bg, #ffffff);
  --van-nav-bar-text-color: var(--nav-text, #1f2937);
  --van-nav-bar-title-text-color: var(--nav-text, #1f2937);
}

/* Vant Tabs 主题适配 */
:root {
  --van-tabs-background: var(--bg-secondary, #ffffff);
  --van-tab-text-color: var(--text-secondary, #4b5563);
  --van-tab-active-text-color: var(--accent-color, #4f46e5);
  --van-tabs-bottom-bar-color: var(--accent-color, #4f46e5);
}

.settings-btn {
  color: var(--text-primary, #1f2937);
  cursor: pointer;
  padding: 4px;
  transition: transform 0.3s ease;
}

.settings-btn:hover {
  transform: rotate(45deg);
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

.page {
  padding: 16px;
}
</style>