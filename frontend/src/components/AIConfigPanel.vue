<template>
  <div class="ai-config-panel">
    <div class="config-header">
      <div class="current-model">
        <span class="model-icon">{{ currentDisplay.providerIcon }}</span>
        <span class="model-name">{{ currentDisplay.modelName }}</span>
        <span class="provider-name">· {{ currentDisplay.providerName }}</span>
      </div>
      <span v-if="config.apiKey" class="tag tag-success">已配置</span>
      <span v-else class="tag tag-warning">未配置</span>
    </div>

    <div class="config-form">
      <!-- 供应商选择 -->
      <div class="form-item">
        <label class="form-label">模型供应商</label>
        <div class="select-wrapper">
          <select v-model="config.provider" class="select-input" @change="onProviderChange">
            <option
              v-for="opt in providerOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.text }}
            </option>
          </select>
          <van-icon name="arrow-down" class="select-arrow" />
        </div>
      </div>

      <!-- 模型选择 -->
      <div class="form-item">
        <label class="form-label">模型</label>
        <div class="select-wrapper">
          <select v-model="config.model" class="select-input">
            <option
              v-for="opt in modelOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.text }}
            </option>
          </select>
          <van-icon name="arrow-down" class="select-arrow" />
        </div>
        <p v-if="currentModelDesc" class="model-desc">{{ currentModelDesc }}</p>
      </div>

      <!-- API Key -->
      <div class="form-item">
        <label class="form-label">
          API Key
          <span class="key-hint">{{ currentProvider.keyHint }}</span>
        </label>
        <div class="key-input-wrapper">
          <input
            v-model="config.apiKey"
            :type="showApiKey ? 'text' : 'password'"
            class="key-input"
            placeholder="请输入 API Key"
          />
          <van-icon
            :name="showApiKey ? 'eye-o' : 'closed-eye'"
            class="toggle-eye"
            @click="showApiKey = !showApiKey"
          />
        </div>
      </div>

      <!-- Base URL（仅自定义时显示） -->
      <div v-if="currentProvider.needBaseUrl" class="form-item">
        <label class="form-label">Base URL</label>
        <input
          v-model="config.baseUrl"
          class="base-url-input"
          placeholder="例如：https://api.example.com/v1"
        />
        <p class="form-tip">使用 OpenAI 兼容协议的服务地址</p>
      </div>

      <!-- 自定义模型（仅自定义时显示） -->
      <div v-if="currentProvider.needBaseUrl" class="form-item">
        <label class="form-label">自定义模型</label>
        <div class="custom-model-list">
          <div
            v-for="(model, idx) in config.customModels"
            :key="idx"
            class="custom-model-item"
          >
            <input
              v-model="model.id"
              placeholder="模型 ID"
              class="custom-input"
            />
            <input
              v-model="model.name"
              placeholder="显示名称"
              class="custom-input"
            />
            <van-icon
              name="cross"
              class="remove-icon"
              @click="removeCustomModel(idx)"
            />
          </div>
          <button class="btn-add" @click="addCustomModel">
            <van-icon name="plus" />
            添加模型
          </button>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button class="btn btn-plain" :disabled="testing" @click="testConnection">
          <van-icon name="success" v-if="!testing" />
          <span v-if="testing">测试中...</span>
          <span v-else>测试连接</span>
        </button>
        <button class="btn btn-primary" @click="saveConfig">
          <van-icon name="success" />
          保存配置
        </button>
      </div>

      <!-- 测试结果 -->
      <div v-if="testResult" class="test-result" :class="testResultClass">
        <van-icon :name="testResult.success ? 'success' : 'warning-o'" />
        <span>{{ testResult.message }}</span>
      </div>

      <!-- 安全提示 -->
      <div class="security-tip">
        <van-icon name="shield-o" />
        <span>API Key 仅保存在你的浏览器本地，不会上传到服务器</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { showToast, showSuccessToast, showFailToast } from 'vant'
import {
  PROVIDERS,
  getAIConfig,
  saveAIConfig,
  getProvider,
  getModelInfo
} from '../utils/aiConfig'
import api from '../api'

const config = reactive(getAIConfig())
const showApiKey = ref(false)
const testing = ref(false)
const testResult = ref(null)

// 供应商选项
const providerOptions = computed(() => {
  return Object.keys(PROVIDERS).map(key => ({
    text: `${PROVIDERS[key].icon} ${PROVIDERS[key].name}`,
    value: key
  }))
})

// 当前供应商
const currentProvider = computed(() => getProvider(config.provider))

// 模型选项
const modelOptions = computed(() => {
  if (config.provider === 'custom') {
    return (config.customModels || []).map(m => ({
      text: m.name || m.id,
      value: m.id
    }))
  }
  return currentProvider.value.models.map(m => ({
    text: m.name,
    value: m.id
  }))
})

// 当前模型描述
const currentModelDesc = computed(() => {
  const model = getModelInfo(config.provider, config.model)
  return model.desc || ''
})

// 当前显示
const currentDisplay = computed(() => {
  const provider = getProvider(config.provider)
  const model = getModelInfo(config.provider, config.model)
  return {
    providerName: provider.name,
    providerIcon: provider.icon,
    modelName: model.name
  }
})

// 测试结果样式
const testResultClass = computed(() => {
  return testResult.value?.success ? 'test-success' : 'test-error'
})

// 切换供应商时重置模型
const onProviderChange = (e) => {
  const newProvider = e.target.value
  if (newProvider === 'custom') {
    config.model = ''
  } else {
    // 默认选中第一个模型
    const firstModel = PROVIDERS[newProvider].models[0]
    if (firstModel) {
      config.model = firstModel.id
    }
  }
  // 自定义时填入默认 baseUrl
  if (newProvider === 'custom' && !config.baseUrl) {
    config.baseUrl = PROVIDERS.custom.baseUrl || ''
  }
}

// 添加自定义模型
const addCustomModel = () => {
  if (!config.customModels) config.customModels = []
  config.customModels.push({ id: '', name: '' })
}

// 删除自定义模型
const removeCustomModel = (idx) => {
  config.customModels.splice(idx, 1)
}

// 保存配置
const saveConfig = () => {
  if (!config.apiKey) {
    showFailToast('请先填写 API Key')
    return
  }
  if (config.provider === 'custom' && !config.baseUrl) {
    showFailToast('自定义供应商需要填写 Base URL')
    return
  }
  if (!config.model) {
    showFailToast('请选择模型')
    return
  }
  const success = saveAIConfig({ ...config })
  if (success) {
    showSuccessToast('配置已保存')
    testResult.value = null
  } else {
    showFailToast('保存失败')
  }
}

// 测试连接
const testConnection = async () => {
  if (!config.apiKey) {
    showFailToast('请先填写 API Key')
    return
  }
  if (config.provider === 'custom' && !config.baseUrl) {
    showFailToast('请填写 Base URL')
    return
  }
  if (!config.model) {
    showFailToast('请选择模型')
    return
  }

  testing.value = true
  testResult.value = null
  try {
    const baseUrl = config.provider === 'custom'
      ? config.baseUrl
      : currentProvider.value.baseUrl

    const res = await api.post('/ai/chat', {
      messages: [{ role: 'user', content: '回复"OK"即可，不要其他内容。' }],
      model: config.model,
      api_key: config.apiKey,
      base_url: baseUrl
    })
    if (res && !res.error && res.content) {
      testResult.value = {
        success: true,
        message: `连接成功！模型响应: "${res.content.substring(0, 20)}"`
      }
      showSuccessToast('连接成功')
    } else {
      testResult.value = {
        success: false,
        message: res?.message || '连接失败，请检查 API Key 和模型配置'
      }
      showFailToast('连接失败')
    }
  } catch (e) {
    console.error('测试连接失败', e)
    testResult.value = {
      success: false,
      message: '连接失败：' + (e.message || '网络错误')
    }
    showFailToast('连接失败')
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.ai-config-panel {
  background: var(--bg-tertiary, #f9fafb);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color, #e5e7eb);
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
}

.current-model {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--text-primary, #1f2937);
}

.model-icon {
  font-size: 18px;
}

.model-name {
  font-weight: 600;
}

.provider-name {
  color: var(--text-tertiary, #9ca3af);
  font-size: 12px;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.tag-success {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.tag-warning {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary, #4b5563);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.key-hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-tertiary, #9ca3af);
}

.select-wrapper {
  position: relative;
}

.select-input {
  width: 100%;
  padding: 9px 32px 9px 12px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  font-size: 13px;
  background: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1f2937);
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.select-input:focus {
  border-color: var(--accent-color, #4f46e5);
}

.select-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary, #9ca3af);
  font-size: 12px;
  pointer-events: none;
}

.key-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.key-input,
.base-url-input {
  flex: 1;
  width: 100%;
  padding: 9px 36px 9px 12px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  font-size: 13px;
  background: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1f2937);
  outline: none;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

.key-input:focus,
.base-url-input:focus {
  border-color: var(--accent-color, #4f46e5);
}

.toggle-eye {
  position: absolute;
  right: 10px;
  color: var(--text-tertiary, #9ca3af);
  cursor: pointer;
  padding: 4px;
}

.form-tip {
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  margin: 0;
}

.model-desc {
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  margin: 0;
  font-style: italic;
}

.custom-model-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.custom-model-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.custom-input {
  flex: 1;
  padding: 7px 10px;
  border: 1px solid var(--border-color, #e5e7eb);
  border-radius: 6px;
  font-size: 12px;
  background: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1f2937);
  outline: none;
}

.remove-icon {
  color: #ef4444;
  cursor: pointer;
  padding: 4px;
}

.btn-add {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px dashed var(--border-color, #d1d5db);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary, #6b7280);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-add:hover {
  border-color: var(--accent-color, #4f46e5);
  color: var(--accent-color, #4f46e5);
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-plain {
  background: var(--bg-primary, #ffffff);
  border: 1px solid var(--border-color, #d1d5db);
  color: var(--text-secondary, #4b5563);
}

.btn-plain:hover:not(:disabled) {
  border-color: var(--accent-color, #4f46e5);
  color: var(--accent-color, #4f46e5);
}

.btn-plain:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--accent-color, #4f46e5);
  color: #ffffff;
}

.btn-primary:hover {
  background: #4338ca;
}

.test-result {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 12px;
  margin-top: 4px;
}

.test-success {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.test-error {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.security-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-tertiary, #9ca3af);
  margin-top: 4px;
  padding: 8px 10px;
  background: var(--bg-secondary, #ffffff);
  border-radius: 6px;
}
</style>
