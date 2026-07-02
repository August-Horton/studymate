// AI 配置管理模块
// 支持切换多个兼容 OpenAI 协议的大模型厂商
// 配置仅保存在浏览器 localStorage，不传后端数据库

const STORAGE_KEY = 'studymate_ai_config'
const RECENT_KEY = 'studymate_ai_recent_models'

// 预设的模型供应商
export const PROVIDERS = {
  deepseek: {
    name: 'DeepSeek',
    icon: '🐋',
    baseUrl: 'https://api.deepseek.com/v1',
    models: [
      { id: 'deepseek-v4', name: 'DeepSeek-V4', desc: '最新旗舰模型，更强更智能' },
      { id: 'deepseek-chat', name: 'DeepSeek-V3', desc: '经典通用对话模型' },
      { id: 'deepseek-reasoner', name: 'DeepSeek-R1', desc: '深度推理模型' }
    ],
    keyHint: '请输入 DeepSeek API Key（以 sk- 开头）'
  },
  openai: {
    name: 'OpenAI',
    icon: '🤖',
    baseUrl: 'https://api.openai.com/v1',
    models: [
      { id: 'gpt-4o', name: 'GPT-4o', desc: '最新多模态旗舰' },
      { id: 'gpt-4o-mini', name: 'GPT-4o mini', desc: '轻量快速' },
      { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', desc: '经典款' }
    ],
    keyHint: '请输入 OpenAI API Key（以 sk- 开头）'
  },
  qwen: {
    name: '通义千问',
    icon: '☁️',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    models: [
      { id: 'qwen-plus', name: 'Qwen-Plus', desc: '平衡性能' },
      { id: 'qwen-turbo', name: 'Qwen-Turbo', desc: '极速响应' },
      { id: 'qwen-max', name: 'Qwen-Max', desc: '最强能力' }
    ],
    keyHint: '请输入阿里云 DashScope API Key（以 sk- 开头）'
  },
  zhipu: {
    name: '智谱 AI',
    icon: '🧠',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    models: [
      { id: 'glm-4-plus', name: 'GLM-4 Plus', desc: '旗舰模型' },
      { id: 'glm-4-flash', name: 'GLM-4 Flash', desc: '免费快速' },
      { id: 'glm-4-air', name: 'GLM-4 Air', desc: '轻量级' }
    ],
    keyHint: '请输入智谱 API Key'
  },
  moonshot: {
    name: 'Moonshot (Kimi)',
    icon: '🌙',
    baseUrl: 'https://api.moonshot.cn/v1',
    models: [
      { id: 'moonshot-v1-8k', name: 'Moonshot v1 (8K)', desc: '短上下文' },
      { id: 'moonshot-v1-32k', name: 'Moonshot v1 (32K)', desc: '中等上下文' },
      { id: 'moonshot-v1-128k', name: 'Moonshot v1 (128K)', desc: '超长上下文' }
    ],
    keyHint: '请输入 Moonshot API Key（以 sk- 开头）'
  },
  custom: {
    name: '自定义 (OpenAI 协议)',
    icon: '⚙️',
    baseUrl: '',
    models: [],
    keyHint: '请输入自定义服务的 API Key',
    needBaseUrl: true
  }
}

// 默认配置
const DEFAULT_CONFIG = {
  provider: 'deepseek',
  model: 'deepseek-v4-pro',
  apiKey: '',
  baseUrl: '',
  customModels: [] // 自定义模型列表
}

/**
 * 读取 AI 配置
 */
export function getAIConfig() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return { ...DEFAULT_CONFIG }
    return { ...DEFAULT_CONFIG, ...JSON.parse(stored) }
  } catch (e) {
    console.error('读取 AI 配置失败', e)
    return { ...DEFAULT_CONFIG }
  }
}

/**
 * 保存 AI 配置
 */
export function saveAIConfig(config) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config))
    addRecentModel(config.provider, config.model)
    return true
  } catch (e) {
    console.error('保存 AI 配置失败', e)
    return false
  }
}

/**
 * 获取最近用过的模型列表（最多 3 个）
 */
export function getRecentModels() {
  try {
    const stored = localStorage.getItem(RECENT_KEY)
    if (!stored) return []
    return JSON.parse(stored)
  } catch (e) {
    return []
  }
}

/**
 * 添加到最近用过
 */
function addRecentModel(provider, model) {
  try {
    const recent = getRecentModels()
    // 移除重复项
    const filtered = recent.filter(item => !(item.provider === provider && item.model === model))
    // 添加到最前面
    filtered.unshift({ provider, model, lastUsed: Date.now() })
    // 只保留 5 个
    const limited = filtered.slice(0, 5)
    localStorage.setItem(RECENT_KEY, JSON.stringify(limited))
  } catch (e) {
    console.error('保存最近模型失败', e)
  }
}

/**
 * 获取供应商信息
 */
export function getProvider(providerId) {
  return PROVIDERS[providerId] || PROVIDERS.deepseek
}

/**
 * 获取模型信息
 */
export function getModelInfo(providerId, modelId) {
  const provider = getProvider(providerId)
  if (providerId === 'custom') {
    // 自定义模型从配置中读取
    const config = getAIConfig()
    const customModel = (config.customModels || []).find(m => m.id === modelId)
    if (customModel) return customModel
    return { id: modelId, name: modelId }
  }
  const model = provider.models.find(m => m.id === modelId)
  if (model) return model
  return { id: modelId, name: modelId }
}

/**
 * 验证配置是否完整
 */
export function validateConfig(config) {
  if (!config.apiKey) {
    return { valid: false, message: '请先填写 API Key' }
  }
  if (config.provider === 'custom' && !config.baseUrl) {
    return { valid: false, message: '自定义供应商需要填写 Base URL' }
  }
  if (!config.model) {
    return { valid: false, message: '请选择模型' }
  }
  return { valid: true }
}

/**
 * 获取当前选择的模型显示名称
 */
export function getCurrentModelDisplay() {
  const config = getAIConfig()
  const provider = getProvider(config.provider)
  const model = getModelInfo(config.provider, config.model)
  return {
    providerName: provider.name,
    providerIcon: provider.icon,
    modelName: model.name,
    fullName: `${provider.name} · ${model.name}`
  }
}

/**
 * 切换到指定模型
 */
export function switchToModel(providerId, modelId) {
  const config = getAIConfig()
  config.provider = providerId
  config.model = modelId
  return saveAIConfig(config)
}
