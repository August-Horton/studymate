import axios from 'axios'

const MAX_RETRIES = 3
const RETRY_DELAY = 1000

let backendStatus = 'unknown'
let retryCount = 0

const api = axios.create({ 
  baseURL: import.meta.env.PROD ? 'http://localhost:8000/api' : '/api',
  timeout: 1200000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  response => {
    retryCount = 0
    backendStatus = 'healthy'
    return response.data
  },
  async error => {
    const originalRequest = error.config
    
    if (!originalRequest || retryCount >= MAX_RETRIES) {
      retryCount = 0
      backendStatus = 'failed'
      return Promise.reject(error)
    }
    
    retryCount++
    backendStatus = 'unhealthy'
    
    console.log(`请求失败，正在重试 (${retryCount}/${MAX_RETRIES})...`)
    
    await new Promise(resolve => setTimeout(resolve, RETRY_DELAY * retryCount))
    
    try {
      const response = await api(originalRequest)
      retryCount = 0
      backendStatus = 'healthy'
      return response
    } catch (err) {
      return Promise.reject(err)
    }
  }
)

export const getBackendStatus = () => backendStatus

export const resetBackendStatus = () => {
  backendStatus = 'unknown'
  retryCount = 0
}

export default api
