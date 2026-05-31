// frontend/src/api/index.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建一个 Axios 实例，利用 vite 的代理解决跨域
const apiClient = axios.create({
  baseURL: '/',
  timeout: 60000 // AI 请求较慢，把超时时间设长一点
})

// 请求拦截器：自动带上我们后端的 Mock Token
apiClient.interceptors.request.use((config) => {
  // 在真实项目中这里会从 localStorage 读 token
  config.headers['Authorization'] = 'Bearer mock-secret-token'
  return config
})

// 响应拦截器：统一处理错误
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    ElMessage.error(error.response?.data?.detail || '网络请求失败，请重试')
    return Promise.reject(error)
  }
)

export const api = {
  // 提交 PR 进行审查
  submitPrReview: (github_pr_url: string) => {
    return apiClient.post('/api/v1/pr/submit', { github_pr_url })
  },
  // 轮询查询审查状态和结果
  getReviewStatus: (task_id: string) => {
    return apiClient.get(`/api/v1/pr/${task_id}/status`)
  }
}