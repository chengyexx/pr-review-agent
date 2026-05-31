<template>
  <div class="submit-container">
    <el-card class="main-card" shadow="hover">
      <div class="header">
        <h1 class="title">AI PR Review Assistant</h1>
        <p class="subtitle">基于 LangGraph 与多 Agent 协同的代码深度审查引擎</p>
      </div>

      <div class="input-section">
        <el-input
          v-model="prUrl"
          placeholder="请输入 GitHub PR 链接，例如: https://github.com/vuejs/core/pull/9652"
          size="large"
          clearable
          @keyup.enter="handleSubmit"
        >
          <template #prefix>
            <span class="icon-github">🐙</span>
          </template>
        </el-input>

        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ loading ? 'AI 深度分析中...' : '开始智能评审' }}
        </el-button>
      </div>

      <div class="quick-links">
        <span>试试这些开源案例：</span>
        <el-tag class="demo-tag" @click="prUrl = 'https://github.com/vuejs/core/pull/9652'">Vue.js Core</el-tag>
        <el-tag class="demo-tag" type="success" @click="prUrl = 'https://github.com/fastapi/fastapi/pull/11693'">FastAPI</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/index'

const prUrl = ref('')
const loading = ref(false)
const router = useRouter()

const handleSubmit = async () => {
  if (!prUrl.value.includes('github.com')) {
    ElMessage.warning('请输入有效的 GitHub PR 链接！')
    return
  }

  loading.value = true
  try {
    // 调用我们在 api/index.ts 中封装的接口
    const res: any = await api.submitPrReview(prUrl.value)
    ElMessage.success('PR 已成功提交，正在启动 AI 引擎...')

    // 携带返回的 task_id 跳转到详情分析页
    setTimeout(() => {
      router.push(`/review/${res.task_id}`)
    }, 1000)

  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.submit-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); /* 渐变极客背景 */
}

.main-card {
  width: 100%;
  max-width: 650px;
  border-radius: 12px;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.title {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.subtitle {
  color: #909399;
  font-size: 14px;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
}

.submit-btn {
  width: 100%;
  font-weight: bold;
}

.icon-github {
  font-size: 18px;
  margin-right: 5px;
}

.quick-links {
  font-size: 12px;
  color: #606266;
  text-align: center;
}

.demo-tag {
  cursor: pointer;
  margin-left: 8px;
  transition: all 0.3s;
}
.demo-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>