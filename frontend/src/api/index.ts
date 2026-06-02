import axios from 'axios'
import { ElMessage } from 'element-plus'
import type {
  PRReviewRequest,
  PRReviewResponse,
  PRChatRequest,
  PRChatResponse,
} from '../types/review'

const apiClient = axios.create({
  baseURL: '/',
  timeout: 300000,
})

apiClient.interceptors.request.use((config) => {
  config.headers['Authorization'] = 'Bearer mock-secret-token'
  return config
})

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const detail = error.response?.data?.detail
    const message = typeof detail === 'string'
      ? detail
      : error.message || '网络请求失败，请重试'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export const api = {
  reviewPr: (payload: PRReviewRequest): Promise<PRReviewResponse> => {
    return apiClient.post('/api/v1/pr/review', payload)
  },

  chatAboutFinding: (payload: PRChatRequest): Promise<PRChatResponse> => {
    return apiClient.post('/api/v1/pr/chat', payload)
  },
}
